import pandas as pd
from quant.stock.barra import Barra
from quant.stock.date import Date
import os


def StockBarraDecomposeReturnQuarter(report_date):

    """
    计算在给定时间点前后一个月 所有股票 拆分的 特异收益 风格收益 行业收益 和 市场收益
    """

    T = 20
    beg_date = Date().get_trade_date_offset(report_date, -T)
    end_date = Date().get_trade_date_offset(report_date, T)
    date_series = Date().get_trade_date_series(beg_date, end_date)
    residual = Barra().get_stock_residual_return()

    result = {}
    for i in range(len(date_series)):

        date = date_series[i]
        residual_date = residual.loc[date, :]
        riskfactor_date = Barra().get_stock_riskfactor_return_date(date)
        residual_date = pd.DataFrame(residual_date.values, index=residual_date.index, columns=["Alpha"])
        all_return = pd.concat([residual_date, riskfactor_date], axis=1)
        result[date] = all_return

    result_panel = pd.Panel(result)
    pct_sum = result_panel.sum(axis=0)

    barra_name = Barra().get_factor_name(['STYLE'])
    barra_name = list(barra_name['NAME_EN'].values)
    pct_sum['Style'] = pct_sum.ix[:, barra_name].sum(axis=1)

    barra_name = Barra().get_factor_name(['INDUSTRY'])
    barra_name = list(barra_name['NAME_EN'].values)
    pct_sum['Industry'] = pct_sum.ix[:, barra_name].sum(axis=1)

    pct_sum['All'] = pct_sum[['ChinaEquity', 'Industry', 'Style', 'Alpha']].sum(axis=1)

    print(" StockBarraDecomposeReturnQuarter %s" % report_date)
    out_path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    file = os.path.join(out_path, "StockBarraDecomposeReturnQuarter", "StockBarraDecomposeReturnQuarter" + report_date + '.csv')
    pct_sum.to_csv(file)


def StockBarraDecomposeReturnAllQuarter():

    """
    计算所有季报时间点 前后一个月 所有股票 拆分的 特异收益 风格收益 行业收益 和 市场收益
    """

    beg_date = "20040101"
    end_date = "20180815"
    date_series = Date().get_normal_date_series(beg_date, end_date, "Q")

    for i in range(len(date_series)):
        date = date_series[i]
        StockBarraDecomposeReturnQuarter(report_date=date)

    return True

if __name__ == '__main__':

    StockBarraDecomposeReturnAllQuarter()
