import numpy as np

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.stock_factor import StockFactor
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraGrowth(RiskFactor):

    """
    成长因子
    未来1年预期盈利增长
    未来3-5年预期盈利增长
    过去5年盈利增速
    过去5年营收增速
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.factor_name = 'cne5_normal_growth'
        self.factor_name_long_term = 'cne5_normal_growth_long_term_predicted_earnings'
        self.raw_factor_name_long_term = 'cne5_raw_growth_long_term_predicted_earnings'
        self.raw_factor_name_short_term = 'cne5_raw_growth_short_term_predicted_earnings'
        self.factor_name_short_term = 'cne5_normal_growth_short_term_predicted_earning'
        self.raw_factor_name_5y_profit = 'cne5_raw_growth_5year_profit'
        self.factor_name_5y_profit = 'cne5_normal_growth_5year_profit'
        self.raw_factor_name_5y_sale = 'cne5_raw_growth_5year_sale'
        self.factor_name_5y_sale = 'cne5_normal_growth_5year_sale'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_barra_growth_long_term_predicted_earnings_growth(self):

        """ 数据为未来2年的预期盈利增长 barra原始是未来3-5年的预期盈利增长 """

        predicted_earnings_growth = Stock().read_factor_h5("FEGR_2")

        self.save_risk_factor_exposure(predicted_earnings_growth, self.raw_factor_name_long_term)
        predicted_earnings_growth = FactorPreProcess().remove_extreme_value_mad(predicted_earnings_growth)
        predicted_earnings_growth = FactorPreProcess().standardization(predicted_earnings_growth)
        self.save_risk_factor_exposure(predicted_earnings_growth, self.factor_name_long_term)

    def cal_factor_barra_growth_short_term_predicted_earnings_growth(self):

        """ 未来1年的预期盈利增长 """

        predicted_earnings_growth = Stock().read_factor_h5("FEGR_1")

        self.save_risk_factor_exposure(predicted_earnings_growth, self.raw_factor_name_short_term)
        predicted_earnings_growth = FactorPreProcess().remove_extreme_value_mad(predicted_earnings_growth)
        predicted_earnings_growth = FactorPreProcess().standardization(predicted_earnings_growth)
        self.save_risk_factor_exposure(predicted_earnings_growth, self.factor_name_short_term)

    @ staticmethod
    def slope(y):

        """  数据 回归 等差数列 的系数 除以 数据的平均值 """

        y = list(y)
        x = list(range(len(y)))
        coef = np.cov(y, x)[0][1] / np.var(x)
        growth = coef / np.mean(y)
        return growth

    def cal_factor_barra_growth_5years_profit_growth(self, beg_date, end_date):

        """ 过去5年每股盈利 回归 等差数列 的系数 除以 每股盈利的平均值 """

        report_data = Stock().read_factor_h5("ReportDateDaily")
        eps = Stock().read_factor_h5("EPS_basic").T

        eps_ttm = eps.rolling(4).sum()
        month = eps_ttm.index[-1][4:6]
        eps_ttm_quarter = eps_ttm.index
        eps_ttm_year = list(filter(lambda x: x[4:6] == month, list(eps_ttm.index)))
        eps_ttm = eps_ttm.loc[eps_ttm_year, :]

        eps_ttm_growth = eps_ttm.rolling(5).apply(self.slope)
        eps_ttm_growth = eps_ttm_growth.loc[eps_ttm_quarter, :]
        eps_ttm_growth = eps_ttm_growth.fillna(method='pad', limit=3).T
        eps_ttm_growth = StockFactor().change_quarter_to_daily_with_disclosure_date(eps_ttm_growth, report_data,
                                                                                    beg_date, end_date)
        self.save_risk_factor_exposure(eps_ttm_growth, self.raw_factor_name_5y_profit)
        eps_ttm_growth = FactorPreProcess().remove_extreme_value_mad(eps_ttm_growth)
        eps_ttm_growth = FactorPreProcess().standardization(eps_ttm_growth)
        self.save_risk_factor_exposure(eps_ttm_growth, self.factor_name_5y_profit)

    def cal_factor_barra_growth_5years_sales_growth(self, beg_date, end_date):

        """  过去5年每股营收 回归 等差数列 的系数 除以 每股盈利的平均值 """

        report_data = Stock().read_factor_h5("ReportDateDaily")
        total_income = Stock().read_factor_h5("OperatingIncomeTotal")
        total_share = Stock().read_factor_h5("TotalShare") / 100000000

        normal_date_series = Date().get_normal_date_series(total_share.columns[0], total_share.columns[-1])
        total_share = total_share.loc[:, normal_date_series]
        total_share = total_share.T.fillna(method='pad', limit=10).T

        total_share, total_income = StockFactor().make_same_index_columns([total_share, total_income])
        income_pre_share = total_income.div(total_share).T

        ips_ttm_growth = income_pre_share.rolling(4).sum()

        month = ips_ttm_growth.index[-1][4:6]
        ips_ttm_quarter = ips_ttm_growth.index
        ips_ttm_year = list(filter(lambda x: x[4:6] == month, list(ips_ttm_growth.index)))
        ips_ttm_growth = ips_ttm_growth.loc[ips_ttm_year, :]

        ips_ttm_growth = ips_ttm_growth.rolling(5).apply(self.slope)
        ips_ttm_growth = ips_ttm_growth.loc[ips_ttm_quarter, :]
        ips_ttm_growth = ips_ttm_growth.fillna(method='pad', limit=3).T
        ips_ttm_growth = StockFactor().change_quarter_to_daily_with_disclosure_date(ips_ttm_growth, report_data,
                                                                                    beg_date, end_date)

        self.save_risk_factor_exposure(ips_ttm_growth, self.raw_factor_name_5y_sale)
        ips_ttm_growth = FactorPreProcess().remove_extreme_value_mad(ips_ttm_growth)
        ips_ttm_growth = FactorPreProcess().standardization(ips_ttm_growth)
        self.save_risk_factor_exposure(ips_ttm_growth, self.factor_name_5y_sale)

    def cal_factor_exposure(self, beg_date, end_date):

        """ 合成成长因子 """

        self.cal_factor_barra_growth_long_term_predicted_earnings_growth()
        self.cal_factor_barra_growth_short_term_predicted_earnings_growth()
        self.cal_factor_barra_growth_5years_profit_growth(beg_date, end_date)
        self.cal_factor_barra_growth_5years_sales_growth(beg_date, end_date)

        long_predicted = 0.18 * self.get_risk_factor_exposure(self.factor_name_long_term)
        short_predicted = 0.11 * self.get_risk_factor_exposure(self.factor_name_short_term)
        profit = 0.24 * self.get_risk_factor_exposure(self.factor_name_5y_profit)
        sales = 0.47 * self.get_risk_factor_exposure(self.factor_name_5y_sale)

        growth = long_predicted.add(short_predicted, fill_value=0.0)
        growth = growth.add(profit, fill_value=0.0)
        growth = growth.add(sales, fill_value=0.0)

        growth = FactorPreProcess().remove_extreme_value_mad(growth)
        growth = FactorPreProcess().standardization(growth)
        self.save_risk_factor_exposure(growth, self.factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = RiskFactorBarraGrowth()
    # self.update_data()
    self.cal_factor_exposure(beg_date, end_date)
