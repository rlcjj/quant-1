import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def SPTTMDaily(beg_date, end_date):

    """
    因子说明：总营收 / 总市值
    TTM 为不同一财报期 最近可以得到的最新财报
    若有一个为负值 结果为负值
    """

    # param
    #################################################################################
    factor_name = "SPTTMDaily"
    ipo_num = 90

    # read data
    #################################################################################
    income = Stock().read_factor_h5("OperatingIncome")
    income = StockFactorOperate().change_single_quarter_to_ttm_quarter(income)
    report_data = Stock().read_factor_h5("ReportDateDaily")
    income = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(income, report_data, beg_date, end_date)
    mv = Stock().read_factor_h5("TotalMarketValue", Stock().get_h5_path("my_alpha"))

    # data precessing
    #################################################################################
    [income, mv] = Stock().make_same_index_columns([income, mv])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)

    for i in range(0, len(date_series)):

        current_date = date_series[i]

        if current_date in income.columns:

            income_date = income[current_date]
            mv_date = mv[current_date]
            print('Calculating factor %s at date %s' % (factor_name, current_date))

            data_date = pd.concat([income_date, mv_date], axis=1)
            data_date.columns = ['income', 'mv']

            data_date = data_date.dropna()
            data_date = data_date[data_date['mv'] != 0.0]
            data_date['ratio'] = data_date['income'] / data_date['mv']

            # 只要有一个是负数 比例为负数
            mimus_index = (data_date['income'] < 0.0) | (data_date['mv'] < 0.0)
            data_date.loc[mimus_index, 'ratio'] = - data_date.loc[mimus_index, 'ratio'].abs()
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            data_date = pd.DataFrame([], columns=["ratio"], index=income.index)

        if i == 0:
            res = pd.DataFrame(data_date['ratio'].values, columns=[current_date], index=data_date.index)
        else:
            res_add = pd.DataFrame(data_date['ratio'].values, columns=[current_date], index=data_date.index)
            res = pd.concat([res, res_add], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = SPTTMDaily(beg_date, end_date)
    print(data)

