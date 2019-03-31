from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaGrossProfitYoY(AlphaFactor):

    """
    因子说明: 当季毛利润的同比增长
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_gross_profit_yoy'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        income = Stock().read_factor_h5("OperatingIncome").T
        cost = Stock().read_factor_h5("OperatingCost").T
        [income, cost] = Stock().make_same_index_columns([income, cost])
        gross_profit = income.sub(cost)
        gross_profit_4 = gross_profit.shift(4)
        profit_yoy = gross_profit / gross_profit_4 - 1.0

        profit_yoy = profit_yoy.T
        report_data = Stock().read_factor_h5("ReportDateDaily")
        profit_yoy = Stock().change_quarter_to_daily_with_disclosure_date(profit_yoy, report_data, beg_date, end_date)

        res = profit_yoy.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaGrossProfitYoY()
    self.cal_factor_exposure(beg_date, end_date)
