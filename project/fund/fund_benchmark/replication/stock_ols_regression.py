from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.fund.fund import Fund
from quant.fund.fund_pool import FundPool
from quant.fund.fund_holder import FundHolder
from quant.stock.stock import Stock
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import Lasso, LassoCV


class StockOLSRegression(Data):

    """
    每个季度末得到主动股票基金的平均持仓
    其他月末得到
    """

    def __init__(self):

        Data.__init__(self)

        self.port_name = "主动股票基金ols"
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor

        self.stock_mv = None
        self.index_return = None
        self.stock_return = None

        self.date_series = None
        self.fund_pool = None

    def get_data(self, beg_date, end_date, period='M'):

        """ 得到回测时间 回测基金池 """

        self.date_series = Date().get_trade_date_series(beg_date, end_date, period=period)

        """ 得到 基金复权净值增长率 股票涨跌幅 基金市值 """
        self.stock_return = Stock().read_factor_h5("Pct_chg").T

        index1 = Index().get_index_factor("885000.WI", attr=['PCT'])
        index2 = Index().get_index_factor("885001.WI", attr=['PCT'])
        index = pd.concat([index1, index2], axis=1)
        index['PctMean'] = index.mean(axis=1)
        self.index_return = pd.DataFrame(index['PctMean']) * 100
        self.index_return.columns = ['IndexReturn']

        self.stock_ratio = Fund().get_fund_factor('Stock_Ratio').T

    def cal_weight_date(self, date, quarter_date):

        days_diff = Date().get_trade_date_diff(quarter_date, date)
        fund_pool = FundPool().get_fund_pool_code(name="基金持仓基准基金池", date=quarter_date)

        for i_fund in range(len(fund_pool)):

            fund = fund_pool[i_fund]
            try:
                fund_holding = FundHolder().get_fund_holding_quarter(fund=fund)
                fund_holding_date = pd.DataFrame(fund_holding[quarter_date])
                fund_holding_date = fund_holding_date.dropna()
                fund_holding_date *= 1.0
                fund_holding_date.columns = [fund]
            except Exception as e:
                fund_holding_date = pd.DataFrame([], columns=[fund])
            if i_fund == 0:
                stock_data = fund_holding_date
            else:
                stock_data = pd.concat([stock_data, fund_holding_date], axis=1)

        stock_data = stock_data.dropna(how='all')
        stock_data_weight = pd.DataFrame(stock_data.sum(axis=1))
        stock_data_weight /= stock_data_weight.sum()
        stock_data_weight.columns = ["Weight"]
        stock_data_weight = stock_data_weight.sort_values(by=['Weight'], ascending=False)

        stock_ratio = pd.DataFrame(self.stock_ratio.loc[fund_pool, quarter_date])
        ratio = stock_ratio.median().values[0] / 100.0

        if days_diff > 30:

            # 得到股票和基金涨跌幅

            stock_pool = list(stock_data_weight.index)
            beg_date = Date().get_trade_date_offset(date, -61)
            date_series = Date().get_trade_date_series(beg_date, date)
            f_pct = self.index_return / ratio
            s_pct = self.stock_return.loc[date_series, stock_pool]
            s_pct = s_pct.T.dropna(how='all').T
            s_pct = s_pct.dropna(how='all')
            f_pct = f_pct.dropna()

            # 准备数据Lasso回归

            data = pd.concat([f_pct, s_pct], axis=1)
            data = data.loc[beg_date:date, :]
            data = data.dropna(subset=['IndexReturn'])
            data = data.fillna(0.0)
            y = np.row_stack(data['IndexReturn'].values)
            x = data.iloc[:, 1:].values

            model = LassoCV(fit_intercept=True, positive=True)

            # LassoCV自动调节alpha可以实现选择最佳的alpha

            model.fit(x, y)
            print(model.alpha_)
            alpha = model.alpha_

            model = Lasso(alpha=alpha, fit_intercept=False, positive=True)
            model.fit(x, y)

            res = pd.DataFrame(model.coef_[model.coef_ > 0.0001],
                               index=s_pct.columns[model.coef_ > 0.0001], columns=[date])
            res = res.sort_values(by=[date], ascending=False)
            result = pd.concat([res, stock_data_weight], axis=1)
            result = result.sort_values(by=['Weight'], ascending=False)

        else:
            result = stock_data_weight
        return result

    def cal_all_wind_file(self):

        """
        计算 季报日 普通股票+偏股混合基金 基金平均持仓
        还要考虑平均仓位
        """

        for i_date in range(len(self.date_series)):

            date = self.date_series[i_date]
            quarter_date = Date().get_last_fund_quarter_date(date)

            fund_pool = FundPool().get_fund_pool_code(name="基金持仓基准基金池", date=quarter_date)
            stock_ratio = pd.DataFrame(self.stock_ratio.loc[fund_pool, quarter_date])
            ratio = stock_ratio.median().values[0] / 100.0

            stock_data_weight = self.cal_weight_date(date, quarter_date)
            stock_data_weight /= stock_data_weight.sum()
            stock_data_weight.columns = ["Weight"]
            print(len(stock_data_weight))

            stock_data_weight.index.name = "Code"
            stock_data_weight *= ratio
            stock_data_weight.loc['Cash', 'Weight'] = 1.0 - ratio
            stock_data_weight["CreditTrading"] = "No"
            stock_data_weight["Date"] = date
            stock_data_weight["Price"] = 0.0
            stock_data_weight["Direction"] = "Long"

            sub_path = os.path.join(self.wind_port_path, self.port_name)
            if not os.path.exists(sub_path):
                os.makedirs(sub_path)

            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, publish_date))
            stock_data_weight.to_csv(file)

    def backtest(self):

        """ 计算 回测结果 """

        port = BackTest()
        port.set_info(self.port_name, '885000.WI')
        port.read_weight_at_all_change_date()
        port.cal_weight_at_all_daily()
        port.cal_port_return()
        port.cal_turnover()
        port.cal_summary()


if __name__ == '__main__':

    self = StockOLSRegression()

    self.get_data("20050101", "20181101", "M")
    # self.cal_all_wind_file()
    # self.backtest()

