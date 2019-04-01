from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaSPTTM(AlphaFactor):

    """
    因子说明：营收收入 / 总市值
    TTM 为不同一财报期 最近可以得到的最新财报
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_sp_ttm'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        income = Stock().read_factor_h5("OperatingIncome")
        income = Stock().change_single_quarter_to_ttm_quarter(income)
        report_data = Stock().read_factor_h5("ReportDateDaily")
        income = Stock().change_quarter_to_daily_with_disclosure_date(income, report_data, beg_date, end_date)

        # data precessing
        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust) / 100000000
        [income, total_mv] = Stock().make_same_index_columns([income, total_mv])
        sp = income.div(total_mv)

        # save data
        sp = sp.T.dropna(how='all').T
        self.save_alpha_factor_exposure(sp, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaSPTTM()
    self.cal_factor_exposure(beg_date, end_date)
