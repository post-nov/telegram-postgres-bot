from db import SQLQuery
from control import Controller
from telegram_bot import TelegramBot

from config import TelegramConfig, DBConfig

if __name__ == '__main__':
    db = SQLQuery(DBConfig)
    controller = Controller(db)
    bot = TelegramBot(TelegramConfig, controller)
    bot.main()

