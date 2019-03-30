from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.fund.fund_pool import FundPool
from quant.fund.fund_holder import FundHolder
from quant.fund.fund_factor import FundFactor
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad

import os
import pandas as pd
from datetime import datetime


class FundHalfYearReplication(Data):

    """
    在每个基金 半年报/年报 买入对应股票
    """

    def __init__(self, fund_code):

        Data.__init__(self)

        self.port_name = "半年报%s" % fund_code
        self.fund_code = fund_code
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor

    def cal_all_wind_file(self):

        """ 生成wind文件 """

        date_series = Date().get_normal_date_series("20150101", datetime.today(), "S")
        fund_holding = FundHolder().get_fund_holding_halfyear(fund=self.fund_code)

        for i_date in range(len(date_series)):

            half_year_date = date_series[i_date]
            publish_date = Date().get_trade_date_offset(half_year_date, 0)
            try:
                fund_holding_date = pd.DataFrame(fund_holding[half_year_date])
                fund_holding_date = fund_holding_date.dropna()

                fund_holding_date.columns = ["Weight"]
                fund_holding_date = fund_holding_date.sort_values(by=['Weight'], ascending=False)
                fund_holding_date["Weight"] /= 100.0
                fund_holding_date.loc['Cash', 'Weight'] = 1 - fund_holding_date["Weight"].sum()

                fund_holding_date.index.name = "Code"
                fund_holding_date["CreditTrading"] = "No"
                fund_holding_date["Date"] = publish_date
                fund_holding_date["Price"] = 0.0
                fund_holding_date["Direction"] = "Long"

                sub_path = os.path.join(self.wind_port_path, self.port_name)
                if not os.path.exists(sub_path):
                    os.makedirs(sub_path)

                file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, publish_date))
                fund_holding_date.to_csv(file)
            except Exception as e:
                pass

    def backtest(self):

        """ 计算 回测结果 """

        port = BackTest()
        port.set_info(self.port_name, self.fund_code)
        port.read_weight_at_all_change_date()
        port.cal_weight_at_all_daily()
        port.cal_port_return(beg_date="20150101")
        port.cal_turnover(annual_number=2)
        port.cal_summary(all_beg_date="20150101")

    def cal_weight_data(self):

        """
        将每天权重结果 和 指数每日涨跌幅表现 写入Index数据当中
        """

        port = BackTest()
        port.set_info(self.port_name, "885000.WI")
        port.get_weight_at_all_daily()
        port.get_port_return()
        port_daily = port.port_hold_daily

        # 写入每日收益率
        data = pd.DataFrame(port.port_return['PortReturn'])
        data.columns = ['PCT']
        data["CLOSE"] = (data['PCT'] + 1.0).cumprod() * 1000
        sub_path = self.data_factor_path
        data.to_csv(os.path.join(sub_path, self.port_name + '.csv'))

        # 写入每日权重
        sub_path = os.path.join(self.data_weight_path, self.port_name)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(port_daily.columns)):

            date = port_daily.columns[i_date]
            weight_date = pd.DataFrame(port_daily[date])
            weight_date = weight_date.dropna()
            weight_date.columns = ['WEIGHT']
            weight_date.index.name = 'CODE'
            file = os.path.join(sub_path, '%s.csv' % date)
            print(file)
            weight_date.to_csv(file)


if __name__ == '__main__':

    fund_code = "163406.OF"
    self = FundHalfYearReplication(fund_code)
    self.cal_all_wind_file()
    self.backtest()

    # file = r'C:\Users\doufucheng\OneDrive\Desktop\基金表现.xlsx'
    # data = pd.read_excel(file, index_col=[0])

    #
    # for i_fund in range(12, len(data)):
    #     fund_code = data.index[i_fund]
    #     self = FundHalfYearReplication(fund_code)
    #     self.cal_all_wind_file()
    #     self.backtest()

