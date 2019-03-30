from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaGprQoQ(AlphaFactor):

    """
    因子说明：毛利率TTM环比变动
    毛利率TTM = （营业收入TTM - 营业成本TTM）/ 营业收入TTM
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_gpr_qoq'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        income = Stock().read_factor_h5("OperatingIncome")
        cost = Stock().read_factor_h5("OperatingCost")
        report_data = Stock().read_factor_h5("ReportDateDaily")

        income_ttm = Stock().change_single_quarter_to_ttm_quarter(income).T
        cost_ttm = Stock().change_single_quarter_to_ttm_quarter(cost).T

        gross_profit_ttm = income_ttm.sub(cost_ttm)
        gross_profit_ratio = gross_profit_ttm.div(income_ttm)
        gpr_qoq = gross_profit_ratio.diff().T
        gpr_qoq = Stock(). change_quarter_to_daily_with_disclosure_date(gpr_qoq, report_data, beg_date, end_date)

        res = gpr_qoq.T.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaGprQoQ()
    self.cal_factor_exposure(beg_date, end_date)
