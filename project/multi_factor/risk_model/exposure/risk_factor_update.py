from datetime import datetime
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.stock.macro import Macro

from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_size import RiskFactorBarraSize
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_beta import RiskFactorBarraBeta
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_bp import RiskFactorBarraBP
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_cube_size import RiskFactorBarraCubeSize
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_growth import RiskFactorBarraGrowth
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_leverage import RiskFactorBarraLeverage
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_liquidity import RiskFactorBarraLiquidity
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_momentum import RiskFactorBarraMomentum
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_residual_volatility import RiskFactorBarraResVol
from quant.project.multi_factor.risk_model.exposure.risk_factor_barra_earning_yield import RiskFactorBarraEarningYield

from quant.project.multi_factor.risk_model.exposure.risk_factor_gem import RiskFactorGEM
from quant.project.multi_factor.risk_model.exposure.risk_factor_fund_etf_holder import RiskFactorFundETFHolder


class RiskFactorUpdate(object):

    """ 更新所有风险因子 """

    def __init__(self):
        pass

    @staticmethod
    def load_data(beg_date, end_date):

        """ 下载所有风险因子需要的数据 """

        print("######## Begin Update Risk Factor Need Data ########")
        # Stock().load_h5_primary_factor()
        Index().load_index_factor(index_code='881001.WI', beg_date=beg_date, end_date=end_date)
        Index().load_index_factor(index_code='000985.CSI', beg_date=beg_date, end_date=end_date)
        Macro().load_daily_risk_free_rate(beg_date, end_date)

    @staticmethod
    def cal_risk_factor_exposure(beg_date, end_date):

        """
        计算所有风险因子暴露
        最浪费时间的是beta的计算 然后是resvol的计算
        """

        print("######## Begin Update Risk Factor Exposure ########")

        RiskFactorBarraSize().cal_factor_exposure()
        RiskFactorBarraBeta().cal_factor_exposure(beg_date, end_date)
        RiskFactorBarraBP().cal_factor_exposure()
        RiskFactorBarraCubeSize().cal_factor_exposure(beg_date, end_date)
        RiskFactorBarraEarningYield().cal_factor_exposure(beg_date, end_date)
        RiskFactorBarraGrowth().cal_factor_exposure(beg_date, end_date)
        RiskFactorBarraLeverage().cal_factor_exposure()
        RiskFactorBarraLiquidity().cal_factor_exposure(beg_date, end_date)
        RiskFactorBarraMomentum().cal_factor_exposure(beg_date, end_date)
        RiskFactorBarraResVol().cal_factor_exposure(beg_date, end_date)

        RiskFactorFundETFHolder().cal_factor_exposure(beg_date, end_date)
        RiskFactorGEM().cal_factor_exposure(beg_date, end_date)

    def update_risk_factor(self):

        """
        下载所有风险因子需要的数据
        计算所有风险因子暴露
        """

        end_date = datetime.today()
        beg_date = Date().get_trade_date_offset(end_date, -20)
        self.load_data(beg_date, end_date)

        end_date = datetime.today()
        beg_date = Date().get_trade_date_offset(end_date, -10)
        self.cal_risk_factor_exposure(beg_date, end_date)


if __name__ == '__main__':

    self = RiskFactorUpdate()
    self.update_risk_factor()
