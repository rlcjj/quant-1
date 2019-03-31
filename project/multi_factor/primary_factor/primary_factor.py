import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess


class PrimaryFactor(Data):

    """
    所有基础股票因子的父类

    注意不管是风险模型、还是alpha模型，其模型的构造都和股票池相关
    """

    def __init__(self):

        """ 数据存储位置 """

        Data.__init__(self)
        self.sub_data_path = r'stock_data\stock_factor'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.exposure_hdf_path = os.path.join(self.data_path, r'primary_factor\hdf')
        self.exposure_csv_path = os.path.join(self.data_path, r'primary_factor\csv')

    def get_primary_factor_exposure(self, factor_name):

        """ 取得风险因子的暴露 """

        data = Stock().read_factor_h5(factor_name, self.exposure_hdf_path)
        return data

    def save_primary_factor_exposure(self, data, factor_name):

        """ 存储成为 CSV 和 HDF 两份 """

        Stock().write_factor_h5(data, factor_name, self.exposure_hdf_path)
        data = self.get_primary_factor_exposure(factor_name)
        data.to_csv(os.path.join(self.exposure_csv_path, '%s.csv' % factor_name))

    def get_all_alpha_factor_name(self):

        """ 得到所有Alpha的名字 """

        path = self.exposure_hdf_path
        file_list = os.listdir(path)
        factor_name_list = list(map(lambda x: x[0:-3], file_list))
        return factor_name_list


if __name__ == '__main__':

    factor_name = "alpha_raw_roe"
    beg_date, end_date, period = None, None, "D"

    self = PrimaryFactor()
    self.get_primary_factor_exposure(factor_name)
