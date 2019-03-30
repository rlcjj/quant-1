import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def PEG(beg_date, end_date):

    """
    因子说明：PE_TTM / 净利润增长速度

    当两者都是负数的时候 结果也为负数
    披露日期 为 最近财报
    """

    # param
    #################################################################################
    factor_name = 'PEG'
    ipo_num = 90

    # read data
    #################################################################################
    net_profit = Stock().read_factor_h5("NetProfit")
    net_profit = StockFactorOperate().change_single_quarter_to_ttm_quarter(net_profit).T
    net_profit_4 = net_profit.shift(4)
    net_profit_g = net_profit / net_profit_4 - 1.0
    net_profit_g_mean = net_profit_g.rolling(window=4).median().T

    report_data = Stock().read_factor_h5("ReportDateDaily")
    net_profit_g_mean = StockFactorOperate().\
        change_quarter_to_daily_with_disclosure_date(net_profit_g_mean, report_data, beg_date, end_date)

    pe_ttm = Stock().read_factor_h5("PE_ttm")

    [pe_ttm, net_profit_g_mean] = Stock().make_same_index_columns([pe_ttm, net_profit_g_mean])

    pe_ttm_negative = pe_ttm < 0.0
    net_profit_g_mean_negative = net_profit_g_mean < 0.0
    double_negative = pe_ttm_negative & net_profit_g_mean_negative
    peg = pe_ttm.div(net_profit_g_mean)
    peg[double_negative] = - peg[double_negative]

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################

    res = peg.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = PEG(beg_date, end_date)
    print(data)
