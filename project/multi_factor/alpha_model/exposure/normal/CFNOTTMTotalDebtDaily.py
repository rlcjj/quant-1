import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def CFNOTTMTotalDebtDaily(beg_date, end_date):

    """
    因子说明: 经营活动现金净流量(TTM)/负债合计, 根据最新财报更新数据
    披露日期 为 最近财报
    总负债可能是负值 000637.SZ 20120331 应交税费为负值 导致整体负债为负值
    """

    # param
    #################################################################################
    factor_name = 'CFNOTTMTotalDebtDaily'
    ipo_num = 90

    # read data
    #################################################################################
    operate_cash = Stock().read_factor_h5("NetOperateCashFlow")
    total_liability = Stock().read_factor_h5("TotalLiability")
    operate_cash = StockFactorOperate().change_single_quarter_to_ttm_quarter(operate_cash)/4

    [operate_cash, total_liability] = Stock().make_same_index_columns([operate_cash, total_liability])
    total_liability[total_liability < 0.0] = np.nan
    cfo_td = operate_cash.div(total_liability)

    report_data = Stock().read_factor_h5("ReportDateDaily")
    cfo_td = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(cfo_td, report_data, beg_date, end_date)

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################

    res = cfo_td.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = CFNOTTMTotalDebtDaily(beg_date, end_date)
    print(data)
