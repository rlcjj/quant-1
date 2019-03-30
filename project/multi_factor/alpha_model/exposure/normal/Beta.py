import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def Beta(beg_date, end_date):

    """
    因子说明：利用回归方法计算个股 Beta = Corr * Stock_Std / BenchMark_Std
    市场收益的股票平均收益
    """

    # param
    #################################################################################
    LongTerm = 120
    MinimumSize = 40
    factor_name = "Beta"
    ipo_num = 90

    # read data
    #################################################################################
    pct = Stock().read_factor_h5("Pct_chg")

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(pct.columns) & set(date_series))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        pct_before = pct.ix[:, data_beg_date:current_date]
        pct_stock = pct_before.T.dropna(how='all')
        pct_average = pct_stock.mean(axis=1)

        if len(pct_stock) > MinimumSize:
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            corr_date = pct_stock.corrwith(pct_average)
            std_stock = pct_stock.std()
            std_market = pct_average.std()
            beta = corr_date * std_stock / std_market
            effective_number = pct_stock.count()
            beta[effective_number <= MinimumSize] = np.nan
            corr_date = pd.DataFrame(corr_date.values, columns=[current_date], index=corr_date.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            corr_date = pd.DataFrame([], columns=[current_date], index=pct.index)

        if i == 0:
            res = corr_date
        else:
            res = pd.concat([res, corr_date], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '2017-01-01'
    end_date = datetime.today()
    data = Beta(beg_date, end_date)
    print(data)

