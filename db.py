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
        self.cur.execute(query)
        self.conn.commit()

    def _fetch_db(self, query, args=None):
        self.cur.execute(query)
        rows = self.cur.fetchall()
        colnames = [d[0] for d in self.cur.description]
        return {'colnames': colnames,
                'rows': rows}
        self.conn.commit()

    def execute(self, query, alter=False):
        try:
            if alter:
                self._change_db(query)
                return 'База данных успешно изменена!'
            else:
                return self._fetch_db(query)
        except Exception as e:
            self.conn.rollback()
            raise e


if __name__ == '__main__':
    db = SQLQuery(DBConfig)
