from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraEarningYield(RiskFactor):

    """
    预期盈利 / 总市值
    经营性现金流净额 / 总市值
    归母净利润TTM / 总市值
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.factor_name = 'cne5_normal_earning_yield'

        self.factor_name_predicted = 'cne5_normal_earning_yield_predicted'
        self.raw_factor_name_predicted = 'cne5_raw_earning_yield_predicted'
        self.factor_name_cash = 'cne5_normal_earning_yield_cash'
        self.raw_factor_name_cash = 'cne5_raw_earning_yield_cash'
        self.factor_name_trailing = 'cne5_normal_earning_yield_trailing'
        self.raw_factor_name_trailing = 'cne5_raw_earning_yield_trailing'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_predicted_earnings_to_price_ratio(self):

        """ 预期盈利 / 总市值 """

        e1_predicted = Stock().read_factor_h5("FE_1")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")

        e1_predicted, price_unadjust = FactorPreProcess().make_same_index_columns([e1_predicted, price_unadjust])
        ep1_predicted = e1_predicted.div(price_unadjust)
        ep1_predicted = ep1_predicted.T.dropna(how='all').T

        self.save_risk_factor_exposure(ep1_predicted, self.raw_factor_name_predicted)
        ep1_predicted = FactorPreProcess().remove_extreme_value_mad(ep1_predicted)
        ep1_predicted = FactorPreProcess().standardization(ep1_predicted)
        self.save_risk_factor_exposure(ep1_predicted, self.factor_name_predicted)

    def cal_cash_earnings_to_price_ratio(self, beg_date, end_date):

        """ 经营性现金流净额 / 总市值 """

        nocf = Stock().read_factor_h5("NetOperateCashFlow")
        report_data = Stock().read_factor_h5("ReportDateDaily")
        nocf = Stock().change_single_quarter_to_ttm_quarter(nocf)
        nocf = Stock().change_quarter_to_daily_with_disclosure_date(nocf, report_data, beg_date, end_date)
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")

        result = FactorPreProcess().make_same_index_columns([nocf, total_share, price_unadjust])
        nocf, total_share, price_unadjust = result
        total_mv = total_share.mul(price_unadjust) / 100000000
        nocf_mv = nocf.div(total_mv)

        nocf_mv = nocf_mv.T.dropna(how='all').T
        self.save_risk_factor_exposure(nocf_mv, self.raw_factor_name_cash)
        nocf_mv = FactorPreProcess().remove_extreme_value_mad(nocf_mv)
        nocf_mv = FactorPreProcess().standardization(nocf_mv)
        self.save_risk_factor_exposure(nocf_mv, self.factor_name_cash)

    def cal_trailing_earnings_to_price_ratio(self):

        """ 归母净利润TTM / 总市值 """

        pe_ttm = Stock().read_factor_h5("PE_ttm")
        ep_ttm = 1.0 / pe_ttm

        ep_ttm = ep_ttm.T.dropna(how='all').T
        self.save_risk_factor_exposure(ep_ttm, self.raw_factor_name_trailing)
        ep_ttm = FactorPreProcess().remove_extreme_value_mad(ep_ttm)
        ep_ttm = FactorPreProcess().standardization(ep_ttm)
        self.save_risk_factor_exposure(ep_ttm, self.factor_name_trailing)

    def cal_factor_exposure(self, beg_date, end_date):

        """
        原始：0.68 * 未来一年预期盈利 / 总市值 +  0.21 * 经营性现金流净额TTM / 总市值 + 0.11 * 归母净利润TTM / 总市值
        由于A股预期数据质量不高 调整三项数据占比 为 0.50 0.30 0.20
        """

        self.cal_predicted_earnings_to_price_ratio()
        self.cal_cash_earnings_to_price_ratio(beg_date, end_date)
        self.cal_trailing_earnings_to_price_ratio()

        predicted_ep = 0.50 * self.get_risk_factor_exposure(self.factor_name_predicted)
        cp = 0.30 * self.get_risk_factor_exposure(self.factor_name_cash)
        ep = 0.20 * self.get_risk_factor_exposure(self.factor_name_trailing)

        earning_yield = predicted_ep.add(cp, fill_value=0.0)
        earning_yield = earning_yield.add(ep, fill_value=0.0)

        earning_yield = FactorPreProcess().remove_extreme_value_mad(earning_yield)
        earning_yield = FactorPreProcess().standardization(earning_yield)
        self.save_risk_factor_exposure(earning_yield, self.factor_name)


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = RiskFactorBarraEarningYield()
    # self.update_data()
    self.cal_factor_exposure(beg_date, end_date)
