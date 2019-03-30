import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def TurnOverBias6m3m(beg_date, end_date):

    """
    因子说明：160天平均换手率 - 60天平均换手率
    函数名有错误 以后可以更改
    """

    # param
    #################################################################################
    LongTerm = 120
    ShortTerm = 60
    factor_name = "TurnOverBias6m3m"
    ipo_num = 90

    # read data
    #################################################################################
    turn_over = Stock().read_factor_h5("TurnOver_Daily").T

    # code set & date set
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(turn_over.index) & set(date_series))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]

        data_beg_date_long = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        data_beg_date_short = Date().get_trade_date_offset(current_date, -(ShortTerm-1))

        turn_over_long = turn_over.ix[data_beg_date_long:current_date, :]
        turn_over_long = turn_over_long.T.dropna(how='all').T
        turn_over_short = turn_over.ix[data_beg_date_short:current_date, :]
        turn_over_short = turn_over_short.T.dropna(how='all').T

        if len(turn_over_long) >= int(0.8*LongTerm):

            print('Calculating factor %s at date %s' % (factor_name, current_date))
            turn_over_diff = turn_over_long.mean() - turn_over_short.mean()

        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            turn_over_diff = pd.DataFrame([], columns=[current_date], index=turn_over.columns)

        if i == 0:
            res = pd.DataFrame(turn_over_diff.values, columns=[current_date], index=turn_over_diff.index)
        else:
            res_add = pd.DataFrame(turn_over_diff.values, columns=[current_date], index=turn_over_diff.index)
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
    data = TurnOverBias6m3m(beg_date, end_date)
    print(data)
