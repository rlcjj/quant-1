from quant.fund.fund import Fund
import os
import pandas as pd
from datetime import datetime
from quant.stock.date import Date


def Cal_AllFund_HalfYear_Holding_Exposure(path, report_date, today):

    """
    计算重点基金最近一个半年报 的持仓风格暴露
    """
    # 参数举例
    #####################################################################
    # path = 'E:\\3_Data\\4_fund_data\\8_fund_index_exposure_weekly\\'
    # report_date = '20171231'
    # today = datetime.today().strftime("%Y%m%d")

    # 基金池
    #####################################################################
    fund_pool_file = os.path.join(path, "fund_pool", '重点基金信息.csv')
    fund_pool = pd.read_csv(fund_pool_file, index_col=[0], encoding='gbk')
    fund_pool = fund_pool[fund_pool['种类'] != '1专户量化']
    date = Date().get_trade_date_offset(report_date, 0)

    # 计算重点所有重点 基金最近一个半年报 的持仓风格暴露
    #####################################################################
    for i_fund in range(0, len(fund_pool)):

        fund_code = fund_pool.index[i_fund]
        Fund().cal_fund_holder_exposure_halfyear(fund_code, beg_date="20171231", end_date=today)
        print(fund_code, report_date)

        if i_fund == 0:
            exposure = Fund().get_fund_holder_exposure_halfyear_date(fund_code, date=report_date, type_list=["STYLE", "COUNTRY"])
        else:
            exposure_add = Fund().get_fund_holder_exposure_halfyear_date(fund_code, date=report_date, type_list=["STYLE", "COUNTRY"])
            exposure = pd.concat([exposure, exposure_add], axis=0)

    #####################################################################
    exposure.index = fund_pool['基金名称']
    cols = list(exposure.columns)
    cols.insert(0, 'Type')
    exposure['Type'] = fund_pool['种类'].values
    exposure = exposure[cols]
    exposure['CTY'] = "ChinaEquity"
    del exposure['ChinaEquity']

    exposure_file = os.path.join(path, "halfyear_holding_exposure", 'FundHalfYearExposure_' + report_date + '.csv')
    exposure.to_csv(exposure_file)
    #####################################################################


if __name__ == '__main__':

    path = 'E:\\Data\\fund_data\\fund_index_exposure_weekly\\'
    report_date = '20180630'
    today = datetime.today().strftime("%Y%m%d")
    Cal_AllFund_HalfYear_Holding_Exposure(path, report_date, today)
