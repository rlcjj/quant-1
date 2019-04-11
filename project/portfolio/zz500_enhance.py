import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.fund.fund_pool import FundPool
from quant.fund.fund_holder import FundHolder
from quant.fund.fund_factor import FundFactor
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad
from quant.utility.write_excel import WriteExcel


class ZZ500_3Factor(Data):

    """ 利用简单的三个因子做一个500增强组合 """

    def __init__(self):

        """ 数据存储位置 """
        Data.__init__(self)
        self.port_name = "ZZ500_3Factor"
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor
        self.beg_date = "20170301"

    def update_data(self):

        """ 下载更新数据 """

        Stock().load_h5_primary_factor()

    def cal_weight_date(self, date):

        """ 得到某一天的权重"""


if __name__ == "__main__":

    self = ZZ500_3Factor()
