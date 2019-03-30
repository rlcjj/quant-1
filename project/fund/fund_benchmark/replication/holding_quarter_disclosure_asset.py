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


class HoldingQuarter(Data):

    """
    普通股票型基金_规模加权季报_披露日
    """

    def __init__(self):

        Data.__init__(self)

        self.port_name = "普通股票型基金_规模加权季报_披露日"
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor

        self.stock_ratio = None

    def get_data(self):

        """ 季度公募主动股票基金股票权重 作为指数股票权重参考标准 """

        self.stock_ratio = FundFactor().get_fund_factor('Stock_Ratio').T
        self.total_asset = FundFactor().get_fund_factor('Total_Asset').T

    def cal_weight_date(self, quarter_date):

        """ 单个季度公募主动股票基金平均权重 每个基金的权都为1 """

        fund_pool = FundPool().get_fund_pool_code(name="普通股票型基金", date=quarter_date)

        for i_fund in range(len(fund_pool)):
            fund = fund_pool[i_fund]
            try:
                asset = self.total_asset.loc[fund, quarter_date] / 100000000
            except Exception as e:
                asset = 0.5
            try:
                fund_holding = FundHolder().get_fund_holding_quarter(fund=fund)
                fund_holding_date = pd.DataFrame(fund_holding[quarter_date])
                fund_holding_date = fund_holding_date.dropna()
                fund_holding_date *= asset
                fund_holding_date.columns = [fund]
            except Exception as e:
                fund_holding_date = pd.DataFrame([], columns=[fund])
            if i_fund == 0:
                stock_data = fund_holding_date
            else:
                stock_data = pd.concat([stock_data, fund_holding_date], axis=1)

        stock_data = stock_data.dropna(how='all')
        stock_data_weight = pd.DataFrame(stock_data.sum(axis=1))
        return stock_data_weight

    def cal_all_wind_file(self):

        """ 计算 所有季报日 公募主动股票基金 基金平均持仓 还要考虑股票仓位 并生成wind文件"""

        date_series = Date().get_normal_date_series("20040101", datetime.today(), "Q")

        for i_date in range(len(date_series)):

            quarter_date = date_series[i_date]
            fund_pool = FundPool().get_fund_pool_code(name="普通股票型基金", date=quarter_date)
            stock_ratio = pd.DataFrame(self.stock_ratio.loc[fund_pool, quarter_date])
            ratio = stock_ratio.median().values[0] / 100.0

            stock_data_weight = self.cal_weight_date(quarter_date)
            stock_data_weight.columns = ["Weight"]
            stock_data_weight /= stock_data_weight.sum()
            publish_date = Date().get_trade_date_offset(quarter_date, 16)

            print(len(stock_data_weight))
            stock_data_weight.index.name = "Code"
            stock_data_weight *= ratio
            stock_data_weight.loc['Cash', 'Weight'] = 1.0 - ratio
            stock_data_weight["CreditTrading"] = "No"
            stock_data_weight["Date"] = publish_date
            stock_data_weight["Price"] = 0.0
            stock_data_weight["Direction"] = "Long"

            sub_path = os.path.join(self.wind_port_path, self.port_name)
            if not os.path.exists(sub_path):
                os.makedirs(sub_path)

            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, publish_date))
            stock_data_weight.to_csv(file)

    def backtest(self):

        """ 计算 回测结果 """

        port = BackTest()
        port.set_info(self.port_name, '885000.WI')
        port.read_weight_at_all_change_date()
        port.cal_weight_at_all_daily()
        port.cal_port_return(beg_date="20040101")
        port.cal_turnover(annual_number=4)
        port.cal_summary(all_beg_date="20040101")

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

    self = HoldingQuarter()

    self.get_data()
    self.cal_all_wind_file()
    self.backtest()
    # self.cal_weight_data()

