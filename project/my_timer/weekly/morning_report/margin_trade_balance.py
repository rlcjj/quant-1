from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel

import numpy as np
import pandas as pd
import os


class MarginTradeBalance(Data):

    """ 晨会内容 融资融券余额"""

    def __init__(self):

        """ 数据存储位置 """
        Data.__init__(self)
        self.sub_data_path = r'stock_data\morning_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self):

        """ 更新所需要的数据 """
        Date().load_trade_date_series("D")
        Stock().load_h5_primary_factor()

    def get_balance_data(self, beg_date, end_date):

        """ 一段时间内的数据 """

        beg_date = Date().get_trade_date_offset(beg_date, 0)
        end_date = Date().get_trade_date_offset(end_date, 0)
        print(beg_date, end_date)
        data = Stock().read_factor_h5("Margin_TradeBalance")
        data = data.fillna(0.0)
        data /= 100000000.0

        concat_data = pd.concat([data[beg_date], data[end_date]], axis=1)
        concat_data.columns = ['BegMv', 'EndMv']

        concat_data['DiffMv'] = concat_data['EndMv'] - concat_data['BegMv']
        concat_data = concat_data.dropna()

        return concat_data

    def hk_inflow_period(self, beg_date, end_date):

        """
        陆股通 整个市场
        1、期末的总市值
        2、净流入（期末数量-期初数量）*期初期末价格平均数
        """
        concat_data = self.get_balance_data(beg_date, end_date)
        begMv_sum = concat_data['BegMv'].sum()
        EndMv_sum = concat_data['EndMv'].sum()
        diff_sum = concat_data['DiffMv'].sum()
        ratio = diff_sum / EndMv_sum

        result = pd.DataFrame([beg_date, begMv_sum, EndMv_sum, diff_sum, ratio],
                              columns=[end_date],
                              index=['开始时间', '期初融资余额(亿元)', '期末融资余额(亿元)',
                                     '期间净流入(亿元)', '净流入占比']).T

        return result

    def hk_inflow_period_industry(self, beg_date, end_date):

        """
        陆股通 分行业
        1、期末的总市值
        2、净流入（期末数量-期初数量）*期初期末价格平均数
        """

        concat_data = self.get_balance_data(beg_date, end_date)

        industry = Stock().read_factor_h5("industry_citic1")
        industry_date = pd.DataFrame(industry[industry.columns[-1]])
        industry_date.columns = ['Industry']

        concat_data = pd.concat([concat_data, industry_date], axis=1)
        concat_data = concat_data.dropna()

        data_gb = concat_data.groupby(by=['Industry']).mean()
        data_gb = data_gb[['BegMv', 'EndMv', 'DiffMv']]
        data_gb = data_gb.dropna()
        data_gb *= 100

        data_gb.index = data_gb.index.map(Stock().get_industry_citic1_name_ch)
        industry_info = Stock().get_industry_citic1()
        industry_info.index = industry_info.Ch
        data_gb = pd.concat([data_gb, industry_info['WindCode']], axis=1)

        data_gb['BegMv'] = data_gb['BegMv'].map(lambda x: np.round(x, 2))
        data_gb['EndMv'] = data_gb['EndMv'].map(lambda x: np.round(x, 2))
        data_gb['DiffMv'] = data_gb['DiffMv'].map(lambda x: np.round(x, 2))
        data_gb['InflowRatio'] = data_gb['DiffMv'] / data_gb['EndMv']
        data_gb = data_gb.sort_values(by=['DiffMv'], ascending=False)
        data_gb.columns = ['期初融资余额(百万元)', '期末融资余额(百万元)',
                           '期间净流入(百万元)', 'wind代码', '净流入占比']

        return data_gb

    def hk_inflow_period_stock(self, beg_date, end_date):

        """ 陆股通 一段时间内平均持股总市值最大、最小的5只股票 """

        concat_data = self.get_balance_data(beg_date, end_date)

        concat_data = concat_data[['BegMv', 'EndMv', 'DiffMv']]
        concat_data = concat_data[concat_data['EndMv'] != 0]
        concat_data = concat_data[concat_data['DiffMv'] != 0.0]
        concat_data = concat_data.dropna()

        concat_data['BegMv'] = concat_data['BegMv'].map(lambda x: np.round(x, 2))
        concat_data['EndMv'] = concat_data['EndMv'].map(lambda x: np.round(x, 2))
        concat_data['Ratio'] = concat_data['DiffMv'] / concat_data['EndMv']
        concat_data = concat_data.dropna()
        concat_data.index = concat_data.index.map(lambda x: Stock().get_stock_name_date(stock_code=x, date=end_date))

        concat_data = concat_data.sort_values(by=['DiffMv'], ascending=False)
        positive = concat_data.iloc[0:10, :]

        concat_data = concat_data.sort_values(by=['DiffMv'], ascending=True)
        negative = concat_data.iloc[0:10, :]

        data = pd.concat([positive, negative], axis=0)
        data.columns = ['期初融资余额(亿元)', '期末融资余额(亿元)', '期间净流入(亿元)', '净流入占比']

        return data

    def generate_excel(self, end_date):

        """ 陆股通信息 输出到Excel """

        beg_date = Date().get_trade_date_offset(end_date, -60)
        beg_1m_date = Date().get_trade_date_offset(end_date, -20)
        beg_1m_date = "20190201"

        # 一段时间内增减持额时间序列
        from quant.stock.index import Index
        index_data = Index().get_index_factor(index_code="000300.SH")
        date_series = Date().get_trade_date_series(beg_date, end_date, "W")
        result = pd.DataFrame([])

        ed_date = end_date
        for i in range(len(date_series)-1):
            bg_date = Date().get_trade_date_offset(ed_date, -5)
            print("Hk Inflow Period %s %s" % (bg_date, ed_date))
            result_add = self.hk_inflow_period(bg_date, ed_date)
            result_add.loc[ed_date, '沪深300'] = index_data.loc[ed_date, "CLOSE"]
            result = pd.concat([result, result_add], axis=0)
            ed_date = bg_date

        result = result.sort_index()
        # 最近一个月平均持股金额最大、最小的几个股票
        stock = self.hk_inflow_period_stock(beg_1m_date, end_date)

        # 最近一个月平均持股金额行业排序
        industry = self.hk_inflow_period_industry(beg_1m_date, end_date)

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, '融资融券情况春节后.xlsx')
        print(filename)
        excel = WriteExcel(filename)
        sheet_name = "融资融券情况"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', "净流入占比"] = '0.00%'
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["净流入金额", '沪深300'],
                                 chart_name="最近3个月每周融资余额净买入金额(亿元)",
                                 insert_pos="I15", cat_beg="B2", cat_end="B13",
                                 val_beg_list=["F2", "H2"], val_end_list=["F13", "H13"])

        num_format_pd = pd.DataFrame([], columns=stock.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', "净流入占比"] = '0.00%'
        excel.write_pandas(stock, worksheet, begin_row_number=0, begin_col_number=8,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        num_format_pd = pd.DataFrame([], columns=industry.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', "净流入占比"] = '0.00%'
        excel.write_pandas(industry, worksheet, begin_row_number=0, begin_col_number=15,
                           num_format_pd=num_format_pd, color="orange", fillna=True)
        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["净流入占比", '净流入金额'],
                                 chart_name="行业最近1月融资净买入金额",
                                 insert_pos="I32", cat_beg="P2", cat_end="P30",
                                 val_beg_list=["U2", "S2"], val_end_list=["U30", "S30"])

        excel.close()

    def generate_excel_history(self, end_date):

        """ 陆股通信息 输出到Excel """

        # 一段时间内增减持额时间序列
        from quant.stock.index import Index
        index_data = Index().get_index_factor(index_code="000300.SH")
        date_series = Date().get_trade_date_series("20170301", end_date, "M")
        result = pd.DataFrame([])

        ed_date = end_date
        for i in range(len(date_series)-1):
            bg_date = Date().get_trade_date_offset(ed_date, -20)
            print("Hk Inflow Period %s %s" % (bg_date, ed_date))
            result_add = self.hk_inflow_period(bg_date, ed_date)
            result_add.loc[ed_date, '沪深300'] = index_data.loc[ed_date, "CLOSE"]
            result = pd.concat([result, result_add], axis=0)
            ed_date = bg_date

        result = result.sort_index()
        result['累计净流入(亿元)'] = result['期间净流入(亿元)'].cumsum()
        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, '融资融券情况历史.xlsx')
        excel = WriteExcel(filename)
        sheet_name = "陆股通北上资金"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', "净流入占比"] = '0.00%'
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)
        excel.close()


if __name__ == '__main__':

    # end_date = datetime.today().strftime("%Y%m%d")
    end_date = "20190222"
    self = MarginTradeBalance()
    self.generate_excel(end_date)
    # self.generate_excel_history(end_date)

