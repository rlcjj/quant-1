import os

import numpy as np
import pandas as pd
from fund.exposure_return.regression.fund_regression_risk_alpha_return_style import FundRegressionRiskAlphaReturnStyle
from quant.fund.fund_pool import FundPool
from quant.stock.date import Date


class FundRegressionReturnStyleBackTest(object):

    def __init__(self):

        self.path = r"E:\3_Data\4_fund_data\2_fund_factor\alpha_factor"

    def cal_fund_regression_return_style_backtest(self, fund, T, date_series, col="AlphaReturn", type="Mean"):

        data = FundRegressionRiskAlphaReturnStyle().get_fund_regression_risk_alpha_return_style(fund)
        result = pd.DataFrame([], index=date_series, columns=[fund])

        for i_date in range(len(date_series)):

            data_end_date = date_series[i_date]
            data_beg_date = Date().get_trade_date_offset(data_end_date, -T)

            if data is not None:
                data_date = data.loc[data_beg_date:data_end_date]
                if len(data_date) > 0:
                    if type == "Mean":
                        result.loc[data_end_date, fund] = data_date[col].mean()
                    elif type == "IR":
                        result.loc[data_end_date, fund] = data_date[col].mean() / data_date[col].std()
                    else:
                        result.loc[data_end_date, fund] = np.nan
                else:
                    result.loc[data_end_date, fund] = np.nan
            else:
                result.loc[data_end_date, fund] = np.nan

        return result

    def cal_fund_regression_return_style_backtest_all(self, T, beg_date, end_date,
                                                      col="AlphaReturn", type="Mean"):

        date_series = Date().get_trade_date_series(beg_date, end_date, "M")
        result = pd.DataFrame([], index=date_series)

        # 基金池信息
        ######################################################################################################
        fund_code_list = FundPool().get_fund_pool_code(date="20180630", name="基金持仓基准基金池")
        # fund_code_list3 = FundPool().get_fund_pool_code(date="20180630", name="量化基金")
        fund_code_list2 = FundPool().get_fund_pool_code(date="20180630", name="东方红基金")
        # fund_code_list4 = FundPool().get_fund_pool_code(date="20180630", name="指数型基金")
        fund_code_list.extend(fund_code_list2)
        # fund_code_list.extend(fund_code_list3)
        # fund_code_list.extend(fund_code_list4)
        fund_code_list = list(set(fund_code_list))
        fund_code_list.sort()

        for i_fund in range(len(fund_code_list)):
            fund = fund_code_list[i_fund]
            print(fund)
            if i_fund == 0:
                result = self.cal_fund_regression_return_style_backtest(fund, T, date_series, col, type)
            else:
                result_add = self.cal_fund_regression_return_style_backtest(fund, T, date_series, col, type)
                result = pd.concat([result, result_add], axis=1)

        result = result.T
        file = os.path.join(self.path, "FundRegressionStyle_" + col + type + "_" + str(T) + '.csv')
        result.to_csv(file)


if __name__ == "__main__":

    beg_date = "20041231"
    end_date = "20180909"
    FundRegressionReturnStyleBackTest().cal_fund_regression_return_style_backtest_all(240, beg_date, end_date, "AlphaReturn", "Mean")
    FundRegressionReturnStyleBackTest().cal_fund_regression_return_style_backtest_all(240, beg_date, end_date, "AlphaReturn", "IR")
    FundRegressionReturnStyleBackTest().cal_fund_regression_return_style_backtest_all(480, beg_date, end_date, "AlphaReturn", "Mean")
    FundRegressionReturnStyleBackTest().cal_fund_regression_return_style_backtest_all(480, beg_date, end_date, "AlphaReturn", "IR")
    FundRegressionReturnStyleBackTest().cal_fund_regression_return_style_backtest_all(720, beg_date, end_date, "AlphaReturn", "Mean")
    FundRegressionReturnStyleBackTest().cal_fund_regression_return_style_backtest_all(720, beg_date, end_date, "AlphaReturn", "IR")
