import pandas as pd
import cvxopt.solvers as sol
from cvxopt import matrix
from quant.stock.date import Date
from quant.stock.index import Index
import numpy as np
import os
from quant.project.fund.fund_selected_department.fund_regression_exposure_index import FundRegressionExposureIndex
from quant.project.fund.fund_selected_department.fund_regression_risk_alpha_return_index import FundRegressionRiskAlphaReturnIndex
from quant.utility.asset_allocation import AssetAllocation


class StockFundPortfolio(object):

    """
    对于组合优化来讲 有两种方式
    1、最大化alpha 约束风格偏露（线性规划）
    s.t. Max alpha
    风格平价暴露下限 < 组合暴露 < 风格平价暴露上限
    基金权重下限 < 基金权重 < 基金权重上限
    权重和为1

    2、最大化alpha - 风格偏露  不约束风格偏露（二次规划）
    s.t. Max alpha- 风格偏露*lambda
    基金权重下限 < 基金权重 < 基金权重上限
    权重和为1

    采用方法1 经常没有优化结果，因为基金池太小，达不到约束要求，若采用大基金池，也许可行
    因子最终采用方法2 需要调参 lambda
    """

    def __init__(self):

        self.index_code_list = ["CI005909.WI", "CI005910.WI", "CI005911.WI", "CI005912.WI", "CI005913.WI",
                                "CI005914.WI", "CI005915.WI", "CI005916.WI"]
        self.fund_pool = ["001017.OF", "002263.OF", '229002.OF',
                          '162213.OF', '001733.OF', '004484.OF', '162216.OF', '162211.OF']

    def get_index_return_daily(self, beg_date, end_date):

        # 参数整理
        ####################################################################
        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        # 取得 指数收益率数据
        ####################################################################
        for i_index in range(len(self.index_code_list)):
            index_code = self.index_code_list[i_index]
            index_return = Index().get_index_factor(index_code, attr=["PCT"])
            if i_index == 0:
                index_return = Index().get_index_factor(index_code, attr=["PCT"])
                index_return_all = index_return
            else:
                index_return_all = pd.concat([index_return_all, index_return], axis=1)

        index_return_all.columns = self.stock_index_code_list
        index_return_all = index_return_all.loc[beg_date:end_date, :]
        index_return_all = index_return_all.dropna()

        return index_return_all

    def get_index_weight_riskparity(self, end_date):

        # 利用风险平价的方法求解不同指数的权重
        ####################################################################
        beg_date = Date().get_trade_date_offset(end_date, -120)
        data = self.get_index_return_daily(beg_date, end_date)
        cov = data.cov() * 250
        weight = AssetAllocation().cal_risk_parity_weights(cov)
        return weight

    def get_fund_exposure(self, end_date):

        # 取得基金的暴露
        ####################################################################
        beg_date = Date().get_trade_date_offset(end_date, -40)
        fund_pool = self.fund_pool

        for i in range(len(fund_pool)):
            fund = fund_pool[i]
            exposure = FundRegressionExposureIndex().get_fund_regression_exposure_index(fund)
            exposure = exposure.loc[beg_date:end_date, :]
            exposure_fund = exposure.median()
            if i == 0:
                exposure_all = exposure_fund
            else:
                exposure_all = pd.concat([exposure_all, exposure_fund], axis=1)
        exposure_all.columns = fund_pool
        return exposure_all.T

    def get_fund_alpha(self, end_date):

        # 取得基金的alpha
        ####################################################################
        period = 180
        beg_date = Date().get_trade_date_offset(end_date, -period)
        fund_pool = self.fund_pool

        alpha_all = pd.DataFrame([], index=fund_pool, columns=["AlphaMed"])
        for i in range(len(fund_pool)):
            fund = fund_pool[i]
            alpha = FundRegressionRiskAlphaReturnIndex().get_fund_regression_risk_alpha_return_index(fund)
            alpha = alpha.loc[beg_date:end_date, "AlphaReturn"]
            if len(alpha) > 0:
                alpha_all.loc[fund, "AlphaMed"] = alpha.median()
                std = alpha.ewm(halflife=int(period / 2)).std().loc[alpha.index[len(alpha) - 1]]
                alpha_all.loc[fund, "AlphaStd"] = std
                alpha_all.loc[fund, "AlphaIR"] = alpha.median() / std

        return alpha_all

    def opt_fund_portfolio_1(self, end_date):

        exposure_low = 0.70
        exposure_up = 1.10
        stock_up = 0.5
        stock_low = 0.0
        stock_index_code_list = ["000300.SH", "000905.SH"]
        fund_pool = self.fund_pool

        alpha = self.get_fund_alpha(end_date)
        alpha = alpha.dropna()
        alpha = pd.DataFrame(alpha["AlphaIR"])
        alpha["AlphaIR"] = alpha['AlphaIR'].map(float)

        exposure = self.get_fund_exposure(end_date)
        exposure = exposure.dropna(how='all')
        exposure = exposure.loc[alpha.index, :]

        index_weight = self.get_stock_index_weight_riskparity(end_date)
        index_weight['Up'] = index_weight["weight"] * exposure_up
        index_weight['Low'] = index_weight["weight"] * exposure_low

        alpha = alpha.loc[fund_pool, :]
        exposure = exposure.loc[fund_pool, stock_index_code_list]
        index_weight = index_weight.loc[stock_index_code_list, :]

        exposure = exposure.T
        alpha["Alpha"] = alpha['Alpha'].map(float)
        C = alpha.values

        # 暴露 上限 下限
        ###################################################
        G_up = exposure.values
        G_low = - exposure.values
        G_exposure = np.row_stack((G_up, G_low))
        h_up = np.row_stack(index_weight['Up'].values)
        h_low = - np.row_stack(index_weight['Low'].values)
        h_exposure = np.row_stack((h_up, h_low))

        # 仓位 上限 下限
        ###################################################
        G_up = np.diag(np.ones(len(alpha)))
        G_low = - np.diag(np.ones(len(alpha)))
        G = np.row_stack((G_up, G_low))
        h_up = np.row_stack(np.ones((len(alpha)))) * stock_up
        h_low = np.row_stack(np.ones((len(alpha)))) * stock_low
        h = np.row_stack((h_up, h_low))

        G = np.row_stack((G, G_exposure))
        h = np.row_stack((h, h_exposure))

        # 总和不超过1
        ###################################################
        A = np.column_stack(np.ones((len(alpha), 1)))
        b = np.array([1.0])

        G = np.row_stack((G, A))
        h = np.row_stack((h, b))

        C = matrix(C)
        G = matrix(G)
        h = matrix(h)

        result = sol.lp(C, G, h)
        res = pd.DataFrame(np.array(result['x'][0:]), index=alpha.index, columns=['Weight'])
        res = res[res.Weight > 0.001]

        exposure_res = exposure.loc[:, res.index]
        exposure_res = exposure_res.T

        exposure_res = pd.concat([res, exposure_res], axis=1)
        exposure_weight = exposure_res.mul(res['Weight'], axis='index')
        exposure_res.loc['Sum', :] = exposure_weight.sum()
        exposure_res.loc['Sum', 'Weight'] = exposure_res['Weight'].sum()

        exposure_res = pd.concat([exposure_res, index_weight.T], axis=0)

        print('########################### Port 1 %s ###########################' % end_date)
        print(exposure_res)

    def opt_fund_portfolio_qp(self, end_date):

        # 参数
        ####################################################################################################
        stock_up = 0.5
        stock_low = 0.0
        lamb = 4  # 平衡alpha和风格偏离 越大 alpha越重要
        port_path = r'E:\3_Data\5_stock_data\4_portfolio_wind'
        port_name = "行业风格平价FOF"

        # 得到基金暴露 基金alpha 指数权重等数据
        ####################################################################################################
        fund_pool = self.fund_pool
        alpha = self.get_fund_alpha(end_date)

        alpha = alpha.dropna()
        alpha = pd.DataFrame(alpha["AlphaIR"])
        alpha["AlphaIR"] = alpha['AlphaIR'].map(float)

        exposure = self.get_fund_exposure(end_date)
        exposure = exposure.dropna(how='all')
        exposure = exposure.loc[alpha.index, :]

        index_weight = self.get_index_weight_riskparity(end_date)

        # 整理数据
        ####################################################################################################
        fund_pool = list(set(fund_pool) & set(alpha.index))
        fund_pool.sort()
        alpha = alpha.loc[fund_pool, :]
        exposure = exposure.loc[fund_pool, self.index_code_list]
        index_weight = index_weight.loc[self.index_code_list, :]

        exposure = exposure.T

        # 基金权重的上下限
        ####################################################################################################
        G_up = np.diag(np.ones(len(alpha)))
        G_low = - np.diag(np.ones(len(alpha)))
        G = np.row_stack((G_up, G_low))
        h_up = np.row_stack(np.ones((len(alpha)))) * stock_up
        h_low = np.row_stack(np.ones((len(alpha)))) * stock_low
        h = np.row_stack((h_up, h_low))

        # 基金总权重 = 1
        ####################################################################################################
        A = np.column_stack(np.ones((len(alpha), 1)))
        b = np.array([1.0])

        # 优化权重
        ####################################################################################################
        P = 2 * np.dot(np.transpose(exposure.values), exposure.values)
        Q = -2 * np.dot(np.transpose(exposure.values), index_weight.values) - lamb * alpha.values

        P = matrix(P)
        Q = matrix(Q)
        G = matrix(G)
        h = matrix(h)
        A = matrix(A)
        b = matrix(b)
        result = sol.qp(P, Q, G, h, A, b)

        # 整理优化结果
        ####################################################################################################
        res = pd.DataFrame(np.array(result['x'][0:]), index=alpha.index, columns=['Weight'])
        res = res[res.Weight > 0.001]

        exposure_res = exposure.loc[:, res.index]
        exposure_res = exposure_res.T

        exposure_res = pd.concat([res, exposure_res], axis=1)
        exposure_weight = exposure_res.mul(res['Weight'], axis='index')
        exposure_res.loc['Sum', :] = exposure_weight.sum()
        exposure_res.loc['Sum', 'Weight'] = exposure_res['Weight'].sum()

        exposure_res = pd.concat([exposure_res, index_weight.T], axis=0)

        print('########################### Begin Opt Fund Port %s ###########################' % end_date)
        print(exposure_res)

        # 生成文件 存储结果
        ####################################################################################################
        sub_path = os.path.join(port_path, port_name)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data = res
        if len(data) > 0:
            data["Code"] = data.index
            data["Price"] = 0.0
            data["Direction"] = "Long"
            data["CreditTrading"] = "No"
            data["Date"] = end_date

            file = port_name + "_" + end_date + '.csv'
            file = os.path.join(sub_path, file)
            data.to_csv(file, index=False)
            ####################################################################################################

if __name__ == '__main__':

    # self = StockFundPortfolio()
    # beg_date = "20180101"
    # end_date = "20180909"
    # i = 9
    # fund_pool = pd.read_excel(self.fund_pool_file, index_col=[0])
    # fund_pool = list(fund_pool.Code)
    # fund = fund_pool[i]

    date_list = Date().get_normal_date_series("20141230", "20181001", period="Q")

    for date in date_list:
        # FundPortfolio().opt_fund_portfolio_1(date)
        StockFundPortfolio().opt_fund_portfolio_2(date)

    from quant.source.wind_portfolio import WindPortUpLoad
    WindPortUpLoad().upload_weight_period("行业风格平价FOF")

    from quant.source.backtest_fund import PortBackTestFund
    Index().load_index_factor("885001.WI")
    backtest = PortBackTestFund()
    backtest.set_info("行业风格平价FOF", "885001.WI")
    backtest.set_weight_at_all_change_date()
    backtest.cal_turnover()
    backtest.set_weight_at_all_daily()
    backtest.cal_port_return()
    backtest.cal_summary()