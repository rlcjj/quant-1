import pandas as pd
import statsmodels.api as sm
from datetime import datetime

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.macro import Macro
from quant.stock.index import Index
from quant.utility.factor_preprocess import FactorPreProcess
from quant.utility.time_series_weight import TimeSeriesWeight
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraBeta(RiskFactor):

    """
    因子说明：利用回归方法计算个股 Beta
    市场收益的股票平均收益
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'cne5_raw_beta'
        self.factor_name = 'cne5_normal_beta'
        self.raw_res_pct_factor_name = "cne5_raw_beta_res_pct"

    @staticmethod
    def update_data(beg_date, end_date):

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()
        Macro().load_daily_risk_free_rate(beg_date, end_date)

    def cal_factor_exposure(self, beg_date="20060101", end_date=datetime.today().strftime("%Y%m%d")):

        """ 计算因子暴露 计算beta和残差收益率 残差收益率还要计算残差波动率 """

        # params
        term = 252
        half_life = 63
        min_periods = 40

        # read data

        pct = Stock().read_factor_h5("Pct_chg")
        pct = Stock().replace_suspension_with_nan(pct)
        pct = Stock().fillna_with_mad_market(pct)
        pct = pct.T

        index_pct = Index().get_index_factor("000985.CSI", attr=['PCT']) * 100
        index_pct.columns = ['Index']
        risk_free_rate = Macro().get_daily_risk_free_rate()

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(pct.index) & set(date_series) & set(index_pct.index) & set(risk_free_rate.index))
        date_series.sort()

        beta = pd.DataFrame([], columns=date_series, index=pct.columns)
        res_pct = pd.DataFrame([], columns=date_series, index=pct.columns)

        for i_date in range(0, len(date_series)):

            current_date = date_series[i_date]
            print('Calculating Barra Risk factor %s at date %s' % (self.factor_name, current_date))
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            pct_before = pct.loc[data_beg_date:current_date, :]
            index_pct_before = index_pct.loc[data_beg_date:current_date, :]
            risk_free_rate_before = risk_free_rate.loc[data_beg_date:current_date, :]

            for i_code in range(len(pct_before.columns)):

                stock_code = pct_before.columns[i_code]
                pct_before_stock = pd.DataFrame(pct_before[stock_code])
                concat_data = pd.concat([index_pct_before, risk_free_rate_before, pct_before_stock], axis=1)
                concat_data = concat_data.dropna()

                weight = pd.DataFrame(TimeSeriesWeight().exponential_weight(len(concat_data), half_life),
                                      index=concat_data.index, columns=['Weight'])
                concat_data['Weight'] = weight
                concat_data['ones'] = 1.0
                concat_data["Index"] -= concat_data["RiskFreeRate"]
                concat_data[stock_code] -= concat_data["RiskFreeRate"]

                if len(concat_data) > min_periods:

                    x = concat_data[['ones', "Index"]].values
                    y = concat_data[stock_code].values
                    model = sm.WLS(y, x, weights=concat_data['Weight'].values).fit()

                    res_series = y - model.fittedvalues
                    beta.loc[stock_code, current_date] = model.params[1]
                    res_pct.loc[stock_code, current_date] = res_series[-1]
                    print(stock_code, current_date, model.params[1], res_series[-1])

        # save data
        beta = beta.T.dropna(how='all').T
        res_pct = res_pct.T.dropna(how='all').T
        self.save_risk_factor_exposure(beta, self.raw_factor_name)
        self.save_risk_factor_exposure(res_pct, self.raw_res_pct_factor_name)
        beta = FactorPreProcess().remove_extreme_value_mad(beta)
        beta = FactorPreProcess().standardization(beta)
        self.save_risk_factor_exposure(beta, self.factor_name)


if __name__ == "__main__":

    beg_date = '20181130'
    end_date = "20190320"

    self = RiskFactorBarraBeta()
    # self.update_data(beg_date, end_date)
    self.cal_factor_exposure(beg_date, end_date)
