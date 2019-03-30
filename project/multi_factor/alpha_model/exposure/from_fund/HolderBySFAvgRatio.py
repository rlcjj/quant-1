import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.fund.fund import Fund
import os
from quant.stock.stock_factor_operate import StockFactorOperate


def HolderBySFAvgRatio(beg_date, end_date):

    """
    因子说明：被主动股票基金季报持有在前十大重仓的平均比例 / 自由流通市值
    数据可得时间在每季度末的15个工作日之后
    """

    # 参数
    ###########################################################################################
    offset_num = 16
    factor_name = "HolderBySFAvgRatio"
    fund_pool_date = "20180630"
    fund_pool_name = "基金持仓基准基金池"
    beg_date = Date().change_to_str(beg_date)
    end_date = Date().change_to_str(end_date)

    fund_pool = Fund().get_fund_pool_code(date=fund_pool_date, name=fund_pool_name)
    stock_ratio = Fund().get_fund_factor('Stock_Ratio', None, None)
    stock_mv = pd.DataFrame([])

    # 每个基金叠加
    ###########################################################################################
    for i_fund in range(0, len(fund_pool)):

        fund = fund_pool[i_fund]
        fund_holding = Fund().get_fund_holding_quarter(fund=fund)
        if fund_holding is not None:
            fund_holding[fund_holding.applymap(lambda x: np.isnan(x))] = 0.0
            stock_ratio_quarter = stock_ratio[fund]
            stock_ratio_quarter = stock_ratio_quarter.loc[list(fund_holding.columns)]
            fund_stock_mv = fund_holding.mul(stock_ratio_quarter, axis='columns') / 100.0
            stock_mv = stock_mv.add(fund_stock_mv, fill_value=0.0)

    date_series = list(stock_mv.columns)
    date_series_publish = list(map(lambda x: Date().get_trade_date_offset(x, offset_num), date_series))
    stock_mv.columns = date_series_publish
    stock_mv = stock_mv.T
    stock_mv = stock_mv.loc[beg_date:end_date, :]

    free_mv = Stock().read_factor_h5("MarketFreeShares").T
    ratio = stock_mv.div(free_mv)
    ratio = ratio.dropna(how='all')

    csv_file = r'C:\Users\doufucheng\OneDrive\Desktop\HolderBySFNumber.csv'
    ratio.to_csv(csv_file)

    date_series_daily = Date().get_trade_date_series(beg_date, end_date, "D")
    ratio = ratio.loc[date_series_daily, :]
    ratio = ratio.fillna(method='pad')
    ratio = ratio.dropna(how='all').T
    ratio = ratio.replace(0.0, np.nan)

    # save data
    #############################################################################
    Stock().write_factor_h5(ratio, factor_name, "my_alpha")
    return ratio
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()
    data = HolderBySFAvgRatio(beg_date, end_date)


