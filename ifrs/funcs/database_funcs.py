import os
import pandas as pd
from sqlalchemy import inspect
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage


def read_file(file, request):
    """Чтение файла (портфеля).

    Считывает данные из портфеля, очищает и приводит типы данных к необходимым.
    В случае успеха возвращает объект класса DataFrame, иначе None.
    """
    file_extension = os.path.splitext(file.name)[1]
    excel_engine = settings.EXCEL_ENGINE[file_extension]
    file_path = os.path.join(default_storage.location, file.name)
    rcp = pd.read_excel(file_path, engine=excel_engine)
    rcp.dropna(how='all', inplace=True)
    received_rows_amount, received_columns_amount = rcp.shape
    expected_columns_amount = len(settings.FIELD_TITLES)
    if received_columns_amount != expected_columns_amount:
        message = f'File "{file.name}" was not uploaded. Invalid number of columns.'
        messages.add_message(request, messages.ERROR, message)
        return None
    elif received_rows_amount < settings.MIN_ROWS_IN_EXCEL_FILE:
        message = f'File "{file.name}" was not uploaded. Invalid number of rows.'
        messages.add_message(request, messages.ERROR, message)
        return None
    else:
        rcp.columns = settings.FIELD_TITLES
        rcp['product_id'].fillna(0, inplace=True)
        rcp.product_id = rcp.product_id.astype('object')
        received_data_types = rcp.dtypes.astype(str).to_dict()
        if all([received_data_types != data_types for data_types in settings.EXPECTED_DATA_TYPES]):
            message = f'File "{file.name}" was not uploaded. Invalid data types.'
            messages.add_message(request, messages.ERROR, message)
            return None
        elif file_extension == '.xlsb':
            rcp.overdue_duration = rcp.overdue_duration.astype('int64')
            rcp.contract_date = pd.to_datetime(
                rcp.contract_date - settings.FROM_EXCEL_TO_UNIX_TIMESTAMP_DELTA, unit='D', )
        return rcp


def save_file_to_media(file):
    """Создание временной копии файла.

    Создает временную копию файла в медиа директории для дальнейшей обработки.
    """
    media_directory = default_storage.location
    file_path = os.path.join(media_directory, file.name)
    if not os.path.exists(media_directory):
        os.makedirs(media_directory)
    with default_storage.open(file_path, 'wb+') as storage:
        for chunk in file.chunks():
            storage.write(chunk)


def get_rcp_data(rcp_name, connection):
    """Получение портфеля из БД."""
    rcp = pd.read_sql_query(f'SELECT * FROM \"{rcp_name}\"', connection)
    rcp.contract_date = pd.to_datetime(rcp.contract_date, format='%Y-%m-%d')
    return rcp


def check_table_exist(sql_engine, table_name):
    """Проверка существования таблицы в БД."""
    nonexistent_table = None
    if table_name not in inspect(sql_engine).get_table_names():
        nonexistent_table = table_name
    return nonexistent_table
