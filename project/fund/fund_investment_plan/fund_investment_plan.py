import os
import numpy as np
import pandas as pd
from datetime import datetime
from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.fund.fund import Fund
from quant.utility.write_excel import WriteExcel


class FundInvestmentPlan(Data):

    """ 基金定投 """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_investment_plan'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def get_pct_data(self):

        """ 收益率数据 """

        index_return = Index().get_index_cross_factor("PCT").T * 100
        fund_return = Fund().get_fund_factor("Repair_Nav_Pct").T
        asset_return = pd.concat([fund_return, index_return], axis=0)
        asset_return = asset_return.T
        asset_return /= 100.0

        return asset_return

    def get_benchmark_pct(self, benchmark_array):

        """ 定投基准的投资收益率 """

        asset_pct = self.get_pct_data()
        result = pd.DataFrame()

        for i in range(len(benchmark_array)):
            code = benchmark_array[i][0]
            ratio = float(benchmark_array[i][1])
            result = pd.concat([result, pd.DataFrame(asset_pct[code]) * ratio], axis=1)

        result['投资指数日收益'] = result.sum(axis=1)
        result = result.dropna()
        return pd.DataFrame(result['投资指数日收益'])

    def plan(self, benchmark_array, invest_days, invest_money,
             beg_date, end_date, file_prefix):

        """ 定投计划回测 """

        data = self.get_benchmark_pct(benchmark_array)
        data = data.loc[beg_date:end_date, :]
        beg_date = data.index[0]
        end_date = data.index[-1]
        filename = "%s_%s_%s.xlsx" % (file_prefix, beg_date, end_date)

        data['星期数'] = data.index.map(lambda x: datetime.strptime(x, '%Y%m%d').strftime("%A"))
        data['当日投资金额'] = data['星期数'].map(lambda x: invest_money if x == invest_days else 0)
        data['累计投资金额'] = data['当日投资金额'].cumsum()
        data['当日投资收益'] = data['累计投资金额'] * data['投资指数日收益']
        data['累计投资收益'] = data['当日投资收益'].cumsum()
        data['累计投资收益率'] = data['累计投资收益'] / data['累计投资金额']

        file = os.path.join(self.data_path, filename)
        excel = WriteExcel(file)
        worksheet = excel.add_worksheet("定投")

        num_format_pd = pd.DataFrame([], columns=data.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', ['累计投资收益率', '投资指数日收益']] = '0.00%'
        excel.write_pandas(data, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="blue", fillna=True)

        data_select = pd.DataFrame(data['累计投资收益率'])
        num_format_pd = pd.DataFrame([], columns=data_select.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(data_select, worksheet, begin_row_number=0, begin_col_number=10,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        excel.line_chart_time_series_plot(worksheet, 0, 10, data_select,
                                          ["累计投资收益率"], file_prefix + '累计投资收益率', "K2", "定投")

        excel.close()

    def update_data(self):

        """ 下载数据"""
        Index().load_index_factor("H00922.CSI", beg_date="20190101", end_date=datetime.today())
        Index().load_index_factor("H00300.CSI", beg_date="20190101", end_date=datetime.today())
        Index().load_index_factor("H00905.CSI", beg_date="20190101", end_date=datetime.today())
        Index().load_index_factor("885008.WI", beg_date="20190101", end_date=datetime.today())
        Index().load_index_factor("885001.WI", beg_date="20190101", end_date=datetime.today())


if __name__ == '__main__':

    self = FundInvestmentPlan()
    # self.update_data()

    #######################################################
    benchmark_array = np.array([["000300.SH", 0.50],
                                ["000905.SH", 0.50]])
    invest_days = "Monday"
    invest_money = 500
    beg_date = "20100101"
    end_date = "20190227"
    file_prefix = "50沪深300_50中证500"

    self.plan(benchmark_array, invest_days, invest_money,
              beg_date, end_date, file_prefix)

    #######################################################
    benchmark_array = np.array([["H00922.CSI", 0.30],
                                ["885001.WI", 0.30],
                                ["000300.SH", 0.20],
                                ["000905.SH", 0.20]
                                ])
    invest_days = "Monday"
    invest_money = 500
    beg_date = "20050101"
    end_date = "20190227"
    file_prefix = "30中证红利_30偏股混合_20沪深300_20中证500"

    self.plan(benchmark_array, invest_days, invest_money,
              beg_date, end_date, file_prefix)

    #######################################################
    benchmark_array = np.array([["H00922.CSI", 0.20],
                                ["885001.WI", 0.20],
                                ["000300.SH", 0.15],
                                ["000905.SH", 0.15],
                                ["885008.WI", 0.30]
                                ])
    invest_days = "Monday"
    invest_money = 500
    beg_date = "20050101"
    end_date = "20190227"
    file_prefix = "20中证红利_20偏股混合_15沪深300_15中证500_30长期纯债"

    self.plan(benchmark_array, invest_days, invest_money,
              beg_date, end_date, file_prefix)

    #######################################################
    benchmark_array = np.array([["H00922.CSI", 0.08],
                                ["885001.WI", 0.08],
                                ["000300.SH", 0.07],
                                ["000905.SH", 0.07],
                                ["885008.WI", 0.70]
                                ])
    invest_days = "Monday"
    invest_money = 500
    beg_date = "20050101"
    end_date = "20190227"
    file_prefix = "8中证红利_8偏股混合_7沪深300_7中证500_70长期纯债"

    self.plan(benchmark_array, invest_days, invest_money,
              beg_date, end_date, file_prefix)

    #######################################################
