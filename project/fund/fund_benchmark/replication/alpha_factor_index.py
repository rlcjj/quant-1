import pandas as pd
import numpy as np
import os

from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.index import Index
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad


class AlphaFactorIndex(object):

    def __init__(self, factor_name="ROETTMDaily"):

        """ 生成Alpha因子指数 用来合成Index取回归跟踪股票基金指数 """

        self.port_name = factor_name
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor
        self.alpha_data = Stock().read_factor_h5(factor_name, Stock().get_h5_path("my_alpha"))
        self.free_mv = Stock().read_factor_h5("Mkt_freeshares", Stock().get_h5_path("mfc_primary"))

    def wind_file(self):

        """ 一般因子不做行业和风格回归 但是限制每个行业不能太多 """

        date_series = Date().get_trade_date_series(self.alpha_data.columns[0], self.alpha_data.columns[-1], "M")
        date_series = list(set(date_series) & set(self.free_mv.columns) & set(self.alpha_data.columns))
        date_series.sort()

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print(date)
            alpha_date = pd.DataFrame(self.alpha_data[date])
            alpha_date.columns = ['Alpha']

            mv_date = pd.DataFrame(self.free_mv[date])
            mv_date.columns = ['FreeMV']
            mv_date['FreeMV'] = mv_date['FreeMV'].map(np.sqrt)

            data = pd.concat([alpha_date, mv_date], axis=1)
            data = data.dropna()

            # 去掉流通市值小的股票
            data = data.sort_values(by=['FreeMV'], ascending=False)
            data = data.iloc[0:int(len(data)*0.60), :]

            data = data.sort_values(by=['Alpha'], ascending=False)

            sub_path = os.path.join(self.wind_port_path, self.port_name)

            if not os.path.exists(sub_path):
                os.makedirs(sub_path)

            if len(data) > 150:

                l = int(len(data)/10)
                data = data.iloc[0:l, :]
                date = date_series[i_date]
                print("Generate File %s" % date, len(data))

                next_date = Date().get_trade_date_offset(date, 1)
                data['Weight'] = data['FreeMV'] / data['FreeMV'].sum()
                data.index.name = 'Code'
                data["CreditTrading"] = "No"
                data["Date"] = next_date
                data["Price"] = 0.0
                data["Direction"] = "Long"
                file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, next_date))
                data.to_csv(file)

    def backtest(self):

        """ 回测 """

        backtest = BackTest()
        backtest.set_info(self.port_name, "885000.WI")
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return()
        backtest.cal_turnover(annual_number=12)
        backtest.cal_summary()

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

    # self = AlphaFactorIndex("ROETTMDaily")
    # self.wind_file()
    # self.backtest()
    # self.cal_weight_data()
    #
    # self = AlphaFactorIndex("ROEQuarterDaily")
    # self.wind_file()
    # self.backtest()
    # self.cal_weight_data()
    #
    # self = AlphaFactorIndex("Momentum6m")
    # self.wind_file()
    # self.backtest()
    # self.cal_weight_data()

    # self = AlphaFactorIndex("ROEQuarterResDaily")
    # self.wind_file()
    # self.backtest()
    # self.cal_weight_data()

    # self = AlphaFactorIndex("NetProfitDeductedYOYDaily")
    # self.wind_file()
    # self.backtest()
    # self.cal_weight_data()

    self = AlphaFactorIndex("ROERankYOY")
    self.wind_file()
    self.backtest()
    self.cal_weight_data()


