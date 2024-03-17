from datetime import datetime


def is_name_correct(name):
    digits = '0123456789'

    for digit in digits:
        if name.count(digit) > 0:
            return False

    words = name.split()

    for word in words:
        if word[0].islower():
            return False

    return True


def is_valid_id_series(id_series):
    if not id_series.isdigit() or len(id_series) != 4:
        return False

    return True


def is_valid_id_number(id_number):
    if not id_number.isdigit() or len(id_number) != 6:
        return False

    return True


def is_regist_correct(regist):
    words = regist.split()

    for word in words:
        if word[0].islower():
            return False

    return True


def is_company_correct(company):

    return True


def is_valid_date(date):
    try:
        datetime.strptime(date, '%d.%m.%Y')  # здесь был большой фрагмент кода, а теперь одна строчка...
        return True
    except ValueError:
        return False