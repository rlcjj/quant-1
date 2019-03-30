import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def InFlowMean2y(beg_date, end_date):

    """
    因子说明： 最近500天资金净流入平均数 时间越近权重越大
    这里的权重为等差数列 并非指数加权平均（即权重为等比数列）
    """

    # param
    #################################################################################
    LongTerm = 500
    factor_name = "InFlowMean2y"
    ipo_num = 90

    # read data
    #################################################################################
    inflow = Stock().read_factor_h5("Mf_Inflow")

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(inflow.columns))
    date_series.sort()


    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        price_before = inflow.ix[:, data_beg_date:current_date]
        price_stock = price_before.T.dropna(how='all')

        if len(price_stock) == LongTerm:
            print('Calculating factor %s at date %s' % (factor_name, current_date))

            weight = np.array(list(range(1, LongTerm + 1)))
            weight = weight * 2 / (1 + LongTerm)
            weight = weight / weight.sum()
            price_mean = pd.DataFrame(np.dot(weight, price_stock.values),
                                       columns=[current_date], index=price_stock.columns)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            price_mean = pd.DataFrame([], columns=[current_date], index=price_stock.columns)

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
    data = InFlowMean2y(beg_date, end_date)
    print(data)

