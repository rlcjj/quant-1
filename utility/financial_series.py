import numpy as np
import pandas as pd

from quant.stock.date import Date


class FinancialSeries(object):

    """
    计算证券时间序列上的各种指标

    1、时间序列本身 收益 风险 风险收益比 最大回撤
    get_interval_return()
    get_interval_std()
    get_interval_return_annual()
    get_interval_std_annual()
    get_interval_max_drawdown()
    get_interval_return_std_ratio()
    get_interval_shape_ratio()

    2、对于时间序列的基准
    get_interval_return_benchmark()
    get_interval_std_benchmark()
    get_interval_return_annual_benchmark()
    get_interval_std_annual_benchmark()
    get_interval_max_drawdown_benchmark()
    get_interval_return_std_ratio_benchmark()
    get_interval_shape_ratio_benchmark()

    3、时间序列相对于基准
    get_interval_tracking_error()
    get_interval_excess_return()
    get_interval_excess_return_annual()
    get_interval_ir()
    get_interval_excess_return_max_drawdown()

    4、得到另外一个时间序列
    get_fund_cum_return_series()
    get_bencnmark_cum_return_series()
    get_fund_and_bencnmark_cum_return_series()
    get_excess_return_series()

    """

    def __init__(self, data, data_benchmark=None, index_ratio=1):

        self.data = data.copy()
        self.data.columns = ['nav']
        self.data["return"] = self.data["nav"].pct_change()
        self.index_ratio = index_ratio

        if data_benchmark is not None:
            self.data_benchmark = data_benchmark.copy()
            self.data_benchmark.columns = ['nav']
            self.data_benchmark["return"] = self.data_benchmark["nav"].pct_change()

    def get_interval_return(self, beg_date, end_date, short_handled=False):

        """ 区间累计收益率 """

        data_interval = self.data.ix[beg_date:end_date]
        data_interval = data_interval.dropna()
        if len(data_interval) == 0:
            return_interval = ""
        else:
            data_interval['cum_return'] = (data_interval["return"] + 1.0).cumprod() - 1.0
            return_interval = data_interval.ix[len(data_interval) - 1, 'cum_return']

            if short_handled:
                if beg_date < self.data.index[0]:
                    return_interval = ""

        return return_interval

    def get_interval_std(self, beg_date, end_date):

        """ 区间日收益率的标准差（非年化） """

        data_interval = self.data.ix[beg_date:end_date]
        std_interval = data_interval["return"].std()
        return std_interval

    def get_interval_return_annual(self, beg_date, end_date):

        """ 区间累计收益率的年化值 """

        data_interval = self.data.ix[beg_date:end_date]
        l = len(data_interval)
        return_interval = self.get_interval_return(beg_date, end_date)
        return_interval_annual = (return_interval + 1.0) ** (250 / l) - 1.0
        return return_interval_annual

    def get_interval_std_annual(self, beg_date, end_date):

        """ 区间日收益率的年化标准差 """

        std_interval = self.get_interval_std(beg_date, end_date)
        std_interval_annual = std_interval * np.sqrt(250)
        return std_interval_annual

    def get_interval_max_drawdown(self, beg_date, end_date):

        """ 区间内最大回撤率 """

        data_interval = self.data.ix[beg_date:end_date]
        data_interval["nav_interval"] = (data_interval['return'] + 1.0).cumprod()
        data_interval["max_dd"] = data_interval["nav_interval"] / data_interval["nav_interval"].expanding().max() - 1.0
        mdd = data_interval["max_dd"].min()
        return mdd

    def get_interval_return_std_ratio(self, beg_date, end_date):

        """ 区间年化收益/年化标准差 """

        std_interval_annual = self.get_interval_std_annual(beg_date, end_date)
        return_interval_annual = self.get_interval_return_annual(beg_date, end_date)
        interval_return_std_ratio = return_interval_annual / std_interval_annual
        return interval_return_std_ratio

    def get_interval_shape_ratio(self, beg_date, end_date, risk_free=0.03):

        """ 区间夏普率=（年化收益-无风险收益）/年化标准差 """

        std_interval_annual = self.get_interval_std_annual(beg_date, end_date)
        return_interval_annual = self.get_interval_return_annual(beg_date, end_date)
        shape_ratio = (return_interval_annual - risk_free) / std_interval_annual
        return shape_ratio

    def get_interval_return_benchmark(self, beg_date, end_date):

        """ 区间基准的累计收益率 """

        data_interval_benchmark = self.data_benchmark.loc[beg_date:end_date]

        if len(data_interval_benchmark) > 0:
            return_interval_benchmark = ((data_interval_benchmark["return"] + 1.0)
                                         .cumprod() - 1.0).iloc[len(data_interval_benchmark) - 1,]
        else:
            return_interval_benchmark = 0.0

        return return_interval_benchmark

    def get_interval_return_benchmark_ratio(self, beg_date, end_date):

        """ 区间基准的累计收益率 * 指数仓位 """

        try:
            data_interval_benchmark = self.get_interval_return_benchmark(beg_date, end_date) * self.index_ratio
        except Exception as e:
            print(e)
            data_interval_benchmark = "None"

        return data_interval_benchmark

    def get_interval_std_benchmark(self, beg_date, end_date):

        """ 区间基准的日收益率的标准差 """

        data_interval_benchmark = self.data_benchmark.ix[beg_date:end_date]
        std_interval_benchmark = data_interval_benchmark["return"].std()
        return std_interval_benchmark

    def get_interval_return_annual_benchmark(self, beg_date, end_date):

        """ 区间基准的累计收益的年化值 """

        data_interval_benchmark = self.data_benchmark.ix[beg_date:end_date]
        l = len(data_interval_benchmark)
        return_interval_benchmark = self.get_interval_return_benchmark(beg_date, end_date)
        return_interval_annual_benchmark = (return_interval_benchmark + 1.0) ** (250 / l) - 1.0
        return return_interval_annual_benchmark

    def get_interval_return_annual_benchmark_ratio(self, beg_date, end_date):

        """ 区间基准的累计收益的年化值() """
        pct = self.get_interval_return_annual_benchmark(beg_date, end_date) * self.index_ratio
        return pct

    def get_interval_std_annual_benchmark(self, beg_date, end_date):

        """ 区间基准的收益的年化标准差 """

        std_interval_benchmark = self.get_interval_std_benchmark(beg_date, end_date)
        std_interval_annual_benchmark = std_interval_benchmark * np.sqrt(250)
        return std_interval_annual_benchmark

    def get_interval_max_drawdown_benchmark(self, beg_date, end_date):

        """ 区间基准的最大回撤率 """

        data_interval_benchmark = self.data_benchmark.ix[beg_date:end_date]
        data_interval_benchmark["nav_interval"] = (data_interval_benchmark['return'] + 1.0).cumprod()
        data_interval_benchmark["max_dd"] = data_interval_benchmark["nav_interval"] / \
                                            data_interval_benchmark["nav_interval"].expanding().max() - 1.0
        mdd = data_interval_benchmark["max_dd"].min()
        return mdd

    def get_interval_return_std_ratio_benchmark(self, beg_date, end_date):

        """ 区间基准的年化收益/年化标准差 """

        std_interval_annual_benchmark = self.get_interval_std_annual_benchmark(beg_date, end_date)
        return_interval_annual_benchmark = self.get_interval_return_annual_benchmark(beg_date, end_date)
        interval_return_std_ratio_benchmark = return_interval_annual_benchmark / std_interval_annual_benchmark
        return interval_return_std_ratio_benchmark

    def get_interval_shape_ratio_benchmark(self, beg_date, end_date, risk_free=0.03):

        """ 区间基准的夏普比率 """

        std_interval_annual_benchmark = self.get_interval_std_annual_benchmark(beg_date, end_date)
        return_interval_annual_benchmark = self.get_interval_return_annual_benchmark(beg_date, end_date)
        shape_ratio_benchmark = (return_interval_annual_benchmark - risk_free) / std_interval_annual_benchmark
        return shape_ratio_benchmark

    def get_interval_tracking_error(self, beg_date, end_date):

        """ 区间跟踪误差 """

        data_interval = self.data.ix[beg_date:end_date]
        data_benchmark_interval = self.data_benchmark.ix[beg_date:end_date]
        data = pd.concat([data_interval, data_benchmark_interval], axis=1)
        data.columns = ["nav", 'return', 'nav_benchmark', 'return_benchmark']
        data = data.dropna()
        if len(data) == 0:
            print("len is zero")
            tracking_error = np.nan
        else:
            data["excess_return"] = data["return"] - data["return_benchmark"] * self.index_ratio
            tracking_error = data["excess_return"].std() * np.sqrt(250)
        return tracking_error

    def get_interval_excess_return(self, beg_date, end_date):

        """ 区间累计超额收益（不是每天超额收益的累加值） """

        interval_return = self.get_interval_return(beg_date, end_date)
        benchmark_return = self.get_interval_return_benchmark(beg_date, end_date)
        try:
            excess_return = interval_return - benchmark_return * self.index_ratio
        except Exception as e:
            excess_return = "None"

        return excess_return

    def get_interval_excess_return_annual(self, beg_date, end_date):

        """ 区间累计超额收益的年化值 """

        data_interval_benchmark = self.data_benchmark.ix[beg_date:end_date]
        l = len(data_interval_benchmark)
        excess_return = self.get_interval_excess_return(beg_date, end_date)

        try:
            excess_return_annual = (excess_return + 1.0) ** (250 / l) - 1.0
        except:
            excess_return_annual = "None"

        return excess_return_annual

    def get_interval_excess_return_mean_annual(self, beg_date, end_date):

        """ 区间日超额收益均值的年化值 """

        data_interval = self.data.ix[beg_date:end_date]
        data_benchmark_interval = self.data_benchmark.ix[beg_date:end_date]
        data = pd.concat([data_interval, data_benchmark_interval], axis=1)
        data.columns = ["nav", 'return', 'nav_benchmark', 'return_benchmark']
        data = data.dropna()
        if len(data) == 0:
            print("len is zero")
            tracking_error = np.nan
        else:
            data["excess_return"] = data["return"] - data["return_benchmark"]
            tracking_error = data["excess_return"].mean() * 250
        return tracking_error

    def get_interval_mean_ir(self, beg_date, end_date):

        """ 区间IR（日超额收益均值年化/跟踪误差） """

        track_error = self.get_interval_tracking_error(beg_date, end_date)
        excess_return_annual = self.get_interval_excess_return_annual(beg_date, end_date)
        try:
            ir = excess_return_annual / track_error
        except:
            ir = "None"

        return ir

    def get_interval_ir(self, beg_date, end_date):

        """ 区间IR (累计年化超额收益/跟踪误差)"""

        track_error = self.get_interval_tracking_error(beg_date, end_date)
        excess_return_annual = self.get_interval_excess_return_annual(beg_date, end_date)
        ir = excess_return_annual / track_error
        return ir

    def get_interval_excess_return_max_drawdown(self, beg_date, end_date):

        """ 区间累计超额收益的最大回撤 """

        data_interval = self.data.ix[beg_date:end_date]
        data_benchmark_interval = self.data_benchmark.ix[beg_date:end_date]
        data = pd.concat([data_interval, data_benchmark_interval], axis=1)
        data.columns = ["nav", 'return', 'nav_benchmark', 'return_benchmark']
        data = data.dropna()
        if len(data) == 0:
            print("len is zero")
            excess_return_max_drawdown = np.nan
        else:
            # data["excess_return"] = (data["return"] + 1.0).cumprod() - (data["return_benchmark"] + 1.0).cumprod()
            data["excess_return"] = data["return"] - data["return_benchmark"]
            data["nav_interval"] = data['excess_return'] + 1.0
            data["max_dd"] = (data["nav_interval"] / data["nav_interval"].expanding().max()) - 1.0
            excess_return_max_drawdown = data["max_dd"].min()
        return excess_return_max_drawdown

    def get_fund_cum_return_series(self, beg_date, end_date):

        """ 基金累计收益率序列 """

        data_interval = self.data.ix[beg_date:end_date]
        data_interval = data_interval.dropna()
        data_interval["cum_return"] = (data_interval["return"] + 1.0).cumprod() - 1.0
        data_interval = pd.DataFrame(data_interval["cum_return"])
        return data_interval

    def get_bencnmark_cum_return_series(self, beg_date, end_date):

        """ 基金基准累计收益率序列 """

        data_interval = self.data_benchmark.ix[beg_date:end_date]
        data_interval = data_interval.dropna()
        data_interval["cum_return"] = (data_interval["return"] + 1.0).cumprod() - 1.0
        data_interval = pd.DataFrame(data_interval["cum_return"])
        return data_interval

    def get_fund_and_bencnmark_cum_return_series(self, beg_date, end_date):

        """ 基金和基金基准累计收益率序列 """

        fund_cum_return = self.get_fund_cum_return_series(beg_date, end_date)
        benchmark_cum_return = self.get_bencnmark_cum_return_series(beg_date, end_date)
        data_cum_return = pd.concat([fund_cum_return, benchmark_cum_return], axis=1)
        data_cum_return.columns = ["fund", 'benchmark']
        data_cum_return = data_cum_return.dropna()
        return data_cum_return

    def get_cum_excess_return_series(self, beg_date, end_date):

        """ 基金日超额累计收益率序列 """

        data_interval = self.data.ix[beg_date:end_date]
        data_benchmark_interval = self.data_benchmark.ix[beg_date:end_date]
        data = pd.concat([data_interval, data_benchmark_interval], axis=1)
        data.columns = ["nav", 'return', 'nav_benchmark', 'return_benchmark']
        data = data.dropna()

        if len(data) == 0:
            print("len is zero")
            data_excess_return = pd.DataFrame([], columns=['cum_excess_return'])
        else:
            data["excess_return"] = data["return"] - data["return_benchmark"] * self.index_ratio
            data_excess_return = pd.DataFrame(data["excess_return"].cumsum())
            data_excess_return.columns = ['cum_excess_return']

        return data_excess_return

    def get_fund_benchmark_daily_return_series(self, beg_date, end_date):

        """ 基金和基准日收益率序列 """

        fund_cum_return = self.data['return']
        benchmark_cum_return = self.data_benchmark['return']
        data_cum_return = pd.concat([fund_cum_return, benchmark_cum_return], axis=1)
        data_cum_return.columns = ["fund", 'benchmark']
        data_cum_return = data_cum_return.dropna()
        data_cum_return = data_cum_return.loc[beg_date:end_date, :]
        return data_cum_return

if __name__ == '__main__':

    # 得到数据
    from quant.mfc.mfc_data import MfcData
    from quant.stock.index import Index

    fund_code = "162216.OF"
    index_code = "000905.SH"

    fund_code = "162213.OF"
    index_code = "000300.SH"

    fund = MfcData().get_mfc_public_fund_nav(fund_code)
    fund = pd.DataFrame(fund["NAV_ADJ"].values, index=fund.index, columns=["FundNav"])
    index = Index().get_index_factor(index_code, attr=["CLOSE"])

    # 计算各种指标
    fs = FinancialSeries(pd.DataFrame(fund), pd.DataFrame(index))

    beg_date = '20170101'
    end_date = '20171231'
    print(fs.get_interval_return(beg_date, end_date))
    print(fs.get_interval_return_annual(beg_date, end_date))
    print(fs.get_interval_excess_return_annual(beg_date, end_date))
    print(fs.get_interval_ir(beg_date, end_date))
    print(fs.get_interval_std_annual(beg_date, end_date))
    print(fs.get_interval_tracking_error(beg_date, end_date))
    print(fs.get_interval_max_drawdown(beg_date, end_date))
    print(fs.get_interval_excess_return_max_drawdown(beg_date, end_date))
    print(fs.get_fund_cum_return_series(beg_date, end_date))
    print(fs.get_fund_and_bencnmark_cum_return_series(beg_date, end_date))
    print(fs.get_cum_excess_return_series(beg_date, end_date))
