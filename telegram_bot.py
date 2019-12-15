import logging
import time

import telegram
import telegram.bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    messagequeue as mq,
)
from telegram.error import (
    TelegramError,
    Unauthorized,
    BadRequest,
    TimedOut,
    ChatMigrated,
    NetworkError
)
from telegram.utils.request import Request

from control import Controller
from config import TelegramConfig
from utils.text import divide_long_message


class MQBot(telegram.bot.Bot):
    '''A subclass of Bot which delegates send method handling to MQ'''

    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).send_message(*args, **kwargs)


class TelegramBot:

    def __init__(self, configs, control):

        msg_queue = mq.MessageQueue(all_burst_limit=3, all_time_limit_ms=3000)
        request = Request(con_pool_size=8,
                          proxy_url=configs.proxy_url,
                          urllib3_proxy_kwargs={
                              'username': configs.username,
                              'password': configs.password,
                          })
        bot = MQBot(configs.token, request=request, mqueue=msg_queue)

        self.updater = Updater(
            # token=configs.token,
            bot=bot,
            use_context=True
        )
        self.dispatcher = self.updater.dispatcher
        self.control = control  # Controller to access to db

        self.admin_pass = configs.admin_pass
        self.admins = set()
        self.users = set()

    def start(self, update, context):
        logging.warning(f'{update.effective_user.username} typed /start')
        if update.effective_user.username not in self.users:
            logging.warning(f'NEW USER JOINED US:\n{update.effective_user.__dict__}')
            self.users.add(update.effective_user.username)
        message = self.control.get_hello()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message)

    def help(self, update, context):
        logging.warning(f'{update.effective_user.username} typed /help')
        message = self.control.get_help()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message)

    def error(self, update, context):
        message = 'Что-то пошло не так. Администратор был уведомлен об ошибке'
        try:
            raise context.error
        except BadRequest as e:
            logging.error(f'{update.effective_user.username} caused error:{e}')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message)
        except TimedOut as e:
            logging.error(f'{update.effective_user.username} caused error:{e}')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message)
        except NetworkError as e:
            logging.error(f'{update.effective_user.username} caused error:{e}')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message)
        except TelegramError as e:
            logging.error(f'{update.effective_user.username} caused error:{e}')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message)

    def admin(self, update, context):
        if update.effective_user.id in self.admins:
            message = 'У вас уже есть права на изменение БД'
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message,
                                     parse_mode=telegram.ParseMode.MARKDOWN)
        elif context.args:
            if self.admin_pass == context.args[0]:
                logging.warning(f'{update.effective_user.username} received admin rights')
                new_admin = update.effective_user.id
                self.admins.add(new_admin)
                message = 'Поздравляю! Теперь вы можете изменять БД'
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=message,
                                         parse_mode=telegram.ParseMode.MARKDOWN)

            else:
                logging.warning(
                    f'{update.effective_user.username} failed at receiving admin rights using {context.args}')
                message = 'Вы не знаете имени разработчика'
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=message,
                                         parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            logging.warning(
                f'{update.effective_user.username} typed /admin command without args')
            message = 'Правильно:\n/admin <Имя разработчика с большой буквы>'
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message,
                                     parse_mode=telegram.ParseMode.MARKDOWN)

    def query(self, update, context):
        query = update.message.text
        logging.warning(f'{update.effective_user.username} queued:\n"{query}"')
        if update.effective_user.id in self.admins:
            result = self.control.execute_command(query, rightful=True)
        else:
            result = self.control.execute_command(query)

        max_chars = telegram.constants.MAX_MESSAGE_LENGTH
        if len(result) >= max_chars:
            if 'result' in context.chat_data:
                del context.chat_data['result']

            result = divide_long_message(result, max_chars)
            first_part = result.pop(0)
            context.chat_data['result'] = result

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=first_part)
            message = '\n'.join([
                'Результат слишком большой.',
                'Попробуйте его ограничить, или введите /continue, чтобы получить его целиком.',
                'Сообщения будут выводиться раз в секунду, и это может занять несколько минут.',
                'Все введенные команды будут обработаны по окончанию вывода.'
            ])
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=result)

    def _continue_query(self, update, context):
        if 'result' in context.chat_data:
            logging.warning(f'{update.effective_user.id} locked bot')
            for part in context.chat_data['result']:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=part)
                time.sleep(1)  # Очень плохой фикс. ОЧЕНЬ плохой.
                # Исправится, как только я разберусь, почему
                # у не работает установки из MessageQueue
            logging.warning(f'{update.effective_user.id} UNlocked bot')
        else:
            message = 'У вас нет больших запросов на выдачу'
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message)

    def requested_report(self, update, context):
        logging.warning(f'{update.effective_user.username} - requested report')
        report = self.control.get_stats()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=report)

    def scheduled_report(self, update, context):
        try:
            freq = int(context.args[0])
            if freq <= 0:
                message = 'Правильно:\n/schedule <*положительное* число>'
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=message,
                                         parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                if 'job' in context.chat_data:
                    old_schedule = context.chat_data['job']
                    old_schedule.schedule_removal()

                new_schedule = context.job_queue.run_repeating(self._scheduled_report,
                                                               freq*60,
                                                               context=update.effective_chat.id)
                context.chat_data['job'] = new_schedule
                logging.warning(
                    f'{update.effective_user.username} scheduled report every {freq} minutes')

                message = '\n'.join(['Отчеты по расписанию включены.',
                                     'Первый отчет будет через {} минут, '
                                     'после чего будет повторяться с указанной периодичностью.',
                                     '',
                                     'Чтобы изменить периодичность, введите:',
                                     '/schedule <минуты>.',
                                     'Чтобы отключить функционал, введите:',
                                     '/stop'])
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=message.format(freq))

        except (IndexError, ValueError):
            logging.warning(
                f'{update.effective_user.username} failed at scheduling report using "{context.args}"')
            message = '/schedule <*число*>'
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=message,
                                     parse_mode=telegram.ParseMode.MARKDOWN)

    def _scheduled_report(self, context):
        logging.warning(f'{context.job.context} - scheduled report')
        report = self.control.get_stats(scheduled=True)
        context.bot.send_message(chat_id=context.job.context,
                                 text=report)

    def stop_report(self, update, context):
        chat_id = update.effective_chat.id
        if 'job' in context.chat_data:
            schedule = context.chat_data['job']
            schedule.schedule_removal()
            logging.warning(f'{update.effective_user.username} disabled scheduled report')
            message = '\n'.join(['Отчеты по расписанию отключены.',
                                 'Чтобы включить введите:',
                                 '/schedule <периодичность в минутах>'])
            context.bot.send_message(chat_id=chat_id,
                                     text=message,
                                     parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            message = '\n'.join(['Чтобы отключить что-то, надо сначала включить что-то.',
                                 'Команда для включения:',
                                 '*"/schedule <периодичность в минутах>"*'])
            context.bot.send_message(chat_id=chat_id,
                                     text=message,
                                     parse_mode=telegram.ParseMode.MARKDOWN)

    def handle_handlers(self):
        handlers = [
            CommandHandler('start', self.start),
            CommandHandler('help', self.help),
            CommandHandler('now', self.requested_report),
            CommandHandler('schedule', self.scheduled_report,
                           pass_args=True,
                           pass_chat_data=True,
                           pass_job_queue=True),
            CommandHandler('stop', self.stop_report),
            MessageHandler(Filters.text, self.query),
            CommandHandler('continue', self._continue_query),
            CommandHandler('admin', self.admin),
        ]

        self.dispatcher.add_error_handler(self.error)
        for handler in handlers:
            self.dispatcher.add_handler(handler)

    def main(self):
        self.handle_handlers()
        self.updater.start_polling()


if __name__ == '__main__':
    bot = TelegramBot(TelegramConfig)
    bot.main()
