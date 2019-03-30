import numpy as np

from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraSize(RiskFactor):

    """
    因子说明 计算总市值的对数值
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'cne5_raw_size'
        self.factor_name = 'cne5_normal_size'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_exposure(self):

        """ 计算因子暴露 """

        # read data
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        total_share = Stock().read_factor_h5("TotalShare")

        # calculate data
        [price_unadjust, total_share] = FactorPreProcess().make_same_index_columns([price_unadjust, total_share])
        total_market_value = price_unadjust.mul(total_share) / 100000000
        log_size_data = np.log(total_market_value)

        # save data
        self.save_risk_factor_exposure(log_size_data, self.raw_factor_name)
        log_size_data = FactorPreProcess().remove_extreme_value_mad(log_size_data)
        log_size_data = FactorPreProcess().standardization(log_size_data)
        self.save_risk_factor_exposure(log_size_data, self.factor_name)


if __name__ == "__main__":

    self = RiskFactorBarraSize()
    self.update_data()
    self.cal_factor_exposure()
