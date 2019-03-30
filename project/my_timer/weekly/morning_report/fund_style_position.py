from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.write_excel import WriteExcel
from quant.fund.fund_stock_style_ratio import FundStockStyleRatio

from datetime import datetime
import pandas as pd
import os


class FundStylePosition(Data):

    """ 晨会内容 基金指数的仓位和风格 """

    def __init__(self):

        """ 数据存储位置 """
        Data.__init__(self)
        self.sub_data_path = r'stock_data\morning_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_fund_style_position(self):

        """ 计算 更新最近4年 普通股票型基金 和偏股混合型基金指数 的风格仓位 """

        # Date().load_trade_date_series("D")
        end_date = datetime.today().strftime("%Y%m%d")
        beg_date = Date().get_trade_date_offset(end_date, -60)

        fssr = FundStockStyleRatio(stock_ratio_low=0.80, stock_ratio_up=0.95)
        fssr.cal_style_position(beg_date, end_date, "885000.WI")

        # 偏股混合型基金
        fssr = FundStockStyleRatio(stock_ratio_low=0.60, stock_ratio_up=0.95)
        fssr.cal_style_position(beg_date, end_date, "885001.WI")

    def get_fund_style_position(self, code, beg_date, end_date):

        """ 基金普通股票型基金 和偏股混合型基金指数的风格仓位 """

        end_date = Date().get_trade_date_offset(end_date, 0)
        beg_date = Date().get_trade_date_offset(beg_date, 0)
        fssr = FundStockStyleRatio()
        data = fssr.get_style_position(code)

        index_code_list = ["801853.SI", "000300.SH", "000905.SH",
                           "000852.SH", "399006.SZ", "885062.WI", 'StockRatio']
        index_name_list = ['绩优股指数', '沪深300', '中证500',
                           '中证1000', '创业板指', '短期纯债基金', '股票仓位']

        data = data[index_code_list]
        data.columns = index_name_list

        # 计算最近1月的风格、仓位时间序列

        index_name_list = ['绩优股指数', '沪深300', '中证500',
                           '中证1000', '中小板指', '创业板指', '短期纯债基金', '股票仓位']
        style_series = data.loc[beg_date:end_date, index_name_list]

        # 计算最近1月的风格、仓位变化总结
        summary = pd.concat([data.loc[end_date, :], data.loc[beg_date, :]], axis=1)
        print(summary.head())
        summary['变化'] = summary[end_date] - summary[beg_date]

        return style_series, summary

    def generate_excel(self, end_date):

        """ 陆股通信息 输出到Excel """

        # beg_date = Date().get_trade_date_offset(end_date, -60)
        # beg_1m_date = Date().get_trade_date_offset(end_date, -20)

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, '股票基金风格仓位.xlsx')
        excel = WriteExcel(filename)

        ###################################################################################
        sheet_name = "普通股票型风格仓位"
        worksheet = excel.add_worksheet(sheet_name)

        date_1m = Date().get_trade_date_offset(end_date, -21)
        style_series, position_series = self.get_fund_style_position("885000.WI", date_1m, end_date)

        num_format_pd = pd.DataFrame([], columns=style_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(style_series, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        num_format_pd = pd.DataFrame([], columns=position_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(position_series, worksheet, begin_row_number=0, begin_col_number=12,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        ###################################################################################
        sheet_name = "偏股混合型风格仓位"
        worksheet = excel.add_worksheet(sheet_name)
        style_series, position_series = self.get_fund_style_position("885001.WI", date_1m, end_date)

        num_format_pd = pd.DataFrame([], columns=style_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(style_series, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        num_format_pd = pd.DataFrame([], columns=position_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(position_series, worksheet, begin_row_number=0, begin_col_number=12,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        excel.close()

    def generate_excel_history(self, end_date):

        """ 陆股通信息 输出到Excel """

        # beg_date = Date().get_trade_date_offset(end_date, -60)
        # beg_1m_date = Date().get_trade_date_offset(end_date, -20)

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, '股票基金风格仓位历史.xlsx')
        excel = WriteExcel(filename)

        ###################################################################################
        sheet_name = "普通股票型风格仓位"
        worksheet = excel.add_worksheet(sheet_name)

        style_series, position_series = self.get_fund_style_position("885000.WI", "20050104", end_date)

        num_format_pd = pd.DataFrame([], columns=style_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(style_series, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        num_format_pd = pd.DataFrame([], columns=position_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(position_series, worksheet, begin_row_number=0, begin_col_number=12,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        ###################################################################################
        sheet_name = "偏股混合型风格仓位"
        worksheet = excel.add_worksheet(sheet_name)
        style_series, position_series = self.get_fund_style_position("885001.WI", "20150104", end_date)

        num_format_pd = pd.DataFrame([], columns=style_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(style_series, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        num_format_pd = pd.DataFrame([], columns=position_series.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(position_series, worksheet, begin_row_number=0, begin_col_number=12,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        excel.close()

if __name__ == '__main__':

    self = FundStylePosition()
    self.cal_fund_style_position()
    end_date = "20190321"
    self.generate_excel(end_date)
    # self.generate_excel_history(end_date)
