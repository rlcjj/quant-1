import os
from datetime import datetime

import pandas as pd
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad
from quant.stock.date import Date
from quant.stock.index import Index

from data.fund.exposure_return.regression import FundRegressionExposure


class IndexOlsRegression(object):


    def __init__(self, index_code_list, port_name):

        """
        跟踪股票基金总指数 基金指数回归各类指数
        """
        self.index_code_list = index_code_list
        self.port_name = port_name
        self.wind_port_path = WindPortUpLoad().path
        self.fund_index_code = "885000.WI"

    def update_data(self, beg_date=None, end_date=None):

        """ 下载更新所需要的指数数据"""

        if end_date is None:
            end_date = datetime.today()
        if beg_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -20)

        Index().load_index_factor(self.fund_index_code, beg_date, end_date)
        for i in range(len(self.index_code_list)):
            try:
                Index().load_index_factor(self.index_code_list[i], beg_date, end_date)
            except Exception as e:
                pass

    def regress(self):

        """ 并回归计算权重 """

        regression = FundRegressionExposure(self.port_name)
        regression.get_data(self.index_code_list)
        regression.cal_fund_regression_exposure(self.fund_index_code, "20040101", datetime.today().strftime("%Y%m%d"))

    def get_wind_file(self):

        """ 得到wind权重 """

        fund_index = FundRegressionExposure(self.port_name).get_fund_regression_exposure(self.fund_index_code)
        fund_index = fund_index.dropna(how='all')
        fund_index = fund_index.T
        date_series = Date().get_trade_date_series(fund_index.columns[0], fund_index.columns[-1], "W")
        date_series = list(set(date_series) & set(fund_index.columns))
        date_series.sort()
        sub_path = os.path.join(self.wind_port_path, self.port_name)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print("Generate File %s" % date)
            data_date = pd.DataFrame(fund_index[date])
            next_date = Date().get_trade_date_offset(date, 1)
            data_date.columns = ['Weight']
            data_date.index.name = 'Code'
            data_date["CreditTrading"] = "No"
            data_date["Date"] = next_date
            data_date["Price"] = 0.0
            data_date["Direction"] = "Long"
            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, next_date))
            data_date.to_csv(file)

    def backtest(self):

        """ 回测 """

        backtest = BackTest()
        backtest.set_info(self.port_name, self.fund_index_code)
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return(beg_date="20040101")
        backtest.cal_turnover(annual_number=50)
        backtest.cal_summary(all_beg_date="20040101")


if __name__ == '__main__':

    #####################################################################################
    # index_code_list = ["H11006.CSI", "H11008.CSI",
    #                    "CI005909.WI", "CI005910.WI", "CI005911.WI",
    #                    "CI005912.WI", "CI005913.WI",
    #                    "CI005914.WI", "CI005915.WI", "CI005916.WI"]
    #
    # port_name = "IndustryIndex"
    # self = IndexOlsRegression(index_code_list, port_name)
    # # self.regress()
    # # self.get_wind_file()
    # self.backtest()
    #
    # ######################################################################################
    # index_code_list = ["H11006.CSI", "H11008.CSI",
    #                    "CI005909.WI", "CI005910.WI", "CI005911.WI",
    #                    "CI005912.WI", "CI005913.WI",
    #                    "CI005914.WI", "CI005915.WI", "CI005916.WI",
    #                    "公募股票基金季报满仓", "HK2C90"]
    #
    # port_name = "HK_Holder_IndustryIndex"
    #
    # self = IndexOlsRegression(index_code_list, port_name)
    # # self.update_data()
    # # self.regress()
    # # self.get_wind_file()
    # self.backtest()
    #
    # ######################################################################################
    # index_code_list = ["885062.WI", "000300.SH", "000905.SH",
    #                    "000852.SH", "399006.SZ", "普通股票型基金跟随"]
    #
    # folder_name = "Holder_SizeIndex"
    #
    # self = IndexOlsRegression(index_code_list, folder_name)
    # self.regress()
    # self.get_wind_file()
    # self.backtest()
    # #######################################################################################

    index_code_list = ["885062.WI", "000300.SH", "000905.SH",
                       "000852.SH", "399006.SZ", "399005.SZ",
                       '000016.SH', '801853.SI', "普通股票型基金_等权季报满仓_披露日"]

    folder_name = "回归_宽基指数7_跟随基金指数"

    self = IndexOlsRegression(index_code_list, folder_name)
    self.regress()
    self.get_wind_file()
    self.backtest()
    # ######################################################################################
    # index_code_list = ["885062.WI", "000300.SH", "000905.SH",
    #                    "000852.SH", "399006.SZ"]
    #
    # folder_name = "SizeIndex"
    #
    # self = IndexOlsRegression(index_code_list, folder_name)
    # # self.regress()
    # # self.get_wind_file()
    # self.backtest()
    #
    # ######################################################################################
    #
    index_code_list = ["885062.WI", "000300.SH", "000905.SH",
                       "000852.SH", "399006.SZ", "399005.SZ",
                       '000016.SH', '801853.SI']

    folder_name = "回归_宽基指数7"

    self = IndexOlsRegression(index_code_list, folder_name)
    self.regress()
    self.get_wind_file()
    self.backtest()

    ######################################################################################
    # index_code_list = ["885062.WI", "882001.WI", "882002.WI", "882003.WI",
    #                    "882004.WI", "882005.WI", "882006.WI",
    #                    "882007.WI", "882008.WI", "882009.WI", "882010.WI", "882011.WI",
    #                    "公募股票基金季报满仓", "ROETTMDaily"]
    #
    # folder_name = "ROE_Holder_WindIndustryIndex"
    #
    # self = IndexOlsRegression(index_code_list, folder_name)
    # self.update_data("20040101", datetime.today().strftime("%Y%m%d"))
    # self.regress()
    # self.get_wind_file()
    # self.backtest()
    ######################################################################################
    #
    index_code_list = ["885062.WI", "882001.WI", "882002.WI", "882003.WI",
                       "882004.WI", "882005.WI", "882006.WI",
                       "882007.WI", "882008.WI", "882009.WI", "882010.WI", "882011.WI"]

    folder_name = "回归_行业指数11"

    self = IndexOlsRegression(index_code_list, folder_name)
    self.regress()
    self.get_wind_file()
    self.backtest()
    #
    # #####################################################################################
    # index_code_list = ["885062.WI", "882001.WI", "882002.WI", "882003.WI",
    #                    "882004.WI", "882005.WI", "882006.WI",
    #                    "882007.WI", "882008.WI", "882009.WI", "882010.WI", "882011.WI",
    #                    "公募股票基金季报满仓", "HK2C90",
    #                    "000300.SH", "000905.SH",
    #                    "000852.SH", "399006.SZ", "399005.SZ", '000016.SH', '801853.SI'
    #                    ]
    #
    # folder_name = "HK_Holder_WindIndustrySizeIndex"
    #
    # self = IndexOlsRegression(index_code_list, folder_name)
    # # self.update_data("20040101", datetime.today().strftime("%Y%m%d"))
    # self.regress()
    # self.get_wind_file()
    # self.backtest()

    # ######################################################################################
    # index_code_list = ["885062.WI", "000300.SH", "000905.SH",
    #                    "000852.SH", "399006.SZ", "399005.SZ", '000925.SH', '801853.SI',
    #                    '801833.SI', '801823.SI']
    #
    # folder_name = "SizeIndex10"
    #
    # self = IndexOlsRegression(index_code_list, folder_name)
    # self.update_data()
    # self.regress()
    # self.get_wind_file()
    # self.backtest()

    # ######################################################################################
    # index_code_list = ["885062.WI", "CI005909.WI", "公募股票基金季报满仓"]
    # # , "ROETTMDaily"
    #
    # folder_name = "Index2"
    #
    # self = IndexOlsRegression(index_code_list, folder_name)
    # self.update_data("20050101", datetime.today().strftime("%Y%m%d"))
    # self.regress()
    # self.get_wind_file()
    # self.backtest()

    # index_code_list = ["H11006.CSI", "H11008.CSI",
    #                    "CI005909.WI", "CI005910.WI", "CI005911.WI",
    #                    "CI005912.WI", "CI005913.WI",
    #                    "CI005914.WI", "CI005915.WI", "CI005916.WI",
    #                    "普通股票型基金跟随", "ROERankYOY"]
    # port_name = "ROERankYOY_Holder_IndustryIndex"
    #
    # self = IndexOlsRegression(index_code_list, port_name)
    # # self.update_data()
    # self.regress()
    # self.get_wind_file()
    # self.backtest()

    # ######################################################################################
    # index_code_list = ["H11006.CSI", "H11008.CSI",
    #                    "公募股票基金季报满仓_Size1", "公募股票基金季报满仓_Size2", "公募股票基金季报满仓_Size3",
    #                    "公募股票基金季报满仓_Size4", "公募股票基金季报满仓_Size5", "公募股票基金季报满仓"]
    #
    # port_name = "HolderSizeIndex6"
    #
    # self = IndexOlsRegression(index_code_list, port_name)
    # # self.update_data()
    # self.regress()
    # self.get_wind_file()
    # self.backtest()

    # index_code_list = ["公募股票基金季报满仓_Industry" + str(x) for x in range(1, 30)]
    # index_code_list.extend(["H11006.CSI", "H11008.CSI"])
    #
    # port_name = "HolderIndustryIndex29"
    #
    # self = IndexOlsRegression(index_code_list, port_name)
    # # self.update_data()
    # self.regress()
    # self.get_wind_file()
    # self.backtest()



