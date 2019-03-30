import pandas as pd
import numpy as np
from quant.stock.date import Date
import os
from quant.fund.fund import Fund


def FundReturnAfter(report_date):

    """
    计算在给定时间点后一个季度的的收益
    """

    T = 60
    beg_date = Date().get_trade_date_offset(report_date, -0)
    end_date = Date().get_trade_date_offset(report_date, T)
    date_series = Date().get_trade_date_series(beg_date, end_date)

    fund_code_list = Fund().get_fund_pool_code(date=report_date, name="基金持仓基准基金池")
    fund_code_list3 = Fund().get_fund_pool_code(date=report_date, name="量化基金")
    fund_code_list2 = Fund().get_fund_pool_code(date="20180630", name="东方红基金")
    fund_code_list.extend(fund_code_list2)
    fund_code_list.extend(fund_code_list3)
    fund_code_list = list(set(fund_code_list))
    fund_code_list.sort()

    fund_pct = Fund().get_fund_factor("Repair_Nav_Pct", date_series, fund_code_list)
    print(" Calculting fund Return At date %s " % report_date)
    fund_pct[fund_pct == 0] = np.nan
    fund_pct_period = pd.DataFrame(fund_pct.sum(skipna=True).values, index=fund_pct.columns, columns=[report_date])
    fund_pct_period[fund_pct_period == 0] = np.nan

    return fund_pct_period


def FundReturnAfterAll():

    beg_date = "20040101"
    end_date = "20180815"
    path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    date_series = Date().get_normal_date_series(beg_date, end_date, "Q")

    for i in range(len(date_series)):
        date = date_series[i]
        if i == 0:
            fund_pct = FundReturnAfter(report_date=date)
        else:
            fund_pct_add = FundReturnAfter(report_date=date)
            fund_pct = pd.concat([fund_pct, fund_pct_add], axis=1)

    file = "FundReturnAfter.csv"
    file = os.path.join(path, "FundReturn", file)
    fund_pct.to_csv(file)


if __name__ == '__main__':

    FundReturnAfterAll()
