import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def TotalAssetYOYDaily(beg_date, end_date):

    """
    因子说明: 当季总资产TTM的同比增长
    披露日期 为 最近财报
    """

    # param
    #################################################################################
    factor_name = 'TotalAssetYOYDaily'
    ipo_num = 90

    # read data
    #################################################################################
    TotalAsset = Stock().read_factor_h5("TotalAsset").T
    TotalAsset_4 = TotalAsset.shift(4)
    TotalAsset_yoy = TotalAsset / TotalAsset_4 - 1.0

    TotalAsset_yoy = TotalAsset_yoy.T
    report_data = Stock().read_factor_h5("ReportDateDaily")
    TotalAsset_yoy = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(TotalAsset_yoy, report_data, beg_date, end_date)

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################

    res = TotalAsset_yoy.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = TotalAssetYOYDaily(beg_date, end_date)
    print(data)
