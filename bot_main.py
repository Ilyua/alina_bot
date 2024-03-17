
from telebot import types
import telebot
import docx2pdf
from os import environ, unlink
# import pythoncom



from docxtpl import DocxTemplate

from validators import is_valid_id_series, is_valid_id_number, is_valid_date, is_name_correct, is_regist_correct, \
    is_company_correct

bot = telebot.TeleBot('7037748695:AAHEP7oCsbraH2Z0HtPbXfG435b3dx8FPzA')
user_data = {}

# MESSAGE HANDLERS #


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.from_user.id, 
    "Добрый день, уважаемый пользователь! \n"
    "На связи первый в России чат-бот для решения юридических вопросов журналистов «Нейроюрист». \n"
    "Нажмите /help, чтобы начать.")


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(
        message.from_user.id,
        "Я все еще учусь, поэтому пока мой функционал ограничен!\n"
        "Нажмите /select и выберите интересующий Вас договор. Укажите всю нужную информацию или нажмите /reset, чтобы сбросить ввод данных.\n"
        "Получите заполненный вариант договора в формате pdf/docx.\n\n"
        "❗Нажимая /select, вы соглашаетесь на обработку персональных данных для заполнения договора.❗\n"
        "Бот не хранит ваши данные после того, как заполняет договор."
    )


@bot.message_handler(commands=['select'])
def send_selection(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button_audio_viz = types.InlineKeyboardButton(
        text='Перереработать чужое/очистить права', callback_data=f'prod_audio_viz')
    button_music_business = types.InlineKeyboardButton(
        text='Создать своё/очистить права', callback_data=f'prod_music_business')
    button_cancel = types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
    keyboard.add(button_audio_viz, button_music_business, button_cancel)

    bot.send_message(message.from_user.id, 'В зависимости от целей работы, выберите что вы хотите сделать с материалом', reply_markup=keyboard)


@bot.message_handler(commands=['reset'])
def send_reset(message):
    bot.send_message(message.from_user.id, 'Вы перестали заполнять договор.')
    bot.next_step_backend.handlers = {}


# CALLBACK HANDLERS #


@bot.callback_query_handler(func=lambda call: call.data.startswith('prod') or call.data == 'cancel')
def handle_selection_callback_query(call):
    """First keyboard"""

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button_alienation = types.InlineKeyboardButton(text='Отчуждение прав', callback_data='cont_alienation')
    button_order = types.InlineKeyboardButton(text='Авторский заказ', callback_data='cont_order')
    button_licence = types.InlineKeyboardButton(text='Лицензионное соглашение', callback_data='cont_licence')
    # button_dummy = types.InlineKeyboardButton(text='Тест', callback_data='cont_dummy')
    button_cancel = types.InlineKeyboardButton(text='Отмена', callback_data='cancel')

    match call.data:
        case 'prod_audio_viz':
            keyboard.add(button_licence)
        case 'prod_music_business':
            keyboard.add(button_order)
        case _:
            bot.answer_callback_query(call.id, 'Вы отменили выбор:(')
            return

    keyboard.add(button_alienation, button_cancel)

    bot.send_message(call.message.chat.id, 'Выберите договор:', reply_markup=keyboard)


def send_format_choice(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    but_format_docx = types.InlineKeyboardButton(text='docx', callback_data='format_docx')
    but_format_pdf = types.InlineKeyboardButton(text='pdf', callback_data='format_pdf')
    keyboard.add(but_format_docx, but_format_pdf)

    bot.send_message(message.from_user.id, 'Выберите в каком формате вы бы хотели получить документ:',
                     reply_markup=keyboard)


class UserHandler:
    def __init__(self, chat_id, scenario):
        self._scenario = scenario
        self._iter = 0
        print(f'Handler by scenario {scenario} created')
        self._chat_id = chat_id
        if len(self._scenario) > 0:
            bot.send_message(chat_id, scenario[self._iter][2])

    def handle_message(self, message):
        if self._iter < len(self._scenario):
            if self._scenario[self._iter][0](message, self._scenario[self._iter][1]):
                self._iter += 1

        if self._iter < len(self._scenario):
            bot.send_message(self._chat_id, self._scenario[self._iter][2])
            bot.register_next_step_handler(message, self.handle_message)
        else:
            send_format_choice(message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('cont') or call.data == 'cancel')
def handle_contract_callback_query(call):
    """Second keyboard"""

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None
    )

    user_data[call.message.chat.id] = {}

    match call.data:
        case 'cont_alienation':
            user_data[call.message.chat.id]['scenario'] = scenario_alienation
        case 'cont_order':
            user_data[call.message.chat.id]['scenario'] = scenario_order
        case 'cont_licence':
            user_data[call.message.chat.id]['scenario'] = scenario_licence
        # case 'cont_dummy':
        #     user_data[call.message.chat.id]['scenario'] = scenario_dummy
        case _:
            bot.answer_callback_query(call.id, 'Вы отменили выбор:(')
            del user_data[call.message.chat.id]
            return

    # try:
    #     next_handler, msg = next(user_data[call.message.chat.id]['scenario'])
    # except StopIteration:
    #     return

    user_data[call.message.chat.id]['handler'] = UserHandler(call.message.chat.id,
                                                             user_data[call.message.chat.id]['scenario'])
    # bot.send_message(call.message.chat.id, msg)
    bot.register_next_step_handler(call.message, user_data[call.message.chat.id]['handler'].handle_message)

    user_data[call.message.chat.id]['document'] = 'templates/' + call.data[5:] + '.docx'


@bot.callback_query_handler(func=lambda call: call.data.startswith('format_'))
def handle_format_file(call):
    """Last keyboard"""

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None
    )

    format = call.data
    message = call.message

    bot.send_message(message.chat.id, 
            "А вот и ваш готовый шаблон договора. Надеюсь, что я смог ускорить бюрократический процесс в редакции и облегчил вам жизнь. \n"
            "Если вам понравилась моя работа, то порекомендуйте, пожалуйста, меня вашим коллегам журналистам! Хорошего вам дня☀️")

    template = DocxTemplate(user_data[message.chat.id]['document'])
    template.render(user_data[message.chat.id])
    template.save(f'tmp/{message.chat.id}.docx')

    if format == 'format_docx':
        with open(f'tmp/{message.chat.id}.docx', 'rb') as fr:
            bot.send_document(message.chat.id, fr)
    else:
        
        docx2pdf.convert(f'tmp/{message.chat.id}.docx', f'tmp/{message.chat.id}.pdf')
        with open(f'tmp/{message.chat.id}.pdf', 'rb') as fr:
            bot.send_document(message.chat.id, fr)
        unlink(f'tmp/{message.chat.id}.pdf')
    unlink(f'tmp/{message.chat.id}.docx')

    del user_data[message.chat.id]


def get_name(message, field):
    name = message.text.strip()

    if not is_name_correct(name):
        bot.send_message(message.chat.id, 'Некорректно введено ФИО, пожалуйста, попробуйте ещё раз')
        # bot.register_next_step_handler(message, get_name)
        return False

    user_data[message.chat.id][field] = name
    return True


def get_series(message, field):
    series = message.text.strip()

    if not is_valid_id_series(series):
        bot.send_message(message.chat.id, 'Некорректно введена серия паспорта, пожалуйста, попробуйте ещё раз')
        # bot.register_next_step_handler(message, get_series)
        return False

    user_data[message.chat.id][field] = series
    return True


def get_number(message, field):
    number = message.text.strip()

    if not is_valid_id_number(number):
        bot.send_message(message.chat.id, 'Некорректно введен номер паспорта, пожалуйста, попробуйте ещё раз')
        # bot.register_next_step_handler(message, get_number)
        return False

    user_data[message.chat.id][field] = number
    return True


def get_registration(message, field):
    registration = message.text.strip()

    if not is_regist_correct(registration):
        bot.send_message(message.chat.id, 'Некорректно введена регистрация, пожалуйста, попробуйте ещё раз')
        # bot.register_next_step_handler(message, get_registration)
        return False

    user_data[message.chat.id][field] = registration
    return True


def get_company(message, field):
    company = message.text.strip()

    if not is_company_correct(company):
        bot.send_message(message.chat.id, 'Некорректно введена компания, пожалуйста, попробуйте ещё раз')
        # bot.register_next_step_handler(message, get_company)
        return False

    user_data[message.chat.id][field] = company
    return True


def get_date(message, field):
    """Always last"""

    date = message.text.strip()

    if not is_valid_date(date):
        bot.send_message(message.chat.id, 'Некорректно введена дата, пожалуйста, попробуйте ещё раз')
        # bot.register_next_step_handler(message, get_date)
        return False

    user_data[message.chat.id][field] = date
    return True


def get_issued(message, field):
    issued = message.text.strip()

    # if not is_regist_correct(issued):
    #     bot.send_message(message.chat.id, 'Некорректно введено кем выдан паспорт, пожалуйста, попробуйте ещё раз')
    #     bot.register_next_step_handler(message, get_issued)
    #     return False

    user_data[message.chat.id][field] = issued
    return True


def get_certificate_number(message, field):
    certificate = message.text.strip()

    # if not is_regist_correct(certificate):
    #     bot.send_message(message.chat.id, 'Некорректно введено кем выдан паспорт, пожалуйста, попробуйте ещё раз')
    #     bot.register_next_step_handler(message, get_certificate_number)
    #     return False

    user_data[message.chat.id][field] = certificate
    return True


def get_object(message, field):
    _object = message.text.strip()
    user_data[message.chat.id][field] = _object
    return True


def get_number_hour(message, field):
    number = message.text.strip()
    user_data[message.chat.id][field] = number
    return True


def get_number_days(message, field):
    number = message.text.strip()
    user_data[message.chat.id][field] = number
    return True


def get_object_name(message, field):
    object_name = message.text.strip()
    user_data[message.chat.id][field] = object_name
    return True


def get_award(message, field):
    award = message.text.strip()
    user_data[message.chat.id][field] = award
    return True


def get_days_contract(message, field):
    number = message.text.strip()
    user_data[message.chat.id][field] = number
    return True


def get_percent(message, field):
    percent = message.text.strip()
    user_data[message.chat.id][field] = percent
    return True


def get_reward_days(message, field):
    reward_days = message.text.strip()
    user_data[message.chat.id][field] = reward_days
    return True


def get_email(message, field):
    email = message.text.strip()
    user_data[message.chat.id][field] = email
    return True


def get_validity_period(message, field):
    validity_period = message.text.strip()
    user_data[message.chat.id][field] = validity_period
    return True


# SCENARIO


scenario_dummy = [
    (get_name, 'Вы выбрали договор чего-то там\nВведите ФИО. Требования к вводу/пример: Иванов Иван Иванович'),
    (get_series, 'Введите серию паспорта'),
    (get_number, 'Введите номер паспорта'),
    (get_registration, 'Введите регистрацию'),
    (get_company, 'Введите компанию'),
    (get_date, 'Введите дату в формате чч.мм.гггг'),
]

scenario_alienation = [
    (get_name, 'name_seller',
     'Вы выбрали договор об отчуждении исключительного права \nВведите ФИО правообладателя. Пример: Иванов Иван Иванович'),
    (get_series, 'series_1', 'Введите серию паспорта правообладателя'),
    (get_number, 'number_1', 'Введите номер паспорта правообладателя'),
    # (get_issued, 'issued_1', 'Введите кем выдан паспорт правообладателя'),
    # (get_company, 'company_seller', 'Введите название ИП правообладателя'),
    (get_certificate_number, 'certificate_number_1',
     'Введите серию свидетельства о государственной регистрации физического лица в качестве индивидуального предпринимателя (правообладателя)'),
    (get_name, 'name_buyer',
     'Введите ФИО приобретателя. Пример: Иванов Иван Иванович'),
    (get_series, 'series_2', 'Введите серию паспорта приобретателя'),
    (get_number, 'number_2', 'Введите номер паспорта приобретателя'),
    # (get_issued, 'issued_2', 'Введите кем выдан паспорт приобретателя'),
    # (get_company, 'company_buyer', 'Введите название ИП приобретателя'),
    (get_certificate_number, 'certificate_number_2',
     'Введите серию свидетельства о государственной регистрации физического лица в качестве индивидуального предпринимателя (приобретателя)'),

    # (get_object, 'object', 'Введите объект договора (сценарий, музыкальное произведение с текстом или без текста, исполнение , актерское исполнение, аудиовизуальное произведение, сайт, графика, произведение живописи/скульптуры, архитектуры, фотография и т. д.)'),
    # (get_number_hour, 'number_hour',
    #  'В течение скольких часов в случае предоставления нерабочей ссылки или некачественного файла Правообладатель обязуется предоставить новую рабочую ссылку с файлом Объекта по требованию Приобретателя?'),
    # (get_number_days, 'number_days',
    #  'В течение скольки календарных дней с момента подписания настоящего Договора Правообладатель обязан предоставить Приобретателю Объект?'),
    (get_object_name, 'object_name', 'Введите название объекта договора'),
    (get_award, 'award',
     'Размер вознаграждения Правообладателя за отчуждение исключительных прав на использование Объекта (в рублях)'),
    # (get_days_contract, 'days_contract', 'В течение скольких дней производится выплата вознаграждения?'),
    # (get_percent, 'percent', 'Укажите процент выплаты неустойки от суммы вознаграждения'),
    # (get_reward_days, 'reward_days',
    #  'В случае задержки на какое количество дней Правообладатель имеет право расторгнуть Договор в одностороннем порядке?'),
    (get_date, 'date', 'Введите дату заключения договора в формате чч.мм.гггг'),
]

scenario_order = [
    (get_name, 'name_seller',
     'Вы выбрали договор авторского заказа \nВведите ФИО Заказчика. Пример: Иванов Иван Иванович'),
    (get_series, 'series_1', 'Введите серию паспорта Заказчика'),
    (get_number, 'number_1', 'Введите номер паспорта Заказчика'),
    # (get_issued, 'issued_1', 'Введите кем выдан паспорт Заказчика'),
    # (get_company, 'company_seller', 'Введите название ИП (Заказчика)'),
    (get_certificate_number, 'certificate_number_1',
     'Введите серию свидетельства о государственной регистрации физического лица в качестве индивидуального предпринимателя (Заказчика)'),
    (get_name, 'name_contractor',
     'Введите ФИО Исполнителя. Пример: Иванов Иван Иванович'),
    (get_series, 'series_2', 'Введите серию паспорта Исполнителя'),
    (get_number, 'number_2', 'Введите номер паспорта Исполнителя'),
    # (get_issued, 'issued_2', 'Введите кем выдан паспорт Исполнителя'),
    (get_company, 'company_contractor', 'Введите название ИП Исполнителя'),
    (get_certificate_number, 'certificate_number_2',
     'Введите серию свидетельства о государственной регистрации физического лица в качестве индивидуального предпринимателя (Исполнителя)'),

    # (get_object, 'object', 'Введите объект договора (сценарий, музыкальное произведение с текстом или без текста, исполнение , актерское исполнение, аудиовизуальное произведение, сайт, графика, произведение живописи/скульптуры, архитектуры, фотография и т. д.)'),
    # (get_number_hour, 'number_hour',
    #  'В течение скольких часов в случае предоставления нерабочей ссылки или некачественного файла Исполнитель обязуется предоставить новую рабочую ссылку с файлом Объекта по требованию Заказчика?'),

    # (get_number_days, 'number_days',
    #  'В течение скольки календарных дней с момента подписания настоящего Договора Правообладатель обязан предоставить Приобретателю Объект?'),
    (get_object_name, 'object_name', 'Введите название объекта договора'),
    (get_award, 'award',
     'Сумма вознаграждения за создание Объекта и отчуждение прав на его использование составляет (в рублях)'),
    # (get_days_contract, 'days_contract',
    #  'В течение скольких дней Заказчик обязуется рассмотреть представленный Исполнителем Объект, известить Исполнителя об одобрении Объекта и подписать Акт?'),
    # (get_percent, 'percent', 'Укажите процент выплаты неустойки от суммы вознаграждения'),
    # (get_reward_days, 'reward_days',
    #  'В случае задержки на какое количество дней Правообладатель имеет право расторгнуть Договор в одностороннем порядке?'),

    # (get_validity_period, 'validity_period',
    #  'Укажите количество лет, в течение которых еще действуют условия конфиденциальности'),

    # (get_email, 'email_licensee', 'Введите адрес электронной почты Заказчика'),
    (get_date, 'date', 'Введите дату заключения договора в формате чч.мм.гггг'),
]

scenario_licence = [
    (get_name, 'name_licensor',
     'Вы выбрали лицензионный договор \nВведите ФИО лицензиара. Пример: Иванов Иван Иванович'),
    (get_series, 'series_1', 'Введите серию паспорта лицензиара'),
    (get_number, 'number_1', 'Введите номер паспорта лицензиара'),
    # (get_issued, 'issued_1', 'Введите кем выдан паспорт правообладателя'),
    # (get_company, 'company_licensor', 'Введите название ИП лицензиара'),
    (get_certificate_number, 'certificate_number_1',
     'Введите серию свидетельства о государственной регистрации физического лица в качестве индивидуального предпринимателя (лицензиара)'),
    (get_name, 'name_licensee',
     'Введите ФИО лицензиата. Пример: Иванов Иван Иванович'),
    (get_series, 'series_2', 'Введите серию паспорта лицензиата'),
    (get_number, 'number_2', 'Введите номер паспорта лицензиата'),
    # (get_issued, 'issued_2', 'Введите кем выдан паспорт лицензиата'),
    # (get_company, 'company_buyer', 'Введите название ИП лицензиата'),
    (get_certificate_number, 'certificate_number_2',
     'Введите серию свидетельства о государственной регистрации физического лица в качестве индивидуального предпринимателя (лицензиата)'),

    # (get_object, 'object', 'Введите объект договора (сценарий, музыкальное произведение с текстом или без текста, исполнение , актерское исполнение, аудиовизуальное произведение, сайт, графика, произведение живописи/скульптуры, архитектуры, фотография и т. д.)'),
    # (get_number_hour, 'number_hour',
    #  'В течение скольких часов в случае предоставления нерабочей ссылки или некачественного файла Лицензиар обязуется предоставить новую рабочую ссылку с файлом Объекта по требованию Лицензиата?'),
    # (get_number_days, 'number_days',
    #  'В течение скольки календарных дней с момента подписания настоящего Договора Лицензиар обязан предоставить Лицензиату Объект?'),
    (get_object_name, 'object_name', 'Введите название объекта договора'),
    (get_award, 'award',
     'Введите сумму вознаграждения, причитающаяся Лицензиару за передачу прав по настоящему Договору (в рублях)'),
    # (get_days_contract, 'days_contract', 'В течение скольких дней производится выплата вознаграждения?'),
    # (get_percent, 'percent', 'Укажите процент выплаты неустойки от суммы вознаграждения '),
    # (get_reward_days, 'reward_days',
    #  'В случае задержки на какое количество дней Лицензиар имеет право расторгнуть Договор в одностороннем порядке?'),
    # (get_email, 'email_licensee', 'Введите адрес электронной почты Лицензиара'),
    (get_date, 'date', 'Введите дату заключения договора в формате чч.мм.гггг'),
]

bot.polling(non_stop=True)
