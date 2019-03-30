import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def Momentum1m(beg_date, end_date):

    """
    因子说明：-1 * 最近1月加权收益率
    权重为线性加权
    """

    # param
    #################################################################################
    factor_name = 'Momentum1m'
    LongTerm = 20
    ipo_num = 90

    # read data
    #################################################################################
    pct = Stock().read_factor_h5("Pct_chg").T

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(pct.index))
    date_series.sort()

    res = pd.DataFrame([], columns=date_series, index=pct.columns)

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm - 1))
        data_period = pct.ix[data_beg_date:current_date, :]
        data_period = data_period.dropna(how='all')

        if len(data_period) == LongTerm:

            print('Calculating factor %s at date %s' % (factor_name, current_date))

            weight = np.array(list(range(1, LongTerm + 1)))
            weight = weight / weight.sum()
            weight_mat = np.transpose(np.tile(weight, (len(data_period.columns), 1)))
            weight_pd = pd.DataFrame(weight_mat, index=data_period.index, columns=data_period.columns)
            weight_pct = weight_pd.mul(data_period)
            data_date = weight_pct.sum(skipna=False)
            res[current_date] = data_date
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))

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
    data = Momentum1m(beg_date, end_date)
    print(data)

