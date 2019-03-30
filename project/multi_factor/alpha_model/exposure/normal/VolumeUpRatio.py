import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def VolumeUpRatio(beg_date, end_date):

    """
    因子说明：1*以当日收盘价为下限 当日收盘价*1.1为上限，
    过去120天的在上下限之间的天的成交额的总和占过去120天总成交额的比例
    最后乘以 -1
    注意：补齐nan为0,，去掉过去120天超过60天交易额为0的股票
    """

    # param
    #################################################################################
    LongTerm = 120
    HalfTerm = int(LongTerm / 2)
    PctRange = 0.1
    factor_name = "VolumeUpRatio"
    ipo_num = 90

    # read data
    #################################################################################
    close = Stock().read_factor_h5("PriceCloseAdjust").T
    trade_amount = Stock().read_factor_h5("TradeAmount").T

    # data precessing
    #################################################################################
    [close, trade_amount] = Stock().make_same_index_columns([close, trade_amount])
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

        if len(amount_before) >= int(0.8*LongTerm):

            print('Calculating factor %s at date %s' % (factor_name, current_date))
            zero_number = amount_before.applymap(lambda x: 1.0 if x == 0.0 else 0.0).sum()
            code_filter_list = (zero_number[zero_number < HalfTerm]).index

            close_low_limit = close.ix[current_date, code_filter_list]
            close_up_limit = close.ix[current_date, code_filter_list] * (1 + PctRange)

            close_before = close.ix[data_beg_date:current_date, code_filter_list]
            price_center = (close_before > close_low_limit) & (close_before < close_up_limit)
            trade_amount_filter_sum = amount_before[price_center].sum()
            trade_amount_sum = amount_before.sum()

            trade_amount_sum = pd.concat([trade_amount_filter_sum, trade_amount_sum], axis=1)
            trade_amount_sum.columns = ['filter_sum', 'sum']
            trade_amount_sum = trade_amount_sum[trade_amount_sum['sum'] != 0.0]
            trade_amount_sum['ratio'] = - trade_amount_sum['filter_sum'] / trade_amount_sum['sum']
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            trade_amount_sum = pd.DataFrame([], columns=['ratio'], index=amount_before.columns)

        if i == 0:
            res = pd.DataFrame(trade_amount_sum['ratio'].values, columns=[current_date], index=trade_amount_sum.index)
        else:
            res_add = pd.DataFrame(trade_amount_sum['ratio'].values, columns=[current_date], index=trade_amount_sum.index)
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
    data = VolumeUpRatio(beg_date, end_date)
    print(data)

