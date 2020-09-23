import pandas as pd
import numpy as np
from functools import reduce
from dateutil.relativedelta import relativedelta
from ifrs.funcs import check_table_exist


def get_nonexistent_tables_pd(report_date, sql_engine):
    """Функция для получения отсутствующих портфелей для расчета PD."""
    nonexistent_tables = []
    for k in range(12, 0, -1):
        current_date = report_date + relativedelta(months=-k + 1)
        past_date = current_date + relativedelta(months=-1)
        dates = [current_date, past_date]
        for date in dates:
            rcp_db_name = date.strftime('RCP_%d.%m.%Y')
            if check_table_exist(sql_engine, rcp_db_name):
                nonexistent_tables.append(rcp_db_name)
    nonexistent_tables = set(nonexistent_tables)
    return nonexistent_tables


def pd_calculation(report_date, sql_engine):
    connection = sql_engine.connect()
    loan_programs = {
        'Автокредит': 'contract_type == "Автокредит"',
        'Кредит на недвижимость': '(contract_type == "Ипотека" or contract_type == "НедвПрч" '
                                  'or contract_type == "НедвСтр" or contract_type == "НедвПок")',
        'Потребительское кредитование': '(contract_type == "Займ" or contract_type == "Потреб")',
        'Delay': 'contract_type == "DELAY"',
        'Кредит Delay': 'contract_type == "Кред.DELAY"',
        'Банковские карты': 'contract_type == "Овердрафт"',
    }
    prob_def = {}
    report_pd = {}

    for k in range(12, 0, -1):
        current_date = report_date + relativedelta(months=-k + 1)
        past_date = current_date + relativedelta(months=-1)
        dates = [current_date, past_date]
        if k == 12:
            data = []
            for date in dates:
                rcp_db_name = date.strftime('RCP_%d.%m.%Y')
                rcp = pd.read_sql_query(f'SELECT * FROM "{rcp_db_name}"', connection)
                rcp.contract_date = pd.to_datetime(rcp.contract_date, format='%Y-%m-%d')
                data.append(rcp)
        else:
            rcp_db_name = current_date.strftime('RCP_%d.%m.%Y')
            rcp = pd.read_sql_query(f'SELECT * FROM "{rcp_db_name}"', connection)
            rcp.contract_date = pd.to_datetime(rcp.contract_date, format='%Y-%m-%d')
            data = data[::-1]
            data[0] = rcp

        for program_name, program_query in loan_programs.items():
            df_report, df_past = map(lambda x: x.query(f'{program_query}'), data)
            df_report = df_report[['contract_number', 'overdue_duration']]
            df_past = df_past[['contract_number', 'overdue_duration']]
            pd_data = pd.merge(df_past, df_report, left_index=True, on='contract_number', how='left')
            pd_data.fillna(0, inplace=True)
            pd_data['month_length'] = pd_data['overdue_duration_y'] - pd_data['overdue_duration_x']
            pd_data = pd_data[pd_data['month_length'] <= 33]
            ranges = ((0, 0), (1, 30), (31, 60), (61, 90), (91, float('inf')))
            matrix = []
            for i in ranges[:-1]:
                row = []
                for j in ranges:
                    row.append(sum(
                        (pd_data.overdue_duration_x >= i[0]) & (pd_data.overdue_duration_x <= i[1]) &
                        (pd_data.overdue_duration_y >= j[0]) & (pd_data.overdue_duration_y <= j[1])
                    ))
                # переход к долям для делея осуществляется позже.
                if program_name != 'Delay' and program_name != 'Кредит Delay':
                    row = list(map(lambda x: x / (sum(row) if sum(row) != 0 else 1), row))
                matrix.append(row)
            matrix.append([0, 0, 0, 0, 1])

            # расчет матриц перехода для программ "Delay" и "Кредит Delay" осуществляется раздельно,
            # но в итоге под программой "Delay" будет пониматься их сумма.
            if program_name == 'Delay' or program_name == 'Кредит Delay':
                pd_year = prob_def.get('Delay') or {}
                part_of_delay = pd_year.get(13 - k)
                delay_exist = False if part_of_delay is None else True
                matrix = np.array(matrix) if not delay_exist else part_of_delay + np.array(matrix)
                pd_month = {13 - k: matrix}
                pd_year.update(pd_month)
                prob_def['Delay'] = pd_year
            else:
                pd_month = {13 - k: np.array(matrix)}
                pd_year = prob_def.get(program_name) or {}
                pd_year.update(pd_month)
                prob_def[program_name] = pd_year

        pd_delay = prob_def.get('Delay').get(13 - k)
        prob_def['Delay'][13 - k] = np.array(
            [list(map(lambda x: x / (sum(row) if sum(row) != 0 else 1), row)) for row in pd_delay])

    for program, pd_year in prob_def.items():
        pd_data = [np.array(pd_year[k]) for k in range(1, 13)]
        program_pd = pd.DataFrame(reduce(lambda a, b: a.dot(b), pd_data),
                                  index=['0', '1-30', '31-60', '61-90', '90+'],
                                  columns=['0', '1-30', '31-60', '61-90', '90+'], )
        report_pd[program] = program_pd['90+']
    connection.close()
    return report_pd
