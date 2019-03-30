import cvxpy as cvx
import numpy as np
import pandas as pd
from project.multi_factor.optimization import OptWeight
from quant.source.wind_portfolio import WindPortUpLoad
from quant.stock.barra import Barra
from quant.stock.date import Date
from quant.stock.stock import Stock


class OptAbsoluteWeight(OptWeight):

    def __init__(self):

        """
        1、max_alpha w为绝对权重 不考虑基准权重

        限制条件：
        1、1 控制风格偏离
        1、2 控制行业偏离
        1、3 控制股票上下限
        1、4 控制换手率
        """
        OptWeight.__init__(self)

        self.port_name = ""
        self.weight_name = ""
        self.benchmark_code = ""
        self.stock_pool_name = ""

        self.industry_deviate = ""
        self.style_deviate = ""
        self.double_turnover = ""
        self.min_tor = 0.001  # 权重最小容忍值
        self.style_columns = []
        self.weight_sum = 0.95
        self.weight_type = 'fixed'

        self.free_mv = None
        self.trading_status = None
        self.alpha_data = None
        self.date_series = None
        self.wind_port_path = WindPortUpLoad().path

    def get_info(self,
                 port_name,
                 weight_name,
                 benchmark_code,
                 stock_pool_name,
                 beg_date,
                 end_date,
                 period,
                 industry_deviate,
                 style_deviate,
                 double_turnover,
                 alpha_name,
                 alpha_type="my_alpha",
                 weight_sum=0.95,
                 weight_type='fixed',
                 min_tor=0.001
                 ):

        """ 回测基础信息 得到全部数据 """

        self.port_name = port_name
        self.weight_name = weight_name
        self.benchmark_code = benchmark_code
        self.stock_pool_name = stock_pool_name
        self.industry_deviate = industry_deviate
        self.style_deviate = style_deviate
        self.double_turnover = double_turnover
        self.weight_sum = weight_sum
        self.weight_type = weight_type
        self.min_tor = min_tor

        self.style_columns = ['Size']
        self.trading_status = Stock().read_factor_h5("TradingStatus")
        self.free_mv = Stock().read_factor_h5("Mkt_freeshares")
        self.get_alpha_factor(alpha_name, alpha_type)

        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        date_series = list(map(lambda x: Date().get_trade_date_offset(x, 24), date_series))
        date_series = list(set(self.trading_status.columns) & set(date_series) &
                           set(self.free_mv.columns))
        date_series.sort()
        self.date_series = date_series

    def opt_date(self, date):

        """ 优化 其中weight为绝对权重 """

        # get data
        next_date = Date().get_trade_date_offset(date, 1)
        alpha_data = self.get_stock_alpha_date(date)
        stock_risk_exposure = self.get_stock_risk_exposure_date(date)
        weight_up = self.get_stock_weight_limit_up(date)
        weight_last = self.get_last_stock_weight(date)
        bench_risk_exposure = self.get_benchmark_risk_exposure_date(date)

        # turnover
        if len(weight_last) == 0:
            turnover = 2.00
        else:
            turnover = self.double_turnover

        # multi_factor list
        stock_can_trade = self.get_can_trade_stock_date(next_date)
        stock_can_trade = list(set(alpha_data.index) & set(stock_can_trade)
                               & set(stock_risk_exposure.index) & set(weight_up.index))

        # data filter
        alpha_data = alpha_data.loc[stock_can_trade, :]
        stock_risk_exposure = stock_risk_exposure.loc[stock_can_trade, :]
        weight_up = weight_up.loc[stock_can_trade, :]
        weight_last = weight_last.loc[stock_can_trade, :]
        weight_last = weight_last.fillna(0.0)

        # limit weight of multi_factor
        alpha_values = alpha_data.values
        weight_up_values = weight_up['UpRatio'].values
        weight_last_values = weight_last['Weight'].values

        # limit of style
        style_columns = list(Barra().get_factor_name(type_list=['STYLE'])['NAME_EN'].values)
        stock_style_values = stock_risk_exposure[style_columns].values
        bench_style_values = bench_risk_exposure[style_columns].values[0]
        bench_style_up_values = bench_style_values.T + self.style_deviate
        bench_style_low_values = bench_style_values.T - self.style_deviate

        # limit of industry
        industry_columns = list(Barra().get_factor_name(type_list=['INDUSTRY'])['NAME_EN'].values)
        stock_industry_values = stock_risk_exposure[industry_columns].values
        bench_industry_values = bench_risk_exposure[industry_columns].values[0]
        bench_industry_up_values = bench_industry_values.T + self.industry_deviate
        bench_industry_low_values = bench_industry_values.T - self.industry_deviate
        bench_industry_low_values = np.array(list(map(lambda x: max(x, 0.0), bench_industry_low_values)))

        # opt
        n = len(stock_can_trade)
        w = cvx.Variable(n)
        prob = cvx.Problem(cvx.Maximize(alpha_values.T * w),
                           [cvx.sum(w) == 1,
                            w >= 0,
                            w <= weight_up_values,
                            cvx.sum(cvx.abs(w - weight_last_values)) <= turnover,
                            stock_style_values.T * w <= bench_style_up_values,
                            stock_style_values.T * w >= bench_style_low_values,
                            stock_industry_values.T * w <= bench_industry_up_values,
                            stock_industry_values.T * w >= bench_industry_low_values,
                            ])
        prob.solve()
        print("status:", prob.status)
        print("optimal value", prob.value)
        weight_precise = pd.DataFrame(w.value, columns=['Weight'], index=stock_can_trade)
        self.generate_weight_file(weight_precise, date, next_date)

        # test result
        result_risk_exposure = weight_precise.T.dot(stock_risk_exposure)
        result_risk_exposure = result_risk_exposure.T
        result_risk_exposure.columns = ['ResultExposure']

        up_risk_exposure = bench_risk_exposure.T.copy()
        up_risk_exposure.columns = ["UpExposure"]
        up_risk_exposure.loc[style_columns, "UpExposure"] += self.style_deviate
        up_risk_exposure.loc[industry_columns, "UpExposure"] += self.industry_deviate

        low_risk_exposure = bench_risk_exposure.T.copy()
        low_risk_exposure.columns = ["LowExposure"]
        low_risk_exposure.loc[style_columns, "LowExposure"] -= self.style_deviate
        low_risk_exposure.loc[industry_columns, "LowExposure"] -= self.industry_deviate
        low_risk_exposure.loc[industry_columns, "LowExposure"] = \
            low_risk_exposure.loc[industry_columns, "LowExposure"].map(lambda x: 0.0 if x < 0.0 else x)

        precise_result = pd.concat([result_risk_exposure, low_risk_exposure, up_risk_exposure], axis=1)
        precise_result = precise_result.loc[stock_risk_exposure.columns, :]


    def opt_all(self):

        """ 每期优化 """

        for i_date in range(len(self.date_series)):

            date = self.date_series[i_date]
            print("Opt Absolute Weight At ", date)
            self.opt_date(date)


if __name__ == '__main__':

    # 测试2
    date = "20171229"
    self = OptAbsoluteWeight()
    port_name = "天风股票基金增强Factor3"
    weight_name = "天风股票基金"
    benchmark_code = "885000.WI"
    stock_pool_name = "AllChinaStockFilter"
    period = "Q"
    beg_date = "20060101"
    end_date = "20181201"
    industry_deviate = 0.015
    style_deviate = 0.02
    double_turnover = 2.00  # 单次双边换手率
    alpha_name = "Factor_Equal_3"
    alpha_type = "my_alpha"
    weight_sum = 0.95
    weight_type = 'fixed'
    min_tor = 0.001

    self.get_info(port_name, weight_name, benchmark_code, stock_pool_name,
                  beg_date, end_date, period, industry_deviate, style_deviate,
                  double_turnover, alpha_name, alpha_type, weight_sum, weight_type, min_tor)
    self.update_data()
    self.opt_all()
    self.backtest()
