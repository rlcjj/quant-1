import os
import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock


class AlphaCompound(object):

    """ 原始因子合成新的因子 """

    def __init__(self):
        pass

    def equal_weight_sum(self, factor_name_list, new_factor_name):

        """ 等权加和 """

        data_sum = pd.DataFrame([])

        for i_factor in range(len(factor_name_list)):

            factor_name = factor_name_list[i_factor]
            data = Stock().read_factor_h5(factor_name, Stock().get_h5_path("my_alpha"))
            data_stand = Stock().remove_extreme_value_mad(data)
            data_stand = Stock().standardization(data_stand)
            data_sum = data_sum.add(data_stand, fill_value=0.0)

        data_sum = data_sum.T.dropna(how='all').T
        Stock().write_factor_h5(data_sum, new_factor_name, Stock().get_h5_path("my_alpha"))


if __name__ == '__main__':

    factor_name_list = ['GrossProfitTTMMarketValueDaily', 'IncomeYOYDaily', 'ROEQuarterDaily']
    new_factor_name = 'Factor_Equal_3'
    AlphaCompound().equal_weight_sum(factor_name_list, new_factor_name)
