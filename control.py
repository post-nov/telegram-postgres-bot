import logging
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
        "Опряделяет наличие в запросе слов, которые могут изменить базу данных"

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

    def _get_stats(self):
        """
        Формирует отчет о размерах таблиц. Делает это в 2 этапа:
        1. Собирает название всех таблицы
        2. Считает количество записей в каждой таблице
        """

        query_tables = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        tables = self.db.execute(query_tables)
        tables = [r[0] for r in tables['rows']]
        query_count = "SELECT COUNT(*) FROM {}"
        tables_count = []
        for table in tables:
            # Не очень красивый участок, которого бы не было, если бы я знал
            # как выгребать эти данные одним запросом.
            # Расшифровывается, как: [данные в целом][данные, как лист][конкретный счетчик]
            rows = self.db.execute(query_count.format(table))['rows'][0][0]
            tables_count.append((table, rows))
        return {'colnames': ['Таблица', 'Записей'],
                'rows': tables_count}

    def get_stats(self, scheduled=False):
        "Возвращает отчет о размерах таблиц"

        stats = self._get_stats()
        report = generate_report(stats, scheduled)
        return report

    def get_help(self):
        return HELP_TEXT

    def get_hello(self):
        return HELLO_TEXT

    def execute_command(self, query, rightful=False):
        """
        Выполняет запрос. Аргумент rightful показывает с какими правами
        он был сделан и можно ли им изменить базу данных.
        """

        if self._is_alterable(query):
            if rightful:
                try:
                    return self.db.execute(query, alter=True)
                except Exception as e:
                    logging.error(f'Query:\n{query}\nfailed with error:\n{e}')
                    return f'Запрос сформулирован неправильно:\n{str(e)}'
            elif not rightful:
                logging.warning(f'Unauthorized attempt to change DB with:\n{query}\n')
                return '\n'.join(['У вас недостаточно прав.',
                                  'Введите /admin <Имя разработчика с большой буквы>,',
                                  'чтобы получить возможность изменять БД.'])
        else:
            try:
                query_result = self.db.execute(query)
                result = generate_table(query_result)
                return result
            except Exception as e:
                logging.error(f'Query:\n{query}\nfailed with error:\n{e}')
                return f'Запрос сформулирован неправильно:\n{str(e)}'
