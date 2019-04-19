from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCIF(AlphaFactor):

    """
    因子说明：过去12个月经营活动现金流入小计
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cif'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        cfo = Stock().read_factor_h5("SubTotalOperateCashInflow")
        cfo_ttm = Stock().change_single_quarter_to_ttm_quarter(cfo)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        cfo_ttm = Stock().change_quarter_to_daily_with_disclosure_date(cfo_ttm, report_data, beg_date, end_date)

        res = cfo_ttm.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCIF()
    self.cal_factor_exposure(beg_date, end_date)
