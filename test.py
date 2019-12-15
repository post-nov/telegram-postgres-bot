import unittest

from config import DBConfig, TelegramConfig
from telegram_bot import TelegramBot
from db import SQLQuery
from control import Controller


class DBTestCase(unittest.TestCase):
    def setUp(self):
        self.db = SQLQuery(DBConfig)
        try:
            self.db.execute('CREATE TABLE test_table (id INT)', alter=True)
        except:
            pass

    def test_connection(self):
        query = "SELECT 1"
        result = self.db.execute(query)
        self.assertIsInstance(result, dict)

    def test_simple_correct_query(self):
        query = "SELECT * FROM test_table"
        result = self.db.execute(query)
        self.assertIsInstance(result, dict)

    def test_simple_wrong_query(self):
        query = "SELECT non_existing_colum FROM test_table"
        with self.assertRaises(Exception):
            self.db.execute(query)

    def test_altering_correct_query(self):
        query = "INSERT INTO test_table (id) VALUES (1)"
        result = self.db.execute(query, alter=True)
        self.assertEqual(result, 'База данных успешно изменена!')

    def test_altering_wrong_query(self):
        query = "INSERT INTO test_table"
        with self.assertRaises(Exception):
            self.db.execute(query, alter=True)

    def tearDown(self):
        self.db.execute('DROP TABLE test_table', alter=True)


class ControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.db = SQLQuery(DBConfig)
        try:
            self.db.execute('CREATE TABLE test_table (id INT)', alter=True)
        except:
            pass
        self.control = Controller(self.db)

    def test_hello(self):
        hello = self.control.get_hello()
        self.assertIsInstance(hello, str)

    def test_help(self):
        help = self.control.get_help()
        self.assertIsInstance(help, str)

    def test_scheduled_stats(self):
        stats = self.control.get_stats(scheduled=True)
        self.assertTrue('Запланированный отчет' in stats)

    def test_requested_stats(self):
        stats = self.control.get_stats()
        self.assertTrue('Внеплановый отчет' in stats)

    # Altering queries
    def test_correct_altering_query_as_admin(self):
        query = 'INSERT INTO test_table VALUES (1)'
        result = self.control.execute_command(query, rightful=True)
        self.assertEqual(result, 'База данных успешно изменена!')

    def test_wrong_altering_query_as_admin(self):
        query = 'DELETE * FROM test_table WHERE'
        result = self.control.execute_command(query, rightful=True)
        self.assertTrue('Запрос сформулирован неправильно' in result)

    def test_correct_altering_query_as_user(self):
        query = 'INSERT INTO test_table VALUES (2)'
        result = self.control.execute_command(query)
        self.assertTrue('У вас недостаточно прав' in result)

    def test_wrong_altering_query_as_user(self):
        query = 'INSERT INTO test_table VALUES (2)'
        result = self.control.execute_command(query)
        self.assertTrue('У вас недостаточно прав' in result)

    # Simple queries
    def test_correct_simple_query_as_admin(self):
        query = 'SELECT * FROM test_table'
        result = self.control.execute_command(query, rightful=True)
        self.assertIsInstance(result, str)

    def test_wrong_simple_query_as_admin(self):
        query = 'SELECT non_existing_colum FROM test_table'
        result = self.control.execute_command(query, rightful=True)
        self.assertIsInstance(result, str)

    def test_correct_simple_query_as_user(self):
        query = 'SELECT * FROM test_table'
        result = self.control.execute_command(query)
        self.assertIsInstance(result, str)

    def test_wrong_simple_query_as_user(self):
        query = 'SELECT non_existing_colum FROM test_table'
        result = self.control.execute_command(query)
        self.assertIsInstance(result, str)

    def tearDown(self):
        self.db.execute('DROP TABLE test_table', alter=True)


if __name__ == '__main__':
    unittest.main()
