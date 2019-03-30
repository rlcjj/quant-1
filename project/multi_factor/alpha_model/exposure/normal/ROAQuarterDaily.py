import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def ROAQuarterDaily(beg_date, end_date):

    """
    因子说明: ROA 单季
    披露日期 为 最近财报
    """

    # param
    #################################################################################
    factor_name = 'ROAQuarterDaily'
    ipo_num = 90

    # read data
    #################################################################################
    net_profit = Stock().read_factor_h5("NetProfit")
    asset = Stock().read_factor_h5("TotalAsset")

    [net_profit, asset] = Stock().make_same_index_columns([net_profit, asset])
    roa = net_profit.div(asset)

    report_data = Stock().read_factor_h5("ReportDateDaily")
    roa = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(roa, report_data, beg_date, end_date)

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################

    res = roa.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = ROAQuarterDaily(beg_date, end_date)
    print(data)
