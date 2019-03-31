import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaROA(AlphaFactor):

    """
    因子说明：ROA 资产收益率 盈利质量
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_roa'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        net_profit = Stock().read_factor_h5("NetProfitDeducted")
        asset = Stock().read_factor_h5("TotalAsset") / 100000000.0

        [net_profit, asset] = Stock().make_same_index_columns([net_profit, asset])
        roe = 4 * net_profit.div(asset)

        report_data = Stock().read_factor_h5("ReportDateDaily")
        roe = Stock().change_quarter_to_daily_with_disclosure_date(roe, report_data, beg_date, end_date)

        res = roe.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaROA()
    self.cal_factor_exposure(beg_date, end_date)
