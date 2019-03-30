import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate
from sklearn.linear_model import LinearRegression


def ROEQuarterResDaily(beg_date, end_date):

    """
    因子说明: ROE 单季
    披露日期 为 最近财报
    """

    # param
    #################################################################################
    factor_name = 'ROEQuarterResDaily'
    ipo_num = 90
    beg_date = Date().get_trade_date_offset(beg_date, -250)

    # read data
    #################################################################################
    net_profit = Stock().read_factor_h5("NetProfitDeducted") * 4
    holder = Stock().read_factor_h5("TotalShareHoldeRequity")

    [net_profit, holder] = Stock().make_same_index_columns([net_profit, holder])
    roe = net_profit.div(holder)

    report_data = Stock().read_factor_h5("ReportDateDaily")
    roe = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(roe, report_data, beg_date, end_date)

    netprofit = Stock().read_factor_h5("NetProfitDeducted") * 4
    total_mv = Stock().read_factor_h5("TotalMarketValue", Stock().get_h5_path("my_alpha"))

    report_data = Stock().read_factor_h5("ReportDateDaily")
    netprofit = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(netprofit, report_data, beg_date, end_date)

    [total_mv, netprofit] = Stock().make_same_index_columns([total_mv, netprofit])
    total_mv /= 100000000

    ep = netprofit.div(total_mv)

    # data precessing
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(ep.columns) & set(roe.columns))
    date_series.sort()

    # calculate data daily
    #################################################################################
    res = pd.DataFrame()

    for i_date in range(len(date_series)):

        date = date_series[i_date]
        data = pd.concat([roe[date], ep[date]], axis=1)
        data = data.dropna()
        data.columns = ['roe', 'ep']
        data['ones'] = 1.0
        y = data['roe'].values
        x = data[['ones', 'ep']].values

        if len(data) > 100:

            try:
                model = LinearRegression(fit_intercept=True)
                model.fit(X=x, y=y)
                y_res = y - np.dot(x, model.coef_)
                y_res = pd.DataFrame(y_res, index=data.index, columns=[date])
                res = pd.concat([res, y_res], axis=1)
                print(len(date), date)
            except Exception as e:
                pass

    res = roe.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()
    data = ROEQuarterResDaily(beg_date, end_date)
    print(data)
