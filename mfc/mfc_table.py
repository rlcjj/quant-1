import numpy as np
import pandas as pd
from quant.stock.date import Date
from quant.stock.index import Index
from quant.mfc.mfc_data import MfcData
from quant.utility.financial_series import FinancialSeries


class MfcTable(object):

    """ 计算基金在一定区间内各种指标（收益率、跟踪误差等等）"""

    def __init__(self):

        pass

    @staticmethod
    def cal_summary_table(fund_name, fund_code, fund_type, date_array, benchmark_array):

        """
        主动股票型基金表现总结
        分区间计算 基金表现（累计收益 年化收益 年化波动 最大回撤 收益波动比）
        分区间计算 分基准 计算基准表现（累计收益 年化收益 年化波动 最大回撤 收益波动比）
        """

        # 分类读取基金数据
        fund_data = MfcData().get_mfc_nav(fund_code, fund_name, fund_type)
        performance_table = pd.DataFrame([], columns=date_array[:, 0])
        fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame([], columns=['nav']))

        for i_date in range(date_array.shape[0]):

            label = date_array[i_date, 0]
            bd = Date().change_to_str(date_array[i_date, 1])
            ed = Date().change_to_str(date_array[i_date, 2])
            performance_table.ix[fund_name + "累计收益", label] = fs.get_interval_return(bd, ed)
            performance_table.ix[fund_name + "年化收益", label] = fs.get_interval_return_annual(bd, ed)
            performance_table.ix[fund_name + "年化波动", label] = fs.get_interval_std_annual(bd, ed)
            performance_table.ix[fund_name + "最大回撤", label] = fs.get_interval_max_drawdown(bd, ed)
            performance_table.ix[fund_name + "收益波动比", label] = fs.get_interval_return_std_ratio(bd, ed)

        for i_benchmark in range(benchmark_array.shape[0]):

            benchmark_name = benchmark_array[i_benchmark, 0]
            benchmark_code = benchmark_array[i_benchmark, 1]
            benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
            fs = FinancialSeries(pd.DataFrame(benchmark_data), pd.DataFrame([], columns=['nav']))

            for i_date in range(date_array.shape[0]):
                label = date_array[i_date, 0]
                bd = Date().change_to_str(date_array[i_date, 1])
                ed = Date().change_to_str(date_array[i_date, 2])

                performance_table.loc[benchmark_name + "累计收益", label] = fs.get_interval_return(bd, ed)
                performance_table.loc[benchmark_name + "年化收益", label] = fs.get_interval_return_annual(bd, ed)
                performance_table.loc[benchmark_name + "年化波动", label] = fs.get_interval_std_annual(bd, ed)
                performance_table.loc[benchmark_name + "最大回撤", label] = fs.get_interval_max_drawdown(bd, ed)

        return performance_table

    @staticmethod
    def cal_summary_table_sample(fund_name, fund_code, fund_type, date_array, benchmark_array):

        """
        主动股票型基金表现总结（简单版）
        分区间计算 基金表现 累计收益
        分区间计算 分基准 计算基准累计收益
        """

        fund_data = MfcData().get_mfc_nav(fund_code, fund_name, fund_type)
        performance_table = pd.DataFrame([], columns=date_array[:, 0])
        fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame([], columns=['nav']))

        for i_date in range(date_array.shape[0]):
            label = date_array[i_date, 0]
            bd = Date().change_to_str(date_array[i_date, 1])
            ed = Date().change_to_str(date_array[i_date, 2])
            print("Cal Interval Return ", bd, ed)
            performance_table.ix[fund_name + "累计收益", label] = fs.get_interval_return(bd, ed)

        for i_benchmark in range(benchmark_array.shape[0]):

            benchmark_name = benchmark_array[i_benchmark, 0]
            benchmark_code = benchmark_array[i_benchmark, 1]
            benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
            fs = FinancialSeries(pd.DataFrame(benchmark_data), pd.DataFrame([], columns=['nav']))

            for i_date in range(date_array.shape[0]):
                label = date_array[i_date, 0]
                bd = Date().change_to_str(date_array[i_date, 1])
                ed = Date().change_to_str(date_array[i_date, 2])
                performance_table.ix[benchmark_name + "累计收益", label] = fs.get_interval_return(bd, ed)

        return performance_table

    @staticmethod
    def cal_summary_table_enhanced_fund(fund_name, fund_code, fund_type, date_array,
                                        benchmark_code, benchmark_name, benchmark_ratio=1.0):

        """
        指数型基金表现总结
        分区间计算 基金和基准表现（累计收益 年化收益 超额收益 跟踪误差 信息比率 超额收益最大回撤等）
        """

        # 分类读取基金数据
        fund_data = MfcData().get_mfc_nav(fund_code, fund_name, fund_type)
        benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])

        enhanced_table = pd.DataFrame([], columns=date_array[:, 0])
        fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data), benchmark_ratio)

        for i_date in range(date_array.shape[0]):
            label = date_array[i_date, 0]
            bd = Date().change_to_str(date_array[i_date, 1])
            ed = Date().change_to_str(date_array[i_date, 2])

            enhanced_table.loc[fund_name + "累计收益", label] = fs.get_interval_return(bd, ed)
            enhanced_table.loc[benchmark_name + "累计收益", label] = fs.get_interval_return_benchmark(bd, ed)
            bench_return = fs.get_interval_return_benchmark_ratio(bd, ed)
            enhanced_table.loc[benchmark_name + "*%s累计收益" % benchmark_ratio, label] = bench_return
            enhanced_table.loc[fund_name + "超额收益", label] = fs.get_interval_excess_return(bd, ed)
            enhanced_table.loc[fund_name + "超额年化收益", label] = fs.get_interval_excess_return_annual(bd, ed)
            enhanced_table.loc[fund_name + "跟踪误差", label] = fs.get_interval_tracking_error(bd, ed)
            enhanced_table.loc[fund_name + "信息比率", label] = fs.get_interval_mean_ir(bd, ed)
            enhanced_table.loc[fund_name + "超额收益最大回撤", label] = fs.get_interval_excess_return_max_drawdown(bd, ed)
            enhanced_table.loc[fund_name + "标准差", label] = fs.get_interval_std_annual(bd, ed)
            enhanced_table.loc[fund_name + "夏普比率", label] = fs.get_interval_shape_ratio(bd, ed, 0.03)
            enhanced_table.loc[fund_name + "最大回撤", label] = fs.get_interval_max_drawdown(bd, ed)
            enhanced_table.loc[fund_name + "年化收益", label] = fs.get_interval_return_annual(bd, ed)
            enhanced_table.loc[benchmark_name + "年化收益", label] = fs.get_interval_return_annual_benchmark(bd, ed)

        return enhanced_table

    def example(self):

        """ 例子 """

        fund_code = "162216.OF"
        fund_name = "泰达宏利中证500"
        fund_type = "公募"
        benchmark_code = "000905.SH"
        benchmark_name = "中证500"
        benchmark_ratio = 0.95

        setup_date = '20160714'
        end_date = '20170930'
        date_array = np.array([["2017年以来", '20170101', end_date],
                               ["成立以来", setup_date, end_date]])

        benchmark_array = np.array([["沪深300", "000300.SH"],
                                    ["中证500", "000905.SH"],
                                    ["股票型基金", '885012.WI']])

        performance_table = self.cal_summary_table(fund_name, fund_code, fund_type, date_array, benchmark_array)
        print(performance_table)
        performance_table = self.cal_summary_table_sample(fund_name, fund_code, fund_type, date_array, benchmark_array)
        print(performance_table)
        performance_table = self.cal_summary_table_enhanced_fund(fund_name, fund_code, fund_type,
                                                                 date_array, benchmark_code,
                                                                 benchmark_name, benchmark_ratio)
        print(performance_table)

if __name__ == '__main__':

    self = MfcTable()
    self.example()
