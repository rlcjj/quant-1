import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaAR2P(AlphaFactor):

    """
    因子说明：预收账款 / 总市值
    表征了股票的对下游的议价能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_ar2p'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        advance = Stock().read_factor_h5("AdvanceReceipts")
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        report_data = Stock().read_factor_h5("ReportDateDaily")

        # data precessing
        advance = Stock().change_quarter_to_daily_with_disclosure_date(advance, report_data, beg_date, end_date)
        [total_share, price_unadjust] = Stock().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust)
        [advance, total_mv] = Stock().make_same_index_columns([advance, total_mv])
        ar2p = advance.div(total_mv)

        res = ar2p.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaAR2P()
    self.cal_factor_exposure(beg_date, end_date)
