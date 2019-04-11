import os
import numpy as np
import pandas as pd
import cvxpy as cvx

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.barra import Barra

from quant.source.wind_portfolio import WindPortUpLoad
from quant.project.multi_factor.optimization.opt_weight import OptWeight


class OptRelativeWeight(OptWeight):

    def __init__(self):

        """
        2、max_alpha w为主动权重 考虑基准权重

        限制条件：
        2、1 风格偏离
        2、2 行业偏离
        2、3 证券绝对权重上下限
        2、4 证券相对权重偏离
        2、5 跟踪误差 ***
        2、6 换手率
        2、7 证券数量约束 ***
        """

        OptWeight.__init__(self)

        self.port_name = ""
        self.benchmark_code = ""
        self.stock_pool_name = ""

        self.industry_deviate = ""
        self.style_deviate = ""
        self.stock_deviate = ""
        self.double_turnover = ""
        self.min_tor = 0.001  # 权重最小容忍值
        self.style_columns = []
        self.weight_sum = 0.95
        self.track_error = 0.05

        self.free_mv = None
        self.trading_status = None
        self.alpha_data = None
        self.date_series = None
        self.wind_port_path = WindPortUpLoad().path

    def get_info(self,
                 port_name,
                 benchmark_code,
                 beg_date,
                 end_date,
                 period,
                 industry_deviate,
                 style_deviate,
                 stock_deviate,
                 double_turnover,
                 alpha_name,
                 stock_pool_name="AllChinaStockFilter",
                 weight_sum=0.95,
                 track_error=0.05,
                 min_tor=0.001
                 ):

        """ 回测基础信息 得到全部数据 """

        self.port_name = port_name
        self.benchmark_code = benchmark_code
        self.stock_pool_name = stock_pool_name
        self.industry_deviate = industry_deviate
        self.style_deviate = style_deviate
        self.stock_deviate = stock_deviate
        self.double_turnover = double_turnover
        self.weight_sum = weight_sum
        self.track_error = track_error
        self.min_tor = min_tor

        self.style_columns = ['Size']
        self.trading_status = Stock().read_factor_h5("TradingStatus")
        self.free_mv = Stock().read_factor_h5("Mkt_freeshares")
        self.alpha_data = self.get_alpha_factor(alpha_name)

        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        date_series = list(set(self.trading_status.columns) & set(date_series) &
                           set(self.free_mv.columns) & set(self.alpha_data.columns))
        date_series.sort()
        self.date_series = date_series

    def opt_date(self, date):

        """ 优化 其中weight为相对权重 """

        # get data
        print("Opt Relative Weight At ", date)
        next_date = Date().get_trade_date_offset(date, 1)
        alpha_data = self.get_stock_alpha_date(date)
        stock_risk_exposure = self.get_stock_risk_exposure_date(date)
        weight_bench = self.get_benchmark_weight_date(date)
        weight_last = self.get_last_stock_weight(date)
        bench_risk_exposure = self.get_benchmark_risk_exposure_date(date)
        stock_cov = self.get_stock_covariance_date(date)

        # turnover
        if len(weight_last) == 0:
            turnover = 2.00
        else:
            turnover = self.double_turnover

        # multi_factor list
        stock_can_trade = self.get_can_trade_stock_date(next_date)
        stock_can_trade = list(set(stock_can_trade) & set(stock_risk_exposure.index) & set(stock_cov.index))

        # data filter
        alpha_data = alpha_data.loc[stock_can_trade, :]
        alpha_data = alpha_data.fillna(alpha_data.mean())
        stock_risk_exposure = stock_risk_exposure.loc[stock_can_trade, :]
        stock_risk_exposure = stock_risk_exposure.dropna(how='all')
        stock_risk_exposure = stock_risk_exposure.fillna(stock_risk_exposure.mean())
        weight_bench = weight_bench.loc[stock_can_trade, :]
        weight_bench = weight_bench.fillna(0.0)
        weight_bench /= weight_bench.sum()
        stock_cov = stock_cov.loc[stock_can_trade, stock_can_trade]


        # weight
        weight_up = pd.DataFrame([], index=weight_bench.index, columns=['WeightUp'])
        weight_up['WeightUp'] = self.stock_deviate
        weight_low = - pd.DataFrame(weight_bench.values, index=weight_bench.index, columns=['WeightLow'])
        weight_low['WeightLow'] = weight_low['WeightLow'].map(lambda x: max(x, - self.stock_deviate))

        weight_last = weight_last.loc[stock_can_trade, :]
        weight_last = weight_last.fillna(0.0)

        # values
        alpha_values = alpha_data.values
        weight_up_values = weight_up['WeightUp'].values
        weight_low_values = weight_low['WeightLow'].values
        weight_last_values = weight_last['Weight'].values
        weight_bench_values = weight_bench['BenchWeight'].values
        stock_cov_values = stock_cov.values

        # limit of style
        style_columns = list(Barra().get_factor_name(type_list=['STYLE'])['NAME_EN'].values)
        stock_style_values = stock_risk_exposure[style_columns].values

        # limit of industry
        industry_columns = list(Barra().get_factor_name(type_list=['INDUSTRY'])['NAME_EN'].values)
        stock_industry_values = stock_risk_exposure[industry_columns].values
        bench_industry_values = bench_risk_exposure[industry_columns].values[0]
        bench_industry_low_values = -bench_industry_values.T
        bench_industry_low_values = np.array(list(map(lambda x: max(x,  -self.industry_deviate),
                                                      bench_industry_low_values)))

        # opt
        n = len(stock_can_trade)

        if n > 0:

            w = cvx.Variable(n)
            prob = cvx.Problem(cvx.Maximize(alpha_values.T * w),
                               [cvx.sum(w) == 0,
                                w >= weight_low_values,
                                w <= weight_up_values,
                                # cvx.quad_form(w, stock_cov_values) <= self.track_error ** 2,
                                # cvx.sum(cvx.abs(w + weight_bench_values - weight_last_values)) <= turnover,
                                stock_style_values.T * w <= self.style_deviate,
                                stock_style_values.T * w >= -self.style_deviate,
                                stock_industry_values.T * w <= self.industry_deviate,
                                stock_industry_values.T * w >= bench_industry_low_values,
                                ])
            prob.solve()
            print("status:", prob.status)
            print("optimal value", prob.value)

            # weight
            weight_bench.columns = ['Weight']
            weight_active = pd.DataFrame(w.value, columns=['Weight'], index=stock_can_trade)
            weight = weight_active.add(weight_bench)
            weight /= weight.sum()
            print("优化结果", len(weight))

            self.generate_weight_file(weight, date, next_date)
            self.analysis_date(date)


    def analysis_date(self, date):

        """ 优化后分析 """

        print("Analysis Port Exposure At ", date)
        next_date = Date().get_trade_date_offset(date, 1)
        alpha_data = self.get_stock_alpha_date(date)
        stock_risk_exposure = self.get_stock_risk_exposure_date(date)
        weight_bench = self.get_benchmark_weight_date(date)
        weight_last = self.get_last_stock_weight(date)
        bench_risk_exposure = self.get_benchmark_risk_exposure_date(date)
        stock_cov = self.get_stock_covariance_date(date)
        weight = self.get_stock_weight(next_date)

        # multi_factor list
        stock_can_trade = self.get_can_trade_stock_date(next_date)
        stock_can_trade = list(set(stock_can_trade) & set(stock_risk_exposure.index) & set(stock_cov.index))

        # data filter
        alpha_data = alpha_data.loc[stock_can_trade, :]
        alpha_data = alpha_data.fillna(alpha_data.mean())
        stock_risk_exposure = stock_risk_exposure.loc[stock_can_trade, :]
        stock_risk_exposure = stock_risk_exposure.dropna(how='all')
        stock_risk_exposure = stock_risk_exposure.fillna(stock_risk_exposure.mean())
        weight_bench = weight_bench.loc[stock_can_trade, :]
        weight_bench = weight_bench.fillna(0.0)
        weight_bench /= weight_bench.sum()
        stock_cov = stock_cov.loc[stock_can_trade, stock_can_trade]

        weight.columns = ['TotalWeight']
        weight_bench.columns = ['BenchWeight']
        weight_analysis = pd.concat([alpha_data, weight, weight_bench], axis=1)
        weight_analysis = weight_analysis.loc[stock_can_trade, :]
        weight_analysis = weight_analysis.fillna(0.0)
        weight_analysis['ActiveWeight'] = weight_analysis['TotalWeight'] - weight_analysis['BenchWeight']
        weight_analysis = weight_analysis.sort_values(by=['ActiveWeight'], ascending=False)

        weight_active = pd.DataFrame(weight_analysis['ActiveWeight'])
        track_error = np.sqrt(weight_active.T.dot(stock_cov).dot(weight_active).values[0][0])
        print(track_error)

        risk_exposure = weight_analysis.T.dot(stock_risk_exposure)
        risk_exposure = risk_exposure.T
        risk_exposure.columns = ["TotalAlpha", "TotalExposure", "BenchExposure", "ActiveExposure"]

        sub_path = os.path.join(self.wind_port_path, self.port_name + '暴露')
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        file = os.path.join(sub_path, '%s暴露_%s.csv' % (self.port_name, next_date))
        risk_exposure.to_csv(file)
        file = os.path.join(sub_path, '%s权重_%s.csv' % (self.port_name, next_date))
        weight_analysis['Name'] = weight_analysis.index.map(lambda x: Stock().get_stock_name_date(x, next_date))
        weight_analysis.to_csv(file)

    def opt_all(self):

        """ 每期优化 """

        for i_date in range(len(self.date_series)):

            date = self.date_series[i_date]
            self.opt_date(date)


if __name__ == '__main__':

    self = OptRelativeWeight()
    date = "20171229"
    # self.update_data()

    """ 沪深300增强 """

    port_name = "沪深300增强"
    benchmark_code = "000300.SH"
    stock_pool_name = "hs300"
    period = "W"
    beg_date = "20190128"
    end_date = "20190401"
    industry_deviate = 0.005
    style_deviate = 0.05
    stock_deviate = 0.015
    double_turnover = 0.20
    alpha_name = "alpha"
    weight_sum = 0.95
    track_error = 0.08
    min_tor = 0.002

    self.get_info(port_name, benchmark_code, beg_date, end_date, period,
                  industry_deviate, style_deviate, stock_deviate, double_turnover,
                  alpha_name, stock_pool_name, weight_sum, track_error, min_tor)
    self.opt_all()
    self.backtest()
    # WindPortUpLoad().upload_weight_period(port_name)

    """ 中证500增强 """

    port_name = "中证500增强"
    benchmark_code = "000905.SH"
    stock_pool_name = "zz500"
    period = "M"
    beg_date = "20110501"
    end_date = "20190401"
    industry_deviate = 0.005
    style_deviate = 0.05
    stock_deviate = 0.015
    double_turnover = 0.20
    alpha_name = "alpha"
    weight_sum = 0.95
    track_error = 0.08
    min_tor = 0.002

    self.get_info(port_name, benchmark_code, beg_date, end_date, period,
                  industry_deviate, style_deviate, stock_deviate, double_turnover,
                  alpha_name, stock_pool_name, weight_sum, track_error, min_tor)

    self.opt_all()
    self.backtest()
