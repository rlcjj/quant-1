import os
import numpy as np
import pandas as pd
import cvxopt.solvers as sol
from cvxopt import matrix
from datetime import datetime

from quant.stock.date import Date
from quant.stock.index import Index
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate


class FundRegressionExposureIndex(object):

    """
    利用有约束的线性回归的方法推测当前基金 在指数上的暴露
    将回归转化成为二次规划
    """

    def __init__(self):

        """
        中证国债 中证企业债
        绩优股指数 沪深300 中证500 中证1000 创业板指
        """

        self.data_path = r"E:\3_Data\4_fund_data\9_fund_selected_department\exposure"
        self.regression_period = 60
        self.regression_period_min = 40
        # self.file_prefix = "Fund_Regression_Risk_Alpha_Index_"
        self.file_prefix = "Fund_Regression_Exposure_Index_Industry_"
        # self.index_code_list = ["H11006.CSI", "H11008.CSI",
        #                         "801853.SI", "000300.SH", "000905.SH", "000852.SH", "399006.SZ"]
        self.index_code_list = ["H11006.CSI", "H11008.CSI",
                                "CI005909.WI", "CI005910.WI", "CI005911.WI", "CI005912.WI", "CI005913.WI",
                                "CI005914.WI", "CI005915.WI", "CI005916.WI"]

    def load_index_return(self, beg_date=None, end_date=None):

        """
        下载指数收益率
        """

        # 参数
        #############################################################
        if beg_date is None:
            end_date = datetime.today().strftime("%Y%m%d")

        if end_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -60)

        # 更新指数数据
        #############################################################
        for index_code in self.index_code_list:
            Index().load_index_factor(index_code, beg_date, end_date)

        #############################################################

    def cal_fund_regression_exposure_index(self, fund, beg_date, end_date, period="D"):

        """
        计算一只基金每日对不同指数的暴露
        """

        # 参数
        ####################################################################
        one_index_up_limit = 1.0
        one_index_low_limit = 0.0
        sum_index = 1.0

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        # 取得 指数收益率数据
        ####################################################################
        for i_index in range(len(self.index_code_list)):
            index_code = self.index_code_list[i_index]
            index_return = Index().get_index_factor(index_code, Nattr=["PCT"])
            if i_index == 0:
                index_return = Index().get_index_factor(index_code, attr=["PCT"])
                index_return_all = index_return
            else:
                index_return_all = pd.concat([index_return_all, index_return], axis=1)

        index_return_all.columns = self.index_code_list

        # 取得 基金涨跌幅数据
        ####################################################################
        if fund[len(fund)-2:] == 'OF':
            fund_return = FundFactor().get_fund_factor("Repair_Nav_Pct", None, [fund]) / 100.0
        else:
            fund_return = Index().get_index_factor(fund, attr=["PCT"])
            fund_return.columns = [fund]

        # 合并数据
        ####################################################################
        data = pd.concat([fund_return, index_return_all], axis=1)
        data = data.dropna(subset=[fund])

        # 回归日期
        ####################################################################
        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        date_series = list(set(date_series) & set(data.index))
        date_series.sort()

        # 循环优化计算每天的暴露
        ####################################################################

        for i_date in range(0, len(date_series)):

            # 约束回归所需要的数据
            #############################################################################################
            period_end_date = date_series[i_date]
            period_beg_date = Date().get_trade_date_offset(period_end_date, -self.regression_period)

            period_date_series = Date().get_trade_date_series(period_beg_date, period_end_date)
            data_periods = data.ix[period_date_series, :]
            data_periods = data_periods.dropna(subset=[fund])
            data_periods = data_periods.T.dropna(how='all').T
            data_periods = data_periods.T.fillna(data_periods.mean(axis=1)).T
            data_periods = data_periods.dropna()

            # 有约束的回归 可以转换为二次规划
            #############################################################################################
            if len(data_periods) > self.regression_period_min and (len(data_periods.columns) > 1):

                # 平方和最小
                #############################################################################################
                y = data_periods.ix[:, 0].values
                x = data_periods.ix[:, 1:].values

                P = 2 * np.dot(x.T, x)
                Q = -2 * np.dot(x.T, y)

                # 单个指数上下限为 0
                #############################################################################################
                G_up = np.diag(np.ones(x.shape[1]))
                G_low = - np.diag(np.ones(x.shape[1]))
                G = np.row_stack((G_up, G_low))
                h_up = np.row_stack(np.ones((x.shape[1], 1))) * one_index_up_limit
                h_low = - np.row_stack(np.ones((x.shape[1], 1))) * one_index_low_limit
                h = np.row_stack((h_up, h_low))

                #############################################################################################
                A = np.column_stack(np.ones((x.shape[1], 1)))
                b = np.array([sum_index])

                # 开始规划求解
                ############################################################################################
                try:
                    P = matrix(P)
                    Q = matrix(Q)
                    G = matrix(G)
                    h = matrix(h)
                    A = matrix(A)
                    b = matrix(b)
                    result = sol.qp(P, Q, G, h, A, b)
                    params_add = pd.DataFrame(np.array(result['x'][0:]),
                                              columns=[period_end_date], index=data_periods.columns[1:]).T
                    print("########## Fund Regression Index Exposure GF %s %s ##########" % (fund, period_end_date))
                except Exception as e:
                    params_add = pd.DataFrame([], columns=[period_end_date], index=data_periods.columns[1:]).T
                    print("########## Quadratic Programming is InCorrect %s %s ##########" % (fund, period_end_date))
            else:
                params_add = pd.DataFrame([], columns=[period_end_date], index=data_periods.columns[1:]).T
                print("########## Fund Regression Data Len is Too Small %s %s ##########" % (fund, period_end_date))

            if i_date == 0:
                params_new = params_add
            else:
                params_new = pd.concat([params_new, params_add], axis=0)

        # 合并新数据 并存储数据
        ####################################################################
        out_file = os.path.join(self.data_path, self.file_prefix + fund + '.csv')

        if os.path.exists(out_file):
            params_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            params_old.index = params_old.index.map(str)
            params = FactorOperate().pandas_add_row(params_old, params_new)
        else:
            params = params_new
        params.to_csv(out_file)
        ####################################################################

    def cal_fund_regression_exposure_index_all(self, beg_date, end_date, period="D",
                                               fund_pool_file="Stock_Fund_Info.xlsx"):

        file = fund_pool_file
        fund_pool = pd.read_excel(file, index_col=[0])
        fund_pool = list(fund_pool.Code)
        # fund_pool = ["001017.OF", "002263.OF", '229002.OF',
        #              '162213.OF', '001733.OF', '004484.OF', '162216.OF', '162211.OF']

        for i_fund in range(0, len(fund_pool)):
            fund_code = fund_pool[i_fund]
            self.cal_fund_regression_exposure_index(fund_code, beg_date, end_date, period)

    def get_fund_regression_exposure_index(self, fund):

        out_file = os.path.join(self.data_path, self.file_prefix + fund + '.csv')
        try:
            exposure = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure.index = exposure.index.map(str)
        except Exception as e:
            exposure = None
        return exposure

    def get_fund_regression_exposure_index_date(self, fund, date):

        try:
            exposure = self.get_fund_regression_exposure_index(fund)
            exposure = pd.DataFrame(exposure.ix[date, :].values, index=exposure.columns, columns=[fund])
        except Exception as e:
            exposure = None
        return exposure


if __name__ == "__main__":

    ############################################################################################################
    fund = '229002.OF'
    beg_date = "20040101"
    end_date = datetime.today().strftime("%Y%m%d")
    period = "D"
    file = r"E:\3_Data\4_fund_data\9_fund_selected_department\fund_pool\Stock_Fund_Info.xlsx"

    FundRegressionExposureIndex().load_index_return("20040101", end_date)  # 下载指数收益率
    FundRegressionExposureIndex().cal_fund_regression_exposure_index_all(beg_date, end_date, period, file)
    ############################################################################################################

