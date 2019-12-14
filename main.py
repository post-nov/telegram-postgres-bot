import logging
from db import SQLQuery
from control import Controller
from telegram_bot import TelegramBot

from config import TelegramConfig, DBConfig

logging.basicConfig(filename='log',
                    format='%(asctime)s - %(message)s',
                    level=logging.INFO)

if __name__ == '__main__':
    db = SQLQuery(DBConfig)
    controller = Controller(db)
    bot = TelegramBot(TelegramConfig, controller)
    bot.main()
