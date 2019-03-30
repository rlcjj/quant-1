from datetime import datetime
import pandas as pd
import numpy as np
import shutil
import os

from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.factor_preprocess import FactorPreProcess


class Barra(Data):

    """
    下载 计算 得到 Barra 因子数据

    1、下载Barra数据
    load_barra_data()

    2、得到Barra数据
    get_factor_name()
    get_factor_return()
    get_stock_riskfactor_return_date()

    3、计算数据
    cal_barra_cum_factor_return()
    cal_stock_riskfactor_return_daily()
    cal_stock_covariance_period()

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'barra_data'
        self.load_from_path = "\\\\10.3.12.202\\fe\\risk_model\\"
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_barra_data(self):

        """
         从网盘下载 'BarraCovariance', 'BarraExposure', 'BarraFactorReturn',
        'BarraSpecificReturn', 'BarraSpecificRisk'
        """

        load_from_path = self.load_from_path
        load_to_path = self.data_path

        sub_list = ['BarraCovariance', 'BarraExposure']

        for i_sub in range(len(sub_list)):

            sub_path = sub_list[i_sub]
            sub_from_path = os.path.join(load_from_path, sub_path)
            sub_to_path = os.path.join(load_to_path, sub_path)

            if not os.path.exists(sub_to_path):
                os.makedirs(sub_to_path)

            from_file_list = list(os.listdir(sub_from_path))
            to_file_list = list(os.listdir(sub_to_path))

            update_file_list = list(set(from_file_list) - set(to_file_list))
            update_file_list.sort()

            for i_file in range(len(update_file_list)):
                file = update_file_list[i_file]
                from_file = os.path.join(sub_from_path, file)
                to_file = os.path.join(sub_to_path, file)
                shutil.copy(from_file, to_file)
                print(" Copy From %s To %s" % (from_file, to_file))

        sub_list = ['BarraFactorReturn', 'BarraSpecificReturn', 'BarraSpecificRisk']

        for i_sub in range(len(sub_list)):

            sub_path = sub_list[i_sub]
            sub_from_path = os.path.join(load_from_path, sub_path)
            sub_to_path = os.path.join(load_to_path, sub_path)

            if not os.path.exists(sub_to_path):
                os.makedirs(sub_to_path)

            from_file_list = list(os.listdir(sub_from_path))
            update_file_list = from_file_list
            update_file_list.sort()

            for i_file in range(len(update_file_list)):
                file = update_file_list[i_file]
                from_file = os.path.join(sub_from_path, file)
                to_file = os.path.join(sub_to_path, file)
                shutil.copy(from_file, to_file)
                print(" Copy From %s To %s" % (from_file, to_file))

    def cal_barra_cum_factor_return(self,
                                    beg_date="20000101",
                                    end_date=datetime.today().strftime("%Y%m%d")):

        """ 计算 barra 因子累计收益率 """

        type_list = ['COUNTRY', 'STYLE', 'INDUSTRY']
        sub_path = 'BarraCumFactorReturn'
        sub_to_path = os.path.join(self.data_path, sub_path)
        sub_to_file = os.path.join(sub_to_path, sub_path + '.csv')

        if not os.path.exists(sub_to_path):
            os.makedirs(sub_to_path)

        data = self.get_factor_return(beg_date, end_date, type_list)
        data = data.cumsum()
        data.to_csv(sub_to_file)
        return data

    def get_factor_name(self, type_list=["STYLE"]):

        """ 得到 barra 因子名 """

        filename = os.path.join(self.data_path, 'BarraName', "Barra_Name.xlsx")
        data = pd.read_excel(filename, encoding='gbk')
        data = data[data['TYPE'].map(lambda x: x in type_list)]
        return data

    def get_factor_return(self,
                          beg_date="20000101",
                          end_date=datetime.today().strftime("%Y%m%d"),
                          type_list=["STYLE"]):

        filename = os.path.join(self.data_path, 'BarraFactorReturn', 'BarraFactorReturn.csv')
        barra_factor_return = pd.read_csv(filename, index_col=[0], encoding='gbk')
        barra_factor_return = barra_factor_return.T
        barra_factor_return.index = barra_factor_return.index.map(Date().change_to_str)

        name = self.get_factor_name(type_list=type_list)
        barra_factor_name = name['NAME_EN'].values

        barra_factor_return = barra_factor_return[barra_factor_name]
        barra_factor_return = barra_factor_return[~barra_factor_return.index.duplicated()]
        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)
        barra_factor_return = barra_factor_return.ix[beg_date:end_date, :]

        return barra_factor_return

    def get_factor_exposure_date(self, date, type_list=["STYLE"]):

        """ 得到 barra 因子暴露值 """

        path = os.path.join(self.data_path, 'BarraExposure')
        date = Date().change_to_str(date)
        filename = os.path.join(path,  date + '.csv')

        name = self.get_factor_name(type_list=type_list)
        barra_factor_name = name['NAME_EN'].values

        if os.path.exists(filename):
            barra_factor_exposure = pd.read_csv(filename, index_col=[0], encoding='gbk')
            barra_factor_exposure = barra_factor_exposure[barra_factor_name]
        else:
            print('barra factor exposure_return at ', str(date), ' not exist ')
            return None

        return barra_factor_exposure

    def get_factor_exposure_average(self, beg_date, end_date, type_list=["STYLE"]):

        """ 得到 barra 因子暴露值平均值 """

        date_series = Date().get_trade_date_series(beg_date, end_date)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            exposure_add = self.get_factor_exposure_date(date, type_list=type_list)
            if i_date == 0:
                exposure = exposure_add
            else:
                exposure = exposure_add + exposure

        exposure /= len(date_series)
        return exposure

    def cal_stock_riskfactor_return_daily(self, beg_date, end_date):

        """
        计算 股票每一日 在行业 风格 上的
        收益 = 当日在风格、行业上的暴露 * 当日风格、行业的因子收益率
        """

        type_list = ['COUNTRY', 'STYLE', 'INDUSTRY']
        factor_return = self.get_factor_return(beg_date, end_date, type_list=type_list)
        path = os.path.join(self.data_path, 'BarraStockRiskReturn')

        for i_date in range(len(factor_return)):

            date = factor_return.index[i_date]
            exposure = self.get_factor_exposure_date(date, type_list=type_list)

            if len(exposure) != 0:

                print("Cal Stock Riskfactor Return Daily is %s" % date)
                factor_return_date = factor_return.ix[date, :]
                factor_return_mat = np.tile(factor_return_date.values, (len(exposure), 1))
                factor_return_mat = pd.DataFrame(factor_return_mat, index=exposure.index, columns=factor_return.columns)
                stock_factor_return = factor_return_mat.mul(exposure)
                file = os.path.join(path, date + '.csv')
                stock_factor_return.to_csv(file)

    def get_stock_riskfactor_return_date(self, date):

        """
        得到 股票每一日 在行业 风格 上的收益
        """

        date = Date().change_to_str(date)
        file = os.path.join(self.data_path, 'BarraStockRiskReturn',  date + '.csv')

        if os.path.exists(file):
            stock_factor_return = pd.read_csv(file, index_col=[0], encoding='gbk')
        else:
            stock_factor_return = pd.DataFrame([])
        return stock_factor_return

    def get_stock_residual_return(self):

        """ 得到 股票 每日 残差收益 """

        file = os.path.join(self.data_path, 'BarraSpecificReturn', 'BarraSpecificReturn.csv')

        if os.path.exists(file):
            stock_residual_return = pd.read_csv(file, index_col=[0], encoding='gbk')
            stock_residual_return = stock_residual_return.T
            stock_residual_return.index = stock_residual_return.index.map(Date().change_to_str)
            stock_residual_return = stock_residual_return[~stock_residual_return.index.duplicated()]
            stock_residual_return *= 100
        else:
            stock_residual_return = pd.DataFrame([])

        return stock_residual_return

    def get_stock_residual_risk(self):

        """ 得到 股票 每日 残差方差 """

        file = os.path.join(self.data_path, 'BarraSpecificRisk', 'BarraSpecificRisk.csv')

        if os.path.exists(file):
            stock_residual_risk = pd.read_csv(file, index_col=[0], encoding='gbk')
            stock_residual_risk = stock_residual_risk.T
            stock_residual_risk.index = stock_residual_risk.index.map(Date().change_to_str)
            stock_residual_risk = stock_residual_risk[~stock_residual_risk.index.duplicated()]
            stock_residual_risk = stock_residual_risk.T
        else:
            stock_residual_risk = pd.DataFrame([])
        return stock_residual_risk

    def get_stock_return(self):

        """ 得到 股票 每日 收益率 """

        from quant.stock.stock import Stock
        pct = Stock().read_factor_h5("Pct_chg")
        return pct

    def get_factor_covariance(self, date):

        """ 得到 股票 当日 因子协方差矩阵 """

        file = os.path.join(self.data_path, 'BarraCovariance', str(date) + '.csv')

        if os.path.exists(file):
            factor_covariance = pd.read_csv(file, index_col=[0], encoding='gbk')
        else:
            factor_covariance = pd.DataFrame([])
        return factor_covariance

    def cal_stock_covariance(self, date):

        """
        计算 股票 当日 股票协方差矩阵
        sigma = B'FB + S
        """

        factor_covariance = self.get_factor_covariance(date)
        exposure = self.get_factor_exposure_date(date, type_list=['COUNTRY', 'STYLE', 'INDUSTRY'])
        if exposure is not None and len(exposure) > 0:

            exposure = exposure[factor_covariance.columns]
            residual_risk = self.get_stock_residual_risk()
            residual_var_diag = np.diag(residual_risk[date].map(lambda x: x ** 2).values)

            code_list = residual_risk.index.values
            residual_var_diag = pd.DataFrame(residual_var_diag, index=code_list, columns=code_list)
            public_var = np.dot(np.dot(exposure.values, factor_covariance.values), exposure.T.values)
            code_list = exposure.index.values
            public_var = pd.DataFrame(public_var, index=code_list, columns=code_list)
            residual_var_diag, public_var = FactorPreProcess().make_same_index_columns([residual_var_diag, public_var])
            total_cov = residual_var_diag.add(public_var)

            path = os.path.join(self.data_path, 'StockCovariance')
            if not os.path.exists(path):
                os.makedirs(path)

            print("Cal Stock Covariance Daily is %s" % date)
            file = os.path.join(path, "StockCovariance_%s.csv" % date)
            total_cov.to_csv(file)
        else:
            print("Exposure is None %s" % date)

    def cal_stock_covariance_period(self, beg_date, end_date):

        """  计算 股票 一段时间内 股票协方差矩阵 """

        date_series = Date().get_trade_date_series(beg_date, end_date)
        for date in date_series:
            self.cal_stock_covariance(date)

    def get_stock_covariance(self, date):

        """  得到 股票 当日 股票协方差矩阵  """

        file = os.path.join(self.data_path, 'StockCovariance', "StockCovariance_%s.csv" % date)

        if os.path.exists(file):
            stock_covariance = pd.read_csv(file, index_col=[0], encoding='gbk')
        else:
            stock_covariance = pd.DataFrame([])
        return stock_covariance

    def update_barra(self, beg_date, end_date):

        self.load_barra_data()
        self.cal_barra_cum_factor_return()
        self.cal_stock_covariance_period(beg_date, end_date)
        self.cal_stock_riskfactor_return_daily(beg_date, end_date)

if __name__ == '__main__':

    """ 更新下载Barra数据 """
    ################################################################################################
    today = datetime.today().strftime("%Y%m%d")
    beg_date = Date().get_trade_date_offset(today, -40)
    Date().load_trade_date_series()
    self = Barra()

    Barra().load_barra_data()
    # Barra().cal_barra_cum_factor_return("20040101", today)
    # Barra().cal_stock_riskfactor_return_daily(beg_date, today)
    Barra().cal_stock_covariance_period("20120518", today)
    ################################################################################################

    """ 读取Barra数据 """
    ################################################################################################
    # print(Barra().get_factor_name())
    # print(Barra().get_factor_return("20171203", "20180709"))
    # print(Barra().get_factor_exposure_date("20171229"))
    # print(Barra().get_stock_riskfactor_return_date("20031221"))
    # print(Barra().get_stock_residual_return())
    # print(Barra().get_stock_return())
    # print(Barra().get_stock_covariance("20171229"))
    ################################################################################################
