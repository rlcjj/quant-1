import os
import pandas as pd
import numpy as np
from cvxopt import matrix
import cvxopt.solvers as sol

from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.fund.fund import Fund
from quant.data.data import Data
from quant.project.fund.lasso_ols.fund_lasso_stock_pool import FundLassoStockPool
from quant.source.wind_portfolio import WindPortUpLoad
from quant.source.backtest import BackTest


class FundOLSStockWeight(Data):

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'4_fund_data\4_fund_holding_predict\ols_stock_weight'
        self.data_path_ols_weight = os.path.join(self.primary_data_path, self.sub_data_path)

        self.ols_stock_pool_number = 25
        self.ols_date_number = 60
        self.ols_date_number_min = 40

        self.stock_mv = None
        self.fund_return = None
        self.stock_return = None
        self.fund_holding = None
        self.fund_stock_ratio = None

        self.date_series = None
        self.fund_pool = None
        self.wind_port_path = WindPortUpLoad().path

    def get_data(self, beg_date, end_date,
                 period='M', fund_pool_name="优质基金池", pool_date='20180630'):

        """ 得到回测时间 回测基金池 """

        self.date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        self.fund_pool = Fund().get_fund_pool_code(pool_date, fund_pool_name)

        """ 得到 基金复权净值增长率 股票涨跌幅 基金市值 """

        self.stock_mv = Stock().read_factor_h5("Mkt_freeshares")
        self.fund_return = Fund().get_fund_factor("Repair_Nav_Pct")
        self.stock_return = Stock().read_factor_h5("Pct_chg").T
        self.fund_holding = Fund().get_fund_holding_all()
        self.fund_stock_ratio = Fund().get_fund_factor("Stock_Ratio") / 100.0

    def cal_ols_stock_weight(self):

        """ 循环基金池 循环日期 计算 OLS 股票权重 """

        for i_fund in range(0, len(self.fund_pool)):

            for i_date in range(0, len(self.date_series)):

                fund_code = self.fund_pool[i_fund]
                period_end_date = self.date_series[i_date]
                period_beg_date = Date().get_trade_date_offset(period_end_date, -(self.ols_date_number - 1))
                print(fund_code, period_end_date)
                res_add = self.cal_ols_stock_weight_date(fund_code, period_beg_date, period_end_date)

                if i_date == 0:
                    res = res_add
                else:
                    res = pd.concat([res, res_add], axis=1)

            file = '最后预测持仓权重_%s_AllDate.csv' % fund_code
            file = os.path.join(self.data_path_ols_weight, file)
            res.to_csv(file)

    def cal_ols_stock_weight_date(self, fund_code, beg_date, end_date):

        """ 利用最近一段时间基金净值和股票收益率 OLS回归出股票权重 """

        # 参数

        up_fund_ratio = 0.3
        down_fund_ratio = 0.5
        up_fund_limit = 0.03
        down_fund_limit = 0.02

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        # 收益率数据

        date_series = Date().get_trade_date_series(beg_date, end_date)
        f_pct = self.fund_return.ix[date_series, fund_code]
        s_pct = self.stock_return.ix[date_series, :]

        # lasso 股票池数据

        lasso_stock_weight = FundLassoStockPool().get_lasso_stock_pool(fund_code)
        if end_date in lasso_stock_weight.columns:
            lasso_stock_weight = pd.DataFrame(lasso_stock_weight[end_date])
            lasso_stock_weight = lasso_stock_weight.dropna()
        else:
            lasso_stock_weight = pd.DataFrame([])
        lasso_stock_pool = list(lasso_stock_weight.index)

        # 上个季度股票池数据

        quarter_date = Date().get_last_fund_quarter_date(end_date)
        last_fund_holding = self.fund_holding[self.fund_holding.ReportDate == quarter_date]
        last_fund_holding = last_fund_holding[last_fund_holding.FundCode == fund_code]
        last_fund_holding.index = last_fund_holding.StockCode
        last_fund_holding['Weight'] /= 100.0
        last_fund_holding = last_fund_holding.sort_values(by=['Weight'], ascending=False)
        last_fund_holding = pd.DataFrame(last_fund_holding.loc[last_fund_holding.index[0:10], 'Weight'])

        # 有效数据大于0 开始计算

        if len(last_fund_holding) > 0 and len(lasso_stock_pool) > 0 and len(f_pct) > self.ols_date_number_min:

            last_fund_pool = list(last_fund_holding.index)
            stock_list = list(set(lasso_stock_pool) | set(last_fund_pool))

            s_pct = s_pct.ix[:, stock_list]
            data = pd.concat([f_pct, s_pct], axis=1)
            data = data.loc[beg_date:end_date, :]
            data = data.dropna(how='all')
            data = data.fillna(0.0)

            # 股票上下限数据

            position = self.fund_stock_ratio.ix[quarter_date, fund_code]
            if np.isnan(position):
                position = 0.80

            # position = np.nanmean([position, f_exp.ix["CTY", :].values[0]])

            # old_fund_up = min(1.2*last_fund_holding.ix[0, 'Weight'], 0.09)  # 有些持仓很分散的股票的上限要小
            # new_fund_up = min(old_fund_up*0.5, 0.035)   # 限制新进股票的最高上限、这里限制的比较严格是因为新近股票就是风险
            # print("old_fund_up", old_fund_up, "new_fund_up", new_fund_up)

            fund_weight = pd.concat([last_fund_holding, lasso_stock_weight], axis=1)
            fund_weight.columns = ['Last_Weight', 'Lasso_Weight']
            fund_weight['Weight'] = fund_weight.max(axis=1)

            fund_weight['Weight'] = fund_weight['Weight'] / fund_weight['Weight'].sum() * position
            fund_weight['Type'] = fund_weight['Last_Weight'].map(lambda x: "New_Stock" if np.isnan(x) else "Old_Stock")

            fund_weight['Weight_up'] = fund_weight['Weight'].map(
                lambda x: min(max(x * (1 + up_fund_ratio), x + up_fund_limit), 0.15))
            fund_weight['Weight_down'] = fund_weight['Weight'].map(
                lambda x: max(min(x * (1 - down_fund_ratio), x - down_fund_limit), 0))

            print(fund_weight[['Weight', 'Weight_up', 'Weight_down']] * 100)

            # 风格约束
            ################################################################
            # end_date = date_series[-1]
            # beg_date = Date().get_trade_date_offset(end_date, -60)
            # s_exp = Barra().get_factor_exposure_average(beg_date, end_date, type_list=['STYLE']).T
            # s_exp = s_exp[stock_list]
            # exp = pd.concat([f_exp, s_exp], axis=1)
            # exp = exp.dropna(how='all')
            # exp = exp.fillna(0.0)
            # y_exp = np.row_stack(exp[fund_code].values)
            # x_exp = exp.iloc[:, 1:].values
            # y_exp_up = y_exp + style_std
            # y_exp_low = y_exp - style_std
            # style_limit = np.row_stack((y_exp_up, -y_exp_low))
            # A = np.row_stack((x_exp, -x_exp))

            # 最小化函数
            ##################################################################
            y = data[fund_code].values
            X = data.iloc[:, 1:].values
            P = 2 * np.dot(np.transpose(X), X)
            Q = -2 * np.dot(np.transpose(X), y)

            # 单个股票权重上下限约束
            ################################################################
            G_up = np.diag(np.ones(len(stock_list)))
            G_low = - np.diag(np.ones(len(stock_list)))
            G = np.row_stack((G_up, G_low))

            h_up = np.vstack(fund_weight['Weight_up'].values)
            h_low = -np.vstack(fund_weight['Weight_down'].values)
            h = np.row_stack((h_up, h_low))

            # 总权重上下限约束
            ################################################################
            G_p_up = np.ones(len(stock_list)).reshape(1, len(stock_list))
            G_p_low = - np.ones(len(stock_list)).reshape(1, len(stock_list))
            G_p = np.row_stack((G_p_up, G_p_low))
            G = np.row_stack((G, G_p))

            h_p_up = [[min(position + 0.05, 0.95)]]
            h_p_low = [[-min(max(position - 0.05, 0.65), h_p_up[0][0])]]

            print("正在计算 %s 在 %s 的股票持仓权重 " % (fund_code, end_date))
            print("基金约束上下限制为 %s %s" % (h_p_low, h_p_up))
            print("基金约束限制矩阵大小为 %s %s" % (G.shape, h.shape))
            h_p = np.row_stack((h_p_up, h_p_low))
            h = np.row_stack((h, h_p))

            # G = np.row_stack((G, A))
            # h = np.row_stack((h, style_limit))

            # 优化求解

            P = matrix(P)
            Q = matrix(Q)
            G = matrix(G)
            h = matrix(h)

            model = sol.qp(P, Q, G, h)

            # 输出结果

            weight = list(model['x'][:])
            res = pd.DataFrame(weight, index=stock_list, columns=[end_date])
            res = res[res[end_date] > 0.0001]
            res = res.sort_values(by=[end_date], ascending=False)

            print("基金仓位为%s 最后预测持仓权重个数%s" % (res[end_date].sum(), len(res)))

            if model['status'] == 'optimal':
                print("二次规划成功，最终结果 %s %s " % (fund_code, end_date))
                return res
            else:
                print("二次规划异常，没有最终结果 %s %s " % (fund_code, end_date))
                return pd.DataFrame([])
        else:
            print("%s 在 %s 的数据长度为0 " % (fund_code, end_date))
            return pd.DataFrame([])

    def get_ols_stock_weight(self, fund_code):

        """ 得到 OLS 股票权重 """

        file = '最后预测持仓权重_%s_AllDate.csv' % fund_code
        file = os.path.join(self.data_path_ols_weight, file)

        if os.path.exists(file):
            data = pd.read_csv(file, encoding='gbk', index_col=[0])
        else:
            data = None
        return data

    def get_ols_stock_weight_date(self, fund_code, date):

        """ 得到 LASSO 股票池 """

        data = self.get_ols_stock_weight(fund_code)
        if data is None:
            data = pd.DataFrame([])
        elif date in data.columns:
            data = pd.DataFrame(data[date])
            data = data.dropna()
        else:
            data = pd.DataFrame([])
        return data

    def get_wind_file_fund(self, fund_code):

        """ 得到wind权重 """

        fund_weight = self.get_ols_stock_weight(fund_code)

        date_series = fund_weight.columns
        sub_path = os.path.join(self.wind_port_path, fund_code + "_Lasso")

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print("Generate File %s" % date)
            data_date = pd.DataFrame(fund_weight[date])
            data_date = data_date.dropna()
            next_date = Date().get_trade_date_offset(date, 1)
            data_date.columns = ['Weight']
            data_date.index.name = 'Code'
            data_date["CreditTrading"] = "No"
            data_date["Date"] = next_date
            data_date["Price"] = 0.0
            data_date["Direction"] = "Long"
            file = os.path.join(sub_path, '%s_%s.csv' % (fund_code + "_Lasso", next_date))
            data_date.to_csv(file)

    def backtest(self, fund_code):

        """ 回测 """

        backtest = BackTest()
        backtest.set_info(fund_code + "_Lasso", fund_code)
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return(beg_date="20040301")
        backtest.cal_turnover(annual_number=12)
        backtest.cal_summary(all_beg_date="20040301")


if __name__ == "__main__":

    from datetime import datetime
    fund_code = "000011.OF"
    self = FundOLSStockWeight()
    self.get_wind_file_fund(fund_code)
    self.backtest(fund_code)

    # self.get_data("20060101", "20181106", fund_pool_name="基金持仓基准基金池")
    # self.cal_ols_stock_weight()
