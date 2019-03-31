import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaIncome2EV(AlphaFactor):

    """
    因子说明：营业总收入TTM / 企业价值（剔除货币资金）
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_income2ev'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        income = Stock().read_factor_h5("OperatingIncomeTotal")
        income_ttm = Stock().change_single_quarter_to_ttm_quarter(income)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        income_ttm = Stock().change_quarter_to_daily_with_disclosure_date(income_ttm, report_data, beg_date, end_date)
        ev = Stock().read_factor_h5("Ev2") / 100000000

        # data precessing
        [income_ttm, ev] = Stock().make_same_index_columns([income_ttm, ev])
        res = income_ttm.div(ev)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaIncome2EV()
    self.cal_factor_exposure(beg_date, end_date)
