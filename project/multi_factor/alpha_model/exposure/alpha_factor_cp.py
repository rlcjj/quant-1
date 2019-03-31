from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCP(AlphaFactor):

    """
    因子说明: -货币资金/总市值, 根据最新财报更新数据
    披露日期 为 最近财报
    表明因子估值能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cp'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        cash = Stock().read_factor_h5("CashEquivalents")
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        report_data = Stock().read_factor_h5("ReportDateDaily")

        # data precessing
        cash = Stock().change_quarter_to_daily_with_disclosure_date(cash, report_data, beg_date, end_date)
        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust) / 100000000
        [cash, total_mv] = Stock().make_same_index_columns([cash, total_mv])
        cp = 4 * cash.div(total_mv)

        # save data
        cp = cp.T.dropna(how='all').T
        self.save_alpha_factor_exposure(cp, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCP()
    self.cal_factor_exposure(beg_date, end_date)
