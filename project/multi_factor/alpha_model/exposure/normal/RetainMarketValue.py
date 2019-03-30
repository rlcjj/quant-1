import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def RetainMarketValue(beg_date, end_date):

    """
    因子说明: 留存收益 / 总市值
    披露日期 为 最近财报
    """

    # param
    #################################################################################
    factor_name = 'RetainMarketValue'
    ipo_num = 90

    # read data
    #################################################################################
    retain = Stock().read_factor_h5("RetainedEarnings")
    mv = Stock().read_factor_h5("TotalMarketValue", Stock().get_h5_path("my_alpha"))
    retain = StockFactorOperate().change_quarter_to_daily_with_report_date(retain, beg_date, end_date)
    [retain, mv] = Stock().make_same_index_columns([retain, mv])

    retain_ratio = retain.div(mv)

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################

    res = retain_ratio.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = RetainMarketValue(beg_date, end_date)
    print(data)
