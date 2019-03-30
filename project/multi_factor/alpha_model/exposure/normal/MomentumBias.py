import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def MomentumBias(beg_date, end_date):

    """
    因子说明：240天扣除近60天涨跌幅/近60天涨跌幅
    暂时按照240天扣除近60天涨跌幅计算
    """

    # param
    #################################################################################
    LongTerm = 240
    ShortTerm = 60
    factor_name = "MomentumBias"
    ipo_num = 90

    # read data
    #################################################################################
    close = Stock().read_factor_h5("PriceCloseAdjust", Stock().get_h5_path("my_alpha"))

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(close.columns))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        long_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        short_date = Date().get_trade_date_offset(current_date, -(ShortTerm-1))

        if (long_date in close.columns) and (short_date in close.columns) and (current_date in close.columns):
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            pct_long = close[short_date] / close[long_date] - 1.0
            # pct_short = close[current_date] / close[short_date] - 1.0
            # pct_ratio = pct_long / pct_short
            pct_long = pd.DataFrame(pct_long.values, columns=[current_date], index=pct_long.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            pct_long = pd.DataFrame([], columns=[current_date], index=close.index)

        if i == 0:
            res = pct_long
        else:
            res = pd.concat([res, pct_long], axis=1)

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
    data = MomentumBias(beg_date, end_date)
    print(data)

