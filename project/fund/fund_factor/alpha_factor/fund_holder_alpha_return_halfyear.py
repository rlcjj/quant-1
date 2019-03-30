import os

import numpy as np
import pandas as pd
from fund.exposure_return.holder.fund_holder_risk_alpha_return_halfyear import FundHolderRiskAlphaReturnHalfYear
from quant.fund.fund_pool import FundPool
from quant.stock.date import Date


class FundHolderReturnHalfYearBackTest(object):

    def __init__(self):

        self.path = r"E:\3_Data\4_fund_data\2_fund_factor\alpha_factor"

    def cal_fund_holder_return_halfyear_backtest(self, fund, T, end_date, col="AlphaReturn", type="Mean"):

        beg_date = Date().get_trade_date_offset(end_date, -T)
        data = FundHolderRiskAlphaReturnHalfYear().get_fund_holder_risk_alpha_return_halfyear(fund, end_date)
        data = data.loc[beg_date:end_date]

        if len(data) > 0.8*T:

            if type == "Mean":
                res = data[col].mean()
            elif type == "IR":
                res = data[col].mean() / data[col].std()
            else:
                res = np.nan
        else:
            res = np.nan
        return res

    def cal_fund_holder_return_halfyear_backtest_all(self, T, beg_date, end_date,
                                                     col="AlphaReturn", type="Mean"):

        date_series = Date().get_normal_date_series(beg_date, end_date, "Q")
        result = pd.DataFrame([], index=date_series)

        for i in range(len(date_series)):

            # 日期
            ######################################################################################################
            report_date = date_series[i]

            # 基金池信息
            ######################################################################################################
            fund_code_list = FundPool().get_fund_pool_code(date=report_date, name="基金持仓基准基金池")
            fund_code_list3 = FundPool().get_fund_pool_code(date=report_date, name="量化基金")
            fund_code_list2 = FundPool().get_fund_pool_code(date="20180630", name="东方红基金")
            fund_code_list.extend(fund_code_list2)
            fund_code_list.extend(fund_code_list3)
            fund_code_list = list(set(fund_code_list))
            fund_code_list.sort()

            for i_fund in range(len(fund_code_list)):
                fund = fund_code_list[i_fund]
                print(report_date, fund)
                try:
                    res = self.cal_fund_holder_return_halfyear_backtest(fund, T, report_date, col, type)
                    result.loc[report_date, fund] = res
                except Exception as e:
                    result.loc[report_date, fund] = np.nan

        result = result.T
        file = os.path.join(self.path, "FundHolderHalfYear_" + col + type + "_" + str(T) + '.csv')
        result.to_csv(file)

if __name__ == "__main__":

    T = 480
    beg_date = "20041231"
    end_date = "20180909"
    col = "AlphaReturn"
    type = "Mean"
    FundHolderReturnHalfYearBackTest().cal_fund_holder_return_halfyear_backtest_all(T, beg_date, end_date, col, type)
    type = "IR"
    FundHolderReturnHalfYearBackTest().cal_fund_holder_return_halfyear_backtest_all(T, beg_date, end_date, col, type)
