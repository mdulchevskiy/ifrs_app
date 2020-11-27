import os
import pandas as pd
from datetime import datetime
from sqlalchemy import inspect
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.shortcuts import (render,
                              redirect, )
from ifrs.forms import (UploadForm,
                        DateChoiceForm, )
from ifrs.models import (UploadInfo,
                         IFRSData, )
from ifrs.funcs import (read_file,
                        save_file_to_media,
                        check_table_exist,
                        ccf_calculation,
                        pd_calculation,
                        lgd_calculation,
                        get_nonexistent_tables_pd,
                        get_nonexistent_tables_lgd,
                        get_nonexistent_tables_ccf,
                        convert_timedelta_to_time, )


def home_page(request):
    sql_engine = settings.SQL_ENGINE

    if request.method == 'GET':
        upload_form = UploadForm()
        date_choice_form = DateChoiceForm()
        database_content = UploadInfo.objects.filter().all().order_by('file_date')
        return render(request, 'home_page.html', {
            'upload_form': upload_form,
            'date_choice_form': date_choice_form,
            'database': database_content,
        })

    elif request.method == 'POST':
        upload_file_flag = request.POST.get('upload_file_flag')
        calculate_flag = request.POST.get('calculate_flag')

        if upload_file_flag:
            upload_form = UploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                start_upload_time = datetime.now()
                file = upload_form.cleaned_data['upload_file']
                file_db_name = os.path.splitext(file.name)[0].replace(' ', '_')
                exist_table_names = inspect(sql_engine).get_table_names()
                if file_db_name in exist_table_names:
                    message = f'File "{file.name}" already uploaded.'
                    messages.add_message(request, messages.WARNING, message)
                else:
                    save_file_to_media(file)
                    rcp = read_file(file, request)
                    if rcp is not None and check_table_exist(sql_engine, file_db_name):
                        connection = sql_engine.connect()
                        rcp.to_sql(file_db_name, connection, index=False)
                        uploading_time = datetime.now() - start_upload_time
                        UploadInfo.objects.create(
                            table_name=file_db_name,
                            table_size=f'{rcp.shape[0]:,} x {rcp.shape[1]}',
                            file_name=file.name,
                            file_type=os.path.splitext(file.name)[1],
                            file_date=datetime.strptime(os.path.splitext(file.name)[0].split(' ')[1], '%d.%m.%Y'),
                            uploading_time=convert_timedelta_to_time(uploading_time), )
                        connection.close()
                        message = f'File "{file.name}" successfully uploaded.'
                        messages.add_message(request, messages.SUCCESS, message)
                    file_path = os.path.join(default_storage.location, file.name)
                    os.remove(file_path)
            else:
                message = list(upload_form.errors.values())[0][0]
                messages.add_message(request, messages.WARNING, message)

        if calculate_flag:
            pd.options.mode.chained_assignment = None
            report_ccf, report_pd, report_lgd = None, None, None
            date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d')
            str_date = date.strftime('%d.%m.%Y')
            data_object = IFRSData.objects.filter(date=date)
            ifrs_comp = request.POST.get('ifrs_comp')
            message = None

            if ifrs_comp == 'ccf':
                nonexistent_tables = get_nonexistent_tables_ccf(date, sql_engine)
                if not nonexistent_tables:
                    report_ccf = ccf_calculation(date, sql_engine)
                    message = {1: f'CCF on {str_date} successfully calculated.'}
                else:
                    tables = sorted(nonexistent_tables, key=lambda x: datetime.strptime(x[4:], "%d.%m.%Y"))
                    message = {0: f'CCF on {str_date} cannot be calculated. The following tables are missing: '
                                  f'{", ".join(tables)}'}

            elif ifrs_comp == 'lgd':
                nonexistent_tables = get_nonexistent_tables_lgd(date, sql_engine)
                if not nonexistent_tables:
                    report_lgd = lgd_calculation(date, sql_engine)
                    message = {1: f'LGD on {str_date} successfully calculated.'}
                else:
                    tables = sorted(nonexistent_tables, key=lambda x: datetime.strptime(x[4:], "%d.%m.%Y"))
                    message = {0: f'LGD on {str_date} cannot be calculated. The following tables are missing: '
                                  f'{", ".join(tables)}'}

            elif ifrs_comp == 'pd':
                nonexistent_tables = get_nonexistent_tables_pd(date, sql_engine)
                if not nonexistent_tables:
                    report_pd = pd_calculation(date, sql_engine)
                    message = {1: f'PD on {str_date} successfully calculated.'}
                else:
                    tables = sorted(nonexistent_tables, key=lambda x: datetime.strptime(x[4:], "%d.%m.%Y"))
                    message = {0: f'PD on {str_date} cannot be calculated. The following tables are missing: '
                                  f'{", ".join(tables)}'}

            elif ifrs_comp == 'all':
                nonexistent_tables_ccf = get_nonexistent_tables_ccf(date, sql_engine)
                nonexistent_tables_lgd = get_nonexistent_tables_lgd(date, sql_engine)
                nonexistent_tables_pd = get_nonexistent_tables_pd(date, sql_engine)
                nonexistent_tables = nonexistent_tables_pd.union(nonexistent_tables_ccf, nonexistent_tables_lgd)
                if not nonexistent_tables:
                    report_ccf = ccf_calculation(date, sql_engine)
                    report_lgd = lgd_calculation(date, sql_engine)
                    report_pd = pd_calculation(date, sql_engine)
                    message = {1: f'PD, LGD, CCF on {str_date} successfully calculated.'}
                else:
                    tables = sorted(nonexistent_tables, key=lambda x: datetime.strptime(x[4:], "%d.%m.%Y"))
                    message = {0: f'PD, LGD, CCF on {str_date} cannot be calculated. The following tables '
                                  f'are missing: {", ".join(tables)}'}

            if message:
                message_text = message.get(1)
                if message_text:
                    messages.add_message(request, messages.SUCCESS, message_text)
                else:
                    messages.add_message(request, messages.ERROR, message.get(0))

            if not nonexistent_tables:
                if report_ccf:
                    data_object = IFRSData.objects.filter(date=date)
                    if data_object.first():
                        data_object.update(ccf_over=report_ccf['Банковские карты'])
                    else:
                        data_object.create(
                            date=date,
                            ccf_over=report_ccf['Банковские карты'], )
                if report_lgd:
                    data_object = IFRSData.objects.filter(date=date)
                    if data_object.first():
                        data_object.update(
                            lgd_auto=report_lgd['Автокредит'],
                            lgd_nedv=report_lgd['Кредит на недвижимость'],
                            lgd_potr=report_lgd['Потребительское кредитование'],
                            lgd_delay=report_lgd['Delay'],
                            lgd_over=report_lgd['Банковские карты'], )
                    else:
                        data_object.create(
                            date=date,
                            lgd_auto=report_lgd['Автокредит'],
                            lgd_nedv=report_lgd['Кредит на недвижимость'],
                            lgd_potr=report_lgd['Потребительское кредитование'],
                            lgd_delay=report_lgd['Delay'],
                            lgd_over=report_lgd['Банковские карты'], )
                if report_pd:
                    data_object = IFRSData.objects.filter(date=date)
                    if data_object.first():
                        data_object.update(
                            pd_auto_0=report_pd['Автокредит'].loc['0'],
                            pd_auto_1_30=report_pd['Автокредит'].loc['1-30'],
                            pd_auto_31_60=report_pd['Автокредит'].loc['31-60'],
                            pd_auto_61_90=report_pd['Автокредит'].loc['61-90'],
                            pd_auto_91=report_pd['Автокредит'].loc['90+'],
                            pd_nedv_0=report_pd['Кредит на недвижимость'].loc['0'],
                            pd_nedv_1_30=report_pd['Кредит на недвижимость'].loc['1-30'],
                            pd_nedv_31_60=report_pd['Кредит на недвижимость'].loc['31-60'],
                            pd_nedv_61_90=report_pd['Кредит на недвижимость'].loc['61-90'],
                            pd_nedv_91=report_pd['Кредит на недвижимость'].loc['90+'],
                            pd_potr_0=report_pd['Потребительское кредитование'].loc['0'],
                            pd_potr_1_30=report_pd['Потребительское кредитование'].loc['1-30'],
                            pd_potr_31_60=report_pd['Потребительское кредитование'].loc['31-60'],
                            pd_potr_61_90=report_pd['Потребительское кредитование'].loc['61-90'],
                            pd_potr_91=report_pd['Потребительское кредитование'].loc['90+'],
                            pd_delay_0=report_pd['Delay'].loc['0'],
                            pd_delay_1_30=report_pd['Delay'].loc['1-30'],
                            pd_delay_31_60=report_pd['Delay'].loc['31-60'],
                            pd_delay_61_90=report_pd['Delay'].loc['61-90'],
                            pd_delay_91=report_pd['Delay'].loc['90+'],
                            pd_over_0=report_pd['Банковские карты'].loc['0'],
                            pd_over_1_30=report_pd['Банковские карты'].loc['1-30'],
                            pd_over_31_60=report_pd['Банковские карты'].loc['31-60'],
                            pd_over_61_90=report_pd['Банковские карты'].loc['61-90'],
                            pd_over_91=report_pd['Банковские карты'].loc['90+'], )
                    else:
                        data_object.create(
                            date=date,
                            pd_auto_0=report_pd['Автокредит'].loc['0'],
                            pd_auto_1_30=report_pd['Автокредит'].loc['1-30'],
                            pd_auto_31_60=report_pd['Автокредит'].loc['31-60'],
                            pd_auto_61_90=report_pd['Автокредит'].loc['61-90'],
                            pd_auto_91=report_pd['Автокредит'].loc['90+'],
                            pd_nedv_0=report_pd['Кредит на недвижимость'].loc['0'],
                            pd_nedv_1_30=report_pd['Кредит на недвижимость'].loc['1-30'],
                            pd_nedv_31_60=report_pd['Кредит на недвижимость'].loc['31-60'],
                            pd_nedv_61_90=report_pd['Кредит на недвижимость'].loc['61-90'],
                            pd_nedv_91=report_pd['Кредит на недвижимость'].loc['90+'],
                            pd_potr_0=report_pd['Потребительское кредитование'].loc['0'],
                            pd_potr_1_30=report_pd['Потребительское кредитование'].loc['1-30'],
                            pd_potr_31_60=report_pd['Потребительское кредитование'].loc['31-60'],
                            pd_potr_61_90=report_pd['Потребительское кредитование'].loc['61-90'],
                            pd_potr_91=report_pd['Потребительское кредитование'].loc['90+'],
                            pd_delay_0=report_pd['Delay'].loc['0'],
                            pd_delay_1_30=report_pd['Delay'].loc['1-30'],
                            pd_delay_31_60=report_pd['Delay'].loc['31-60'],
                            pd_delay_61_90=report_pd['Delay'].loc['61-90'],
                            pd_delay_91=report_pd['Delay'].loc['90+'],
                            pd_over_0=report_pd['Банковские карты'].loc['0'],
                            pd_over_1_30=report_pd['Банковские карты'].loc['1-30'],
                            pd_over_31_60=report_pd['Банковские карты'].loc['31-60'],
                            pd_over_61_90=report_pd['Банковские карты'].loc['61-90'],
                            pd_over_91=report_pd['Банковские карты'].loc['90+'], )

        return redirect('home_page')
