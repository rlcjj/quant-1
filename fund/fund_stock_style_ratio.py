from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate

from datetime import datetime
import pandas as pd
import cvxpy as cvx
import os


class FundStockStyleRatio(Data):

    """
    通过回归的方法来获得基金或者基金指数风格仓位
    例如：泰达宏利逆向策略，沪深300占20%、中证500占65%、现金债券15%
    """

    def __init__(self,
                 regress_length=25, regress_length_min=20,
                 stock_ratio_up=0.95, stock_ratio_low=0.60,
                 turnover_daily=0.035,
                 index_code_list=None):

        Data.__init__(self)
        self.data_path = os.path.join(self.primary_data_path, r'fund_data\fund_stock_style_ratio')
        index_close = Index().get_index_cross_factor(factor_name='CLOSE')
        index_pct = index_close.pct_change() * 100
        fund_return = FundFactor().get_fund_factor("Repair_Nav_Pct")
        self.data_return = pd.concat([index_pct, fund_return], axis=1)

        self.regress_length = regress_length
        self.regress_length_min = regress_length_min
        self.stock_ratio_up = stock_ratio_up
        self.stock_ratio_low = stock_ratio_low
        self.turnover_daily = turnover_daily

        if index_code_list is None:
            # 需要有债券指数 来测量股债仓位
            self.index_code_list = ["885062.WI",
                                    "801853.SI", "000300.SH", "000905.SH", "000852.SH", "399006.SZ"]
            self.index_name_list = ['短期纯债基金',
                                    '绩优股指数', '沪深300', '中证500', '中证1000', '创业板指']
        else:
            self.index_code_list = index_code_list

    def update_data(self):

        """ 更新需要的数据 """

        end_date = datetime.today().strftime("%Y%m%d")
        beg_date = Date().get_trade_date_offset(end_date, -40)
        # Fund().update_fund_factor(beg_date, end_date)
        Index().load_index_factor("885000.WI", beg_date, end_date)
        Index().load_index_factor("885001.WI", beg_date, end_date)
        for index in self.index_code_list:
            Index().load_index_factor(index, beg_date, end_date)

    def cal_style_position_all_fund(self, beg_date, end_date):

        """ 计算所有基金风格仓位和仓位 利用OLS无约束回归 """

        fund_pool = FundPool().get_fund_pool_code(name="基金持仓基准基金池", date="20180630")

        for i_fund in range(len(fund_pool)):
            fund = fund_pool[i_fund]
            self.cal_style_position(beg_date, end_date, fund)

    def cal_style_position(self, beg_date, end_date, code):

        """ 计算一个基金或指数的风格仓位和仓位 利用OLS有约束回归 """

        x_pct = self.data_return[self.index_code_list]
        x_pct = x_pct.dropna(how='all')
        y_pct = pd.DataFrame(self.data_return[code])
        y_pct = y_pct.dropna()

        all_date_series = Date().get_trade_date_series(beg_date, end_date, period="D")
        y_series = Date().get_trade_date_series(y_pct.index[0], y_pct.index[-1])
        date_series = list(set(y_series) & set(all_date_series))
        date_series.sort()
        error = False

        for i_date in range(len(date_series)):

            ed_date = date_series[i_date]
            bg_date = Date().get_trade_date_offset(ed_date, -self.regress_length)
            last_date = Date().get_trade_date_offset(ed_date, -1)

            x_pct_period = x_pct.loc[bg_date:ed_date, :]
            x_pct_period = x_pct_period.T.dropna().T
            x_columns = x_pct_period.columns
            data = pd.concat([y_pct, x_pct_period], axis=1)
            data = data.dropna()

            # 如果是第一天或者上次结果错误 则开放换手率 并假定上次平均持仓

            if i_date != 0:
                turnover_daily = self.turnover_daily
                old_weight = old_weight.loc[x_columns, :]
                old_weight = old_weight.fillna(0.0)
            else:
                n = len(x_columns)
                old_weight = pd.DataFrame(n * [1.0 / n], index=x_columns, columns=[last_date])
                turnover_daily = 2.0

            if error:
                n = len(x_columns)
                old_weight = pd.DataFrame(n * [1.0 / n], index=x_columns, columns=[last_date])
                turnover_daily = 2.00

            # print(error, old_weight.columns)
            print("## Cal Regress %s %s %s %s TurnOver %s##" % (code, bg_date, ed_date, data.shape, turnover_daily))

            if len(data) >= self.regress_length_min:
                y = data[code].values
                x = data.iloc[:, 1:].values
                k = x.shape[1]
                old = old_weight.T.values[0]

                try:
                    w = cvx.Variable(k)
                    sigma = y - x * w
                    prob = cvx.Problem(cvx.Minimize(cvx.sum_squares(sigma)),
                                       [cvx.sum(w) == 1.0,
                                        cvx.sum(w[1:]) >= self.stock_ratio_low,
                                        cvx.sum(w[1:]) <= self.stock_ratio_up,
                                        cvx.sum(cvx.abs(w - old)) <= turnover_daily,
                                        w >= 0
                                        ])
                    prob.solve()

                    print('Solver Status : ', prob.status)
                    params_add = pd.DataFrame(w.value, columns=[ed_date], index=x_columns)
                    stock_sum = params_add.loc[self.index_code_list[1:], ed_date].sum()
                    concat_data = pd.concat([params_add, old_weight], axis=1)
                    concat_data = concat_data.dropna()
                    turnover_real = (concat_data[last_date] - concat_data[ed_date]).abs().sum()

                    params_add.loc['StockRatio', ed_date] = stock_sum
                    params_add.loc['BondRatio', ed_date] = params_add.loc[self.index_code_list[0], ed_date]
                    params_add.loc['TurnOverDaily', ed_date] = turnover_real
                    print(params_add.T)
                    old_weight = params_add
                    error = False
                except Exception as e:
                    print(end_date, code, "回归失败")
                    error = True
            else:
                print(end_date, code, "数据长度不够")
                error = True

            if i_date == 0:
                params_new = params_add
            else:
                params_new = pd.concat([params_new, params_add], axis=1)

        # 合并新数据
        ####################################################################
        params_new = params_new.T
        out_file = os.path.join(self.data_path, 'RestraintOLSStylePosition_%s.csv' % code)

        if os.path.exists(out_file):
            params_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            params_old.index = params_old.index.map(str)
            params = FactorOperate().pandas_add_row(params_old, params_new)
        else:
            params = params_new

        params.to_csv(out_file)
        ####################################################################

    def get_style_position(self, code):

        """ 得到优化结果 """

        file = os.path.join(self.data_path, 'RestraintOLSStylePosition_%s.csv' % code)
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data.index = data.index.map(str)
        return data

    def get_style_position_date(self, code, date):

        """ 得到优化结果(某天) """

        file = os.path.join(self.data_path, 'RestraintOLSStylePosition_%s.csv' % code)
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data.index = data.index.map(str)
        ratio = pd.DataFrame(data.loc[date, :])
        return ratio

    def get_position_date(self, code, date):

        """ 得到基金仓位 """

        file = os.path.join(self.data_path, 'RestraintOLSStylePosition_%s.csv' % code)
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data.index = data.index.map(str)
        stock_ratio = data.loc[date, "StockRatio"]
        return stock_ratio

    def cal_style_position_fundindex(self, beg_date, end_date):

        """ 计算普通股票型基金 和偏股混合型基金 仓位"""

        # 普通股票型基金
        self.stock_ratio_low = 0.80
        self.stock_ratio_up = 0.95
        code = "885000.WI"
        self.cal_style_position(beg_date, end_date, code)

        # 偏股混合型基金
        self.stock_ratio_low = 0.60
        self.stock_ratio_up = 0.95
        code = "885001.WI"
        self.cal_style_position(beg_date, end_date, code)


if __name__ == '__main__':

    # 000001.OF
    ########################################################################
    self = FundStockStyleRatio(stock_ratio_low=0.60, stock_ratio_up=0.95)
    # self.update_data()
    code = "000001.OF"
    end_date = '20100321'
    beg_date = "20050101"

    # self.cal_style_position(beg_date, end_date, code)
    self.cal_style_position_fundindex(beg_date, end_date)
    ########################################################################
