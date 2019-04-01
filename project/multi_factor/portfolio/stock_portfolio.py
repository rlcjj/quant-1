import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess


class StockPortfolio(Data):

    """
    生成股票投资组合

    最大化Alpha - 跟踪误差
    在控制风格和行业风险一定的情况下

    """

    def __init__(self):

        """ 数据存储位置 """

        Data.__init__(self)
        self.sub_data_path = r'stock_data\alpha_model'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)