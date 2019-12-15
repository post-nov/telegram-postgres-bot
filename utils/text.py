from datetime import datetime


HELP_TEXT = '\n'.join([
    'Тестовое задание для компании "Тензор"',
    '',
    'Команды:',
    '/help: отобразить это сообщение',
    '/schedule <минуты>: включить запланированные отчеты каждые N минут',
    '/stop: отключить запланированные отчеты',
    '/now: получить внеплановый отчет',
    '<SQL запрос>: выполнить запрос на БД с отображением результатов'
])


HELLO_TEXT = '\n'.join([
    'Тестовое задание для компании "Тензор"',
    '',
    'Разработано @post_nov',
    'Репозиторий на GitHub:',
    'github.com/post-nov/telegram-postgres-bot/',
    '',
    'Бот может:',
    '1. Выдавать отчет о состоянии базы данных каждые N минут (периодичность указывает пользователь)',
    '2. Выдавать отчет о состоянии базы данных по требованию пользователя',
    '3. Выполнять произвольный запрос на базу данных с отображением результата',
    'Чтобы узнать список доступных команд, введите /help'
])


def generate_table(data):
    """
    Создает относительно компактную таблицу формата:
    # | column1 | column2
    1 | val | val
    """

    head = ' | '.join(['#'] + data['colnames'])
    rows = []
    for num, row in enumerate(data['rows'], start=1):
        rows.append(' | '.join([str(num)] + [str(i) for i in row]))
    return '\n'.join([head]+rows)


def generate_report(stats, scheduled=False):
    "Переводит данные о состоянии БД в удобный отчет"

    if scheduled:
        head = "Запланированный отчет\n"
    else:
        head = "Внеплановый отчет\n"

    time = datetime.now().strftime('%d/%m/%Y  %H:%M')
    time_head = 'Данные актуальны на {}\n'.format(time)

    total_records = sum([rows[1] for rows in stats['rows']])
    total_head = "Всего записей в таблице: {}\n".format(total_records)

    table = generate_table({'colnames': ['Таблица', 'Записей'],
                            'rows': stats['rows']})

    return head+total_head+time_head+table


def divide_long_message(long_text, max_chars):
    """
    Делит длинный текст на отрезки, не превышающие максимального значения.
    Деление происходит по знаку новой строки, чтобы строки не расползалась
    на несколько отрезков
    """

    separated_text = []
    start = 0
    while True:
        end_index = long_text.rfind('\n', start, (start+max_chars))
        if end_index == -1 or end_index == start:
            separated_text.append(long_text[start:])
            break
        separated_text.append(long_text[start:end_index].strip())
        start = end_index

    return separated_text
