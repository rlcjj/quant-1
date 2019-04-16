import os
import numpy as np
import pandas as pd

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.barra import Barra

from quant.project.multi_factor.alpha_model.sample.alpha_split import AlphaSplit
from quant.project.multi_factor.alpha_model.sample.alpha_summary import AlphaSummary
from quant.project.multi_factor.alpha_model.sample.alpha_concat import AlphaConcat
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_update import AlphaFactorUpdate


class AlphaMain(object):

    """
    对于不同股票池
    1、计算 Alpha 因子暴露
    2、计算因子收益率 和因子表现
    3、等权合成大类因子 （估值、盈利、情绪、量价、成长）
    4、计算大类因子收益率及 因子表现
    5、ICIR加权合成最终Alpha因子
    6、计算Alpha因子收益率及 因子表现
    """

    def __init__(self):
        pass

    def update_data(self):

        """ 更新数据 """

        Stock().load_h5_primary_factor()
        Barra().load_barra_data()

    def alpha_pool(self, beg_date, end_date, period, stock_pool_name):

        """ 更新Alpha因子 在某个股票池 """

        # AlphaSplit().split_alpha_all(beg_date, end_date, "D", stock_pool_name)

        # factor_name_list = AlphaFactor().get_all_alpha_factor_name()
        # AlphaSummary().cal_all_factor_return("20040101", end_date, factor_name_list, period, stock_pool_name, 1)
        # AlphaSummary().cal_all_factor_summary("20040101", end_date, factor_name_list, period, stock_pool_name, 1)

        # AlphaConcat().ew_to_all_major_alpha(stock_pool_name, beg_date, end_date, period)
        factor_name_list = AlphaFactor().get_major_alpha_name()
        AlphaSummary().cal_all_factor_return("20040101", end_date, factor_name_list, period, stock_pool_name, 1)
        AlphaSummary().cal_all_factor_summary("20040101", end_date, factor_name_list, period, stock_pool_name, 1)

        # AlphaConcat().ew_to_alpha(stock_pool_name)
        AlphaSummary().cal_all_factor_return("20040101", end_date, ["alpha"], period, stock_pool_name, 1)
        AlphaSummary().cal_all_factor_summary("20040101", end_date, ["alpha"], period, stock_pool_name, 1)
        AlphaSummary().concat_summary(stock_pool_name)

    def alpha_main(self, beg_date, end_date, period):

        """ 更新Alpha因子在所有股票池 """

        # AlphaFactorUpdate().update_alpha_factor(beg_date, end_date)
        # AlphaFactorUpdate().check_alpha_factor_update_date()
        self.alpha_pool(beg_date, end_date, period, "AllChinaStockFilter")
        self.alpha_pool(beg_date, end_date, period, "hs300")
        self.alpha_pool(beg_date, end_date, period, "zz500")

if __name__ == '__main__':

    beg_date, end_date, period = "20190101", "20190404", "W"
    self = AlphaMain()
    # self.update_data()
    self.alpha_main(beg_date, end_date, period)
