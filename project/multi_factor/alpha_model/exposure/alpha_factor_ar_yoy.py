import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaARYoY(AlphaFactor):

    """
    因子说明：预收账款同比增长率
    表征了股票的对下游的议价能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_ar_yoy'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        advance = Stock().read_factor_h5("AdvanceReceipts").T
        advance_4 = advance.shift(4)
        advance_yoy = advance / advance_4 - 1.0

        advance_yoy = advance_yoy.T
        report_data = Stock().read_factor_h5("ReportDateDaily")
        advance_yoy = Stock().change_quarter_to_daily_with_disclosure_date(advance_yoy, report_data, beg_date, end_date)

        res = advance_yoy.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaARYoY()
    self.cal_factor_exposure(beg_date, end_date)
