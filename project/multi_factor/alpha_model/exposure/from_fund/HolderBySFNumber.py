import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.fund.fund import Fund
import os
from quant.stock.stock_factor_operate import StockFactorOperate


def HolderBySFNumber(beg_date, end_date):

    """
    因子说明：被主动股票基金季报持有在前十大重仓的基金数量 持有数量0转化为NAN
    数据可得时间在每季度末的15个工作日之后
    """

    # 参数
    ###########################################################################################
    offset_num = 16
    factor_name = "HolderBySFNumber"
    fund_pool_date = "20180630"
    fund_pool_name = "基金持仓基准基金池"
    beg_date = Date().change_to_str(beg_date)
    end_date = Date().change_to_str(end_date)

    fund_pool = Fund().get_fund_pool_code(date=fund_pool_date, name=fund_pool_name)
    holdernumber = pd.DataFrame([])

    # 每个基金叠加
    ###########################################################################################
    for i_fund in range(0, len(fund_pool)):

        fund = fund_pool[i_fund]
        fund_holding = Fund().get_fund_holding_quarter(fund=fund)
        if fund_holding is not None:
            print(fund)
            fund_holding[fund_holding.applymap(lambda x: ~np.isnan(x))] = 1.0
            fund_holding[fund_holding.applymap(lambda x: np.isnan(x))] = 0.0
            holdernumber = holdernumber.add(fund_holding, fill_value=0.0)

    date_series = list(holdernumber.columns)
    date_series_publish = list(map(lambda x: Date().get_trade_date_offset(x, offset_num), date_series))
    holdernumber.columns = date_series_publish
    holdernumber = holdernumber.T
    holdernumber = holdernumber.loc[beg_date:end_date, :]
    csv_file = r'C:\Users\doufucheng\OneDrive\Desktop\HolderBySFNumber.csv'
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
    data = HolderBySFNumber(beg_date, end_date)


