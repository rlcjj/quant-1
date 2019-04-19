import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCFNO2Income(AlphaFactor):

    """
    因子说明：净经营性现金流TTM / 营业收入TTM
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cfno2income'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        cfo = Stock().read_factor_h5("NetOperateCashFlow")
        cfo_ttm = Stock().change_single_quarter_to_ttm_quarter(cfo)

        income = Stock().read_factor_h5("OperatingIncome")
        income_ttm = Stock().change_single_quarter_to_ttm_quarter(income) / 4.0

        cfo2income = cfo_ttm.div(income_ttm)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        cfo2income = Stock().change_quarter_to_daily_with_disclosure_date(cfo2income, report_data, beg_date, end_date)

        res = cfo2income.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCFNO2Income()
    self.cal_factor_exposure(beg_date, end_date)
