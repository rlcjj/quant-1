from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel

from datetime import datetime
import pandas as pd
import numpy as np
import os


class MajorHolderDeal(Data):

    """ 晨会内容 重要股东二级市场交易情况汇总 """

    def __init__(self):

        """ 数据存储位置 """
        Data.__init__(self)
        self.sub_data_path = r'stock_data\morning_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self):

        """ 更新所需要的数据 """

        Date().load_trade_date_series("D")
        end_date = datetime.today().strftime("%Y%m%d")
        beg_date = Date().get_trade_date_offset(end_date, -12)
        Stock().load_major_holder_deal(beg_date, end_date)

    def major_holder_deal_period_sum(self, beg_date, end_date):

        """ 一段时间内 股票增减持市场总和 """

        data = Stock().get_major_holder_deal()
        data_period = data[data['announcement_date'] <= end_date]
        data_period = data_period[data_period['announcement_date'] > beg_date]
        data_period = data_period[['wind_code', 'name', 'direction', 'value_change']]
        data_period['value_change'] /= 10000.0
        data_period['sign'] = data_period['direction'].map(lambda x: -1 if x == "减持" else 1)
        data_period['values_change_sign'] = data_period['sign'] * data_period['value_change']
        data_period = data_period.reset_index()

        value_change_sum = data_period['values_change_sign'].sum()
        number = len(data_period)

        result = pd.DataFrame([beg_date, end_date, value_change_sum, number],
                              columns=[end_date],
                              index=['开始时间', '结束时间', '增减持金额(亿)', '涉及股东个数']).T
        return result

    def major_holder_deal_period_industry(self, beg_date, end_date):

        """ 一段时间内 股票增减持股票行业分布 """

        data = Stock().get_major_holder_deal()
        data_period = data[data['announcement_date'] <= end_date]
        data_period = data_period[data_period['announcement_date'] > beg_date]
        data_period = data_period[['wind_code', 'name', 'direction', 'value_change']]
        data_period['value_change'] /= 10000.0
        data_period['sign'] = data_period['direction'].map(lambda x: -1 if x == "减持" else 1)
        data_period['values_change_sign'] = data_period['sign'] * data_period['value_change']
        data_period = data_period.reset_index()

        industry = Stock().read_factor_h5("industry_citic1")
        industry_date = pd.DataFrame(industry[industry.columns[-1]])
        industry_date.columns = ['Industry']

        data_gb_stock = data_period.groupby(by=['wind_code']).sum()
        data_gb_stock = data_gb_stock.dropna()
        data_gb_stock = data_gb_stock.sort_values(by=['values_change_sign'], ascending=False)

        data_concat = pd.concat([data_gb_stock, industry_date], axis=1)
        data_concat = data_concat.dropna(subset=['Industry', 'values_change_sign'])
        data_gb_industry = pd.DataFrame(data_concat.groupby(by=['Industry']).sum()['values_change_sign'])
        data_gb_industry.index = data_gb_industry.index.map(Stock().get_industry_citic1_name_ch)
        data_gb_industry = data_gb_industry.sort_values(by=['values_change_sign'], ascending=False)
        data_gb_industry['values_change_sign'] = data_gb_industry['values_change_sign'].map(lambda x: np.round(x, 2))

        data_gb_industry.columns = ['增减持金额(亿)']

        return data_gb_industry

    def major_holder_deal_period_stock(self, beg_date, end_date):

        """ 一段时间内 股票增减持最大、最小股票 """

        data = Stock().get_major_holder_deal()
        data_period = data[data['announcement_date'] <= end_date]
        data_period = data_period[data_period['announcement_date'] > beg_date]
        data_period = data_period[['wind_code', 'name', 'direction', 'value_change']]
        data_period['value_change'] /= 10000.0
        data_period['sign'] = data_period['direction'].map(lambda x: -1 if x == "减持" else 1)
        data_period['values_change_sign'] = data_period['sign'] * data_period['value_change']
        data_period = data_period.reset_index()
        data_gb_stock = data_period.groupby(by=['name']).sum()
        data_gb_stock = data_gb_stock.dropna()

        # 最大的5股
        data_gb_stock = data_gb_stock.sort_values(by=['values_change_sign'], ascending=False)
        positive = data_gb_stock.iloc[0:min(5, len(data_gb_stock)), :]
        positive = pd.DataFrame(positive['values_change_sign'])
        positive['values_change_sign'] = positive['values_change_sign'].map(lambda x: np.round(x, 2))
        positive.columns = ['增减持金额(亿)']

        # 最小的5股
        data_gb_stock = data_gb_stock.sort_values(by=['values_change_sign'], ascending=False)
        negative = data_gb_stock.iloc[-5:, :]
        negative = pd.DataFrame(negative['values_change_sign'])
        negative['values_change_sign'] = negative['values_change_sign'].map(lambda x: np.round(x, 2))
        negative.columns = ['增减持金额(亿)']

        result = pd.concat([positive, negative], axis=0)
        return result

    def generate_excel(self, end_date):

        """ 大股东增减持信息 输出到EXcel"""

        beg_date = Date().get_trade_date_offset(end_date, -60)
        beg_1m_date = Date().get_trade_date_offset(end_date, -20)

        # 一段时间内增减持额时间序列
        from quant.stock.index import Index
        index_data = Index().get_index_factor(index_code="000300.SH")

        date_series = Date().get_trade_date_series(beg_date, end_date, "W")
        result = pd.DataFrame([])

        ed_date = end_date

        for i in range(len(date_series)-1):
            bg_date = Date().get_trade_date_offset(ed_date, -5)
            print("Major Holder Deal %s %s" % (bg_date, ed_date))
            result_add = self.major_holder_deal_period_sum(bg_date, ed_date)
            result_add.loc[ed_date, '沪深300'] = index_data.loc[ed_date, "CLOSE"]
            result = pd.concat([result, result_add], axis=0)
            ed_date = bg_date

        result = result.sort_index()
        # 最近一个月增减持额最大的几个股票
        stock = self.major_holder_deal_period_stock(beg_1m_date, end_date)

        # 最近一个月增减持额行业排序
        industry = self.major_holder_deal_period_industry(beg_1m_date, end_date)

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, '重要股东二级市场交易.xlsx')
        excel = WriteExcel(filename)
        sheet_name = "读写EXCEL测试"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)
        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["增减持金额(亿)", "沪深300"],
                                 chart_name="最近3个月每周大股东增减持总和",
                                 insert_pos="O2", cat_beg="D2", cat_end="D14",
                                 val_beg_list=["E2", "G2"], val_end_list=["E14", "G14"])

        num_format_pd = pd.DataFrame([], columns=stock.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        excel.write_pandas(stock, worksheet, begin_row_number=0, begin_col_number=8,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        num_format_pd = pd.DataFrame([], columns=industry.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        excel.write_pandas(industry, worksheet, begin_row_number=0, begin_col_number=11,
                           num_format_pd=num_format_pd, color="orange", fillna=True)
        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["行业分布"],
                                 chart_name="行业最近1月增减持金额",
                                 insert_pos="O16", cat_beg="L2", cat_end="L30",
                                 val_beg_list=["M2"], val_end_list=["M30"])
        excel.close()

    def generate_excel_history(self, end_date):

        """ 大股东增减持历史信息 2017年至今 """

        # 一段时间内增减持额时间序列
        from quant.stock.index import Index
        index_data = Index().get_index_factor(index_code="000300.SH")

        date_series = Date().get_trade_date_series("20150101", end_date, "M")
        result = pd.DataFrame([])

        ed_date = end_date

        for i in range(len(date_series)-1):
            bg_date = Date().get_trade_date_offset(ed_date, -20)
            print("Major Holder Deal %s %s" % (bg_date, ed_date))
            result_add = self.major_holder_deal_period_sum(bg_date, ed_date)
            result_add.loc[ed_date, '沪深300'] = index_data.loc[ed_date, "CLOSE"]
            result = pd.concat([result, result_add], axis=0)
            ed_date = bg_date

        result = result.sort_index()

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        filename = os.path.join(sub_path, '重要股东二级市场交易历史.xlsx')
        excel = WriteExcel(filename)
        sheet_name = "读写EXCEL测试"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)
        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["增减持金额(亿)", "沪深300"],
                                 chart_name="历史每月大股东增减持总和",
                                 insert_pos="O2", cat_beg="D2", cat_end="D40",
                                 val_beg_list=["E2", "G2"], val_end_list=["E40", "G40"])
        excel.close()


if __name__ == '__main__':

    end_date = "20190404"
    self = MajorHolderDeal()
    self.update_data()
    self.generate_excel(end_date)
    # self.generate_excel_history(end_date)
