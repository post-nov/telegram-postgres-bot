import psycopg2
from config import DBConfig


class SQLQuery:

    def __init__(self, config):
        self.conn = psycopg2.connect(user=config.username,
                                     password=config.password,
                                     database=config.database,
                                     host='localhost')
        self.cur = self.conn.cursor()  # cursor

    def _change_db(self, query, args=None):
        self.cur.execute(query, args)
        self.conn.commit()

    def _fetch_db(self, query, args=None):
        if args:
            self.cur.execute(query, args[0])
        else:
            self.cur.execute(query)
        # results = [r[0] for r in self.cur.fetchall()]
        rows = self.cur.fetchall()
        colnames = [d[0] for d in self.cur.description]
        return {'colnames': colnames,
                'rows': rows}
        self.conn.commit()

    def execute(self, query, args=None, alter=False):
        try:
            if alter:
                self._change_db(query, args=None)
                return 'База данных успешно изменена!'
            else:
                return self._fetch_db(query, args=None)
        except Exception as e:
            self.conn.rollback()
            return e


if __name__ == '__main__':
    db = SQLQuery(DBConfig)
