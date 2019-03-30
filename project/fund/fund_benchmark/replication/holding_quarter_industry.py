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
    每个季度末得到公募主动股票基金的平均持仓 满仓股票 按照市值分成5组
    """

    def __init__(self):

        Data.__init__(self)

        self.port_name = "公募股票基金季报满仓"
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor

        self.stock_ratio = None
        self.industry_citic1 = None
        self.pct = None
        self.group = list(range(1, 30))

    def get_data(self):

        """ 季度公募主动股票基金股票权重 作为指数股票权重参考标准 """

        self.stock_ratio = FundFactor().get_fund_factor('Stock_Ratio').T
        self.industry_citic1 = Stock().read_factor_h5("industry_citic1", Stock().get_h5_path("mfc_primary"))
        self.pct = Stock().read_factor_h5("Pct_chg")  # 调整股票的调整日的权重

    def cal_weight_date(self, quarter_date):

        """ 单个季度公募主动股票基金平均权重 每个基金的权都为1 """

        fund_pool = FundPool().get_fund_pool_code(name="基金持仓基准基金池", date=quarter_date)

        for i_fund in range(len(fund_pool)):
            fund = fund_pool[i_fund]
            try:
                fund_holding = FundHolder().get_fund_holding_quarter(fund=fund)
                fund_holding_date = pd.DataFrame(fund_holding[quarter_date])
                fund_holding_date = fund_holding_date.dropna()
                fund_holding_date *= 1.0
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
        group = 5

        for i_date in range(len(date_series)):

            quarter_date = date_series[i_date]
            stock_data_weight = self.cal_weight_date(quarter_date)
            stock_data_weight.columns = ["Weight"]
            stock_data_weight /= stock_data_weight.sum()

            publish_date = Date().get_trade_date_offset(quarter_date, 16)
            industry_date = pd.DataFrame(self.industry_citic1[publish_date])
            industry_date.columns = ['Industry']

            data = pd.concat([stock_data_weight, industry_date], axis=1)
            data = data.dropna()
            data = data.sort_values(by=['Industry'], ascending=False)

            print(len(data), quarter_date)

            for i in self.group:

                data_group = data[data['Industry'] == i]

                if len(data_group) > 0:
                    data_group['Weight'] /= data_group['Weight'].sum()
                    data_group.index.name = "Code"
                    data_group["CreditTrading"] = "No"
                    data_group["Date"] = publish_date
                    data_group["Price"] = 0.0
                    data_group["Direction"] = "Long"
                    port_name = self.port_name + '_Industry%s' % i
                    sub_path = os.path.join(self.wind_port_path, port_name)
                    if not os.path.exists(sub_path):
                        os.makedirs(sub_path)

                    file = os.path.join(sub_path, '%s_%s.csv' % (port_name, publish_date))
                    data_group.to_csv(file)

    def backtest(self):

        """ 计算 回测结果 """
        for i in self.group:
            port_name = self.port_name + '_Industry%s' % i
            port = BackTest()
            port.set_info(port_name, '885000.WI')
            port.read_weight_at_all_change_date()
            port.cal_weight_at_all_daily()
            port.cal_port_return()
            port.cal_turnover()
            port.cal_summary()

    def cal_weight_data(self):

        """
        将每天权重结果 和 指数每日涨跌幅表现 写入Index数据当中
        """
        for i in self.group:
            port_name = self.port_name + '_Industry%s' % i
            port = BackTest()
            port.set_info(port_name, "885000.WI")
            port.get_weight_at_all_daily()
            port.get_port_return()
            port_daily = port.port_hold_daily

            # 写入每日收益率
            data = pd.DataFrame(port.port_return['PortReturn'])
            data.columns = ['PCT']
            data["CLOSE"] = (data['PCT'] + 1.0).cumprod() * 1000
            sub_path = self.data_factor_path
            data.to_csv(os.path.join(sub_path, port_name + '.csv'))

            # 写入每日权重
            # sub_path = os.path.join(self.data_weight_path, self.port_name)
            # if not os.path.exists(sub_path):
            #     os.makedirs(sub_path)
            #
            # for i_date in range(len(port_daily.columns)):
            #     date = port_daily.columns[i_date]
            #     weight_date = pd.DataFrame(port_daily[date])
            #     weight_date = weight_date.dropna()
            #     weight_date.columns = ['WEIGHT']
            #     weight_date.index.name = 'CODE'
            #     file = os.path.join(sub_path, '%s.csv' % date)
            #     print(file)
            #     weight_date.to_csv(file)


if __name__ == '__main__':

    self = HoldingQuarter()

    self.get_data()
    # self.cal_all_wind_file()
    # self.backtest()
    self.cal_weight_data()

