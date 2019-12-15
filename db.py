import logging
import psycopg2
from config import DBConfig


class SQLQuery:

    def __init__(self, config):
        self.conn = psycopg2.connect(user=config.username,
                                     password=config.password,
                                     database=config.database,
                                     host='localhost')
        self.cur = self.conn.cursor()  # cursor

    def _change_db(self, query):
        "Выполняет изменяющий запрос"

        self.cur.execute(query)
        self.conn.commit()

    def _fetch_db(self, query):
        """
        Выполняет неизменяющий запрос на БД. Выдает словарь, содержащий
        название колонок и данные.
        """

        self.cur.execute(query)
        rows = self.cur.fetchall()
        colnames = [d[0] for d in self.cur.description]
        self.conn.commit()
        return {'colnames': colnames,
                'rows': rows}

    def execute(self, query, alter=False):
        """
        Выполняет запрос. В случае ошибки возвращает прежнее состояние БД
        и выдает исключение, содержащее указание на ошибку.
        """

        try:
            if alter:
                self._change_db(query)
                return 'База данных успешно изменена!'
            else:
                return self._fetch_db(query)
        except Exception as e:
            self.conn.rollback()
            raise e
