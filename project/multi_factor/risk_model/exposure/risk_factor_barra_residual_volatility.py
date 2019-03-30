import numpy as np
import pandas as pd
import statsmodels.api as sm

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.index import Index
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraResVol(RiskFactor):

    """
    因子说明：利用回归方法计算个股 Beta
    市场收益的股票平均收益
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.factor_name = 'cne5_normal_res_vol'
        self.raw_factor_name_std = 'cne5_raw_res_vol_std'
        self.factor_name_std = "cne5_normal_res_vol_std"
        self.raw_factor_name_range = 'cne5_raw_res_vol_cumulative_range'
        self.factor_name_range = 'cne5_normal_res_vol_cumulative_range'
        self.raw_factor_name_hsigma = 'cne5_raw_res_vol_hsigma'
        self.factor_name_hsigma = 'cne5_normal_res_vol_hsigma'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_barra_std(self, beg_date, end_date):

        """ 利用过去120天的收益率计算波动率（未来可以考虑不够120天的情况） """

        # param
        term = 252
        half_life = 42
        min_periods = 120

        # read data
        pct_chg = Stock().read_factor_h5("Pct_chg")
        pct_chg = Stock().replace_suspension_with_nan(pct_chg)
        pct_chg = Stock().fillna_with_mad_market(pct_chg)
        pct_chg = pct_chg.T

        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(pct_chg.index) & set(date_series))
        date_series.sort()

        res = pd.DataFrame([])

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            print('Calculating Barra Risk factor %s at date %s' % (self.factor_name_std, current_date))
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            data_pre = pct_chg.ix[data_beg_date:current_date, :]
            data_pre = data_pre.dropna(how='all')

            if len(data_pre) > 0:
                data_std = data_pre.ewm(halflife=half_life, min_periods=min_periods).std().loc[current_date, :]
                data_date = pd.DataFrame(data_std) * np.sqrt(250)
                data_date.columns = [current_date]
                res = pd.concat([res, data_date], axis=1)

        res = res.T.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name_std)
        res = Stock().remove_extreme_value_mad(res)
        res = Stock().standardization(res)
        self.save_risk_factor_exposure(res, self.factor_name_std)

    def cal_factor_barra_cumulative_range(self, beg_date, end_date):

        """ 过去1-12月最大累计收益 和最小累计收益的差 """

        # param
        t = 12
        month_days = 21

        pct_chg = Stock().read_factor_h5("Pct_chg").applymap(lambda x: np.log(x / 100 + 1)).T

        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(pct_chg.columns))
        date_series.sort()

        pct_chg_panel = pd.Panel()

        for i in range(t):

            length = month_days * (i + 1)
            pct_chg_sum = pct_chg.rolling(length).sum()
            pct_chg_sum = pct_chg_sum.dropna(how='all')
            pct_chg_panel = pd.concat([pct_chg_panel, pct_chg_sum], axis=0)

        pct_max = pct_chg_panel.max(axis=0)
        pct_max = pct_max.applymap(lambda x: np.log(x + 1)).T
        pct_min = pct_chg_panel.min(axis=0)
        pct_min = pct_min.applymap(lambda x: np.log(x + 1)).T
        res = pct_max.sub(pct_min)

        self.save_risk_factor_exposure(res, self.raw_factor_name_range)
        res = Stock().remove_extreme_value_mad(res)
        res = Stock().standardization(res)
        self.save_risk_factor_exposure(res, self.factor_name_range)

    def cal_factor_barra_hsigma(self,  beg_date, end_date):

        """
        股票收益率和市场收益率回归之后的残差收益率标准差 (残差收益率的beta中计算过了)
        需要 Beta Size 因子做回归取残差
        """

        term = 252
        half_life = 62
        min_periods = 20

        res_pct = self.get_risk_factor_exposure("cne5_raw_beta_res_pct").T
        size_data = self.get_risk_factor_exposure("cne5_normal_size")
        beta_data = self.get_risk_factor_exposure("cne5_normal_beta")

        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(res_pct.index) & set(date_series) & set(size_data.columns) & set(beta_data.columns))
        date_series.sort()

        res = pd.DataFrame([])

        for i in range(0, len(date_series)):

            date = date_series[i]
            print('Calculating Barra Risk factor %s at date %s' % (self.factor_name, date))
            data_beg_date = Date().get_trade_date_offset(date, -(term - 1))
            data_pre = res_pct.ix[data_beg_date:date, :]
            data_pre = data_pre.dropna(how='all')

            data_std = data_pre.ewm(halflife=half_life, min_periods=min_periods).std().loc[date, :]
            data_date = pd.DataFrame(data_std) * np.sqrt(250)
            data_date.columns = [date]

            regression_data = pd.concat([size_data[date], beta_data[date], data_date], axis=1)
            regression_data.columns = ['sise', 'beta', 'y']
            regression_data = regression_data.dropna()

            if len(regression_data) > 0:

                y = regression_data['y'].values
                x = regression_data[['sise', 'beta']].values
                x_add = sm.add_constant(x)
                model = sm.OLS(y, x_add).fit()
                regression_data['res'] = regression_data['y'] - model.fittedvalues
                res_data_date = pd.DataFrame(regression_data['res'])
                res_data_date.columns = [date]
                res = pd.concat([res, res_data_date], axis=1)

        res = res.T.dropna(how='all').T

        if len(res) != 0:
            self.save_risk_factor_exposure(res, self.raw_factor_name_hsigma)
            res = Stock().remove_extreme_value_mad(res)
            res = Stock().standardization(res)
            self.save_risk_factor_exposure(res, self.factor_name_hsigma)
        else:
            print("The Result Risk factor %s from date %s to %s" % (self.factor_name, beg_date, end_date))

    def cal_factor_exposure(self, beg_date, end_date):

        """ 残差波动率因子加和（考虑有其中几个数据缺失该怎么办） """

        self.cal_factor_barra_std(beg_date, end_date)
        self.cal_factor_barra_cumulative_range(beg_date, end_date)
        self.cal_factor_barra_hsigma(beg_date, end_date)

        dastd = 0.74 * self.get_risk_factor_exposure("cne5_normal_res_vol_std")
        cr = 0.16 * self.get_risk_factor_exposure("cne5_normal_res_vol_cumulative_range")
        hsigma = 0.10 * self.get_risk_factor_exposure("cne5_normal_res_vol_hsigma")

        size_data = self.get_risk_factor_exposure("cne5_normal_size")
        beta_data = self.get_risk_factor_exposure("cne5_normal_beta")

        residual_volatility = dastd.add(cr, fill_value=0.0)
        residual_volatility = residual_volatility.add(hsigma, fill_value=0.0)
        residual_volatility = residual_volatility.T.dropna(how='all').T

        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(size_data.columns) & set(residual_volatility.columns) &
                           set(beta_data.columns) & set(date_series))
        date_series.sort()

        residual_volatility_res = pd.DataFrame([])

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print('Calculating Barra Risk factor %s at date %s' % (self.factor_name, date))
            regression_data = pd.concat([size_data[date], beta_data[date], residual_volatility[date]], axis=1)
            regression_data.columns = ['size', 'beta', 'residual_volatility']
            regression_data = regression_data.dropna()

            if len(regression_data) > 0:
                y = regression_data['residual_volatility'].values
                x = regression_data[['size', 'beta']].values
                x_add = sm.add_constant(x)
                model = sm.OLS(y, x_add).fit()
                regression_data['res'] = regression_data['residual_volatility'] - model.fittedvalues
                res_date = pd.DataFrame(regression_data['res'])
                res_date.columns = [date]
                residual_volatility_res = pd.concat([residual_volatility_res, res_date], axis=1)

        # save data
        res = Stock().remove_extreme_value_mad(residual_volatility_res)
        res = Stock().standardization(res)
        self.save_risk_factor_exposure(res, self.factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = "20190101"
    end_date = datetime.today().strftime("%Y%m%d")

    self = RiskFactorBarraResVol()
    # self.update_data()
    self.cal_factor_exposure(beg_date, end_date)
