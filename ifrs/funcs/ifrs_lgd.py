import pandas as pd
from numpy import mean
from itertools import filterfalse
from dateutil.relativedelta import relativedelta
from django.conf import settings
from ifrs.funcs import check_table_exist


def get_nonexistent_tables_lgd(report_date, sql_engine):
    """Функция для получения отсутствующих портфелей для расчета LGD."""
    nonexistent_tables = []
    for i in range(4):
        first_date = report_date + relativedelta(months=-3 * i)
        for j in range(4):
            second_date = first_date + relativedelta(years=-j)
            rcp_db_name = second_date.strftime('RCP_%d.%m.%Y')
            if check_table_exist(sql_engine, rcp_db_name):
                nonexistent_tables.append(rcp_db_name)
    nonexistent_tables = set(nonexistent_tables)
    return nonexistent_tables


def lgd_calculation(report_date, sql_engine):
    connection = sql_engine.connect()
    include = settings.LGD_PROGRAM_INCLUDE
    exclude = settings.LGD_PROGRAM_EXCLUDE
    comission_coefs = settings.COMISSION_COEFS
    loan_programs = {
        'Автокредит': 'contract_type == "Автокредит"',
        'Кредит на недвижимость': '(contract_type == "Ипотека" or contract_type == "НедвПрч" '
                                  'or contract_type == "НедвСтр" or contract_type == "НедвПок")',
        'Потребительское кредитование': '(contract_type == "Займ" or contract_type == "Потреб")',
        'Delay': '(contract_type == "Кред.DELAY" or contract_type == "DELAY")',
        'Банковские карты': 'contract_type == "Овердрафт"',
    }
    lgd = []
    report_lgd = {}

    for i in range(4):
        first_date = report_date + relativedelta(months=-3 * i)
        lgd_year = {}
        rcp_dict = {}
        for j in range(4):
            second_date = first_date + relativedelta(years=-j)
            rcp_db_name = second_date.strftime('RCP_%d.%m.%Y')
            rcp = pd.read_sql_query(f'SELECT * FROM "{rcp_db_name}"', connection)
            rcp.contract_date = pd.to_datetime(rcp.contract_date, format='%Y-%m-%d')
            rcp_dict[f'{second_date.year}'] = rcp

        for program_name, program_query in loan_programs.items():
            data_dict = {}
            for k, (year, rcp) in enumerate(rcp_dict.items()):
                first_criterion = rcp.query(f'npl == "NPL" and {program_query}')
                second_criterion = rcp.query(f'npl == "NO" and write_off_debt != 0 and {program_query}')
                data = pd.concat([first_criterion, second_criterion])
                data['year'] = int(year)
                data_dict[f'data_{k + 1}'] = data
            data = pd.concat(list(data_dict.values()))
            # формирует из выборки банковских карт подвыборку программ, по которым ведется работа
            # правового диалога. Для этой подвыборки будут применяться комиссионные коэффициенты.
            if program_name == 'Банковские карты':
                sample_data = data[data['product_id'].str.contains(include).fillna(False)]
                sample_data = sample_data[~sample_data['product_id'].str.contains(exclude).fillna(True)]
                data = pd.concat([data, sample_data]).drop_duplicates(keep=False)
            total_collection = 0
            collection_amount = 0

            iterations = 2 if program_name == 'Банковские карты' else 1
            for m in range(iterations):
                coefs = comission_coefs[program_name] if not m else comission_coefs['Выборочные программы']
                groupset = data.groupby('contract_number') if not m else sample_data.groupby('contract_number')
                for _, group in groupset:
                    group_size = len(group)
                    remove_group = group['total_debt'].sum() == 0 or group_size == 1 and group.iloc[0][
                        'year'] == first_date.year
                    skip_group = group['total_debt'].sum() != 0 and group_size == 1 and group.iloc[0][
                        'year'] != first_date.year
                    if skip_group:
                        total_collection += 1
                        collection_amount += 1
                    elif not remove_group:
                        df = group.copy().sort_values('year', ascending=True)
                        df['rate'] = df.iloc[0]['current_rate'] or df.iloc[0]['contract_rate']
                        df['accrued_interest'] = df['accrued_interest_balance'] + df['accrued_interest_off_balance']
                        df['debt_amount'] = df['accrued_interest'] + df['total_debt']
                        df['delta_debt'] = -(df['total_debt'] - df['total_debt'].shift(1))
                        if not m:
                            df['comission_coefs'] = df['overdue_duration'].apply(
                                lambda x: 0 if x == 0 else (
                                    coefs[0] if x <= 30 else (coefs[1] if x <= 90 else coefs[2])))
                        else:
                            df['comission_coefs'] = df['overdue_duration'].apply(
                                lambda x: 0 if x == 0 else (
                                    coefs[0] if x <= 40 else (coefs[1] if x <= 120 else coefs[2])))
                        df['adjusted_debt'] = df['delta_debt'] * (1 - df['comission_coefs'])
                        debt_amount = list(filterfalse(lambda x: bool(x) is False, df['debt_amount']))[0]
                        df['collection'] = df['adjusted_debt'] / debt_amount * (
                                    1 / (1 + (df['rate'] / 100)) ** (df['year'] - df['year'].iloc[0]))
                        df['collection'] = df['collection'].apply(lambda x: 0 if x < 0 else x)
                        total_collection += df['collection'].sum()
                        collection_amount += 1
            lgd_year[program_name] = 1 - total_collection / collection_amount
        lgd.append(lgd_year)

    for program_name in loan_programs:
        report_lgd[program_name] = mean([lgd_dict[program_name] for lgd_dict in lgd])
    connection.close()
    return report_lgd
