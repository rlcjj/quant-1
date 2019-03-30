import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def VolumeMean20d(beg_date, end_date):

    """
    因子说明：过去20个交易日的平均交易额
    """

    # param
    #################################################################################
    LongTerm = 20
    factor_name = "VolumeMean20d"
    ipo_num = 90

    # read data
    #################################################################################
    trade_amount = Stock().read_factor_h5("TradeAmount")

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(trade_amount.columns) & set(date_series))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        trade_amount_before = trade_amount.ix[:, data_beg_date:current_date]

        if current_date in trade_amount.columns:
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            avg_trade_amount = trade_amount_before.mean(axis=1)
            avg_trade_amount = pd.DataFrame(avg_trade_amount.values,
                                            columns=[current_date], index=avg_trade_amount.index)

        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            avg_trade_amount = pd.DataFrame([], columns=[current_date], index=trade_amount.index)

        if i == 0:
            res = avg_trade_amount
        else:
            res = pd.concat([res, avg_trade_amount], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '2018-01-01'
    end_date = datetime.today()
    data = VolumeMean20d(beg_date, end_date)
    print(data)

