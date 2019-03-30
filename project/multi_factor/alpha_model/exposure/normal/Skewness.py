import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def Skewness(beg_date, end_date):

    """
    因子说明： -1 * 偏度
    """

    # param
    #################################################################################
    LongTerm = 150
    MinimumSize = 120
    factor_name = "Skewness"
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

        if len(pct_stock) > MinimumSize:
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            skew_date = -pct_stock.skew()
            effective_number = pct_stock.count()
            skew_date[effective_number <= MinimumSize] = np.nan
            skew_date = pd.DataFrame(skew_date.values, columns=[current_date], index=skew_date.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            skew_date = pd.DataFrame([], columns=[current_date], index=pct.index)

        if i == 0:
            res = skew_date
        else:
            res = pd.concat([res, skew_date], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20180501'
    end_date = datetime.today()
    data = Skewness(beg_date, end_date)
    print(data)

