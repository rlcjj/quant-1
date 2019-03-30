import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def SNNBias(beg_date, end_date):

    """
    因子说明： 最近10天平均 减去 之前30天平均 新浪财经点击数量 的负值
    """

    # param
    #################################################################################
    LongTerm = 40
    HalfTerm = int(LongTerm/2)
    factor_name = "SNNBias"
    ipo_num = 90

    # read data
    #################################################################################
    click_num = Stock().read_factor_h5("SNN")

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(click_num.columns))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        data_period = click_num.ix[:, data_beg_date:current_date]
        data_period = data_period.T.dropna(how='all')

        if len(data_period) > HalfTerm:
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            data_date_pre30 = data_period.ix[0:30, :].mean()
            data_date_next10 = data_period.ix[-10:, :].mean()
            data_date = -(data_date_next10 - data_date_pre30)
            effective_number = data_period.count()
            data_date[effective_number <= HalfTerm] = np.nan
            data_date = pd.DataFrame(data_date.values, columns=[current_date], index=data_date.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            data_date = pd.DataFrame([], columns=[current_date], index=click_num.index)

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
    data = SNNBias(beg_date, end_date)
    print(data)

