from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaResearch2Asset(AlphaFactor):

    """
    因子说明：研发费用TTM/总资产
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_research2asset'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        research = Stock().read_factor_h5("ResearchDevelopmentExpense")
        asset = Stock().read_factor_h5("TotalAsset")

        research_ttm = Stock().change_single_quarter_to_ttm_quarter(research)
        asset_ttm = Stock().change_single_quarter_to_ttm_quarter(asset) / 4.0

        [research_ttm, asset_ttm] = Stock().make_same_index_columns([research_ttm, asset_ttm])
        roa = research_ttm.div(asset_ttm)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        roa = Stock().change_quarter_to_daily_with_disclosure_date(roa, report_data, beg_date, end_date)

        res = roa.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaResearch2Asset()
    self.cal_factor_exposure(beg_date, end_date)
