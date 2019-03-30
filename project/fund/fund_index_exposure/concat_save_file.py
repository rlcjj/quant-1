import pandas as pd
import os
from datetime import datetime
from quant.utility.write_excel import WriteExcel


def concat_file(path, report_date, last_date):

    #########################################################################################################
    # path = 'E:\\3_Data\\4_fund_data\\8_fund_index_exposure_weekly\\'
    # report_date = '20171231'
    # last_date = '20180831'

    #########################################################################################################
    exposure_file = os.path.join(path, "halfyear_holding_exposure", 'FundHalfYearExposure_' + report_date + '.csv')
    fund_halyear_exposure = pd.read_csv(exposure_file, index_col=[0], encoding='gbk')

    cols = list(fund_halyear_exposure.columns)
    quant_fund_exposure = fund_halyear_exposure[fund_halyear_exposure['Type'].map(lambda x: '主动量化' in x)].mean()
    quant_fund_exposure = pd.DataFrame(quant_fund_exposure, columns=['重点量化基金平均']).T
    active_fund_exposure = fund_halyear_exposure[fund_halyear_exposure['Type'].map(lambda x: '主动股票' in x)].mean()
    active_fund_exposure = pd.DataFrame(active_fund_exposure, columns=['重点主动基金平均']).T
    fund_halyear_exposure_add = pd.concat([quant_fund_exposure, active_fund_exposure, fund_halyear_exposure], axis=0)
    fund_halyear_exposure_add['Type'] = fund_halyear_exposure_add['Type'].fillna('基金平均')
    fund_halyear_exposure_add = fund_halyear_exposure_add[cols]

    exposure_file = os.path.join(path, "halfyear_holding_exposure", 'IndexHalfYearExposure_' + report_date + '.csv')
    index_halyear_exposure = pd.read_csv(exposure_file, index_col=[0], encoding='gbk')

    exposure_file = os.path.join(path, "lastyear_holding_exposure", 'IndexLastDateExposure_' + last_date + '.csv')
    index_lastdate_exposure = pd.read_csv(exposure_file, index_col=[0], encoding='gbk')

    exposure_file = os.path.join(path, "lastyear_holding_exposure", 'FundLastDateExposure_' + last_date + '.csv')
    fund_lastdate_exposure = pd.read_csv(exposure_file, index_col=[0], encoding='gbk')

    halfyear_exposure = pd.concat([index_halyear_exposure, fund_halyear_exposure_add], axis=0)
    lastdate_exposure = pd.concat([index_lastdate_exposure, fund_lastdate_exposure], axis=0)

    #########################################################################################################
    exposure_file = os.path.join(path, "output_exposure", 'IndexFundExposure' + last_date + '.xlsx')

    excel = WriteExcel(exposure_file)
    worksheet = excel.add_worksheet("最近交易日风格暴露")
    num_format_pd = pd.DataFrame([], columns=lastdate_exposure.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.000'
    excel.write_pandas(lastdate_exposure, worksheet, begin_row_number=0, begin_col_number=1,
                       num_format_pd=num_format_pd, color="blue", fillna=True)
    excel.conditional_format(worksheet, 1, 2,
                             1 + len(lastdate_exposure), len(lastdate_exposure.columns) - 1,
                             None)
    excel.conditional_format(worksheet, 1, len(lastdate_exposure.columns),
                             1 + len(lastdate_exposure),  len(lastdate_exposure.columns),
                             {'type': 'data_bar'})

    worksheet = excel.add_worksheet("最近半年报风格暴露")
    num_format_pd = pd.DataFrame([], columns=halfyear_exposure.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.000'
    excel.write_pandas(halfyear_exposure, worksheet, begin_row_number=0, begin_col_number=1,
                       num_format_pd=num_format_pd, color="blue", fillna=True)
    excel.conditional_format(worksheet, 1, 2,
                             1 + len(halfyear_exposure), len(halfyear_exposure.columns) - 1,
                             None)
    excel.conditional_format(worksheet, 1, len(halfyear_exposure.columns),
                             1 + len(halfyear_exposure),  len(halfyear_exposure.columns),
                             {'type': 'data_bar'})
    excel.close()

    exposure_file = os.path.join(path, "output_exposure", '最近交易日风格暴露' + last_date + '.xlsx')

    excel = WriteExcel(exposure_file)
    worksheet = excel.add_worksheet("最近交易日风格暴露")
    num_format_pd = pd.DataFrame([], columns=lastdate_exposure.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.000'
    excel.write_pandas(lastdate_exposure, worksheet, begin_row_number=0, begin_col_number=1,
                       num_format_pd=num_format_pd, color="blue", fillna=True)
    excel.conditional_format(worksheet, 1, 2,
                             1 + len(lastdate_exposure), len(lastdate_exposure.columns) - 1,
                             None)
    excel.conditional_format(worksheet, 1, len(lastdate_exposure.columns),
                             1 + len(lastdate_exposure),  len(lastdate_exposure.columns),
                             {'type': 'data_bar'})
    excel.close()

    exposure_file = os.path.join(path, "output_exposure", '最近半年报风格暴露' + report_date + '.xlsx')
    excel = WriteExcel(exposure_file)
    worksheet = excel.add_worksheet("最近半年报风格暴露")
    num_format_pd = pd.DataFrame([], columns=halfyear_exposure.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.000'
    excel.write_pandas(halfyear_exposure, worksheet, begin_row_number=0, begin_col_number=1,
                       num_format_pd=num_format_pd, color="blue", fillna=True)
    excel.conditional_format(worksheet, 1, 2,
                             1 + len(halfyear_exposure), len(halfyear_exposure.columns) - 1,
                             None)
    excel.conditional_format(worksheet, 1, len(halfyear_exposure.columns),
                             1 + len(halfyear_exposure),  len(halfyear_exposure.columns),
                             {'type': 'data_bar'})
    excel.close()

    #########################################################################################################

if __name__ == '__main__':

    #########################################################################################################
    path = 'E:\\Data\\fund_data\\fund_index_exposure_weekly\\'
    report_date = '20180630'
    last_date = '20190118'
    concat_file(path, report_date, last_date)
    #########################################################################################################
