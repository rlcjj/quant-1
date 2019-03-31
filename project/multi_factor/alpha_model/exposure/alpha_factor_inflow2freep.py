import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaInflow2FreeP(AlphaFactor):

    """
    因子说明：过去 10天 资金净流入额/自由流通市值
    流入为当日成交价上升的时候的成交额和成交量 流出为当日成交价下降时候的成交额和成交量
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_inflow2freep'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        term = 10

        # read data
        inflow = Stock().read_factor_h5("Mf_Inflow")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        free_share = Stock().read_factor_h5("Free_FloatShare")

        # calculate data
        [price_unadjust, free_share] = Stock().make_same_index_columns([price_unadjust, free_share])
        free_mv = price_unadjust.mul(free_share) / 100000000
        [inflow, free_mv] = Stock().make_same_index_columns([inflow, free_mv])
        ratio = inflow.div(free_mv)

        res = ratio.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaInflow2FreeP()
    self.cal_factor_exposure(beg_date, end_date)
