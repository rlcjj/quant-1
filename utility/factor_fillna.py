import numpy as np
import pandas as pd

from quant.utility.factor_operate import FactorOperate
from quant.stock.stock_factor_data import StockFactorData


class FactorFillNa(object):

    """
    将停牌当日的数据替换成为NAN
    补充因子的缺失值
    补充范围： 自上市之日起 到退市之日终止
    1、补充当日截面的中位数
    2、补充对应行业的中位数
    3、因子值根据其他因子值做线性回归得到 (Barra Risk Model)
    """

    def __init__(self):
        pass

    def replace_suspension_with_nan(self, data):

        factor = data.copy()
        status = StockFactorData().read_factor_h5("TradingStatus")
        factor, status = FactorOperate().make_same_index_columns([factor, status])
        statusif = status.applymap(lambda x: x == 1.0)
        factor[statusif] = np.nan
        return factor

    def fillna_with_mad_market(self, data):

        factor = data.copy()
        factor_val = factor.values

        status = StockFactorData().read_factor_h5("TradingStatus")
        factor, status = FactorOperate().make_same_index_columns([factor, status])

        if_list = status.applymap(lambda x: x in [0.0, 1.0])
        if_nan = factor.isnull()

        mask_val = (if_list & if_nan).values
        md_val = factor.median(axis=0).values
        md_remat_val = np.tile(np.vstack(md_val), (1, factor.shape[0])).T
        factor_fill_mad_val = np.where(mask_val, md_remat_val, factor_val)
        factor_fill_mad_pandas = pd.DataFrame(factor_fill_mad_val, index=factor.index, columns=factor.columns)

        return factor_fill_mad_pandas

if __name__ == '__main__':

    from quant.stock.stock import Stock
    data = Stock().read_factor_h5("Pct_chg")  # "Pct_chg" 原始数据停牌有可能是0 也有可能是NAN

    data = FactorFillNa().replace_suspension_with_nan(data)
    print(data)