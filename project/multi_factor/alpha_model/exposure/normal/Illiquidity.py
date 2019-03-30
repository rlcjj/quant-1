import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def Illiquidity(beg_date, end_date):

    """
    因子说明： 涨跌幅的绝对值 / 交易额
    最近20天均值
    """

    # param
    #################################################################################
    LongTerm = 20
    HalfTerm = LongTerm / 2
    factor_name = "Illiquidity"
    ipo_num = 90

    # read data
    #################################################################################
    pct = Stock().read_factor_h5("Pct_chg").T
    trade_amount = Stock().read_factor_h5("TradeAmount").T

    # data precessing
    #################################################################################
    [pct, trade_amount] = Stock().make_same_index_columns([pct, trade_amount])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(pct.index))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        trade_amount_before = trade_amount.ix[data_beg_date:current_date, :]
        trade_amount_before = trade_amount_before.dropna(how='all')
        trade_amount_before = trade_amount_before.fillna(0.0)

        if len(trade_amount_before) > HalfTerm:
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            zero_number = trade_amount_before.applymap(lambda x: 1.0 if x == 0.0 else 0.0).sum()
            code_filter_list = (zero_number[zero_number < HalfTerm]).index
            amount_before = trade_amount.ix[data_beg_date:current_date, code_filter_list]
            pct_before = pct.ix[data_beg_date:current_date, code_filter_list]
            illiq = pct_before.abs().div(amount_before, axis='index') * 100000000
            illiq[illiq > 100.0] = np.nan
            illiq_mean = illiq.mean()
            price_mean = pd.DataFrame(illiq_mean.values, columns=[current_date], index=illiq_mean.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            price_mean = pd.DataFrame([], columns=[current_date], index=trade_amount_before.columns)

        if i == 0:
            res = price_mean
        else:
            res = pd.concat([res, price_mean], axis=1)

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
    data = Illiquidity(beg_date, end_date)
    print(data)

