import numpy as np
import pandas as pd
import statsmodels.api as sm

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraLiquidity(RiskFactor):

    """
    流动性因子 LIQUIDITY
    LIQUIDITY = 0.35 * LIQUIDITY_STOM + 0.35 * LIQUIDITY_STOQ + 0.3 * LIQUIDITY_STOA
    LIQUIDITY 在对 SIZE 因子做回归取残差
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.factor_name = 'cne5_normal_liquidity'
        self.raw_factor_name_month = 'cne5_raw_liquidity_month'
        self.factor_name_month = 'cne5_normal_liquidity_month'
        self.raw_factor_name_quarter = 'cne5_raw_liquidity_quarter'
        self.factor_name_quarter = 'cne5_normal_liquidity_quarter'
        self.raw_factor_name_yearly = 'cne5_raw_liquidity_yearly'
        self.factor_name_yearly = 'cne5_normal_liquidity_yearly'


    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_liquidity_month(self):

        """ LIQUIDITY_STOM 最近21个交易日的换手率总和的对数值 """

        P = 21
        turnover_daily = Stock().read_factor_h5("TurnOver_Daily").T
        turnover_period = turnover_daily.rolling(window=P).sum().applymap(np.log)
        turnover_period = turnover_period.T.dropna(how='all')

        self.save_risk_factor_exposure(turnover_period, self.raw_factor_name_month)
        turnover_period = FactorPreProcess().remove_extreme_value_mad(turnover_period)
        turnover_period = FactorPreProcess().standardization(turnover_period)
        self.save_risk_factor_exposure(turnover_period, self.factor_name_month)

    def cal_factor_liquidity_quarter(self):

        """ LIQUIDITY_STOM 最近63个交易日的换手率总和的对数值 """

        P = 63
        turnover_daily = Stock().read_factor_h5("TurnOver_Daily").T
        turnover_period = turnover_daily.rolling(window=P).sum().applymap(np.log)
        turnover_period = turnover_period.T.dropna(how='all')

        self.save_risk_factor_exposure(turnover_period, self.raw_factor_name_quarter)
        turnover_period = FactorPreProcess().remove_extreme_value_mad(turnover_period)
        turnover_period = FactorPreProcess().standardization(turnover_period)
        self.save_risk_factor_exposure(turnover_period, self.factor_name_quarter)

    def cal_factor_liquidity_yearly(self):

        """ LIQUIDITY_STOM 最近252个交易日的换手率总和的对数值 """

        P = 252
        turnover_daily = Stock().read_factor_h5("TurnOver_Daily").T
        turnover_period = turnover_daily.rolling(window=P).sum().applymap(np.log)
        turnover_period = turnover_period.T.dropna(how='all')

        self.save_risk_factor_exposure(turnover_period, self.raw_factor_name_yearly)
        turnover_period = FactorPreProcess().remove_extreme_value_mad(turnover_period)
        turnover_period = FactorPreProcess().standardization(turnover_period)
        self.save_risk_factor_exposure(turnover_period, self.factor_name_yearly)

    def cal_factor_exposure(self, beg_date, end_date):

        """
        流动性因子 LIQUIDITY
        LIQUIDITY = 0.35 * LIQUIDITY_STOM + 0.35 * LIQUIDITY_STOQ + 0.3 * LIQUIDITY_STOA
        LIQUIDITY 在对 SIZE 因子做回归取残差
        """

        # params
        self.cal_factor_liquidity_month()
        self.cal_factor_liquidity_quarter()
        self.cal_factor_liquidity_yearly()

        # calculate
        turnover_month = 0.35 * self.get_risk_factor_exposure(self.factor_name_month)
        turnover_quarter = 0.35 * self.get_risk_factor_exposure(self.factor_name_quarter)
        turnover_yearly = 0.30 * self.get_risk_factor_exposure(self.factor_name_yearly)

        liquidity = turnover_month.add(turnover_quarter, fill_value=0.0)
        liquidity = liquidity.add(turnover_yearly, fill_value=0.0)
        liquidity = liquidity.T.dropna(how='all').T

        # get res of regression
        size_data = self.get_risk_factor_exposure("cne5_normal_size")
        [size_data, liquidity] = FactorPreProcess().make_same_index_columns([size_data, liquidity])

        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(liquidity.columns))
        date_series.sort()

        turnover_res = pd.DataFrame([])

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print('Calculating Barra Risk factor %s at date %s' % (self.factor_name, date))
            regression_data = pd.concat([size_data[date], liquidity[date]], axis=1)
            regression_data.columns = ['x', 'y']
            regression_data = regression_data.dropna()
            y = regression_data['y'].values
            x = regression_data['x'].values
            x_add = sm.add_constant(x)
            model = sm.OLS(y, x_add).fit()
            regression_data['res'] = regression_data['y'] - model.fittedvalues
            res_date = pd.DataFrame(regression_data['res'])
            res_date.columns = [date]
            turnover_res = pd.concat([turnover_res, res_date], axis=1)

        turnover_res = FactorPreProcess().remove_extreme_value_mad(turnover_res)
        turnover_res = FactorPreProcess().standardization(turnover_res)
        self.save_risk_factor_exposure(turnover_res, self.factor_name)


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = RiskFactorBarraLiquidity()
    # self.update_data()
    self.cal_factor_exposure(beg_date, end_date)
