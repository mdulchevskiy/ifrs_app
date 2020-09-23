import os
from sqlalchemy import (inspect,
                        MetaData, )
from sqlalchemy.ext.declarative import declarative_base
from django.conf import settings
from ifrs.models import UploadInfo
from ifrs.funcs.database_funcs import check_table_exist


def remove_chunk():
    """Очистка мусора.

    Функция выполняется единожды при запуске сайта.
    Очищает директории "/chunk" и "/media" от файлов.
    """
    dirs = (settings.CHUNK_ROOT, settings.MEDIA_ROOT)
    for directory in dirs:
        if os.path.exists(directory):
            chunk_list = os.listdir(directory)
            for chunk in chunk_list:
                chunk_path = os.path.join(directory, chunk)
                os.remove(chunk_path)


def sync_databases():
    """Синхронизация баз данных.

    Функция выполняется единожды при запуске сайта.
    Синхронизирует портфели и их логи (ifrs_uploadinfo) в случае расхождений.
    Под синхронизацией понимается удаление разницы в записях имен таблиц.
    """
    # проверяет наличие базы данных.
    check_db = os.path.exists(os.path.join(settings.BASE_DIR, f'{settings.RCP_DATABASE_NAME}.sqlite3'))
    if check_db:
        table_name = f'{UploadInfo._meta.app_label}_{str(UploadInfo.__name__).lower()}'
        # проверяет наличие таблицы логов в базе данных.
        if not check_table_exist(settings.SQL_ENGINE, table_name):
            sql_engine = settings.SQL_ENGINE
            ifrs_db = UploadInfo.objects.filter().all()
            # получает список всех загруженных портфелей из базы данных (таблиц, начинающихся на "RCP").
            rcp_db_table_names = {name for name in inspect(sql_engine).get_table_names() if name.startswith('RCP')}
            # получает список всех загруженных потрфелей из таблицы логов.
            ifrs_db_table_names = {obj.table_name for obj in ifrs_db}
            # получает разницу имен в списках загруженных портфелей.
            rcp_extra = rcp_db_table_names.difference(ifrs_db_table_names)
            ifrs_extra = ifrs_db_table_names.difference(rcp_db_table_names)
            # удаляет портфели из базы данных.
            base = declarative_base()
            metadata = MetaData(sql_engine, reflect=True)
            table_list = []
            for table_name in rcp_extra:
                table = metadata.tables.get(table_name)
                if table is not None:
                    table_list.append(table)
            if table_list:
                base.metadata.drop_all(sql_engine, table_list, checkfirst=True)
            # удаляет логи загрузки портфелей из таблицы логов.
            for table_name in ifrs_extra:
                UploadInfo.objects.filter(table_name=table_name).delete()
