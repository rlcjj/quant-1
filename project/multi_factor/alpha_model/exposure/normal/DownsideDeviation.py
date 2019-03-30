import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def DownsideDeviation(beg_date, end_date):

    """
    因子说明： 下行偏差
    """

    # param
    #################################################################################
    LongTerm = 150
    MinimumSize = 40
    factor_name = "DownsideDeviation"
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
    date_series = list(set(date_series) & set(pct.columns))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        pct_before = pct.ix[:, data_beg_date:current_date]
        pct_stock = pct_before.T.dropna(how='all')
        pct_stock /= 100

        if len(pct_stock) > MinimumSize:
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            down_dev_date = (pct_stock.applymap(lambda x: min(x, 0)) ** 2).mean() * np.sqrt(250)
            effective_number = pct_stock.count()
            down_dev_date[effective_number <= MinimumSize] = np.nan
            down_dev_date = pd.DataFrame(down_dev_date.values, columns=[current_date], index=down_dev_date.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            down_dev_date = pd.DataFrame([], columns=[current_date], index=pct.index)

        if i == 0:
            res = down_dev_date
        else:
            res = pd.concat([res, down_dev_date], axis=1)

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
    data = DownsideDeviation(beg_date, end_date)
    print(data)

