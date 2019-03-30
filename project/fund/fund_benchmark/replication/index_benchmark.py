import pandas as pd
import os

from quant.stock.date import Date
from quant.stock.index import Index
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad


class IndexBenchmark(object):

    def __init__(self):

        """ 回测股票权重 验证backtest程序正确与否 """

        self.port_name = ""
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor

    def wind_file(self, port_name, index_code):

        """ 生成wind文件 """

        self.port_name = port_name
        filter_stock = Index().get_weight_hdf(index_code)
        date_series = Date().get_trade_date_series(beg_date=filter_stock.columns[0],
                                                   end_date=filter_stock.columns[-1], period="2W")

        date_series = list(set(filter_stock.columns) & set(date_series))
        date_series.sort()

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            try:
                data = pd.DataFrame(filter_stock[date])
                if data.sum().values[0] > 10:
                    data = data.dropna() / 100.0
                data.columns = ['Weight']
            except Exception as e:
                data = pd.DataFrame([], columns=['Weight'])

            sub_path = os.path.join(self.wind_port_path, self.port_name)

            if not os.path.exists(sub_path):
                os.makedirs(sub_path)

            print("Generate File %s" % date)
            data.index.name = 'Code'
            data["CreditTrading"] = "No"
            data["Date"] = date
            data["Price"] = 0.0
            data["Direction"] = "Long"
            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, date))
            data.to_csv(file)

    def backtest(self, benchmark="H00300.CSI"):

        """ 回测 """

        backtest = BackTest()
        backtest.set_info(self.port_name, benchmark)
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return()
        backtest.cal_turnover(annual_number=12)
        backtest.cal_summary()


if __name__ == '__main__':

    port_name = "zz500"
    index_code = "SH000905"

    self = IndexBenchmark()
    self.wind_file(port_name, index_code)
    self.backtest("H00905.CSI")

    # port_name = "hs300"
    # index_code = "SH000300"
    #
    # self = IndexBenchmark()
    # self.wind_file(port_name, index_code)
    # self.backtest("H00300.CSI")
