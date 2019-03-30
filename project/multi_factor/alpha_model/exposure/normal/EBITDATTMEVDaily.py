import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def EBITDATTMEVDaily(beg_date, end_date):

    """
    因子说明：EBITDA / EV
    折旧摊销息税前利润 / 企业价值（剔除货币资金）
    若有一个为负值 结果为负值
    """

    # param
    #################################################################################
    factor_name = 'EBITDATTMEVDaily'
    ipo_num = 90

    # read data
    #################################################################################
    ebitda = Stock().read_factor_h5("EBITDA")
    ebitda = StockFactorOperate().change_cum_quarter_to_ttm_quarter(ebitda, factor_name="EBITDA")

    report_data = Stock().read_factor_h5("ReportDateDaily")
    ebitda = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(ebitda, report_data, beg_date, end_date)

    ev = Stock().read_factor_h5("Ev2")

    # data precessing
    #################################################################################
    [ebitda, ev] = Stock().make_same_index_columns([ebitda, ev])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)

    for i in range(0, len(date_series)):

        current_date = date_series[i]

        if current_date in ev.columns:
            ev_date = ev[current_date]
            ebitda_date = ebitda[current_date]
            print('Calculating factor %s at date %s' % (factor_name, current_date))

            data_date = pd.concat([ebitda_date, ev_date], axis=1)
            data_date.columns = ['ebitda_ttm', 'ev']
            data_date['ev'] /= 100000000.0
            data_date = data_date.dropna()
            data_date = data_date[data_date['ev'] != 0.0]
            data_date['ratio'] = data_date['ebitda_ttm'] / data_date['ev']

            # 只要有一个是负数 比例为负数
            mimus_index = (data_date['ev'] < 0.0) | (data_date['ebitda_ttm'] < 0.0)
            data_date.loc[mimus_index, 'ratio'] = - data_date.loc[mimus_index, 'ratio'].abs()
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            data_date = pd.DataFrame([], columns=["ratio"], index=ev.index)

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

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = EBITDATTMEVDaily(beg_date, end_date)
