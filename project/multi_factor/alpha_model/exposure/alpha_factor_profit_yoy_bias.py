import pandas as pd

from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaProfitYoYBias(AlphaFactor):

    """
    因子说明：当季 净利润 同比增长 的 环减值
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_income_yoy_bias'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        profit = Stock().read_factor_h5("OperatingIncome").T
        profit_4 = profit.shift(4)
        profit_yoy = profit / profit_4 - 1.0

        yoy_bias = profit_yoy.diff().T
        report_data = Stock().read_factor_h5("ReportDateDaily")
        yoy_bias = Stock().change_quarter_to_daily_with_disclosure_date(yoy_bias, report_data, beg_date, end_date)

        res = yoy_bias.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaProfitYoYBias()
    self.cal_factor_exposure(beg_date, end_date)
