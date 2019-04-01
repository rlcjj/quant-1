import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.barra import Barra
from quant.utility.factor_neutral import FactorNeutral
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaSplitSample(Data):

    """
    Alpha因子直接剥离风险因子
    风险模型可以选择Barra模型、也可以选择自己的风险模型
    收益率也要拆分成分残差收益
    直接采用简单线性回归的方式
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_path = r'stock_data\alpha_model\split\sample_split'
        self.data_path = os.path.join(self.primary_data_path, self.sub_path)
        self.hdf_factor_path = os.path.join(self.data_path, "factor_hdf")
        self.csv_factor_path = os.path.join(self.data_path, "factor_csv")

    def get_alpha_res_exposure(self, factor_name):

        """ 得到残差Alpha的暴露 """

        data = Stock().read_factor_h5(factor_name, self.hdf_factor_path)
        return data

    def save_alpha_res_exposure(self, data, factor_name):

        """ 存储成为 CSV 和 HDF 两份 """

        Stock().write_factor_h5(data, factor_name, self.hdf_factor_path)
        data = self.get_alpha_res_exposure(factor_name)
        data.to_csv(os.path.join(self.csv_factor_path, '%s.csv' % factor_name))

    def split_alpha(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """计算每个换仓周期的因子收益率\计算因子残差暴露\因子与其他因子的相关性"""

        # get data
        period = period
        alpha_factor_name = factor_name
        year_number = Date().get_period_number_for_year(period)
        alpha = AlphaFactor().get_standard_alpha_factor(self.alpha_factor_name)
        stock_pool_name = stock_pool_name

        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        date_series = list(set(date_series) & set(self.alpha.columns))
        date_series.sort()

        for i_date in range(len(self.date_series) - 2):

            data_date = self.date_series[i_date]
            output = (self.alpha_factor_name, data_date, self.stock_pool_name)
            print("Split %s Alpha Return At %s %s" % output)

            alpha_date = pd.DataFrame(self.alpha[data_date])
            alpha_date.columns = ['Alpha']
            alpha_date = alpha_date.dropna()

            risk_exposure = Barra().get_factor_exposure_date(data_date, type_list=['STYLE', 'INDUSTRY'])
            stock_pool = Stock().get_invest_stock_pool(date=data_date, stock_pool_name=self.stock_pool_name)
            stock_pool = list(set(stock_pool) & set(risk_exposure.index) & set(alpha_date.index))
            stock_pool.sort()
            alpha_date = alpha_date.loc[stock_pool, "Alpha"]
            risk_exposure = risk_exposure.loc[stock_pool, :]

            if len(alpha_date) > self.min_stock_number:

                params, t_values, alpha_date_res = FactorNeutral().factor_exposure_neutral(alpha_date, risk_exposure)
                exposure_corr = FactorNeutral().factor_exposure_corr(alpha_date, risk_exposure)
                exposure_corr.columns = [data_date]
                self.corr = pd.concat([self.corr, exposure_corr], axis=1)
                self.alpha_res.loc[data_date, :] = alpha_date_res


if __name__ == "__main__":

    self = AlphaSplitSample()
    self.split_alpha()