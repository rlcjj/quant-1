import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def AverageHolderDaily(beg_date, end_date):

    """
    因子说明：户均持股比例
    就是持股户数的倒数
    去掉新股和未上市企业
    按照披露日期
    """

    # param
    #################################################################################
    factor_name = 'AverageHolderDaily'
    ipo_num = 90

    # read data
    #################################################################################
    holder = Stock().read_factor_h5("HolderAvgPct")
    report_data = Stock().read_factor_h5("ReportDateDaily")
    holder = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(holder, report_data, beg_date, end_date)
    # ipo = Stock().get_factor_h5("ipo_normal_days", None, "primary_dfc")

    # data precessing
    #################################################################################
    # [holder, ipo] = Stock().make_same_index_columns([holder, ipo])

    res = holder.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = AverageHolderDaily(beg_date, end_date)
    print(data)

