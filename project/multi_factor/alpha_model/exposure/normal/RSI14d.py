import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def RSI14d(beg_date, end_date):

    """
    因子说明： 14天 RSI

    A——N日内收盘涨幅之和
    B——N日内收盘跌幅之和(取正值)
    N日RSI=A/（A+B）×100
    实际理解为：在某一阶段价格上涨所产生的波动占整个波动的百分比。取值的
    """

    # param
    #################################################################################
    LongTerm = 14
    HalfTerm = int(LongTerm / 2)
    factor_name = "RSI14d"
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
        data_period = pct.ix[:, data_beg_date:current_date]
        data_period = data_period.T.dropna(how='all')

        if len(data_period) > HalfTerm:
            print('Calculating factor %s at date %s' % (factor_name, current_date))

            data_positive = data_period[data_period > 0.0].sum()
            data_negative = - data_period[data_period <= 0.0].sum()
            data_sum = data_positive + data_negative
            code_list = data_sum[data_sum != 0.0].index
            data_date = data_positive[code_list] / data_sum[code_list]
            effective_number = data_period.count()
            data_date[effective_number <= HalfTerm] = np.nan
            data_date = pd.DataFrame(data_date.values, columns=[current_date], index=data_date.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            data_date = pd.DataFrame([], columns=[current_date], index=pct.index)

        if i == 0:
            res = data_date
        else:
            res = pd.concat([res, data_date], axis=1)

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
    data = RSI14d(beg_date, end_date)
    print(data)

