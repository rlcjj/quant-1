import os
import pandas as pd
from sklearn.linear_model import Lasso, LassoCV

from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.index import Index
from quant.source.wind_portfolio import WindPortUpLoad
from quant.source.backtest import BackTest


class StockLassoRegression(Data):

    def __init__(self):

        Data.__init__(self)
        self.wind_data_path = WindPortUpLoad().path

        self.stock_pool_ratio = 0.60
        self.lasso_stock_pool_number = 150
        self.lasso_date_number = 60
        self.lasso_date_number_min = 40
        self.port_name = '主动股票基金Lasso'

        self.stock_mv = None
        self.index_return = None
        self.stock_return = None

        self.date_series = None
        self.fund_pool = None

    def get_data(self, beg_date, end_date,
                 period='M'):

        """ 得到回测时间 回测基金池 """

        self.date_series = Date().get_trade_date_series(beg_date, end_date, period=period)

        """ 得到 基金复权净值增长率 股票涨跌幅 基金市值 """

        self.stock_mv = Stock().read_factor_h5("Mkt_freeshares")
        self.stock_return = Stock().read_factor_h5("Pct_chg").T

        index1 = Index().get_index_factor("885000.WI", attr=['PCT'])
        index2 = Index().get_index_factor("885001.WI", attr=['PCT'])
        index = pd.concat([index1, index2], axis=1)
        index['PctMean'] = index.mean(axis=1)
        self.index_return = pd.DataFrame(index['PctMean']) * 100
        self.index_return.columns = ['IndexReturn']

    def cal_lasso_stock_wind_file(self):

        """ 循环日期 计算 LASSO 结果 """

        sub_path = os.path.join(self.wind_data_path, self.port_name)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        stock_ratio = Fund().get_fund_factor('Stock_Ratio').T

        for i_date in range(0, len(self.date_series)):

            period_end_date = self.date_series[i_date]
            period_beg_date = Date().get_trade_date_offset(period_end_date, -(self.lasso_date_number - 2))
            data_date = self.cal_lasso_stock_wind_file_date(period_beg_date, period_end_date)

            quarter_date = Date().get_last_fund_quarter_date(period_end_date)
            fund_pool = Fund().get_fund_pool_code(name="基金持仓基准基金池", date=quarter_date)
            stock_ratio_date = pd.DataFrame(stock_ratio.loc[fund_pool, quarter_date])
            ratio = stock_ratio_date.median().values[0] / 100.0

            print(period_end_date, ratio)
            data_date.columns = ['Weight']
            data_date['Weight'] = data_date['Weight'] / data_date['Weight'].sum() * ratio
            data_date.loc['Cash', 'Weight'] = 1 - ratio
            data_date.index.name = 'Code'
            data_date["CreditTrading"] = "No"
            data_date["Date"] = period_end_date
            data_date["Price"] = 0.0
            data_date["Direction"] = "Long"
            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, period_end_date))
            data_date.to_csv(file)

    def cal_lasso_stock_wind_file_date(self, beg_date, end_date):

        """ 利用最近一段时间基金净值和股票收益率 Lasso回归 """

        trade_beg_date = Date().change_to_str(beg_date)
        trade_end_date = Date().change_to_str(end_date)

        # 股票市值前2/3作为Lasso股票池

        stock_mv_date = pd.DataFrame(self.stock_mv[trade_end_date])
        stock_mv_date = stock_mv_date.sort_values(by=[trade_end_date], ascending=False)
        stock_mv_date = stock_mv_date.dropna()
        stock_mv_date = stock_mv_date.iloc[0:int(self.stock_pool_ratio * len(stock_mv_date)), :]
        stock_pool = list(stock_mv_date.index)

        # 得到股票和基金涨跌幅

        date_series = Date().get_trade_date_series(trade_beg_date, trade_end_date)
        f_pct = self.index_return
        s_pct = self.stock_return.loc[date_series, stock_pool]
        s_pct = s_pct.T.dropna().T
        s_pct = s_pct.dropna(how='all')
        f_pct = f_pct.dropna()

        # 准备数据Lasso回归

        data = pd.concat([f_pct, s_pct], axis=1)
        data = data.loc[beg_date:end_date, :]
        data = data.dropna(how='all')
        data = data.fillna(0.0)
        y = data['IndexReturn'].values
        x = data.iloc[:, 1:].values

        # Lasso回归函数

        if len(data) > self.lasso_date_number_min and len(f_pct) > self.lasso_date_number_min:

            model = LassoCV(fit_intercept=True, positive=True)

            # LassoCV自动调节alpha可以实现选择最佳的alpha

            model.fit(x, y)
            print(model.alpha_)
            alpha = model.alpha_

            model = Lasso(alpha=alpha, fit_intercept=False, positive=True)
            model.fit(x, y)

            res = pd.DataFrame(model.coef_[model.coef_ > 0.0001],
                               index=s_pct.columns[model.coef_ > 0.0001], columns=[trade_end_date])
            res = res.sort_values(by=[trade_end_date], ascending=False)

            print("From %s To %s Data Len is %s" % (trade_beg_date, trade_end_date, len(data)))
            print("LASSO回归股票池的个数: %s, 权重绝对值之和为 %s" % (str(len(res)), res.abs().sum()))
        else:
            print("From %s To %s Data Len is %s" % (trade_beg_date, trade_end_date, len(data)))
            print("The Result is None")
            res = pd.DataFrame([])
        return res

    def backtest(self):

        port = BackTest()
        port.set_info(self.port_name, '885000.WI')
        port.read_weight_at_all_change_date()
        port.cal_weight_at_all_daily()
        port.cal_port_return(beg_date="20060101")
        port.cal_turnover()
        port.cal_summary(all_beg_date="20060101")


if __name__ == "__main__":

    from datetime import datetime
    self = StockLassoRegression()
    self.get_data("20060101", "20181106")
    # self.cal_lasso_stock_wind_file()
    self.backtest()