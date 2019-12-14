from utils.text import (
    generate_table,
    generate_report,
    HELP_TEXT,
    HELLO_TEXT,
)


class Controller:

    def __init__(self, db):
        self.db = db

    def _is_alterable(self, query):
        stop_words = {
            'CREATE',
            'INSERT',
            'DROP',
            'TRUNCATE',
            'ALTER',
            'SET',
            'UPDATE',
            'DELETE',
        }
        for word in query.split():
            if word.upper() in stop_words:
                return True
        else:
            return False

    def _get_list_of_tables(self):
        query = """
        SELECT
            table_name
        FROM
            information_schema.tables
        WHERE
            table_schema = 'public'
        """
        tables = self.db.execute(query)
        return tables['rows']

    def _get_stats(self):
        tables = [r[0] for r in self._get_list_of_tables()]
        query = """
        SELECT
            COUNT(*)
        FROM
            {}
        """
        tables_count = []
        for table in tables:
            # Немного уродливо получилось с этим [1][0][0],
            # но это уникальная функция с уникальной формой
            # выдачи данных, поэтому ради нее одной ставить костыли
            # в других местах нет смысла.
            # По сути,  это она расшифровывается, как:
            # [данные в целом][данные, как лист][конкретный счетчик]
            rows = self.db.execute(query.format(table))['rows'][0][0]
            tables_count.append((table, rows))
        return {'colnames': ['Таблица', 'Записей'],
                'rows': tables_count}

    def get_stats(self, scheduled=False):
        stats = self._get_stats()
        report = generate_report(stats, scheduled)
        return report

    def get_help(self):
        return HELP_TEXT

    def get_hello(self):
        return HELLO_TEXT

    def execute_command(self, query, rightful=None):
        if self._is_alterable(query):
            if rightful:
                try:
                    return self.db.execute(query, alter=True)
                except TypeError as e:
                    return f'Запрос сформулирован неправильно:\n{str(e)}'
            elif not rightful:
                return '\n'.join(['У вас недостаточно прав.',
                                  'Введите /admin <Имя разработчика с большой буквы>,',
                                  'чтобы получить возможность изменять БД.'])
        else:
            try:
                query_result = self.db.execute(query)
                result = generate_table(query_result)
                return result
            except TypeError as e:
                return f'Запрос сформулирован неправильно:\n{str(e)}'
