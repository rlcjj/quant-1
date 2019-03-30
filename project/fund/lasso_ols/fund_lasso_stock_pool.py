import os
import pandas as pd
from sklearn.linear_model import Lasso

from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.fund.fund import Fund
from quant.data.data import Data


class FundLassoStockPool(Data):

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'4_fund_data\4_fund_holding_predict\lasso_stock_pool'
        self.data_path_lasso_pool = os.path.join(self.primary_data_path, self.sub_data_path)

        self.lasso_stock_pool_number = 20
        self.lasso_date_number = 60
        self.lasso_date_number_min = 40

        self.stock_mv = None
        self.fund_return = None
        self.stock_return = None

        self.date_series = None
        self.fund_pool = None

    def get_data(self, beg_date, end_date,
                 period='M', fund_pool_name="优质基金池", pool_date='20180630'):

        """ 得到回测时间 回测基金池 """

        self.date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        self.fund_pool = Fund().get_fund_pool_code(pool_date, fund_pool_name)

        """ 得到 基金复权净值增长率 股票涨跌幅 基金市值 """

        self.stock_mv = Stock().read_factor_h5("Mkt_freeshares")
        self.fund_return = Fund().get_fund_factor("Repair_Nav_Pct")
        self.stock_return = Stock().read_factor_h5("Pct_chg").T

    def cal_lasso_stock_pool(self):

        """ 循环基金池 循环日期 计算 LASSO 股票池 """

        for i_fund in range(0, len(self.fund_pool)):

            for i_date in range(0, len(self.date_series)):

                fund_code = self.fund_pool[i_fund]
                period_end_date = self.date_series[i_date]
                period_beg_date = Date().get_trade_date_offset(period_end_date, -(self.lasso_date_number - 1))
                res_add = self.cal_lasso_stock_pool_date(fund_code, period_beg_date, period_end_date)

                if i_date == 0:
                    res = res_add
                else:
                    res = pd.concat([res, res_add], axis=1)

            file = 'LASSO回归股票池_%s_AllDate.csv' % fund_code
            res.to_csv(os.path.join(self.data_path_lasso_pool, file))

    def cal_lasso_stock_pool_date(self, fund_code, beg_date, end_date):

        """ 利用最近一段时间基金净值和股票收益率 Lasso回归出股票池 控制股票数量在20只附近 """

        trade_beg_date = Date().change_to_str(beg_date)
        trade_end_date = Date().change_to_str(end_date)

        # 股票市值前60%作为Lasso股票池

        stock_mv_date = pd.DataFrame(self.stock_mv[trade_end_date])
        stock_mv_date = stock_mv_date.sort_values(by=[trade_end_date], ascending=False)
        stock_mv_date = stock_mv_date.dropna()
        stock_mv_date = stock_mv_date.iloc[0:int(0.60 * len(stock_mv_date)), :]
        stock_pool = list(stock_mv_date.index)

        # 得到股票和基金涨跌幅

        date_series = Date().get_trade_date_series(trade_beg_date, trade_end_date)
        f_pct = self.fund_return.loc[date_series, fund_code]
        s_pct = self.stock_return.loc[date_series, stock_pool]
        s_pct = s_pct.T.dropna().T
        s_pct = s_pct.dropna(how='all')
        f_pct = f_pct.dropna()

        # 准备数据Lasso回归

        data = pd.concat([f_pct, s_pct], axis=1)
        data = data.loc[beg_date:end_date, :]
        data = data.dropna(how='all')
        data = data.fillna(0.0)
        y = data[fund_code].values
        x = data.iloc[:, 1:].values

        # Lasso回归函数

        def lasso_regression(x, y, trade_end_date, alpha=0.50):

            model = Lasso(alpha=alpha, fit_intercept=False)
            model.fit(x, y)

            res = pd.DataFrame(model.coef_[model.coef_ > 0.001],
                               index=s_pct.columns[model.coef_ > 0.001], columns=[trade_end_date])
            res = res.sort_values(by=[trade_end_date], ascending=False)
            return res

        # 得到结果 只要大于20只 一直回归

        if len(data) > self.lasso_date_number_min and len(f_pct) > self.lasso_date_number_min:

            l, alpha, i = 50, 0.60, 0

            while l > self.lasso_stock_pool_number:
                res = lasso_regression(x, y, trade_end_date, alpha)
                alpha *= 1.1
                i += 1
                l = len(res)
                print("第%s次回归" % i)

            print("%s From %s To %s Data Len is %s" % (fund_code, trade_beg_date, trade_end_date, len(data)))
            print("LASSO回归股票池的个数: %s, 权重绝对值之和为 %s" % (str(len(res)), res.abs().sum()))
        else:
            print("%s From %s To %s Data Len is %s" % (fund_code, trade_beg_date, trade_end_date, len(data)))
            print("The Result is None")
            res = pd.DataFrame([])
        return res

    def get_lasso_stock_pool(self, fund_code):

        """ 得到 LASSO 股票池 """

        file = 'LASSO回归股票池_%s_AllDate.csv' % fund_code
        file = os.path.join(self.data_path_lasso_pool, file)

        if os.path.exists(file):
            data = pd.read_csv(file, encoding='gbk', index_col=[0])
        else:
            data = None
        return data

    def get_lasso_stock_pool_date(self, fund_code, date):

        """ 得到 LASSO 股票池 """

        data = self.get_lasso_stock_pool(fund_code)
        if data is None:
            data = pd.DataFrame([])
        elif date in data.columns:
            data = pd.DataFrame(data[date])
        else:
            data = pd.DataFrame([])
        return data

if __name__ == "__main__":

    from datetime import datetime
    self = FundLassoStockPool()
    self.get_data("20060101", "20181106", fund_pool_name="优质基金池")
    self.cal_lasso_stock_pool()
