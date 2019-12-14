import os


class TelegramConfig:
    token = os.environ.get('TENSOR_TEST_TG_TOKEN')
    proxy_url = os.environ.get('TENSOR_TEST_TG_PROXY_URL')
    username = os.environ.get('TENSOR_TEST_TG_USERNAME')
    password = os.environ.get('TENSOR_TEST_TG_PASSWORD')
    admin_pass = os.environ.get('TENSOR_TEST_TG_ADMIN_PASS')


class DBConfig:
    username = os.environ.get('TENSOR_TEST_DB_USERNAME')
    password = os.environ.get('TENSOR_TEST_DB_PASSWORD')
    database = os.environ.get('TENSOR_TEST_DB_NAME')
