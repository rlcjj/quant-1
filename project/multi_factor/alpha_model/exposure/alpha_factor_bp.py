from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaBP(AlphaFactor):

    """
    因子说明: 净资产/总市值, 根据最新财报更新数据
    披露日期 为 最近财报
    表明因子估值能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_bp'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        holder = Stock().read_factor_h5("TotalShareHoldeRequity")
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        report_data = Stock().read_factor_h5("ReportDateDaily")

        # data precessing
        holder = Stock().change_quarter_to_daily_with_disclosure_date(holder, report_data, beg_date, end_date)
        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust)
        [holder, total_mv] = Stock().make_same_index_columns([holder, total_mv])
        bp = holder.div(total_mv)

        # save data
        bp = bp.T.dropna(how='all').T
        self.save_alpha_factor_exposure(bp, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaBP()
    self.cal_factor_exposure(beg_date, end_date)
