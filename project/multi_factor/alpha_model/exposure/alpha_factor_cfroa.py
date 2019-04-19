from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCFROA(AlphaFactor):

    """
    因子说明：CFNO_TTM / 总资产
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cf_roa'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        cfo = Stock().read_factor_h5("NetOperateCashFlow")
        cfo_ttm = Stock().change_single_quarter_to_ttm_quarter(cfo)

        asset = Stock().read_factor_h5("TotalAsset") / 100000000.0
        asset_ttm = Stock().change_single_quarter_to_ttm_quarter(asset) / 4.0

        [cfo_ttm, asset_ttm] = Stock().make_same_index_columns([cfo_ttm, asset_ttm])
        roa = cfo_ttm.div(asset_ttm)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        roa = Stock().change_quarter_to_daily_with_disclosure_date(roa, report_data, beg_date, end_date)

        res = roa.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCFROA()
    self.cal_factor_exposure(beg_date, end_date)
