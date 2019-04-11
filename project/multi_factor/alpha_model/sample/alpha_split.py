import os
import pandas as pd
import statsmodels.api as sm

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.barra import Barra
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaSplit(Data):

    """
    1、直接采用简单线性回归的方式，计算Alpha残差暴露
    2、计算Alpha在风险因子上的暴露程度
    3、计算残差Alpha暴露的稳定性
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_path = r'stock_data\alpha_model\split'
        self.data_path = os.path.join(self.primary_data_path, self.sub_path)
        self.min_stock_number = 0

    def get_all_alpha_factor_name(self, stock_pool_name):

        """ 得到所有Alpha的名字 """

        hdf_res_path = os.path.join(self.data_path, stock_pool_name, "res_alpha\hdf")
        file_list = os.listdir(hdf_res_path)
        factor_name_list = list(map(lambda x: x[0:-3], file_list))
        return factor_name_list

    def get_alpha_res_exposure(self, factor_name, stock_pool_name):

        """ 得到残差Alpha的暴露 """

        hdf_res_path = os.path.join(self.data_path, stock_pool_name, "res_alpha\hdf")
        data = Stock().read_factor_h5(factor_name, hdf_res_path)
        return data

    def get_alpha_risk_exposure(self, factor_name, stock_pool_name):

        """ 得到Alpha在风险因子上的暴露 """

        hdf_risk_path = os.path.join(self.data_path, stock_pool_name, "exposure_risk\hdf")
        data = Stock().read_factor_h5(factor_name, hdf_risk_path)
        return data

    def save_alpha_res_exposure(self, data, factor_name, stock_pool_name):

        """ 残差Alpha的暴露 存储成为 CSV 和 HDF 两份 """

        hdf_res_path = os.path.join(self.data_path, stock_pool_name, "res_alpha\hdf")
        csv_res_path = os.path.join(self.data_path, stock_pool_name, "res_alpha\csv")

        if not os.path.exists(hdf_res_path):
            os.makedirs(hdf_res_path)
        if not os.path.exists(csv_res_path):
            os.makedirs(csv_res_path)

        Stock().write_factor_h5(data, factor_name, hdf_res_path)
        data = self.get_alpha_res_exposure(factor_name, stock_pool_name)
        data.to_csv(os.path.join(csv_res_path, '%s.csv' % factor_name))

    def save_alpha_risk_exposure(self, data, factor_name, stock_pool_name):

        """ Alpha在风险因子上的暴露 存储成为 CSV 和 HDF 两份 """

        hdf_risk_path = os.path.join(self.data_path, stock_pool_name, "exposure_risk\hdf")
        csv_risk_path = os.path.join(self.data_path, stock_pool_name, "exposure_risk\csv")
        if not os.path.exists(hdf_risk_path):
            os.makedirs(hdf_risk_path)
        if not os.path.exists(csv_risk_path):
            os.makedirs(csv_risk_path)
        Stock().write_factor_h5(data, factor_name, hdf_risk_path)
        data = self.get_alpha_risk_exposure(factor_name, stock_pool_name)
        data.to_csv(os.path.join(csv_risk_path, '%s.csv' % factor_name))

    def get_alpha_res_corr(self, factor_name, beg_date, end_date, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 计算残差暴露前后两期平均相关性 """

        alpha_res = self.get_alpha_res_exposure(factor_name, stock_pool_name)
        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        date_series = list(set(date_series) & set(alpha_res.columns))
        date_series.sort()
        data = alpha_res.loc[:, date_series]

        corr = pd.DataFrame([], index=date_series, columns=['Corr'])

        for i in range(len(data.columns)-1):
            date = data.columns[i]
            date_next = data.columns[i + 1]
            data_date = pd.concat([data[date], data[date_next]], axis=1)
            data_date = data_date.dropna()
            corr.loc[date, "Corr"] = data_date.corr().iloc[0, 1]
        corr_mean = corr.mean().values[0]
        return corr_mean

    def split_alpha(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 计算残差Alpha 回归风格因子和行业 计算在风格和行业上的暴露 """

        alpha = AlphaFactor().get_standard_alpha_factor(factor_name)
        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        barra_date_series = Barra().get_exposure_date_series()
        date_series = list(set(date_series) & set(alpha.columns) & set(barra_date_series))
        date_series.sort()

        res_alpha = pd.DataFrame()
        exposure_risk = pd.DataFrame()

        for i_date in range(len(date_series)):

            date = date_series[i_date]

            alpha_date = pd.DataFrame(alpha[date])
            alpha_date.columns = ['Alpha']
            alpha_date = alpha_date.dropna()

            risk_exposure = Barra().get_factor_exposure_date(date, type_list=['STYLE', 'INDUSTRY', "COUNTRY"])

            stock_pool = Stock().get_invest_stock_pool(date=date, stock_pool_name=stock_pool_name)
            stock_pool = list(set(stock_pool) & set(risk_exposure.index) & set(alpha_date.index))
            stock_pool.sort()

            alpha_date = alpha_date.loc[stock_pool, "Alpha"]
            risk_exposure = risk_exposure.loc[stock_pool, :]

            concat_data = pd.concat([alpha_date, risk_exposure], axis=1)
            concat_data = concat_data.dropna()

            if len(concat_data) > self.min_stock_number:

                factor_val = concat_data.iloc[:, 0]
                neutral_val = concat_data.iloc[:, 1:]
                print("Split %s Alpha Exposure At %s %s" % (factor_name, date, stock_pool_name))

                model = sm.OLS(factor_val.values, neutral_val.values)
                regress = model.fit()

                params = pd.DataFrame(regress.params, index=neutral_val.columns, columns=['param'])
                factor_res = factor_val - regress.predict(neutral_val)

                params = pd.DataFrame(params)
                params.columns = [date]
                res_alpha_date = pd.DataFrame(factor_res)
                res_alpha_date.columns = [date]

                exposure_risk = pd.concat([exposure_risk, params], axis=1)
                res_alpha = pd.concat([res_alpha, res_alpha_date], axis=1)

            else:
                print("Split %s Alpha Exposure At %s %s is Null" % (factor_name, date, stock_pool_name))

        res_alpha = FactorPreProcess().remove_extreme_value_mad(res_alpha)
        res_alpha = FactorPreProcess().standardization(res_alpha)
        self.save_alpha_risk_exposure(exposure_risk, factor_name, stock_pool_name)
        self.save_alpha_res_exposure(res_alpha, factor_name, stock_pool_name)

    def split_alpha_all(self, beg_date, end_date, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 拆分所有Alpha """

        alpha_factor_list = AlphaFactor().get_all_alpha_factor_name()
        for i in range(0, len(alpha_factor_list)):
            alpha_name = alpha_factor_list[i]
            self.split_alpha(beg_date, end_date, alpha_name, period, stock_pool_name)


if __name__ == "__main__":

    """ 参数 """

    self = AlphaSplit()
    beg_date, end_date, period = "20040101", "20190329", "W"
    stock_pool_name = "AllChinaStockFilter"
    factor_name = "alpha_raw_sue0"

    """ 计算单个因子 """

    self.split_alpha(beg_date, end_date, factor_name, period, "AllChinaStockFilter")
    self.split_alpha(beg_date, end_date, factor_name, period, "hs300")
    self.split_alpha(beg_date, end_date, factor_name, period, "zz500")
    print(self.get_alpha_res_corr(factor_name, beg_date, end_date, period, stock_pool_name))
    print(self.get_alpha_risk_exposure(factor_name, stock_pool_name))

    """ 计算所有因子 """

    # self.split_alpha_all(beg_date, end_date, period, "AllChinaStockFilter")
    # self.split_alpha_all(beg_date, end_date, period, "hs300")
    # self.split_alpha_all(beg_date, end_date, period, "zz500")
