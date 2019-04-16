from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaResearch2Income(AlphaFactor):

    """
    因子说明：研发费用TTM/总营收
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_research2income'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        research = Stock().read_factor_h5("ResearchDevelopmentExpense")
        research = research.fillna(0.0)
        income = Stock().read_factor_h5("OperatingIncome")

        research_ttm = Stock().change_single_quarter_to_ttm_quarter(research)
        income_ttm = Stock().change_single_quarter_to_ttm_quarter(income) / 4.0

        [research_ttm, income_ttm] = Stock().make_same_index_columns([research_ttm, income_ttm])
        roa = research_ttm.div(income_ttm)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        roa = Stock().change_quarter_to_daily_with_disclosure_date(roa, report_data, beg_date, end_date)

        res = roa.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaResearch2Income()
    self.cal_factor_exposure(beg_date, end_date)
