from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad


import os
import pandas as pd
from datetime import datetime


class FundHolderSimulation(Data):

    """
    利用基金半年报、年报以及基金证监会行业权重来补全基金季报
    """

    def __init__(self, port_name):

        Data.__init__(self)
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor
        self.port_name = '天风股票基金'

    def get_data_from_out(self):

        file1 = r'C:\Users\doufucheng\OneDrive\Desktop\普通股票型基金.csv'
        file2 = r'C:\Users\doufucheng\OneDrive\Desktop\偏股.csv'

        fund_index_code = "885000.WI"
        port_name = self.port_name

        data1 = pd.read_csv(file1, encoding='gbk')
        data2 = pd.read_csv(file2, encoding='gbk')
        data = pd.concat([data1, data2], axis=0)
        data = data.reset_index(drop=True)

        date_series = list(set(data.report_period.values))
        date_series.sort()

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

    def get_data(self):

        """ 季度公募主动股票基金股票权重 作为指数股票权重参考标准 """

        self.stock_ratio = FundFactor().get_fund_factor('Stock_Ratio').T
        self.pct = Stock().read_factor_h5("Pct_chg")  # 调整股票的调整日的权重

    def get_data_from_out_position(self):

        file1 = r'C:\Users\doufucheng\OneDrive\Desktop\普通股票型基金.csv'
        file2 = r'C:\Users\doufucheng\OneDrive\Desktop\偏股.csv'
        port_name = '天风股票基金仓位'
        fund_index_code = "885000.WI"

        data1 = pd.read_csv(file1, encoding='gbk')
        data2 = pd.read_csv(file2, encoding='gbk')
        data = pd.concat([data1, data2], axis=0)
        data = data.reset_index(drop=True)

        date_series = list(set(data.report_period.values))
        date_series.sort()


        wind_port_path = WindPortUpLoad().path
        sub_path = os.path.join(wind_port_path, port_name)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(date_series)):

            date = date_series[i_date]

            quarter_date = str(date)
            fund_pool = FundPool().get_fund_pool_code(name="基金持仓基准基金池", date=quarter_date)
            stock_ratio = pd.DataFrame(self.stock_ratio.loc[fund_pool, quarter_date])
            ratio = stock_ratio.median().values[0] / 100.0

            data_date = data[data.report_period == date]
            data_gb = data_date.groupby(by=['stock_code']).sum()['weight']
            data_gb = pd.DataFrame(data_gb)
            data_gb.columns = ['Weight']
            data_gb['Weight'] = data_gb['Weight'] / data_gb['Weight'].sum()

            data_date = data_gb
            publish_date = Date().get_trade_date_offset(date, 17)
            data_date.columns = ['Weight']
            data_date['Weight'] *= ratio
            data_date.loc["Cash", "Weight"] = 1 - ratio
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

    self = FundHolderSimulation()
    # self.get_data()
    # self.get_data_from_out_position()
    self.get_data_from_out()
    self.cal_weight_data()






