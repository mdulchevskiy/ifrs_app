import os
import subprocess
from django.conf import settings
from django.contrib import messages
from django.shortcuts import (render,
                              redirect, )
from sqlalchemy import (MetaData,
                        inspect, )
from sqlalchemy.ext.declarative import declarative_base
from ifrs.models import UploadInfo
from ifrs.funcs import (get_rcp_data,
                        convert_table, )


def rcp_page(request, rcp_name):
    sql_engine = settings.SQL_ENGINE
    connection = sql_engine.connect()
    rcp_db_table_names = inspect(sql_engine).get_table_names()
    if rcp_name not in rcp_db_table_names:
        return render(request, '404_page.html')
    rcp_info_object = UploadInfo.objects.filter(table_name=rcp_name)
    rcp_info = rcp_info_object.first()

    if request.method == 'GET':
        rcp = get_rcp_data(rcp_name, connection)
        fields = settings.FIELD_TITLES
        fields_rus = settings.FIELD_TITLES_RUS
        head_data = convert_table(rcp.head(), fields)
        tail_data = convert_table(rcp.tail(), fields)
        data_dict = {
            'titles': fields_rus,
            'head_data': head_data,
            'tail_data': tail_data,
            'info_data': rcp_info,
        }
        connection.close()
        return render(request, 'rcp_page.html', {'data': data_dict})

    if request.method == 'POST':
        save_file_flag = request.POST.get('save_file')
        delete_table_flag = request.POST.get('delete_table')

        if save_file_flag:
            rcp = get_rcp_data(rcp_name, connection)
            if not os.path.exists(settings.CHUNK_ROOT):
                os.makedirs(settings.CHUNK_ROOT)
            file_path = os.path.join(settings.CHUNK_ROOT, f'{rcp_info.table_name}.csv')
            rcp.to_csv(
                file_path,
                sep='\t',
                decimal=',',
                index=False,
                encoding='cp1251',
                header=settings.FIELD_TITLES_RUS,
            )
            subprocess.call(file_path, shell=True)

        elif delete_table_flag:
            base = declarative_base()
            metadata = MetaData(sql_engine, reflect=True)
            table = metadata.tables.get(rcp_name)
            if table is not None:
                base.metadata.drop_all(sql_engine, [table], checkfirst=True)
                rcp_info_object.delete()
                message = f'Table "{rcp_name}" successfully deleted.'
                messages.add_message(request, messages.SUCCESS, message)
                connection.close()
                return redirect('home_page')

        connection.close()
        return redirect(f'{rcp_name}', )
