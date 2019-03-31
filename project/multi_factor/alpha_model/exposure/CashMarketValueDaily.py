import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def CashMarketValueDaily(beg_date, end_date):

    """
    因子说明: 货币资金/总市值, 根据最新财报更新数据
    披露日期 为 最近财报
    """

    # param
    #################################################################################
    factor_name = 'CashMarketValueDaily'
    ipo_num = 90

    # read data
    #################################################################################
    cash = Stock().read_factor_h5("CashEquivalents")
    total_mv = Stock().read_factor_h5("TotalMarketValue", Stock().get_h5_path("my_alpha"))

    report_data = Stock().read_factor_h5("ReportDateDaily")
    cash = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(cash, report_data, beg_date, end_date)

    [cash, total_mv] = Stock().make_same_index_columns([cash, total_mv])
    cash_price = cash.div(total_mv)

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################

    res = cash_price.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = CashMarketValueDaily(beg_date, end_date)
    print(data)
