import cvxpy as cvx
import numpy as np
import pandas as pd
from project.multi_factor.optimization import OptWeight
from quant.source.wind_portfolio import WindPortUpLoad
from quant.stock.barra import Barra
from quant.stock.date import Date
from quant.stock.stock import Stock


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
        self.weight_name = ""
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
                 stock_deviate,
                 double_turnover,
                 alpha_name,
                 alpha_type,
                 weight_sum=0.95,
                 weight_type='fixed',
                 track_error=0.05,
                 min_tor = 0.001
                 ):

        """ 回测基础信息 得到全部数据 """

        self.port_name = port_name
        self.weight_name = weight_name
        self.benchmark_code = benchmark_code
        self.stock_pool_name = stock_pool_name
        self.industry_deviate = industry_deviate
        self.style_deviate = style_deviate
        self.stock_deviate = stock_deviate
        self.double_turnover = double_turnover
        self.weight_sum = weight_sum
        self.track_error = track_error
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

        """ 优化 其中weight为相对权重 """

        # get data
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
        stock_can_trade = list(set(alpha_data.index) & set(stock_can_trade)
                               & set(stock_risk_exposure.index)
                               & set(stock_cov.index))

        # data filter
        alpha_data = alpha_data.loc[stock_can_trade, :]
        stock_risk_exposure = stock_risk_exposure.loc[stock_can_trade, :]
        weight_bench = weight_bench.loc[stock_can_trade, :]
        weight_bench = weight_bench.fillna(0.0)
        weight_bench /= weight_bench.sum()
        stock_cov = stock_cov.loc[stock_can_trade, stock_can_trade]

        # weight
        weight_up = weight_bench.copy() * self.stock_deviate
        weight_up.columns = ['WeightUp']
        weight_low = weight_bench.copy() * -1
        weight_low.columns = ['WeightLow']
        weight_low['WeightLow'] = weight_low['WeightLow'].map(lambda x: max(x, -self.stock_deviate))

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
        w = cvx.Variable(n)
        prob = cvx.Problem(cvx.Maximize(alpha_values.T * w),
                           [cvx.sum(w) == 0,
                            w >= weight_low_values,
                            w <= weight_up_values,
                            # cvx.quad_form(w, stock_cov_values) <= self.track_error ** 2,
                            cvx.sum(cvx.abs(w + weight_bench_values - weight_last_values)) <= turnover,
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
        self.generate_weight_file(weight, date, next_date)
        self.analysis_stock_weight(weight, weight_bench, weight_active, alpha_data, stock_cov)

    def analysis_style_deviate(self):

        """ 分析本期风格行业偏离 """

        # result_risk_exposure = weight_precise.T.dot(stock_risk_exposure)
        # result_risk_exposure = result_risk_exposure.T
        # result_risk_exposure.columns = ['ResultExposure']
        #
        # up_risk_exposure = bench_risk_exposure.T.copy()
        # up_risk_exposure.columns = ["UpExposure"]
        # up_risk_exposure.loc[style_columns, "UpExposure"] += self.style_deviate
        # up_risk_exposure.loc[industry_columns, "UpExposure"] += self.industry_deviate
        #
        # low_risk_exposure = bench_risk_exposure.T.copy()
        # low_risk_exposure.columns = ["LowExposure"]
        # low_risk_exposure.loc[style_columns, "LowExposure"] -= self.style_deviate
        # low_risk_exposure.loc[industry_columns, "LowExposure"] -= self.industry_deviate
        # low_risk_exposure.loc[industry_columns, "LowExposure"] = \
        #     low_risk_exposure.loc[industry_columns, "LowExposure"].map(lambda x: 0.0 if x < 0.0 else x)
        #
        # precise_result = pd.concat([result_risk_exposure, low_risk_exposure, up_risk_exposure], axis=1)
        # precise_result = precise_result.loc[stock_risk_exposure.columns, :]

    def analysis_stock_weight(self, weight, weight_bench, weight_active, alpha_data, stock_cov):

        """ 分析本期股票偏离 """

        weight.columns = ['TotalWeight']
        weight_bench.columns = ['BenchWeight']
        alpha_data.columns = ['Alpha']
        weight_analysis = pd.concat([alpha_data, weight, weight_bench], axis=1)
        weight_analysis['ActiveWeight'] = weight_analysis['TotalWeight'] - weight_analysis['BenchWeight']
        weight_analysis = weight_analysis.fillna(0.0)
        weight_analysis = weight_analysis.sort_values(by=['ActiveWeight'], ascending=False)
        weight_analysis[['TotalWeight', 'ActiveWeight', 'BenchWeight']] *= 100.0

        track_error = np.sqrt(weight_active.T.dot(stock_cov).dot(weight_active).values[0][0])
        print(track_error)

    def opt_all(self):

        """ 每期优化 """

        for i_date in range(len(self.date_series)):

            date = self.date_series[i_date]
            print("Opt Relative Weight At ", date)
            self.opt_date(date)


if __name__ == '__main__':

    # 测试1
    # date = "20171229"
    # self = OptRelativeWeight()
    # port_name = "天风股票基金增强Factor3"
    # weight_name = "天风股票基金"
    # benchmark_code = "885000.WI"
    # stock_pool_name = "AllChinaStockFilter"
    # period = "Q"
    # beg_date = "20060101"
    # end_date = "20181201"
    # industry_deviate = 0.015
    # style_deviate = 0.02
    # stock_deviate = 0.02
    # double_turnover = 2.00  # 单次双边换手率
    # alpha_name = "Factor_Equal_3"
    # alpha_type = "my_alpha"
    # weight_sum = 0.95
    #
    # self.get_info(port_name, weight_name, benchmark_code, stock_pool_name,
    #               beg_date, end_date, period, industry_deviate, style_deviate, stock_deviate,
    #               double_turnover, alpha_name, alpha_type, weight_sum)
    # self.update_data()
    # self.opt_all()
    # self.backtest()

    # 测试2
    # date = "20171229"
    # self = OptRelativeWeight()
    # port_name = "沪深300_ROEQuarterDaily"
    # weight_name = "000300.SH"
    # benchmark_code = "000300.SH"
    # stock_pool_name = "AllChinaStockFilter"
    # period = "M"
    # beg_date = "20180201"
    # end_date = "20181201"
    # industry_deviate = 0.03
    # style_deviate = 0.30
    # stock_deviate = 0.03
    # double_turnover = 2.00  # 单次双边换手率
    # alpha_name = "ROEQuarterDaily"
    # alpha_type = "my_res_sample_alpha"
    # weight_sum = 0.95
    # track_error = 0.08
    # weight_type = 'fixed'
    # min_tor = 0.002
    #
    # self.get_info(port_name, weight_name, benchmark_code, stock_pool_name,
    #               beg_date, end_date, period, industry_deviate, style_deviate, stock_deviate,
    #               double_turnover, alpha_name, alpha_type, weight_sum, weight_type, track_error, min_tor)
    # self.update_data()
    # self.opt_all()
    # self.backtest()

    # 测试3
    date = "20171229"
    self = OptRelativeWeight()
    port_name = "中证500_ROEQuarterDaily"
    weight_name = "000905.SH"
    benchmark_code = "000905.SH"
    stock_pool_name = "AllChinaStockFilter"
    period = "M"
    beg_date = "20111101"
    end_date = "20181201"
    industry_deviate = 0.03
    style_deviate = 0.30
    stock_deviate = 0.03
    double_turnover = 2.00  # 单次双边换手率
    alpha_name = "ROEQuarterDaily"
    alpha_type = "my_res_sample_alpha"
    weight_sum = 0.95
    track_error = 0.08
    weight_type = 'fixed'
    min_tor = 0.002

    self.get_info(port_name, weight_name, benchmark_code, stock_pool_name,
                  beg_date, end_date, period, industry_deviate, style_deviate, stock_deviate,
                  double_turnover, alpha_name, alpha_type, weight_sum, weight_type, track_error, min_tor)
    # self.update_data()
    # self.opt_all()
    self.backtest()
