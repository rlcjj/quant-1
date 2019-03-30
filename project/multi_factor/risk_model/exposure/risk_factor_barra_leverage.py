from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraLeverage(RiskFactor):

    """
    资产负债比 = 总负债/总资产
    市场杠杆 =（普通股市场价值（总市值）+ 优先股账面价值 + 长期负债账面价值）/普通股市场价值（总市值）
    账面杠杆 =（普通股账面价值+优先股账面价值+长期负债）/ 普通股账面价值
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.factor_name = 'cne5_normal_leverage'

        self.factor_name_debt_to_asset = 'cne5_normal_leverage_debt_to_asset'
        self.raw_factor_name_debt_to_asset = 'cne5_raw_leverage'
        self.factor_name_market_leverage = 'cne5_normal_leverage_market_leverage'
        self.raw_factor_name_market_leverage = 'cne5_raw_leverage_market_leverage'
        self.factor_name_book_leverage = 'cne5_normal_leverage_book_leverage'
        self.raw_factor_name_book_leverage = 'cne5_raw_leverage_book_leverage'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_barra_leverage_debt_to_asset(self):

        """ 资产负债比 = 总负债/总资产 """

        total_debt = Stock().read_factor_h5("TotalLiabilityDaily")
        total_asset = Stock().read_factor_h5('TotalAssetDaily')

        debt_to_asset = total_debt.div(total_asset)
        debt_to_asset = debt_to_asset.T.dropna(how='all').T

        self.save_risk_factor_exposure(debt_to_asset, self.raw_factor_name_debt_to_asset)
        debt_to_asset = FactorPreProcess().remove_extreme_value_mad(debt_to_asset)
        debt_to_asset = FactorPreProcess().standardization(debt_to_asset)
        self.save_risk_factor_exposure(debt_to_asset, self.factor_name_debt_to_asset)

    def cal_factor_barra_leverage_market_leverage(self):

        """
        市场杠杆 =（普通股市场价值 + 优先股账面价值 + 长期负债账面价值）/ 普通股市场价值
        """

        long_loan = Stock().read_factor_h5("LongTermLoanDaily")
        preferred_equity = Stock().read_factor_h5("PreferredEquityDaily")
        common_share = Stock().read_factor_h5("CommonShareDaily")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")

        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([common_share, price_unadjust])
        common_mv = total_share.mul(price_unadjust)

        add = common_mv.add(long_loan, fill_value=0.0)
        add = add.add(preferred_equity, fill_value=0.0)
        market_leverage = add.div(common_mv)

        market_leverage = market_leverage.T.dropna(how='all').T
        self.save_risk_factor_exposure(market_leverage, self.raw_factor_name_market_leverage)
        market_leverage = FactorPreProcess().remove_extreme_value_mad(market_leverage)
        market_leverage = FactorPreProcess().standardization(market_leverage)
        self.save_risk_factor_exposure(market_leverage, self.factor_name_market_leverage)

    def cal_factor_barra_leverage_book_leverage(self):

        """
        账面杠杆 =（普通股账面价值+优先股账面价值+长期负债）/ 普通股账面价值
        """
        holder_equity = Stock().read_factor_h5("TotalShareHoldeRequityDaily")
        preferred_equity = Stock().read_factor_h5("PreferredEquityDaily")
        common_equity = holder_equity.sub(preferred_equity)
        long_loan = Stock().read_factor_h5("LongTermLoanDaily")

        add = holder_equity.add(long_loan, fill_value=0.0)
        book_leverage = add.div(common_equity)

        book_leverage = book_leverage.T.dropna(how='all').T
        self.save_risk_factor_exposure(book_leverage, self.raw_factor_name_book_leverage)
        book_leverage = FactorPreProcess().remove_extreme_value_mad(book_leverage)
        book_leverage = FactorPreProcess().standardization(book_leverage)
        self.save_risk_factor_exposure(book_leverage, self.factor_name_book_leverage)

    def cal_factor_exposure(self):

        """ 合成因子 """

        self.cal_factor_barra_leverage_debt_to_asset()
        self.cal_factor_barra_leverage_market_leverage()
        self.cal_factor_barra_leverage_book_leverage()

        debt_to_asset = 0.35 * self.get_risk_factor_exposure(self.factor_name_debt_to_asset)
        market_leverage = 0.38 * self.get_risk_factor_exposure(self.factor_name_market_leverage)
        book_leverage = 0.27 * self.get_risk_factor_exposure(self.factor_name_book_leverage)

        leverage = debt_to_asset.add(market_leverage, fill_value=0.0)
        leverage = leverage.add(book_leverage, fill_value=0.0)

        leverage = FactorPreProcess().remove_extreme_value_mad(leverage)
        leverage = FactorPreProcess().standardization(leverage)
        self.save_risk_factor_exposure(leverage, self.factor_name)

if __name__ == '__main__':

    self = RiskFactorBarraLeverage()
    # self.update_data()
    self.cal_factor_exposure()
