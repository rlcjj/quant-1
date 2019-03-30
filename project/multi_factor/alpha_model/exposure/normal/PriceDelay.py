import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
import statsmodels.api as sm


def PriceDelay(beg_date, end_date):

    """
    因子说明：价格延迟
    时间序列上，用股票收益对当期市场收益做回归，记为回归1，回归长度为LongTerm
    时间序列上，用股票收益对当期市场收益和过去N天市场收益做回归，记为回归2，回归长度为LongTerm
    计算回归1的R2除以回归2的R2作为Price Delay
    此数据越大，说明股票不反映过去信息
    """

    # param
    #################################################################################
    LongTerm = 40
    HalfTerm = int(LongTerm/2)
    N = 5
    factor_name = "PriceDelay"
    ipo_num = 90

    # read data
    #################################################################################
    pct = Stock().read_factor_h5("Pct_chg").T

    # data precessing
    #################################################################################
    pass

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(pct.index))
    date_series.sort()

    res = pd.DataFrame([], index=pct.index, columns=pct.columns)

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date_1 = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        pct_before_1 = pct.ix[data_beg_date_1:current_date, :]
        market_pct_1 = pct_before_1.mean(axis=1)

        data_beg_date_2 = Date().get_trade_date_offset(current_date, -(LongTerm+N-1))
        current_date_2 = Date().get_trade_date_offset(current_date, -N)
        pct_before_2 = pct.ix[data_beg_date_2:current_date_2, :]
        market_pct_2 = pct_before_2.mean(axis=1)

        if len(pct_before_2) == len(pct_before_1) and len(pct_before_1) == LongTerm:

            market_pct_2 = pd.DataFrame(market_pct_2.values, index=market_pct_1.index)
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            for i_code in range(len(pct_before_1.columns)):
                code = pct_before_1.columns[i_code]
                reg_data = pd.concat([pct_before_1[code], market_pct_1, market_pct_2], axis=1)
                reg_data.columns = [code, 'Market_Pct_1', 'Market_Pct_2']
                reg_data = reg_data.dropna()

                if len(reg_data) > HalfTerm:
                    y = reg_data[code].values
                    x = reg_data['Market_Pct_1'].values
                    x = sm.add_constant(x)
                    model = sm.OLS(y, x).fit()
                    r1 = model.rsquared

                    x = reg_data[['Market_Pct_1', 'Market_Pct_2']].values
                    x = sm.add_constant(x)
                    model = sm.OLS(y, x).fit()
                    r2 = model.rsquared
                    res.ix[current_date, code] = r1 / r2

        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))

    res = res.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20180101'
    end_date = datetime.today()
    data = PriceDelay(beg_date, end_date)
    print(data)

