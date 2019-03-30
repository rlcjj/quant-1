import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel


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

    def get_risk_factor_exposure(self, factor_name):

        """ 取得风险因子的暴露 """

        data = Stock().read_factor_h5(factor_name, self.exposure_hdf_path)
        return data

    def save_risk_factor_exposure(self, data, factor_name):

        """ 存储成为 CSV 和 HDF 两份 """

        Stock().write_factor_h5(data, factor_name, self.exposure_hdf_path)
        data = self.get_risk_factor_exposure(factor_name)
        data.to_csv(os.path.join(self.exposure_csv_path, '%s.csv' % factor_name))

    def get_all_alpha_factor_name(self):

        """ 得到所有Alpha的名字 """

        path = AlphaFactor().exposure_hdf_path
        file_list = os.listdir(path)
        factor_name_list = list(map(lambda x: x[0:-3], file_list))
        return factor_name_list

if __name__ == '__main__':

    factor_name = "alpha_raw_advance_receipts_equity_daily"
    self = AlphaFactor()
    self.get_risk_factor_exposure(factor_name)
