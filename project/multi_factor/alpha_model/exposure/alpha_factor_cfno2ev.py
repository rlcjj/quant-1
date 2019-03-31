import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCFNO2EV(AlphaFactor):

    """
    因子说明：净经营性现金流TTM / 企业价值（剔除货币资金）
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cfno2ev'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        cfo = Stock().read_factor_h5("NetOperateCashFlow")
        cfo_ttm = Stock().change_single_quarter_to_ttm_quarter(cfo)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        cfo_ttm = Stock().change_quarter_to_daily_with_disclosure_date(cfo_ttm, report_data, beg_date, end_date)
        ev = Stock().read_factor_h5("Ev2") / 100000000

        # data precessing
        [cfo_ttm, ev] = Stock().make_same_index_columns([cfo_ttm, ev])
        res = cfo_ttm.div(ev)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCFNO2EV()
    self.cal_factor_exposure(beg_date, end_date)
