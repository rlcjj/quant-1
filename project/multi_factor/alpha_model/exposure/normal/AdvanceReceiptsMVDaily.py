import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def AdvanceReceiptsMVDaily(beg_date, end_date):

    """
    因子说明：预收账款 / 总市值
    同一财报期
    若有一个为负值 结果为负值
    """

    # param
    #################################################################################
    factor_name = 'AdvanceReceiptsMVDaily'
    ipo_num = 90

    # read data
    #################################################################################
    advance = Stock().read_factor_h5("AdvanceReceipts")
    report_data = Stock().read_factor_h5("ReportDateDaily")
    mv = Stock().read_factor_h5("TotalMarketValue", Stock().get_h5_path("my_alpha"))
    advance = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(advance, report_data, beg_date, end_date)

    # data precessing
    #################################################################################
    [advance, mv] = Stock().make_same_index_columns([advance, mv])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)

    for i in range(0, len(date_series)):

        current_date = date_series[i]

        if current_date in advance.columns:
            advance_date = advance[current_date]
            equity_date = mv[current_date]
            print('Calculating factor %s at date %s' % (factor_name, current_date))

            data_date = pd.concat([advance_date, equity_date], axis=1)
            data_date.columns = ['advance_date', 'equity_date']
            data_date = data_date.dropna()
            data_date = data_date[data_date['equity_date'] != 0.0]
            data_date['ratio'] = data_date['advance_date'] / data_date['equity_date']

            # 只要有一个是负数 比例为负数
            mimus_index = (data_date['advance_date'] < 0.0) | (data_date['equity_date'] < 0.0)
            data_date.loc[mimus_index, 'ratio'] = - data_date.loc[mimus_index, 'ratio'].abs()
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            data_date = pd.DataFrame([], columns=["ratio"], index=advance.index)

        if i == 0:
            res = pd.DataFrame(data_date['ratio'].values, columns=[current_date], index=data_date.index)
        else:
            res_add = pd.DataFrame(data_date['ratio'].values, columns=[current_date], index=data_date.index)
            res = pd.concat([res, res_add], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2018-05-01'
    end_date = datetime.today()
    data = AdvanceReceiptsMVDaily(beg_date, end_date)
    print(data)

