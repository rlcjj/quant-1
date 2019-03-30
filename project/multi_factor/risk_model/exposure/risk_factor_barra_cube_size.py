import os
import pandas as pd
import statsmodels.api as sm
from datetime import datetime

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraCubeSize(RiskFactor):

    """
    因子说明
    市值因子的立方和市值因子回归取残差 再去极值和标准化
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.factor_name = 'cne5_normal_cube_size'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_exposure(self, beg_date=None, end_date=None):

        """ 计算因子暴露 """

        # read data
        size_data = self.get_risk_factor_exposure("cne5_normal_size")
        square_size_data = size_data ** 3

        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(size_data.columns))
        date_series.sort()
        res_data = pd.DataFrame([])

        # calculate everyday
        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print('Calculating Barra Risk factor %s at date %s' % (self.factor_name, date))
            regression_data = pd.concat([size_data[date], square_size_data[date]], axis=1)
            regression_data.columns = ['x', 'y']
            regression_data = regression_data.dropna()
            y = regression_data['y'].values
            x = regression_data['x'].values
            x_add = sm.add_constant(x)
            model = sm.OLS(y, x_add).fit()
            regression_data['res'] = regression_data['y'] - model.fittedvalues
            res_data_date = pd.DataFrame(regression_data['res'])
            res_data_date.columns = [date]
            res_data = pd.concat([res_data, res_data_date], axis=1)

        res_data = res_data.T.dropna(how='all').T
        res_data = FactorPreProcess().remove_extreme_value_mad(res_data)
        res_data = FactorPreProcess().standardization(res_data)
        self.save_risk_factor_exposure(res_data, self.factor_name)


if __name__ == "__main__":

    beg_date = '20040101'
    end_date = datetime.today()

    self = RiskFactorBarraCubeSize()
    # self.update_data()
    self.cal_factor_exposure(beg_date, end_date)
