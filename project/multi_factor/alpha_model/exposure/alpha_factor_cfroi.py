from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCFROI(AlphaFactor):

    """
    因子说明：(经营性净现金流_TTM + 财务费用_TTM) * (1-税率) / (股东权益 + 债务 - 现金)
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cf_roi'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        cfo = Stock().read_factor_h5("NetOperateCashFlow")
        cfo_ttm = Stock().change_single_quarter_to_ttm_quarter(cfo)

        expense = Stock().read_factor_h5("FinanceExpenseQuarter")
        expense_ttm = Stock().change_single_quarter_to_ttm_quarter(expense) / 100000000.0

        tax_rate = Stock().read_factor_h5("TaxRate")
        tax_rate = tax_rate.T.fillna(method="pad", limit=5).T

        expense_ttm_adjust = expense_ttm.mul(1 - tax_rate)
        cfo_ttm_adjust = cfo_ttm.add(expense_ttm_adjust)

        holder = Stock().read_factor_h5("TotalShareHoldeRequity") / 100000000.0
        debt = Stock().read_factor_h5("InterestDebt") / 100000000.0
        cash = Stock().read_factor_h5("CashEquivalents") / 100000000.0
        operate_net_asset = holder + debt - cash

        cfroi = cfo_ttm_adjust.div(operate_net_asset)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        cfroi = Stock().change_quarter_to_daily_with_disclosure_date(cfroi, report_data, beg_date, end_date)

        res = cfroi.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCFROI()
    self.cal_factor_exposure(beg_date, end_date)
