import pandas as pd

from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaATBias(AlphaFactor):

    """
    总资产周转率环减 Asset TurnOver Bias
    因子说明：当季度（营业收入TTM / 总资产加权）- 本季度（营业收入TTM / 总资产加权）
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_at_bias'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        income = Stock().read_factor_h5("OperatingIncome")
        total_asset = Stock().read_factor_h5("TotalAsset") / 100000000
        report_data = Stock().read_factor_h5("ReportDateDaily")
        income_ttm = Stock().change_single_quarter_to_ttm_quarter(income)
        total_asset = Stock().change_single_quarter_to_ttm_quarter(total_asset) / 4.0

        turnover = income_ttm.div(total_asset)
        at_bias = turnover.T.diff().T
        at_bias = Stock().change_quarter_to_daily_with_disclosure_date(at_bias, report_data, beg_date, end_date)

        at_bias = at_bias.T.dropna(how='all').T
        self.save_alpha_factor_exposure(at_bias, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaATBias()
    self.cal_factor_exposure(beg_date, end_date)
