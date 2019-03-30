from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaEP(AlphaFactor):

    """
    因子说明: 最近季度净利润/总市值, 根据最新财报更新数据
    披露日期 为 最近财报
    表明因子估值能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_ep'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        profit = Stock().read_factor_h5("NetProfitDeductedDaily")
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")

        # data precessing
        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust) / 100000000
        [profit, total_mv] = Stock().make_same_index_columns([profit, total_mv])
        ep = 4 * profit.div(total_mv)

        # save data
        ep = ep.T.dropna(how='all').T
        self.save_risk_factor_exposure(ep, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaEP()
    self.cal_factor_exposure(beg_date, end_date)
