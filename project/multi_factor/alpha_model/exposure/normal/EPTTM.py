import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def EPTTM(beg_date, end_date):

    """
    因子说明：pe_ttm的倒数
    """

    # param
    #################################################################################
    factor_name = "EPTTM"
    ipo_num = 90

    # read data
    #################################################################################
    pe_ttm = Stock().read_factor_h5("PE_ttm")

    # code set & date set
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(pe_ttm.columns) & set(date_series))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]

        if current_date in list(pe_ttm.columns):

            print('Calculating factor %s at date %s' % (factor_name, current_date))
            data_cur = pe_ttm[current_date]
            data_cur = data_cur[data_cur != 0.0]
            ep_ttm = 1.0 / data_cur
            ep_ttm = pd.DataFrame(ep_ttm.values, columns=[current_date], index=ep_ttm.index)
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            ep_ttm = pd.DataFrame([], columns=[current_date], index=pe_ttm.columns)

        if i == 0:
            res = pd.DataFrame(ep_ttm.values, columns=[current_date], index=ep_ttm.index)
        else:
            res_add = pd.DataFrame(ep_ttm.values, columns=[current_date], index=ep_ttm.index)
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
    data = EPTTM(beg_date, end_date)
    print(data)
