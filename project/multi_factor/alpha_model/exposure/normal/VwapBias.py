import pandas as pd
from quant.stock.stock import Stock
from quant.stock.date import Date


def VwapBias(beg_date, end_date):

    """
    因子说明：（（当日最高价*当日最低价）**（0.5）- 当日均价 ）/ 当日收盘价 均价价差
    再取过去10天的总和
    未上市股票和新股 的值为 NAN
    """

    # param
    #################################################################################
    LongTerm = 10
    factor_name = "VwapBias"
    ipo_num = 90

    # read data
    #################################################################################
    close = Stock().read_factor_h5("Price_Adjust").T
    vwap = Stock().read_factor_h5("Price_Vwap_Adjust").T
    high = Stock().read_factor_h5("Price_High_Adjust").T
    low = Stock().read_factor_h5("Price_Low_Adjust").T

    # data precessing
    #################################################################################
    [close, vwap, high, low] = Stock().make_same_index_columns([close, vwap, high, low])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(close.index) & set(date_series))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))

        close_pre60 = close.ix[data_beg_date:current_date, :]
        vwap_pre60 = vwap.ix[data_beg_date:current_date, :]
        high_pre60 = high.ix[data_beg_date:current_date, :]
        low_pre60 = low.ix[data_beg_date:current_date, :]

        number_date = min(len(close_pre60), len(vwap_pre60), len(high_pre60), len(low_pre60))

        if number_date >= int(0.8*LongTerm):

            print('Calculating factor %s at date %s' % (factor_name, current_date))
            mul = high_pre60.mul(low_pre60) ** (1 / 2)
            bias = mul.sub(vwap_pre60) / close_pre60
            bias_sum10 = bias.sum(skipna=False)
            # bias_sum10 = bias.mean()
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            bias_sum10 = pd.DataFrame([], columns=[current_date], index=low_pre60.columns)

        if i == 0:
            res = pd.DataFrame(bias_sum10.values, columns=[current_date], index=bias_sum10.index)
        else:
            res_add = pd.DataFrame(bias_sum10.values, columns=[current_date], index=bias_sum10.index)
            res = pd.concat([res, res_add], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()
    data = VwapBias(beg_date, end_date)
    print(data)

