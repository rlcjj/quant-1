from datetime import datetime
import os
import pandas as pd
import numpy as np
from quant.fund.fund_pool import FundPool
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.param.param import Parameter
from quant.stock.macro import Macro
import calendar


class MorningStarRiskAdjustedReturn(object):

    def __init__(self):

        self.path = r"E:\3_Data\4_fund_data\2_fund_factor\alpha_factor"

    def cal_factor_mrar(self, fund, T, r, end_date, fund_data, macro_data):

        # T = 12
        # r = 2

        def fun_date(x):
            year = int(x[0:4])
            month = int(x[4:6])
            day = calendar.monthrange(year, month)[1]
            date = datetime(year, month, day).strftime("%Y%m%d")
            return date

        end_date = Date().get_normal_date_last_month_end_day(end_date)
        fund_data = pd.DataFrame(fund_data.loc[:end_date, fund])
        fund_data = fund_data.dropna()
        fund_data["Month"] = fund_data.index.map(lambda x: x[0:6])
        fund_month = fund_data.groupby(by=["Month"]).sum()
        fund_month.index = fund_month.index.map(fun_date)

        concat_data = pd.concat([fund_month, macro_data], axis=1)
        concat_data.columns = ["FundReturn", "FreeRiskReturn"]
        concat_data = concat_data.dropna()
        concat_data["ExcessMonthRerurn"] = concat_data["FundReturn"] - concat_data["FreeRiskReturn"]

        excess_return = pd.DataFrame(concat_data.loc[concat_data.index[-T:], "ExcessMonthRerurn"])
        excess_return /= 100.0

        if len(excess_return) == T:
            excess_return["R"] = excess_return["ExcessMonthRerurn"].map(lambda x: (1+x)**(-r))
            res = excess_return["R"].mean() ** (-12/r)
        else:
            res = np.nan
        return res

    def cal_factor_mrar_all(self, T, r, beg_date, end_date):

        date_series = Date().get_normal_date_series(beg_date, end_date, "Q")
        result = pd.DataFrame([], index=date_series)

        def fun_date(x):
            year = int(x[0:4])
            month = int(x[4:6])
            day = calendar.monthrange(year, month)[1]
            date = datetime(year, month, day).strftime("%Y%m%d")
            return date

        macro_code = "S0059744"
        macro_name = "中债国债到期收益率-1年"
        macro_data = Macro().get_macro_data(macro_code, None, None)
        macro_data.columns = [macro_name]
        macro_data['YearMonth'] = macro_data.index.map(lambda x: x[0:6])
        macro_data = macro_data.groupby(by=['YearMonth']).mean()[macro_name]
        macro_data.index = macro_data.index.map(fun_date)
        macro_data = pd.DataFrame(macro_data)
        macro_data.columns = [macro_name]
        macro_data /= 12.0

        fund_data = Fund().get_fund_factor("Repair_Nav_Pct", None, None)

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
                    res = self.cal_factor_mrar(fund, T, r, end_date, fund_data, macro_data)
                    result.loc[report_date, fund] = res
                except Exception as e:
                    result.loc[report_date, fund] = np.nan

        result = result.T
        file = os.path.join(self.path, "MorningStar_MRAR_" + str(r) + "_" + str(T) + '.csv')
        result.to_csv(file)


if __name__ == "__main__":

    beg_date = "20040331"
    end_date = "20180909"
    fund = "000001.OF"
    T = 12
    r = 2
    MorningStarRiskAdjustedReturn().cal_factor_mrar_all(T, r, beg_date, end_date)