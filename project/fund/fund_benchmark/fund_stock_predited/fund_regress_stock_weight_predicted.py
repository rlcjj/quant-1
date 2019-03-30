import os
import pandas as pd
import cvxpy as cvx
import numpy as np
from datetime import datetime

from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad
from quant.utility.factor_operate import FactorOperate


class FundRegressStockWeightPredicted(Data):

    """
    推算当前基金股票权重(上期重仓股票)

    目标：利用上期重仓股票去拟合最近基金收益率 最小化跟踪误差

    指数权重之和（加入债券指数）为1
    指数不能做空
    指数和上期季报权重换手不能太大
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\stock_predict'
        self.data_path_exposure = os.path.join(self.primary_data_path, self.sub_data_path)
        self.wind_port_path = WindPortUpLoad().path

        # 885062.WI 为短期纯债基金指数 为了拟合基金仓位
        self.fund_code_list = Fund().get_fund_pool_code(name="基金持仓基准基金池")
        self.stock_pct = Stock().read_factor_h5("Pct_chg").T
        self.fund_pct = Fund().get_fund_factor("Repair_Nav_Pct")
        self.fund_pct = self.fund_pct[self.fund_code_list]
        self.bold_pct = Index().get_index_factor("885062.WI", attr=['PCT']) * 100
        self.bold_pct.columns = ['885062.WI']
        self.stock_ratio = Fund().get_fund_factor("Stock_Ratio")
        self.regression_len = 60
        self.regression_min_len = 12

    def get_fund_stock_ratio(self, fund_code, quarter_date):

        """ 得到上个季度的股票的仓位（如果值缺失，利用上季度同类基金的平均）"""

        try:
            stock_ratio = self.stock_ratio.loc[quarter_date, fund_code]
        except Exception as e:
            stock_ratio = np.nan

        if np.isnan(stock_ratio):
            stock_ratio = self.stock_ratio.loc[quarter_date].median()

        return stock_ratio

    def regress_fund(self, fund_code, beg_date, end_date):

        """ 回归基金净值 和上季度重仓股票的涨跌幅和债券基金 """

        period = "W"
        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        fund_return = self.fund_pct[fund_code]
        fund_return = fund_return.dropna()
        date_series = list(set(date_series) & set(fund_return.index))
        date_series.sort()

        # 季报持仓
        quarter_weight = Fund().get_fund_holding_quarter(fund_code)
        r2_series = pd.DataFrame([], index=date_series, columns=['r2'])

        for i_date in range(0, len(date_series)):

            # 时间确定
            # 若此时离上个季报时间较短 则回归时间很短
            # 若此时离上个季报时间较长 则回归时间较长
            ed_date = date_series[i_date]
            ed_date = Date().get_trade_date_offset(ed_date, -0)
            quarter_date = Date().get_last_fund_quarter_date(ed_date)

            bg_date = Date().get_trade_date_offset(ed_date, -(self.regression_len - 1))
            bg_date = max(bg_date, quarter_date)
            bg_date = Date().get_trade_date_offset(bg_date, -0)

            date_diff = Date().get_trade_date_diff(bg_date, ed_date)

            # 上期持仓
            try:
                stock_weight = pd.DataFrame(quarter_weight[quarter_date])
                stock_weight = stock_weight.dropna()
                stock_weight.columns = ['Weight']

                # 收益率数据
                data = pd.concat([fund_return, self.stock_pct, self.bold_pct], axis=1)
                data['885062.WI'] = data['885062.WI'].fillna(0.0)
                regress_date_series = Date().get_trade_date_series(bg_date, ed_date)
                data = data.loc[regress_date_series, :]
                data = data.T.dropna(thresh=self.regression_min_len).T
                data = data.fillna(data.mean(axis=1))

                # 股票池
                stock_pool = list(stock_weight.index)
                stock_pool = list(set(stock_pool) & set(data.columns[1:]))
                stock_pool.sort()
                stock_pool.append("885062.WI")

                stock_ratio = self.get_fund_stock_ratio(fund_code, quarter_date)
                stock_weight['Weight'] /= stock_weight['Weight'].sum()
                stock_weight['Weight'] *= stock_ratio
                stock_weight.loc["885062.WI", "Weight"] = 100 - stock_ratio
                stock_weight /= 100.0
                stock_weight = stock_weight.loc[stock_pool, :]
                stock_weight['Weight'] /= stock_weight['Weight'].sum()

                print("## Cal Regress %s %s %s %s %s ##" % (fund_code, quarter_date, bg_date, ed_date, len(data)))

                if (len(data) > self.regression_min_len) and (len(stock_pool) > 4):

                    # 利用股票拟合基金收益率 最小化跟踪误差的前提
                    # 指数权重之和为1 指数不能做空 指数和上期季报权重换手不能太大

                    y = data[fund_code].values / 100.0
                    x = data[stock_pool].values / 100.0
                    n = len(y)
                    k = x.shape[1]
                    weight_old = stock_weight.T.values[0]
                    turnover = date_diff * 0.8 / 100
                    print("TurnOver %s " % turnover)

                    # 最优化
                    ##############################################################################
                    w = cvx.Variable(k)
                    sigma = y - x * w
                    prob = cvx.Problem(cvx.Minimize(cvx.sum_squares(sigma)),
                                       [cvx.sum(w) == 1.0,
                                        w >= 0,
                                        cvx.sum(cvx.abs(w - weight_old)) <= turnover
                                        ])
                    prob.solve()

                    print('Solver Status : ', prob.status)
                    params_add = pd.DataFrame(w.value, columns=[ed_date], index=stock_pool)

                    # 计算回归R2
                    ##############################################################################
                    tss = np.sum((y - np.mean(y)) ** 2) / n
                    y_res = y - np.dot(x, w.value)
                    rss = np.sum(y_res ** 2) / (n - k - 1)
                    r2 = 1 - rss / tss
                    params_add.loc["R2", ed_date] = r2

                    print(params_add.T)

                else:
                    params_add = pd.DataFrame([], columns=[ed_date], index=stock_pool)
            except Exception as e:
                params_add = pd.DataFrame([], columns=[ed_date])

            if i_date == 0:
                params_new = params_add
            else:
                params_new = pd.concat([params_new, params_add], axis=1)

        # 合并新数据
        ####################################################################
        params_new = params_new.T
        out_file = os.path.join(self.data_path_exposure, fund_code + '.csv')

        if os.path.exists(out_file):
            params_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            params_old.index = params_old.index.map(str)
            params = FactorOperate().pandas_add_row(params_old, params_new)
        else:
            params = params_new

        params.to_csv(out_file)

    def regress_fund_pool(self,
                          name="基金持仓基准基金池",
                          beg_date="20040301",
                          end_date=datetime.today().strftime("%Y%m%d")):

        """ 计算所有基金的 一段时间内 重仓股比例 """

        fund_code_list = Fund().get_fund_pool_code(name=name)

        for i_code in range(1, len(fund_code_list)):
            code = fund_code_list[i_code]
            self.regress_fund(code, beg_date, end_date)

    def get_wind_file_fund(self, fund_code):

        """ 将每次获得的基金内持仓股票 生成得到wind权重 """

        out_file = os.path.join(self.data_path_exposure, fund_code + '.csv')
        fund_weight = pd.read_csv(out_file, index_col=[0], encoding='gbk').T

        date_series = fund_weight.columns
        sub_path = os.path.join(self.wind_port_path, fund_code)

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
            file = os.path.join(sub_path, '%s_%s.csv' % (fund_code, next_date))
            data_date.to_csv(file)

    def backtest(self):

        """ 回测 """

        backtest = BackTest()
        backtest.set_info(fund_code, fund_code)
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return(beg_date="20040301")
        backtest.cal_turnover(annual_number=50)
        backtest.cal_summary(all_beg_date="20040301")

if __name__ == '__main__':

    beg_date = "20040301"
    end_date = "20181130"
    fund_code = "000001.OF"
    self = FundRegressStockWeightPredicted()
    # self.regress_fund_pool()
    self.regress_fund(fund_code, beg_date, end_date)
    # self.get_wind_file_fund(fund_code)
    # self.backtest()

