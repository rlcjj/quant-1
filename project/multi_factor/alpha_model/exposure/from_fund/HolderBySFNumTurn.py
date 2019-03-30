import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.fund.fund import Fund
import os
from quant.utility.factor_preprocess import FactorPreProcess


def HolderBySFNumTurn(beg_date, end_date):

    """
    因子说明：被主动股票基金季报持有在前十大重仓的基金数量的加权 持有数量0转化为NAN
    权值为基金换手率 换手率越高的权重越小
    数据可得时间在每季度末的15个工作日之后
    """

    # 参数
    ###########################################################################################
    offset_num = 16
    factor_name = "HolderBySFNumTurn"
    fund_pool_date = "20180630"
    fund_pool_name = "基金持仓基准基金池"
    beg_date = Date().change_to_str(beg_date)
    end_date = Date().change_to_str(end_date)

    # Fund().cal_fund_turnover()

    fund_pool = Fund().get_fund_pool_code(date=fund_pool_date, name=fund_pool_name)
    fund_turnover = Fund().get_fund_turnover()
    fund_turnover = fund_turnover.replace(0.0, np.nan)
    fund_turnover[fund_turnover < 10] = np.nan
    fund_turnover = fund_turnover.loc[fund_pool, :]
    fund_turnover = fund_turnover.rank(ascending=False) / fund_turnover.count()
    # fund_turnover1 = FactorPreProcess().inv_normalization(fund_turnover)
    fund_turnover = fund_turnover.T
    holdernumber = pd.DataFrame([])

    # 每个基金叠加
    ###########################################################################################
    for i_fund in range(0, len(fund_pool)):

        fund = fund_pool[i_fund]
        fund_holding = Fund().get_fund_holding_quarter(fund=fund)

        if fund_holding is not None:
            print(fund)
            fund_turnover_fund = pd.DataFrame(fund_turnover[fund])
            fund_turnover_fund = fund_turnover_fund.loc[fund_holding.columns, :]
            fund_turnover_fund = fund_turnover_fund.fillna(method='pad')
            fund_turnover_fund = fund_turnover_fund.shift(1)
            fund_turnover_fund = fund_turnover_fund[fund]
            fund_holding[fund_holding.applymap(lambda x: ~np.isnan(x))] = 1.0
            fund_holding[fund_holding.applymap(lambda x: np.isnan(x))] = 0.0
            fund_holding = fund_holding.mul(fund_turnover_fund, axis=1)
            fund_holding[fund_holding.applymap(lambda x: np.isnan(x))] = 0.0
            holdernumber = holdernumber.add(fund_holding, fill_value=0.0)

    date_series = list(holdernumber.columns)
    date_series_publish = list(map(lambda x: Date().get_trade_date_offset(x, offset_num), date_series))
    holdernumber.columns = date_series_publish
    holdernumber = holdernumber.T
    holdernumber = holdernumber.loc[beg_date:end_date, :]
    csv_file = r'C:\Users\doufucheng\OneDrive\Desktop\HolderBySFNumTurn.csv'
    holdernumber.to_csv(csv_file)

    date_series_daily = Date().get_trade_date_series(beg_date, end_date, "D")
    holdernumber = holdernumber.loc[date_series_daily, :]
    holdernumber = holdernumber.fillna(method='pad')
    holdernumber = holdernumber.dropna(how='all').T
    holdernumber = holdernumber.replace(0.0, np.nan)

    # save data
    #############################################################################
    Stock().write_factor_h5(holdernumber, factor_name, "my_alpha")
    return holdernumber
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()
    data = HolderBySFNumTurn(beg_date, end_date)


