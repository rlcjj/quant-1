import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor
from quant.project.multi_factor.alpha_model.split.alpha_split_sample import AlphaSplitSample
from quant.project.multi_factor.alpha_model.split.alpha_split_sample import AlphaSplitSample


class ConcatSimpleAlpha(Data):

    """
    Alpha因子简单拆分后
    合成大类因子
    """

    def __init__(self):

        Data.__init__(self)

    def concat_ew_alpha(self, stock_pool_name):

        """ 等权合成因子 """

        factor_list = AlphaFactor().get_all_alpha_factor_file()
        major_factor_list = list(set(factor_list.index))

        for i in range(len(major_factor_list)):

            major_factor = major_factor_list[i]
            factor_select = factor_list[factor_list.index == major_factor]
            factor_name_list = list(factor_select["因子名"].values)
            result = pd.DataFrame()

            for i_factor in range(len(factor_name_list)):

                name = factor_name_list[i_factor]
                alpha = AlphaSplitSample().get_alpha_res_exposure(name, stock_pool_name)
                result = result.add(alpha, fill_value=0)

            result /= len(factor_name_list)
            AlphaSplitSample().save_alpha_res_exposure(result, major_factor, stock_pool_name)


if __name__ == "__main__":

    self = ConcatSimpleAlpha()
    stock_pool_name = "AllChinaStockFilter"
    self.concat_ew_alpha(stock_pool_name)
    self.concat_ew_alpha("hs300")
    self.concat_ew_alpha("zz500")