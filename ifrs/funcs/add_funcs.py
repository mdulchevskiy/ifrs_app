import datetime
from ifrs.models import UploadInfo


def get_dates_for_choice_field():
    """Формирование доступных дат для формы выбора даты."""
    database = UploadInfo.objects.filter().all().order_by('-file_date')
    dates = list([rcp_object.file_date for rcp_object in database if rcp_object.file_date >= datetime.date(2018, 1, 1)])
    choices = [(date, date.strftime('%d.%m.%Y')) for date in dates]
    choices.insert(0, (None, '-'))
    return choices


def convert_timedelta_to_time(timedelta):
    """Создание объекта класса Time из объекта класса Timedelta."""
    time_object = datetime.time(
        timedelta.seconds // 3600,
        timedelta.seconds % 3600 // 60,
        timedelta.seconds % 3600 % 60,
        timedelta.microseconds, )
    return time_object


def convert_table(data, fields):
    """Преобразование данных таблицы.

    Преобразует данные из объекта класса DataFrame в объект класса Dict для удобного вывода в html.
    Возвращает объект класса Dict.
    """
    data = data.to_dict()
    data_row_numbers = list(list(data.values())[0].keys())
    new_data = [{field: data[field][row] for field in fields} for row in data_row_numbers]
    [data_dict.update({'row': data_row_numbers[i] + 1}) for i, data_dict in enumerate(new_data)]
    return new_data
