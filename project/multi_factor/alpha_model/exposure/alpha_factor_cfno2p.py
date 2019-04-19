from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaCFNO2P(AlphaFactor):

    """
    因子说明: 净经营性现金流TTM /总市值
    表明因子估值能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_cfno2p'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        cfo = Stock().read_factor_h5("NetOperateCashFlow")
        cfo_ttm = Stock().change_single_quarter_to_ttm_quarter(cfo)

        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        report_data = Stock().read_factor_h5("ReportDateDaily")

        # data precessing
        cfo_ttm = Stock().change_quarter_to_daily_with_disclosure_date(cfo_ttm, report_data, beg_date, end_date)
        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust) / 100000000
        [cfo_ttm, total_mv] = Stock().make_same_index_columns([cfo_ttm, total_mv])
        cfno2p = cfo_ttm.div(total_mv)

        # save data
        cfno2p = cfno2p.T.dropna(how='all').T
        self.save_alpha_factor_exposure(cfno2p, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaCFNO2P()
    self.cal_factor_exposure(beg_date, end_date)
