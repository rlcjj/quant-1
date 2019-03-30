import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def InFlowFreeMv(beg_date, end_date):

    """
    因子说明：过去 10天 资金净流入额/自由流通市值
    流入为当日成交价上升的时候的成交额和成交量 流出为当日成交价下降时候的成交额和成交量
    """

    # param
    #################################################################################
    LongTerm = 10
    factor_name = "InFlowFreeMv"
    ipo_num = 90

    # read data
    #################################################################################
    inflow = Stock().read_factor_h5("Mf_Inflow").T
    free_mv = Stock().read_factor_h5("FreeMarketValue", Stock().get_h5_path("my_alpha")).T

    # code set & date set
    #################################################################################
    [inflow, free_mv] = Stock().make_same_index_columns([inflow, free_mv])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(inflow.index))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        inflow_pre = inflow.ix[data_beg_date:current_date, :]
        free_mv_pre = free_mv.ix[data_beg_date:current_date, :]

        if len(inflow_pre) >= int(0.8*LongTerm):

            print('Calculating factor %s at date %s' % (factor_name, current_date))

            inflow_pre_sum = inflow_pre.sum()
            free_mv_pre_sum = free_mv_pre.sum()

            date_data = pd.concat([inflow_pre_sum, free_mv_pre_sum], axis=1)
            date_data.columns = ['inflow', 'free_mv']
            date_data = date_data[date_data['free_mv'] != 0.0]
            date_data['ratio'] = date_data['inflow'] / date_data['free_mv'] * 100000000
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            date_data = pd.DataFrame([], columns=['ratio'], index=free_mv.columns)

        if i == 0:
            res = pd.DataFrame(date_data['ratio'].values, columns=[current_date], index=date_data.index)
        else:
            res_add = pd.DataFrame(date_data['ratio'].values, columns=[current_date], index=date_data.index)
            res = pd.concat([res, res_add], axis=1)

    res = res.T.dropna(how='all').T
    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '2018-01-01'
    end_date = datetime.today()
    data = InFlowFreeMv(beg_date, end_date)
    print(data)
