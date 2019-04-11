from quant.fund.fund import Fund
from quant.mfc.mfc_data import MfcData
from quant.stock.date import Date
import os
import pandas as pd
from datetime import datetime


def Cal_MfcFund_LastDate_Holding_Exposure(path, report_date, today):

    """
    计算部门基金最近一个半年报 的持仓风格暴露
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
    fund_pool = fund_pool[fund_pool['种类'].map(lambda x: x in ["1部门量化", '1专户量化'])]
    date = Date().get_trade_date_offset(report_date, 0)
    beg_date = Date().get_trade_date_offset(report_date, -10)
    end_date = today

    # 计算部门基金  基金最近交易日 的持仓风格暴露
    #####################################################################
    for i_fund in range(len(fund_pool)):

        fund_code = fund_pool.index[i_fund]
        fund_type = fund_pool.loc[fund_code, '种类']
        if fund_type == '1专户量化':
            fund_name = fund_code
        else:
            fund_name = MfcData().get_mfc_fund_name(fund_code)
        MfcData().cal_mfc_holding_barra_exposure_period(fund_name, beg_date, end_date)

        if i_fund == 0:
            exposure = MfcData().get_mfc_holding_barra_exposure_date(fund_name, date)
            exposure['CTY'] = MfcData().get_mfc_stock_ratio(fund_name, date)
        else:
            exposure_add = MfcData().get_mfc_holding_barra_exposure_date(fund_name, date)
            exposure_add['CTY'] = MfcData().get_mfc_stock_ratio(fund_name, date)
            exposure = pd.concat([exposure, exposure_add], axis=0)

    #####################################################################
    exposure_file = os.path.join(path, "lastyear_holding_exposure", 'FundLastDateExposure_' + date + '.csv')
    exposure.to_csv(exposure_file)
    #####################################################################


if __name__ == '__main__':

    path = 'E:\\Data\\fund_data\\fund_index_exposure_weekly\\'
    last_date = '20190131'
    today = datetime.today().strftime("%Y%m%d")
    Cal_MfcFund_LastDate_Holding_Exposure(path, last_date, today)
