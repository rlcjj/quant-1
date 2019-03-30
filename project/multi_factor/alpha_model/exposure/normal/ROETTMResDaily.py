import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def ROETTMDaily(beg_date, end_date):

    """
    因子说明: ROE_TTM 对PE取残差
    披露日期 为 最近财报
    """

    # param
    #################################################################################
    factor_name = 'ROETTMResDaily'
    ipo_num = 90

    # read data
    #################################################################################
    net_profit = Stock().read_factor_h5("NetProfitDeducted")
    holder = Stock().read_factor_h5("TotalShareHoldeRequity")
    net_profit_ttm = StockFactorOperate().change_single_quarter_to_ttm_quarter(net_profit)
    holder_ttm = StockFactorOperate().change_single_quarter_to_ttm_quarter(holder) / 4.0

    [net_profit_ttm, holder_ttm] = Stock().make_same_index_columns([net_profit_ttm, holder_ttm])
    roe = net_profit_ttm.div(holder_ttm)

    report_data = Stock().read_factor_h5("ReportDateDaily")
    roe = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(roe, report_data, beg_date, end_date)

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################

    res = roe.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = ROETTMDaily(beg_date, end_date)
    print(data)
