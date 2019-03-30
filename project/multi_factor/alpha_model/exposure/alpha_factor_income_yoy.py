import pandas as pd

from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaIncomeYoY(AlphaFactor):

    """
    因子说明：营业收入同比增长率
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_income_yoy'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        income = Stock().read_factor_h5("OperatingIncome").T
        income_4 = income.shift(4)
        income_yoy = income / income_4 - 1.0

        income_yoy = income_yoy.T
        report_data = Stock().read_factor_h5("ReportDateDaily")
        income_yoy = Stock().change_quarter_to_daily_with_disclosure_date(income_yoy, report_data, beg_date, end_date)

        res = income_yoy.T.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaIncomeYoY()
    self.cal_factor_exposure(beg_date, end_date)
