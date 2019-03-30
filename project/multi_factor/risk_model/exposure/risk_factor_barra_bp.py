from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraBP(RiskFactor):

    """
    因子说明: 净资产/总市值, 根据最新财报更新数据
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'cne5_raw_bp'
        self.factor_name = 'cne5_normal_bp'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_exposure(self):

        """ 计算因子暴露 """

        # read data
        holder = Stock().read_factor_h5("TotalShareHoldeRequityDaily")
        total_share = Stock().read_factor_h5("TotalShare")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")

        # data precessing
        [total_share, price_unadjust] = FactorPreProcess().make_same_index_columns([total_share, price_unadjust])
        total_mv = total_share.mul(price_unadjust)
        [holder, total_mv] = Stock().make_same_index_columns([holder, total_mv])
        holder_price = holder.div(total_mv)

        # save data
        pb_data = holder_price.T.dropna(how='all').T
        self.save_risk_factor_exposure(pb_data, self.raw_factor_name)
        pb_data = FactorPreProcess().remove_extreme_value_mad(pb_data)
        pb_data = FactorPreProcess().standardization(pb_data)
        self.save_risk_factor_exposure(pb_data, self.factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = RiskFactorBarraBP()
    self.update_data()
    self.cal_factor_exposure()
