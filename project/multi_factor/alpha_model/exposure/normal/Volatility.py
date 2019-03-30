import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def Volatility(beg_date, end_date):

    """
    因子说明：利用过去120天的收益率计算波动率
    每只股票单独计算
    """

    # param
    #################################################################################
    LongTerm = 120
    MininumSize = 60
    factor_name = "Volatility"
    ipo_num = 90

    # read data
    #################################################################################
    pct_chg = Stock().read_factor_h5("Pct_chg").T

    # code set & date set
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(pct_chg.index) & set(date_series))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm - 1))
        data_pre = pct_chg.ix[data_beg_date:current_date, :]
        data_pre = data_pre.dropna(how='all').T

        if len(data_pre) > int(0.8*LongTerm):

            print('Calculating factor %s at date %s ' % (factor_name, current_date))
            data_pre = data_pre.replace(0.0, np.nan)
            code_list = list(data_pre.index[data_pre.count(axis=1) > MininumSize].values)
            data_pre = data_pre.ix[code_list, :]
            data_pre = data_pre.fillna(value=data_pre.median().to_dict())
            vol_date = data_pre.std(axis=1) * np.sqrt(250)
            vol_date = pd.DataFrame(vol_date.values, columns=[current_date], index=vol_date.index)

        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            vol_date = pd.DataFrame([], columns=[current_date], index=data_pre.index)

        if i == 0:
            res = vol_date
        else:
            res = pd.concat([res, vol_date], axis=1)

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
    data = Volatility(beg_date, end_date)
    print(data)

