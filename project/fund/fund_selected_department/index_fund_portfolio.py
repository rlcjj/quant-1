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
    组合优化 最大化alpha - 风格偏露  不约束风格偏露（二次规划）
    s.t. Max alpha- 风格偏露*lambda
    基金权重下限 < 基金权重 < 基金权重上限
    权重和为1
    """

    def __init__(self):

        self.stock_index_pool = ["CI005909.WI", "CI005910.WI", "CI005911.WI", "CI005912.WI", "CI005913.WI",
                                 "CI005914.WI", "CI005915.WI", "CI005916.WI"]
        self.bond_index_pool = ["H11006.CSI", "H11008.CSI"]
        self.fund_pool = ["001017.OF", "002263.OF", '229002.OF', '162213.OF',
                          '001733.OF', '004484.OF', '162216.OF', '162211.OF']

        file = r"E:\3_Data\4_fund_data\9_fund_selected_department\fund_pool\Stock_Fund_Info.xlsx"
        fund_pool = pd.read_excel(file)
        fund_pool = list(fund_pool.Code)
        self.fund_pool = fund_pool
        self.period_risk_parity = 120
        self.period_alpha = 180
        self.period_exposure = 40

    def get_index_return_daily(self, beg_date, end_date, type="multi_factor"):

        # 参数整理
        ####################################################################
        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        if type == "multi_factor":
            index_pool = self.stock_index_pool
        else:
            index_pool = self.bond_index_pool

        # 取得 指数收益率数据
        ####################################################################
        for i_index in range(len(index_pool)):
            index_code = index_pool[i_index]
            index_return = Index().get_index_factor(index_code, attr=["PCT"])
            if i_index == 0:
                index_return = Index().get_index_factor(index_code, attr=["PCT"])
                index_return_all = index_return
            else:
                index_return_all = pd.concat([index_return_all, index_return], axis=1)

        index_return_all.columns = index_pool
        index_return_all = index_return_all.loc[beg_date:end_date, :]
        index_return_all = index_return_all.dropna()

        return index_return_all

    def get_index_weight_riskparity(self, end_date, type):

        # 利用风险平价的方法求解不同指数的权重
        ####################################################################
        beg_date = Date().get_trade_date_offset(end_date, - self.period_risk_parity)
        data = self.get_index_return_daily(beg_date, end_date, type)
        cov = data.cov() * 250
        weight = AssetAllocation().cal_risk_parity_weights(cov)
        return weight

    def get_fund_exposure(self, end_date, type="multi_factor"):

        # 取得基金的暴露
        ####################################################################
        beg_date = Date().get_trade_date_offset(end_date, -self.period_exposure)
        fund_pool = self.fund_pool

        if type == "multi_factor":
            index_pool = self.stock_index_pool
        else:
            index_pool = self.bond_index_pool

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
        exposure_all = exposure_all.loc[index_pool, :]
        return exposure_all.T

    def get_fund_exposure_stock_bond(self, end_date):

        exposure_stock = self.get_fund_exposure(end_date, type="multi_factor")
        exposure_stock = exposure_stock.sum(axis=1)
        exposure_bond = self.get_fund_exposure(end_date, type="bond")
        exposure_bond = exposure_bond.sum(axis=1)
        exposure = pd.concat([exposure_bond, exposure_stock], axis=1)
        exposure.columns = ["Bond", "Stock"]
        return exposure

    def get_fund_alpha(self, end_date):

        # 取得基金的alpha
        ####################################################################
        beg_date = Date().get_trade_date_offset(end_date, -self.period_alpha)
        fund_pool = self.fund_pool

        alpha_all = pd.DataFrame([], index=fund_pool, columns=["AlphaMed"])
        for i in range(len(fund_pool)):
            fund = fund_pool[i]
            alpha = FundRegressionRiskAlphaReturnIndex().get_fund_regression_risk_alpha_return_index(fund)
            alpha = alpha.loc[beg_date:end_date, "AlphaReturn"]
            if len(alpha) > 0:
                alpha_all.loc[fund, "AlphaMed"] = alpha.median()
                std = alpha.ewm(halflife=int(self.period_alpha / 2)).std().loc[alpha.index[len(alpha) - 1]]
                alpha_all.loc[fund, "AlphaStd"] = std
                alpha_all.loc[fund, "AlphaIR"] = alpha.median() / std

        alpha_all = alpha_all.astype(float)
        return alpha_all

    def opt_fund_portfolio_qp(self, end_date, stock_up, stock_low,
                              lamb, port_path, port_name,
                              exposure_stock_low, exposure_bond_low):

        # 参数
        ####################################################################################################
        # stock_up = 0.5
        # stock_low = 0.0
        # lamb = 4  # 平衡alpha和风格偏离 越大 alpha越重要
        # port_path = r'E:\3_Data\5_stock_data\4_portfolio_wind'
        # port_name = "行业风格平价FOF"
        # exposure_stock_low = 0.80
        # exposure_bond_low = 0.0

        if end_date > "20150630":
            exposure_bond_low = 0.65

        # 得到基金暴露 基金alpha 指数权重等数据
        ####################################################################################################
        fund_pool = self.fund_pool
        alpha = self.get_fund_alpha(end_date)
        exposure = self.get_fund_exposure(end_date, type="multi_factor")
        exposure_stock_bond = self.get_fund_exposure_stock_bond(end_date)
        index_weight = self.get_index_weight_riskparity(end_date, type="multi_factor")

        alpha = alpha.dropna()
        alpha = pd.DataFrame(alpha["AlphaIR"])
        exposure = exposure.dropna(how='all')

        # 整理数据
        ####################################################################################################
        fund_pool = list(set(fund_pool) & set(alpha.index) & set(exposure.index))
        fund_pool.sort()
        alpha = alpha.loc[fund_pool, :]
        print(alpha)
        exposure = exposure.loc[fund_pool, self.stock_index_pool]
        index_weight = index_weight.loc[self.stock_index_pool, :]
        exposure_stock_bond = exposure_stock_bond.loc[fund_pool, :]
        print(exposure_stock_bond)
        # bond_mad = exposure_stock_bond["Bond"] - exposure_stock_bond["Bond"].median()
        # bond_low = exposure_stock_bond["Bond"].median() + bond_mad.abs().median() * 3.0
        exposure = exposure.T
        exposure_stock_bond = exposure_stock_bond.T

        # 基金权重的上下限
        ####################################################################################################
        G_up = np.diag(np.ones(len(alpha)))
        G_low = - np.diag(np.ones(len(alpha)))
        G = np.row_stack((G_up, G_low))
        h_up = np.row_stack(np.ones((len(alpha)))) * stock_up
        h_low = np.row_stack(np.ones((len(alpha)))) * stock_low
        h = np.row_stack((h_up, h_low))

        # 股票部分暴露下限
        ####################################################################################################
        exposure_stock = - exposure_stock_bond.loc[["Stock", "Bond"], :].values
        # print(exposure_bond_low, bond_low)
        # exposure_bond_low = min(exposure_bond_low, bond_low)
        exposure_stock_bond_low = np.row_stack((-exposure_stock_low, -exposure_bond_low))
        G = np.row_stack((G, exposure_stock))
        h = np.row_stack((h, exposure_stock_bond_low))

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

        exposure_stock_bond = exposure_stock_bond.loc[:, res.index]
        exposure_stock_bond = exposure_stock_bond.T

        exposure_res = pd.concat([res, exposure_res, exposure_stock_bond], axis=1)
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

    # 参数举例
    ####################################################################################################
    self = StockFundPortfolio()
    beg_date = "20180101"
    end_date = "20180909"
    i = 9
    fund = "229002.OF"

    # stock_up = 0.5
    # stock_low = 0.0
    # lamb = 4  # 平衡alpha和风格偏离 越大 alpha越重要
    # port_path = r'E:\3_Data\5_stock_data\4_portfolio_wind'
    # port_name = "行业风格平价FOF"
    # benchmark_code = "885001.WI"
    # exposure_stock_low = 0.80
    # exposure_bond_low = 0.00

    stock_up = 0.80
    stock_low = 0.0
    lamb = 4  # 平衡alpha和风格偏离 越大 alpha越重要
    port_path = r'E:\3_Data\5_stock_data\4_portfolio_wind'
    port_name = "行业风格平价低风险FOF"
    benchmark_code = "885002.WI"
    exposure_stock_low = 0.15
    exposure_bond_low = 0.50

    # 每期优化
    ####################################################################################################
    # date_list = Date().get_normal_date_series("20141230", "20181001", period="Q")
    # for end_date in date_list:
    #     StockFundPortfolio().opt_fund_portfolio_qp(end_date, stock_up, stock_low,
    #                                                lamb, port_path, port_name,
    #                                                exposure_stock_low, exposure_bond_low)
    #
    # 上传到wind
    ###################################################################################################
    from quant.source.wind_portfolio import WindPortUpLoad
    WindPortUpLoad().upload_weight_period(port_name)

    # 本地计算其收益
    ####################################################################################################
    from quant.source.backtest_fund import PortBackTestFund
    Index().load_index_factor(benchmark_code)
    backtest = PortBackTestFund()
    backtest.set_info(port_name, benchmark_code)
    backtest.set_weight_at_all_change_date()
    backtest.cal_turnover()
    backtest.set_weight_at_all_daily()
    backtest.cal_port_return()
    backtest.cal_summary()
    ###################################################################################################
