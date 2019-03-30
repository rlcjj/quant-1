from quant.data.data import Data
from quant.stock.date import Date
from quant.fund.fund_static import FundStatic
from quant.fund.fund_holder import FundHolder
from quant.fund.fund_pool import FundPool

import os
import pandas as pd
from datetime import datetime


class FundHolderSimulation(Data):

    """
    利用基金半年报、年报以及基金证监会行业权重来补全基金季报
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_holding_data\fund_holding_quarter_simulation'
        self.data_path_holder_simulate = os.path.join(self.primary_data_path, self.sub_data_path)
        self.industry_data = None
        self.stock_data = None

    def get_data(self):

        self.industry_data = FundHolder().get_fund_holding_industry_all()
        self.stock_data = FundHolder().get_fund_holding_all()

    def get_quarter_fund_data(self, quarter_date, fund_code):

        fund_stock_data = self.stock_data[self.stock_data.ReportDate == quarter_date]
        fund_stock_data = fund_stock_data[fund_stock_data.FundCode == fund_code]
        fund_stock_data = fund_stock_data.reset_index(drop=True)
        fund_stock_data = fund_stock_data.sort_values(by=['Weight'], ascending=False)
        fund_stock_data = fund_stock_data.iloc[0:10, :]

        fund_industry_data = self.industry_data[self.industry_data.ReportDate == quarter_date]
        fund_industry_data = fund_industry_data[fund_industry_data.FundCode == fund_code]
        fund_industry_data = fund_industry_data.reset_index(drop=True)

        return fund_stock_data, fund_industry_data

    def get_halfyear_fund_data(self, quarter_date, fund_code):

        fund_stock_data = self.stock_data[self.stock_data.ReportDate == quarter_date]
        fund_stock_data = fund_stock_data[fund_stock_data.FundCode == fund_code]
        fund_stock_data = fund_stock_data.reset_index(drop=True)

        fund_industry_data = self.industry_data[self.industry_data.ReportDate == quarter_date]
        fund_industry_data = fund_industry_data[fund_industry_data.FundCode == fund_code]
        fund_industry_data = fund_industry_data.reset_index(drop=True)

        return fund_stock_data, fund_industry_data

    def simulation_fund_date(self):

        fund_code = "000001.OF"
        quarter_date = "20170930"
        halfyear_date = "20170630"
        stock_quarter, industry_quarter = self.get_quarter_fund_data(quarter_date, fund_code)
        stock_halfyear, industry_halfyear = self.get_quarter_fund_data(halfyear_date, fund_code)

        stock_quarter = stock_quarter[['StockCode', 'Weight']]
        industry_quarter = industry_quarter[['IndustryCode', 'Weight']]

    def get_data_from_out(self):

        file = r'C:\Users\doufucheng\OneDrive\Desktop\普通股票型基金.csv'
        port_name = '普通股票基金'
        fund_index_code = "885000.WI"

        data = pd.read_csv(file, encoding='gbk')
        date_series = list(set(data.report_period.values))
        date_series.sort()

        from quant.source.backtest import BackTest
        from quant.source.wind_portfolio import WindPortUpLoad

        wind_port_path = WindPortUpLoad().path
        sub_path = os.path.join(wind_port_path, port_name)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(date_series)):
            date = date_series[i_date]
            data_date = data[data.report_period == date]

            data_gb = data_date.groupby(by=['stock_code']).sum()['weight']
            data_gb = pd.DataFrame(data_gb)
            data_gb.columns = ['Weight']
            data_gb['Weight'] = data_gb['Weight'] / data_gb['Weight'].sum()

            data_date = data_gb
            publish_date = Date().get_trade_date_offset(date, 17)
            data_date.columns = ['Weight']
            data_date.index.name = 'Code'
            data_date["CreditTrading"] = "No"
            data_date["Date"] = publish_date
            data_date["Price"] = 0.0
            data_date["Direction"] = "Long"
            file = os.path.join(sub_path, '%s_%s.csv' % (port_name, publish_date))
            data_date.to_csv(file)

        backtest = BackTest()
        backtest.set_info(port_name, fund_index_code)
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return(beg_date="20040101")
        backtest.cal_turnover(annual_number=4)
        backtest.cal_summary(all_beg_date="20040101")


if __name__ == '__main__':

    self = FundHolderSimulation()
    self.get_data_from_out()
