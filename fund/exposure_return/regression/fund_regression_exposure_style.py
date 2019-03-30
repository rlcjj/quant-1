import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import cvxopt.solvers as sol
from cvxopt import matrix
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.barra import Barra
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate


class FundRegressionExposureStyle(Data):

    """
    利用有约束的线性回归的方法推测当前基金的Barra风格暴露

    将回归转化成为二次规划：限制基金的仓位上下限 和风格暴露上下限

    cal_fund_regression_exposure()
    cal_fund_regression_exposure_all()
    get_fund_regression_exposure()
    """

    def __init__(self):

        Data.__init__(self)
        self.regression_exposure_name = 'Fund_Regression_Exposure_Style'
        self.regression_period = 60
        self.regression_period_min = 40
        self.sub_data_path = r'fund_data\fund_exposure'
        self.data_path_exposure = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_fund_regression_exposure_style(self, fund, beg_date, end_date, period="D"):

        # 参数
        ####################################################################
        up_style_exposure = 1.25
        up_position_exposure = 0.95
        low_position_exposure = 0.75
        position_sub = 0.08

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        # 取得数据 因子收益率数据 和 基金涨跌幅数据
        ####################################################################
        type_list = ['STYLE', 'COUNTRY']

        barra_name = list(Barra().get_factor_name(type_list)['NAME_EN'].values)
        barra_return = Barra().get_factor_return(None, None, type_list)

        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)

        if fund[len(fund)-2:] == 'OF':
            fund_return = FundFactor().get_fund_factor("Repair_Nav_Pct", None, [fund])
        else:
            fund_return = Index().get_index_factor(fund, attr=["PCT"]) * 100
            fund_return.columns = [fund]

        data = pd.concat([fund_return, barra_return], axis=1)
        data = data.dropna()
        print(" Fund Code Total Len %s " % len(data))
        factor_number = len(barra_name)
        stock_ratio = FundFactor().get_fund_factor("Stock_Ratio", None, [fund]) / 100

        date_series = list(set(date_series) & set(data.index))
        date_series.sort()

        # 循环回归计算每天的暴露 计算当天的暴露之时需要 前一天及之前数据
        ####################################################################

        for i_date in range(0, len(date_series)):

            # 回归所需要的数据
            ####################################################################
            period_end_date = date_series[i_date]
            period_beg_date = Date().get_trade_date_offset(period_end_date, -self.regression_period)
            data_end_date = Date().get_trade_date_offset(period_end_date, -0)

            period_date_series = Date().get_trade_date_series(period_beg_date, data_end_date)
            data_periods = data.ix[period_date_series, :]
            data_periods = data_periods.dropna()

            # 上个季度基金仓位
            #####################################################################################
            quarter_date = Date().get_last_fund_quarter_date(period_end_date)
            stock_ratio_fund = stock_ratio.loc[quarter_date, fund]
            print("########## Calculate Regression Exposure %s %s %s %s %s %s ##########"
                  % (fund, period_beg_date, period_end_date, quarter_date, len(data_periods), stock_ratio_fund))

            if len(data_periods) > self.regression_period_min:

                y = data_periods.ix[:, 0].values
                x = data_periods.ix[:, 1:].values
                x_add = sm.add_constant(x)

                low_position_exposure = max(stock_ratio_fund - position_sub, low_position_exposure)
                if np.isnan(low_position_exposure):
                    low_position_exposure = 0.75

                P = 2 * np.dot(x_add.T, x_add)
                Q = -2 * np.dot(x_add.T, y)

                G_up = np.diag(np.ones(factor_number + 1))
                G_low = - np.diag(np.ones(factor_number + 1))
                G = np.row_stack((G_up, G_low))
                h_up = np.row_stack((np.ones((factor_number, 1)) * up_style_exposure, np.array([up_position_exposure])))
                h_low = np.row_stack((np.ones((factor_number, 1)) * up_style_exposure, np.array([-low_position_exposure])))
                h = np.row_stack((h_up, h_low))

                P = matrix(P)
                Q = matrix(Q)
                G = matrix(G)
                h = matrix(h)
                try:
                    result = sol.qp(P, Q, G, h)
                    params_add = pd.DataFrame(np.array(result['x'][1:]), columns=[period_end_date], index=barra_name).T
                    print(params_add)
                except Exception as e:
                    params_add = pd.DataFrame([], columns=[period_end_date], index=barra_name).T
                    print(params_add)

            else:
                params_add = pd.DataFrame([], columns=[period_end_date], index=barra_name).T
                print(params_add)

            if i_date == 0:
                params_new = params_add
            else:
                params_new = pd.concat([params_new, params_add], axis=0)

        # 合并新数据
        ####################################################################
        out_path = os.path.join(self.data_path_exposure, 'fund_regression_exposure_style')
        out_file = os.path.join(out_path, 'Fund_Regression_Exposure_Style_' + fund + '.csv')

        if os.path.exists(out_file):
            params_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            params_old.index = params_old.index.map(str)
            params = FactorOperate().pandas_add_row(params_old, params_new)
        else:
            params = params_new
        print(params)
        params.to_csv(out_file)

    def cal_fund_regression_exposure_style_all(self, beg_date, end_date, period="M", fund_pool="基金持仓基准基金池"):

        quarter_date = Date().get_last_fund_quarter_date(end_date)
        fund_pool = FundPool().get_fund_pool_code(quarter_date, fund_pool)

        for i_fund in range(0, len(fund_pool)):
            fund_code = fund_pool[i_fund]
            self.cal_fund_regression_exposure_style(fund_code, beg_date, end_date, period)

    def get_fund_regression_exposure_style(self, fund):

        out_path = os.path.join(self.data_path_exposure, 'fund_regression_exposure_style')
        out_file = os.path.join(out_path, 'Fund_Regression_Exposure_Style_' + fund + '.csv')
        print(out_file)
        try:
            exposure = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure.index = exposure.index.map(str)
        except Exception as e:
            exposure = None
        return exposure

    def get_fund_regression_exposure_style_date(self, fund, date):

        try:
            exposure = self.get_fund_regression_exposure_style(fund)
            exposure = pd.DataFrame(exposure.ix[date, :].values, index=exposure.columns, columns=[fund])
        except Exception as e:
            exposure = None
        return exposure


if __name__ == "__main__":

    # fund = '229002.OF'
    fund = "881001.WI"
    fund = "885012.WI"
    fund = "000300.SH"
    beg_date = "20140101"
    end_date = datetime.today().strftime("%Y%m%d")

    # FundRegressionExposureStyle().cal_fund_regression_exposure_style(fund, beg_date, end_date)
    # FundRegressionExposureStyle().cal_fund_regression_exposure_style_all("20031231", end_date, period="D")
    # FundRegressionExposureStyle().cal_fund_regression_exposure_style_all("20031231", end_date, period="D", fund_pool="量化基金")
    FundRegressionExposureStyle().cal_fund_regression_exposure_style_all("20031231", end_date, period="D", fund_pool="指数增强型基金")
