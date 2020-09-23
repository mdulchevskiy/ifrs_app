import pandas as pd
from dateutil.relativedelta import relativedelta
from numpy import mean
from ifrs.funcs import check_table_exist


def get_nonexistent_tables_ccf(report_date, sql_engine):
    """Функция для получения отсутствующих портфелей для расчета CCF."""
    nonexistent_tables = []
    for i in range(12):
        current_date = report_date + relativedelta(months=-i * 3)
        past_date = current_date + relativedelta(months=-3)
        dates = [current_date, past_date]
        for date in dates:
            rcp_db_name = date.strftime('RCP_%d.%m.%Y')
            if check_table_exist(sql_engine, rcp_db_name):
                nonexistent_tables.append(rcp_db_name)
    nonexistent_tables = set(nonexistent_tables)
    return nonexistent_tables


def ccf_calculation(report_date, sql_engine):
    connection = sql_engine.connect()
    loan_programs = {'Банковские карты': 'contract_type == "Овердрафт"', }
    report_ccf = {}
    ccf_dict = {}

    for i in range(12):
        current_date = report_date + relativedelta(months=-i * 3)
        past_date = current_date + relativedelta(months=-3)
        dates = [current_date, past_date]
        if i == 0:
            data = []
            for date in dates:
                rcp_db_name = date.strftime('RCP_%d.%m.%Y')
                rcp = pd.read_sql_query(f'SELECT * FROM "{rcp_db_name}"', connection)
                rcp.contract_date = pd.to_datetime(rcp.contract_date, format='%Y-%m-%d')
                data.append(rcp)
        else:
            rcp_db_name = past_date.strftime('RCP_%d.%m.%Y')
            rcp = pd.read_sql_query(f'SELECT * FROM "{rcp_db_name}"', connection)
            rcp.contract_date = pd.to_datetime(rcp.contract_date, format='%Y-%m-%d')
            data = data[::-1]
            data[1] = rcp

        for program_name, program_query in loan_programs.items():
            new_data = list(map(lambda x: x.query(f'{program_query}'), data))
            for j, df in enumerate(new_data):
                df = df[['contract_number', 'credit_limit', 'debt', 'npl', 'write_off_debt']]
                df['current_default'] = 0
                df['current_default'][(df['npl'] == 'NPL') | (df['write_off_debt'] != 0)] = 1
                new_data[j] = df
            ccf_data = pd.merge(new_data[0], new_data[1], left_index=True, on='contract_number', how='left')
            ccf_data = ccf_data[(ccf_data['current_default_x'] == 1) & (ccf_data['current_default_y'] == 0)]
            ccf_data['ccf'] = ccf_data['debt_x'] / ccf_data['credit_limit_x']
            ccf_month = {i: ccf_data['ccf'].mean()}
            ccf_program = ccf_dict.get(program_name) or {}
            ccf_program.update(ccf_month)
            ccf_dict[program_name] = ccf_program

    for program_name in loan_programs:
        report_ccf[program_name] = mean([ccf for ccf in ccf_dict[program_name].values()])
    connection.close()
    return report_ccf
