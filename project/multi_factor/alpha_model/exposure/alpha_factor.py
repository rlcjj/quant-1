import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess


class AlphaFactor(Data):

    """
    所有Alpha因子的父类
    注意不管是风险模型、还是alpha模型，其模型的构造都和股票池相关
    """

    def __init__(self):

        """ 数据存储位置 """

        Data.__init__(self)
        self.sub_data_path = r'stock_data\alpha_model'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.exposure_hdf_path = os.path.join(self.data_path, r'factor\hdf')
        self.exposure_csv_path = os.path.join(self.data_path, r'factor\csv')
        self.factor_performance_path = os.path.join(self.data_path, r'factor_performance')

    def get_alpha_factor_exposure(self, factor_name):

        """ 取得风险因子的暴露 """

        data = Stock().read_factor_h5(factor_name, self.exposure_hdf_path)
        return data

    def save_alpha_factor_exposure(self, data, factor_name):

        """ 存储成为 CSV 和 HDF 两份 """

        Stock().write_factor_h5(data, factor_name, self.exposure_hdf_path)
        data = self.get_alpha_factor_exposure(factor_name)
        data.to_csv(os.path.join(self.exposure_csv_path, '%s.csv' % factor_name))

    def get_all_alpha_factor_name(self):

        """ 得到所有Alpha的名字 """

        data = self.get_all_alpha_factor_file()
        factor_name_list = list(data['因子名'].values)
        factor_name_list.sort()
        return factor_name_list

    def get_all_alpha_factor_file(self):

        """ 得到所有Alpha的文件 """

        file = os.path.join(self.data_path, r"factor\param\UseAlpha.xlsx")
        data = pd.read_excel(file, index_col=[0])
        data = data.dropna(subset=["因子名"])

        return data

    def get_major_alpha_name(self):

        """ 得到 Alpha 大类因子名 """
        
        factor_list = self.get_all_alpha_factor_file()
        major_factor_list = list(set(factor_list.index))
        major_factor_list.sort()
        return major_factor_list

    def get_standard_alpha_factor(self, factor_name):

        """ 预处理Alpha因子 包括去极值、标准化 """

        factor_data = self.get_alpha_factor_exposure(factor_name)
        factor_remove = FactorPreProcess().remove_extreme_value_mad(factor_data)
        factor_stand = FactorPreProcess().standardization(factor_remove)

        return factor_stand


if __name__ == '__main__':

    factor_name = "alpha_raw_roe"
    beg_date, end_date, period = None, None, "D"

    self = AlphaFactor()
    # self.get_alpha_factor_exposure(factor_name)
    print(self.get_major_alpha_name())
