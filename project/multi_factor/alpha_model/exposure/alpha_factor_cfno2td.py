import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCFNO2TD(AlphaFactor):

    """
    因子说明：净经营性现金流TTM / 负债合计TTM
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cfno2td'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        cfo = Stock().read_factor_h5("NetOperateCashFlow")
        cfo_ttm = Stock().change_single_quarter_to_ttm_quarter(cfo)

        debt = Stock().read_factor_h5("TotalLiability") / 100000000
        debt_ttm = Stock().change_single_quarter_to_ttm_quarter(debt) / 4.0

        cfo2d = cfo_ttm.div(debt_ttm)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        cfo2d = Stock().change_quarter_to_daily_with_disclosure_date(cfo2d, report_data, beg_date, end_date)

        res = cfo2d.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCFNO2TD()
    self.cal_factor_exposure(beg_date, end_date)
