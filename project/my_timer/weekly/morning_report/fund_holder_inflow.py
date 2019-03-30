from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.fund.fund_holder import FundHolder
from quant.utility.write_excel import WriteExcel

import numpy as np
import pandas as pd
import os


class FundHolderInflow(Data):

    """ 晨会内容 基金持股金额数据 """

    def __init__(self):

        """ 数据存储位置 """
        Data.__init__(self)
        self.sub_data_path = r'stock_data\morning_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self):

        """ 更新所需要的数据 """
        Date().load_trade_date_series("D")
        Stock().load_h5_primary_factor()
        FundHolder().load_fund_holding_stock()

    def get_fund_holder_data(self, quarter_date, quarter_last_date):

        """ 得到数据 """

        # date
        quarter_trade_date = Date().get_trade_date_offset(quarter_date, 0)
        quarter_last_trade_date = Date().get_trade_date_offset(quarter_last_date, 0)
        print(quarter_date, quarter_last_date)
        print(quarter_trade_date, quarter_last_trade_date)

        # share
        data = FundHolder().get_fund_holding_stock_all()
        data_quarter = data[data.ReportDate == quarter_date]
        data_quarter = data_quarter[data_quarter.PublishDate <= Date().get_trade_date_offset(quarter_date, 20)]
        quarter_share = pd.DataFrame(data_quarter.groupby(by=['StockCode']).sum()['Share'])

        data_quarter = data[data.ReportDate == quarter_last_date]
        data_quarter = data_quarter[data_quarter.PublishDate <= Date().get_trade_date_offset(quarter_last_date, 20)]
        quarter_last_share = pd.DataFrame(data_quarter.groupby(by=['StockCode']).sum()['Share'])

        # price
        adjust_factor = Stock().read_factor_h5("AdjustFactor")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        quarter_adjust = adjust_factor[quarter_trade_date] / adjust_factor[quarter_last_trade_date]
        quarter_price = price_unadjust[quarter_trade_date]
        quarter_price_last = price_unadjust[quarter_last_trade_date]
        average_price = (price_unadjust[quarter_trade_date] +
                         price_unadjust[quarter_last_trade_date] / quarter_adjust) / 2.0

        # industry
        industry = Stock().read_factor_h5("industry_citic1")
        industry_date = pd.DataFrame(industry[industry.columns[-1]])
        industry_date.columns = ['Industry']

        # concat
        result = pd.concat([quarter_share, quarter_last_share, quarter_price, quarter_price_last,
                            average_price, quarter_adjust, industry_date], axis=1)
        result.columns = ['ShareQuarter', 'ShareQuarterLast', 'PriceQuarter', 'PriceQuarterLast',
                          'PriceMean', 'Adjust', 'Industry']

        result = result.dropna(subset=['Adjust', 'Industry'])
        result = result.fillna(0.0)

        # cal
        result['ShareQuarterLastAdjust'] = result['ShareQuarterLast'] * result['Adjust']
        result['MvQuarter'] = result['ShareQuarter'] * result['PriceQuarter']
        result['MvQuarterLast'] = result['ShareQuarterLast'] * result['PriceQuarterLast']
        result['Inflow'] = (result['ShareQuarter'] - result['ShareQuarterLastAdjust']) * result['PriceMean']

        result['MvQuarter'] /= 100000000.0
        result['Inflow'] /= 100000000.0
        result['MvQuarterLast'] /= 100000000.0

        return result

    def fund_holder_quarter_sum(self, quarter_date, quarter_last_date):

        """ 基金重仓持股金额 季报 """

        result = self.get_fund_holder_data(quarter_date, quarter_last_date)
        result = result[['MvQuarterLast', 'MvQuarter', 'Inflow']]

        data = pd.DataFrame(result.sum()).T
        data.index = [quarter_date]
        data.columns = ['上期持股总市值', '本期持股总市值', "净流入金额"]
        data['净流入占比'] = data['净流入金额'] / data['本期持股总市值']

        return data

    def fund_holder_quarter_industry(self, quarter_date, quarter_last_date):

        """ 基金季度重仓持股 最近一个季度行业净流入金额 """

        # quarter_date = "20180930"
        # quarter_last_date = "20180630"
        result = self.get_fund_holder_data(quarter_date, quarter_last_date)

        # groupby industry
        data_gb_industry = pd.DataFrame(result.groupby(by=['Industry']).sum()[['MvQuarter', 'MvQuarterLast', 'Inflow']])
        data_gb_industry.index = data_gb_industry.index.map(Stock().get_industry_citic1_name_ch)

        data_gb_industry['MvQuarterLast'] = data_gb_industry['MvQuarterLast'].map(lambda x: np.round(x, 2))
        data_gb_industry['MvQuarter'] = data_gb_industry['MvQuarter'].map(lambda x: np.round(x, 2))
        data_gb_industry['Inflow'] = data_gb_industry['Inflow'].map(lambda x: np.round(x, 2))
        data_gb_industry.columns = [['%s持股总市值' % quarter_date, '%s持股总市值' % quarter_last_date, '净流入金额']]
        data_gb_industry['净流入占比'] = data_gb_industry['净流入金额'] / data_gb_industry['%s持股总市值' % quarter_date]
        data_gb_industry = data_gb_industry.sort_values(by=['净流入金额'], ascending=False)

        return data_gb_industry

    def hk_inflow_period_stock(self, quarter_date, quarter_last_date):

        """ 基金季度重仓持股 最近一个季度股票净流入金额 """

        # quarter_date = "20180930"
        # quarter_last_date = "20180630"
        result = self.get_fund_holder_data(quarter_date, quarter_last_date)

        result = result.sort_values(by=['Inflow'], ascending=False)
        result['InflowRatio'] = result['Inflow'] / result['MvQuarter']
        result = result[['MvQuarterLast', 'MvQuarter', 'Inflow', 'InflowRatio']]
        result = result.dropna()

        positive = result.iloc[0:10, :]
        negative = result.iloc[-10:, :]
        data = pd.concat([positive, negative], axis=0)

        data['MvQuarterLast'] = data['MvQuarterLast'].map(lambda x: np.round(x, 2))
        data['MvQuarter'] = data['MvQuarter'].map(lambda x: np.round(x, 2))
        data['Inflow'] = data['Inflow'].map(lambda x: np.round(x, 2))
        data.index = data.index.map(lambda x: Stock().get_stock_name_date(stock_code=x, date=quarter_date))

        data.columns = ['%s持股总市值' % quarter_last_date, '%s持股总市值' % quarter_date, "净流入金额", '净流入占比']

        return data

    def generate_excel(self, end_date, quarter_date, quarter_last_date):

        """ 陆股通信息 输出到Excel """

        beg_date = Date().get_trade_date_offset(end_date, -400)
        quarter_date_series = Date().get_normal_date_series(beg_date, end_date, "Q")

        # 最近4个季度重仓持股金额
        from quant.stock.index import Index
        index_data = Index().get_index_factor(index_code="000300.SH")
        result = pd.DataFrame()
        for i in range(len(quarter_date_series)-1):
            quarter_last_date_temp = quarter_date_series[i]
            quarter_date_temp = quarter_date_series[i + 1]
            add = self.fund_holder_quarter_sum(quarter_date_temp, quarter_last_date_temp)
            quarter_trade_date = Date().get_trade_date_offset(quarter_date_temp, 0)
            add.loc[quarter_date_temp, '沪深300'] = index_data.loc[quarter_trade_date, "CLOSE"]
            result = pd.concat([result, add], axis=0)

        # 最近一个月平均持股金额最大、最小的几个股票
        stock = self.hk_inflow_period_stock(quarter_date, quarter_last_date)

        # 最近一个月平均持股金额行业排序
        industry = self.fund_holder_quarter_industry(quarter_date, quarter_last_date)

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, '基金重仓季报持股.xlsx')
        excel = WriteExcel(filename)
        sheet_name = "基金重仓季报持股"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        num_format_pd.ix['format', "净流入占比"] = '0.00%'
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["季度流入金额", '沪深300'],
                                 chart_name="基金季报重仓持股净流入金额(亿元)",
                                 insert_pos="B10", cat_beg="B2", cat_end="B6",
                                 val_beg_list=["E2", "G2"], val_end_list=["E6", "G6"])

        num_format_pd = pd.DataFrame([], columns=stock.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        num_format_pd.ix['format', "净流入占比"] = '0.00%'
        excel.write_pandas(stock, worksheet, begin_row_number=0, begin_col_number=8,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        num_format_pd = pd.DataFrame([], columns=industry.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        num_format_pd.ix['format', "净流入占比"] = '0.00%'
        excel.write_pandas(industry, worksheet, begin_row_number=0, begin_col_number=15,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["季度流入金额", "季度流入占比"],
                                 chart_name="基金季报重仓行业净流入金额(亿元)",
                                 insert_pos="B26", cat_beg="P2", cat_end="P30",
                                 val_beg_list=["S2", "T2"], val_end_list=["S30", "T30"])

        excel.close()


if __name__ == '__main__':

    end_date = "20190214"
    quarter_date = "20181231"
    quarter_last_date = "20180930"

    self = FundHolderInflow()
    self.generate_excel(end_date, quarter_date, quarter_last_date)

