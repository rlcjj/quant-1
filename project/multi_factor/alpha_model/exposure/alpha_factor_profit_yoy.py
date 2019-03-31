import pandas as pd

from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaProfitYoY(AlphaFactor):

    """
    因子说明：扣非净利润同比增长率
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_profit_yoy'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        profit = Stock().read_factor_h5("NetProfitDeducted").T
        profit_4 = profit.shift(4)
        profit_yoy = profit / profit_4 - 1.0

        profit_yoy = profit_yoy.T
        report_data = Stock().read_factor_h5("ReportDateDaily")
        profit_yoy = Stock().change_quarter_to_daily_with_disclosure_date(profit_yoy, report_data, beg_date, end_date)

        res = profit_yoy.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaProfitYoY()
    self.cal_factor_exposure(beg_date, end_date)
