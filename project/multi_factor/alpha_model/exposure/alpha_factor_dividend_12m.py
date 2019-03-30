from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaDividend12m(AlphaFactor):

    """
    因子说明: 最近季度净利润/总市值, 根据最新财报更新数据
    披露日期 为 最近财报
    表明因子估值能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_dividend_12m'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        dividend_12m = Stock().read_factor_h5("dividendyield2")
        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)
        dividend_12m = dividend_12m.loc[:, beg_date:end_date]

        res = dividend_12m.T.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaDividend12m()
    self.cal_factor_exposure(beg_date, end_date)
