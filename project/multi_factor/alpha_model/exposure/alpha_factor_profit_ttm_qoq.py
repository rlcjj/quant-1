import pandas as pd

from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaProfitTTMQoQ(AlphaFactor):

    """
    因子说明：扣非净利润环比增长率
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_profit_ttm_qoq'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        profit = Stock().read_factor_h5("NetProfitDeducted")
        profit_ttm = Stock().change_single_quarter_to_ttm_quarter(profit).T
        profit_ttm_1 = profit_ttm.shift(1)
        profit_qoq = profit_ttm.div(profit_ttm_1) - 1.0
        profit_qoq = profit_qoq.T

        report_data = Stock().read_factor_h5("ReportDateDaily")
        profit_qoq = Stock().change_quarter_to_daily_with_disclosure_date(profit_qoq, report_data, beg_date, end_date)

        res = profit_qoq.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaProfitTTMQoQ()
    self.cal_factor_exposure(beg_date, end_date)
