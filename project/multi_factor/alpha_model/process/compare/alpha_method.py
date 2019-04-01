import pandas as pd
import numpy as np
import os
from datetime import datetime
import statsmodels.api as sm
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.utility.factor_preprocess import FactorPreProcess
from quant.utility.write_excel import WriteExcel


class AlphaMethod(object):

    def __init__(self):

        """
        比较很多计算alpha因子的方法的异同
        """
        pass

    def get_data_real(self):

        # 参数
        ###############################################################################################################
        date = "20171229"
        factor_name = "ROEQuarterDaily"
        next_date = Date().get_trade_date_offset(date, 40)

        # read data
        ###############################################################################################################
        price = Stock().read_factor_h5("PriceCloseAdjust")
        alpha_val = Stock().read_factor_h5(factor_name, Stock().get_h5_path("my_alpha"))

        size = Stock().read_factor_h5("NORMAL_CNE5_SIZE", Stock().get_h5_path("my_barra_risk"))
        beta = Stock().read_factor_h5("NORMAL_CNE5_BETA", Stock().get_h5_path("my_barra_risk"))
        nolin_size = Stock().read_factor_h5("NORMAL_CNE5_NON_LINEAR_SIZE", Stock().get_h5_path("my_barra_risk"))
        industry = Stock().read_factor_h5("industry_citic1")
        pct = pd.DataFrame(price[next_date] / price[date] - 1.0)

        # make same columns
        ###############################################################################################################
        industry_date = industry[date]
        industry_dummy_date = pd.get_dummies(industry_date)
        industry_columns = list(map(lambda x: 'industry_' + str(int(x)), list(industry_dummy_date.columns)))
        industry_dummy_date.columns = industry_columns

        data = pd.concat([pct, alpha_val[date], size[date], beta[date], nolin_size[date], industry_dummy_date], axis=1)
        data = data.dropna()
        data = data
        columns = ['pct', 'alpha', 'size', 'beta', 'nolin_size']
        style_columns = ['size', 'beta', 'nolin_size']
        columns.extend(industry_columns)
        data.columns = columns

        stand = FactorPreProcess().standardization(data[['alpha', 'size', 'beta', 'nolin_size']])
        data[['alpha', 'size', 'beta', 'nolin_size']] = stand
        ###############################################################################################################

        return data, style_columns, industry_columns

    def method_matrix(self):

        #############################################################################
        data, style_columns, industry_columns = self.get_data_real()
        r = data['pct'].values
        alpha_columns = ['alpha']
        alpha_columns.extend(style_columns)
        X = data[alpha_columns].values

        # 方法1 矩阵
        #############################################################################
        fmp = np.dot(np.linalg.inv(np.dot(np.transpose(X), X)), np.transpose(X))

        fmp_alpha_weight = pd.DataFrame(fmp[0, :], index=data.index)
        factor_return = np.dot(fmp, r)
        fmp_exposure = np.dot(fmp, X)
        #############################################################################

    def method_regression(self):

        #############################################################################
        data, style_columns, industry_columns = self.get_data_real()
        r = data['pct'].values
        alpha_val = data['alpha'].values
        style_val = data[style_columns].values
        X_columns = ['alpha']
        X_columns.extend(style_columns)
        X_val = data[X_columns].values

        # 方法2 回归残差
        #############################################################################
        import statsmodels.api as sm
        style_add = sm.add_constant(style_val)
        model = sm.OLS(alpha_val, style_add).fit()
        res_alpha = alpha_val - model.fittedvalues
        # res_alpha /= data['alpha'].abs().sum()
        exposure = np.dot(np.transpose(X_val), res_alpha)
        res_alpha = pd.DataFrame(res_alpha / exposure[0], index=data.index)

        import statsmodels.api as sm
        X_add = sm.add_constant(X_val)
        model = sm.OLS(alpha_val, X_add).fit()
        res_alpha = alpha_val - model.fittedvalues
        # res_alpha /= data['alpha'].abs().sum()
        exposure = np.dot(np.transpose(X_add), res_alpha)
        res_alpha = pd.DataFrame(res_alpha / exposure[0], index=data.index)
        factor_return = data['pct'].mul(res_alpha).sum()

    def method_qp(self):

        # 方法3 最优化
        #############################################################################
        P = np.diag(np.ones(shape=(X.shape[0])))
        q = np.zeros(shape=(X.shape[0]))
        A = np.transpose(X)
        b = np.row_stack([1.0, 0.0, 0.0, 0.0])
        A_add = np.column_stack(np.ones(shape=(X.shape[0])))
        b_add = np.array([0.0])
        A = np.row_stack((A, A_add))
        b = np.row_stack((b, b_add))

        import cvxopt.solvers as sol
        from cvxopt import matrix

        P_m = matrix(P)
        q_m = matrix(q)
        A_m = matrix(A)
        b_m = matrix(b)
        result = sol.qp(P=P_m, q=q_m, A=A_m, b=b_m)
        params_add = pd.DataFrame(np.array(result['x'][0:]), index=data.index)

        all_data = pd.concat([fmp_alpha, res_alpha, params_add], axis=1)


if __name__ == '__main__':

    self = AlphaMethod()