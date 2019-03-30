import pandas as pd
import numpy as np
import os

from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def StockName(beg_date, end_date):

    """
    股票名称
    """

    # param
    #################################################################################
    factor_name = "StockName"
    ipo_num = 90

    # read data
    #################################################################################
    # Stock().load_stock_name()
    data = Stock().get_stock_change_name()
    data_now = Stock().get_stock_name_now()
    stock_code = Stock().get_all_stock_code_now()
    date_series = Date().get_trade_date_series(beg_date, end_date)
    res = pd.DataFrame([], columns=date_series, index=stock_code)

    for i_code in range(len(date_series)):
        for i_date in range(len(stock_code)):

            date = date_series[i_code]
            code = stock_code[i_date]
            print(date, code)
            data_code = data[data['wind_code'] == code]
            data_code = data_code.sort_values(by=['name_change_date'])
            data_date = data_code[data_code['name_change_date'] <= date]

            if len(data_date) == 0 and len(data_code) != 0:
                name = data_code.loc[data_code.index[0], "sec_name_before"]
            elif len(data_date) != 0:
                name = data_date.loc[data_date.index[-1], "sec_name_after"]
            else:
                name = data_now.loc[code, "SEC_NAME"]
            print(name)
            res.loc[code, date] = name

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    res.to_csv(os.path.join(Stock().get_h5_path("my_alpha"), factor_name + '.csv'))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '20181218'
    end_date = datetime.today()
    data = StockName(beg_date, end_date)
    print(data)

