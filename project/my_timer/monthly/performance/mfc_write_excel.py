import os
import numpy as np
import pandas as pd

from quant.data.data import Data
from quant.stock.index import Index
from quant.mfc.mfc_data import MfcData
from quant.fund.fund_rank import FundRank
from quant.mfc.mfc_table import MfcTable
from quant.utility.write_excel import WriteExcel
from quant.utility.financial_series import FinancialSeries


class MfcWriteExcel(Data):

    """ 公司基金业绩汇总Excel """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\performance'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def write_fund(self, end_date, fund_name, fund_code, fund_type,
                 benchmark_code, benchmark_name, benchmark_ratio,
                 setup_date, date_array, benchmark_array):

        fund_name = '泰达宏利中证财富大盘'
        fund_code = '162213.OF'
        fund_type = "公募"

        benchmark_code = '000940.SH'
        benchmark_name = '中证财富大盘指数'
        benchmark_ratio = 0.95

        setup_date = '20141003'
        date_array = np.array([
            ["转型(20180317)以来", '20180317', end_date, '20170930'],
            ["2019年", "20190101", end_date, "20181231"],
            ["2018年", "20180101", '20181231', "20170930"],
            ["2017年", "20170101", '20171231', "20160930"],
            ["2016年", "20160101", "20161231", "20150930"],
            ["2015年", "20150101", "20151231", "20150101"],
            ["2015年至转型", "20150101", "20180317", "20150101"],
            ["管理(20141003)以来", setup_date, end_date, setup_date]])

        benchmark_array = np.array([["沪深300", "000300.SH"],
                                    ["中证500", "000905.SH"],
                                    ["中证财富大盘指数", "000940.SH"],
                                    ["WIND全A", '881001.WI']])

        # 准备文件
        file_name = os.path.join(self.data_path, "OutFile", fund_name + '.xlsx')
        excel = WriteExcel(file_name)
        worksheet = excel.add_worksheet(fund_name)

        # 简单收益总结
        performance_table = MfcTable().cal_summary_table_sample(fund_name, fund_code,
                                                                fund_type, date_array, benchmark_array)
        rank0 = FundRank().rank_fund_array2(fund_code, date_array, "wind", excess=False)
        rank1 = FundRank().rank_fund_array2(fund_code, date_array, "被动指数型基金", excess=True)
        rank2 = FundRank().rank_fund_array2(fund_code, date_array, "指数型基金", excess=True)
        rank3 = FundRank().rank_fund_array2(fund_code, date_array, "指数增强型基金", excess=True)
        performance_table = pd.concat([performance_table, rank0, rank1, rank2, rank3], axis=0)

        col_number = 1
        num_format_pd = pd.DataFrame([], columns=performance_table.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(performance_table, worksheet, begin_row_number=0, begin_col_number=col_number,
                           num_format_pd=num_format_pd, color="red", fillna=True)
        col_number = col_number + performance_table.shape[1] + 2



