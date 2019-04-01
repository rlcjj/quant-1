from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaRetain2P(AlphaFactor):

    """
    因子说明: 留存收益/总市值, 根据最新财报更新数据
    表明因子估值能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_retain2p'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        retain = Stock().read_factor_h5("RetainedEarnings")
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        report_data = Stock().read_factor_h5("ReportDateDaily")

        # data precessing
        retain = Stock().change_quarter_to_daily_with_disclosure_date(retain, report_data, beg_date, end_date)
        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust) / 100000000
        [retain, total_mv] = Stock().make_same_index_columns([retain, total_mv])
        retain2p = 4 * retain.div(total_mv)

        # save data
        retain2p = retain2p.T.dropna(how='all').T
        self.save_alpha_factor_exposure(retain2p, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaRetain2P()
    self.cal_factor_exposure(beg_date, end_date)
