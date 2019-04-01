import os
import numpy as np
import pandas as pd

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
        self.sub_path = r'stock_data\alpha_model\split'
        self.data_path = os.path.join(self.primary_data_path, self.sub_path)
        self.hdf_res_path = os.path.join(self.data_path, "res_alpha\hdf")
        self.csv_res_path = os.path.join(self.data_path, "res_alpha\csv")
        self.hdf_risk_path = os.path.join(self.data_path, "exposure_risk\hdf")
        self.csv_risk_path = os.path.join(self.data_path, "exposure_risk\csv")
        self.min_stock_number = 100

    def get_alpha_res_exposure(self, factor_name):

        """ 得到残差Alpha的暴露 """

        data = Stock().read_factor_h5(factor_name, self.hdf_res_path)
        return data

    def get_alpha_risk_exposure(self, factor_name):

        """ 得到Alpha在风险因子上的暴露 """

        data = Stock().read_factor_h5(factor_name, self.hdf_risk_path)
        print(data)
        return data

    def save_alpha_res_exposure(self, data, factor_name):

        """ 残差Alpha的暴露 存储成为 CSV 和 HDF 两份 """

        Stock().write_factor_h5(data, factor_name, self.hdf_res_path)
        data = self.get_alpha_res_exposure(factor_name)
        data.to_csv(os.path.join(self.csv_res_path, '%s.csv' % factor_name))

    def save_alpha_risk_exposure(self, data, factor_name):

        """ Alpha在风险因子上的暴露 存储成为 CSV 和 HDF 两份 """

        Stock().write_factor_h5(data, factor_name, self.hdf_risk_path)
        data = self.get_alpha_risk_exposure(factor_name)
        data.to_csv(os.path.join(self.csv_risk_path, '%s.csv' % factor_name))

    def split_alpha(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 计算残差Alpha 回归风格因子和行业 计算在风格和行业上的暴露 """

        alpha = AlphaFactor().get_standard_alpha_factor(factor_name)
        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        date_series = list(set(date_series) & set(alpha.columns))
        date_series.sort()

        res_alpha = pd.DataFrame()
        exposure_risk = pd.DataFrame()

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print("Split %s Alpha Exposure At %s %s" % (factor_name, date, stock_pool_name))

            alpha_date = pd.DataFrame(alpha[date])
            alpha_date.columns = ['Alpha']
            alpha_date = alpha_date.dropna()

            risk_exposure = Barra().get_factor_exposure_date(date, type_list=['STYLE', 'INDUSTRY'])

            stock_pool = Stock().get_invest_stock_pool(date=date, stock_pool_name=stock_pool_name)
            stock_pool = list(set(stock_pool) & set(risk_exposure.index) & set(alpha_date.index))
            stock_pool.sort()

            alpha_date = alpha_date.loc[stock_pool, "Alpha"]
            risk_exposure = risk_exposure.loc[stock_pool, :]

            if len(alpha_date) > self.min_stock_number:

                params, t_values, res_alpha_date = FactorNeutral().factor_exposure_neutral(alpha_date, risk_exposure)
                params = pd.DataFrame(params)
                params.columns = [date]
                res_alpha_date = pd.DataFrame(res_alpha_date)
                res_alpha_date.columns = [date]

            exposure_risk = pd.concat([exposure_risk, params], axis=1)
            res_alpha = pd.concat([res_alpha, res_alpha_date], axis=1)

        self.save_alpha_risk_exposure(exposure_risk, factor_name)
        self.save_alpha_res_exposure(res_alpha, factor_name)

    def split_alpha_all(self, beg_date, end_date, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 拆分所有Alpha """

        alpha_factor_list = AlphaFactor().get_all_alpha_factor_name()

        for alpha_name in alpha_factor_list:

            self.split_alpha(beg_date, end_date, alpha_name, period, stock_pool_name)


if __name__ == "__main__":

    from datetime import datetime

    self = AlphaSplitSample()
    beg_date, end_date, period = "20040101", datetime.today().strftime("%Y%m%d"), "W"
    stock_pool_name = "AllChinaStockFilter"

    # factor_name = "alpha_raw_ep"
    # self.split_alpha(beg_date, end_date, factor_name, period, stock_pool_name)

    self.split_alpha_all(beg_date, end_date, period, stock_pool_name)
