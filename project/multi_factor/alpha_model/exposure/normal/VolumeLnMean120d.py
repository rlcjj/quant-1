import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def VolumeLnMean120d(beg_date, end_date):

    """
    因子说明：过去120天的-1*log(交易额)的加权平均 权为随时间线性递减
    """

    # param
    #################################################################################
    LongTerm = 120
    HalfTerm = int(LongTerm/2)
    factor_name = 'VolumeLnMean120d'
    ipo_num = 90

    # read data
    #################################################################################
    trade_amount = Stock().read_factor_h5("TradeAmount").T

    # code set & date set
    #################################################################################
    trade_amount = trade_amount.fillna(0.0)

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(trade_amount.index) & set(date_series))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        amount_before = trade_amount.ix[data_beg_date:current_date, :]

        if len(amount_before) == LongTerm:

            print('Calculating factor %s at date %s' % (factor_name, current_date))
            zero_number = amount_before.applymap(lambda x: 1.0 if x == 0.0 else 0.0).sum()
            code_filter_list = (zero_number[zero_number < HalfTerm]).index

            amount_before = trade_amount.ix[data_beg_date:current_date, code_filter_list]
            amount_before_log = amount_before.applymap(lambda x: np.nan if x == 0 else -np.log(x))

            weight = np.array(list(range(1, LongTerm + 1)))
            weight_amount_log_val = np.dot(amount_before_log.T.values, weight)
            weight_amount_log = pd.DataFrame(weight_amount_log_val,
                                             index=amount_before_log.columns, columns=[current_date])

        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            weight_amount_log = pd.DataFrame([], columns=[current_date], index=trade_amount.columns)

        if i == 0:
            res = weight_amount_log
        else:
            res_add = weight_amount_log
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
    data = VolumeLnMean120d(beg_date, end_date)
    print(data)
