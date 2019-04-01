import pandas as pd
import numpy as np
import os
import cvxopt.solvers as sol
from cvxopt import matrix
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.barra import Barra
from quant.utility.factor_preprocess import FactorPreProcess
from quant.utility.write_excel import WriteExcel


class TransferSignalToFMP(object):

    """
    Transfer Alpha Signal to Factor Mimicking Portfolio
    1 Quadratic Programming for Solution
    2 Need to Know What Risk Factor to Neutral
       2.1 The Factor has a large negative return
       2.2 The Factor has a negative or positive exposure_return in history
    """

    def __init__(self):

        self.alpha_data = None
        self.style_data = None
        self.industry_data = None
        self.price_data = None
        self.free_mv_data = None

        self.use_date_series = None
        self.change_date_series = None
        self.alpha_factor_name = None
        self.style_factor_name = None
        self.industry_factor_name = None
        self.risk_factor_name = None
        self.min_stock_num = 50
        self.annual_number = 50
        self.path = r'E:\3_Data\5_stock_data\3_alpha_model\fmp'

    def get_data(self, alpha_factor_name, beg_date, end_date, periods="W", annual_number=50):

        # get data
        #############################################################################################
        self.alpha_data = Stock().read_factor_h5(alpha_factor_name, Stock().get_h5_path("my_alpha"))
        self.price_data = Stock().read_factor_h5("PriceCloseAdjust")
        self.free_mv_data = Stock().read_factor_h5("Mkt_freeshares") / 100000000.0
        self.trade_status = Stock().read_factor_h5("TradingStatus")
        self.alpha_factor_name = alpha_factor_name
        self.annual_number = annual_number

        # get date series
        #############################################################################################
        alpha_date_series = list(self.alpha_data.columns)
        free_mv_date_series = list(self.free_mv_data.columns)
        price_date_series = list(self.price_data.columns)
        date_series = Date().get_trade_date_series(beg_date, end_date, 'D')

        use_date_series = list(set(alpha_date_series) & set(date_series) & set(price_date_series) &
                               set(free_mv_date_series))
        use_date_series.sort()
        self.use_date_series = use_date_series
        self.change_date_series = Date().get_trade_date_series(use_date_series[0], use_date_series[-1], periods)
        self.get_data_date("20171229")
        #############################################################################################

    def get_data_date(self, date):

        # alpha data date
        ####################################################################################################
        alpha_date_list = list(self.alpha_data.columns)
        alpha_date_list = list(filter(lambda x: x <= date, alpha_date_list))

        alpha_date = pd.DataFrame(self.alpha_data[max(alpha_date_list)])
        alpha_date.columns = [self.alpha_factor_name]
        # alpha_date = FactorPreProcess().standardization(alpha_date)

        # industry data date
        ####################################################################################################
        risk_factor_name = []
        type_list = ['INDUSTRY']
        barra_industry_date = Barra().get_factor_exposure_date(date=date, type_list=type_list)
        industry_columns = barra_industry_date.columns
        risk_factor_name.extend(industry_columns)
        self.industry_factor_name = industry_columns
        self.risk_factor_name = risk_factor_name

        # style data date
        ####################################################################################################
        type_list = ['STYLE']
        barra_style_date = Barra().get_factor_exposure_date(date=date, type_list=type_list)
        barra_style_date = FactorPreProcess().standardization(barra_style_date)
        style_columns = barra_style_date.columns
        risk_factor_name.extend(style_columns)
        self.style_factor_name = style_columns
        self.risk_factor_name = risk_factor_name

        free_mv_date = pd.DataFrame(self.free_mv_data[date])
        free_mv_date.columns = ['FreeMv']

        return alpha_date, barra_industry_date, barra_style_date, free_mv_date

    def get_stock_return(self, beg_date, end_date):

        stock_return = pd.DataFrame(self.price_data[end_date] / self.price_data[beg_date]) - 1.0
        stock_return.columns = ['Pct']
        return stock_return

    def cal_risk_factor_return(self):

        """
        stock_return ~ country + style + industry (restrict for industry)
        can solve factor return for risk factor
        """

        for i_date in range(len(self.change_date_series) - 1):

            # date
            ####################################################################################################
            date = self.change_date_series[i_date]
            next_date = self.change_date_series[i_date + 1]
            change_date = Date().get_trade_date_offset(date, 1)
            next_change_date = Date().get_trade_date_offset(next_date, 1)

            # data
            ####################################################################################################
            alpha_date, barra_industry_date, barra_style_date, free_mv_date = self.get_data_date(date)
            stock_return = self.get_stock_return(change_date, next_change_date)
            data = pd.concat([stock_return, barra_style_date, barra_industry_date, free_mv_date], axis=1)

            # 有些股票没有行业
            data = data.dropna()
            data = data.loc[barra_industry_date.sum(axis=1) == 1.0, :]
            data['FreeMvSqrt'] = data['FreeMv'].map(lambda x: x**(1/4))
            data['ChinaEquity'] = 1.0

            if len(data) > self.min_stock_num:

                # style data
                ####################################################################################################
                free_mv_date = data['FreeMv']
                free_mv_date = free_mv_date / free_mv_date.sum()

                barra_style_date = pd.DataFrame(data[self.style_factor_name])
                barra_style_weight_mean = barra_style_date.mul(free_mv_date, axis='index').mean()
                barra_style_std = barra_style_date.std()
                barra_style_date_new = barra_style_date.sub(barra_style_weight_mean, axis='columns')
                barra_style_date_new = barra_style_date_new.div(barra_style_std, axis='columns')

                """
                # 保证流通市值加权平均为0 标准差为1
                print(barra_style_date_new.mul(free_mv_date, axis='index').mean())
                print(barra_style_date_new.std())
                """

                # industry data
                ####################################################################################################
                industry_dummy_date = pd.DataFrame(data[self.industry_factor_name])
                weight_sum = industry_dummy_date.mul(free_mv_date, axis='index').sum().sum()
                industry_weight = industry_dummy_date.mul(free_mv_date, axis='index').sum() / weight_sum
                industry_weight = pd.DataFrame(industry_weight)
                industry_weight.columns = ['Weight']
                industry_weight.loc["ChinaEquity", "Weight"] = 0.0
                for style in self.style_factor_name:
                    industry_weight.loc[style, "Weight"] = 0.0

                # other data
                ####################################################################################################
                free_mv_sqrt_date = pd.DataFrame(data['FreeMvSqrt'])
                china_date = pd.DataFrame(data["ChinaEquity"])
                stock_return = pd.DataFrame(data['Pct'])

                # exposure_return
                ####################################################################################################
                exposure = pd.concat([barra_style_date_new, industry_dummy_date], axis=1)
                sub_path = os.path.join(self.path, 'stock_risk_exposure')
                exposure.to_csv(os.path.join(sub_path, 'StockRiskExposure_%s.csv' % date))

                # stock_return ~ country + style + industry (restrict for industry)
                ####################################################################################################
                y = stock_return.values
                X = exposure.values

                S_inv = np.diag((free_mv_sqrt_date.T.values[0]))
                y = np.dot(S_inv, y)
                X = np.dot(S_inv, X)

                # import statsmodels.api as sm
                # model = sm.OLS(y, X).fit()
                # print(model.params[:])

                P = 2 * np.dot(X.T, X)
                Q = -2 * np.dot(X.T, y)

                # weight = np.column_stack(industry_weight.loc[exposure_return.columns, "Weight"].values)
                # A = weight
                # b = np.array([0.0])

                try:
                    P = matrix(P)
                    Q = matrix(Q)
                    # A = matrix(A)
                    # b = matrix(b)
                    result = sol.qp(P, Q)
                    risk_factor_return = pd.DataFrame(np.array(result['x'][:]), columns=[date], index=exposure.columns).T
                    print("########## Contribution On Style And Industry At %s ##########" % date)
                except Exception as e:
                    risk_factor_return = pd.DataFrame([], columns=[date], index=exposure.columns).T
                    print("########## Quadratic Programming is InCorrect %s ##########" % date)

                # concat
                ####################################################################################################
                if i_date == 0:
                    risk_factor_return_all = risk_factor_return
                else:
                    risk_factor_return_all = pd.concat([risk_factor_return_all, risk_factor_return], axis=0)

        # write data
        ####################################################################################################
        sub_path = os.path.join(self.path, 'risk_factor_return')
        risk_factor_return_all.to_csv(os.path.join(sub_path, 'RiskFactorReturn.csv'))
        risk_factor_return_all.cumsum().to_csv(os.path.join(sub_path, 'RiskFactorReturnCumSum.csv'))
        ####################################################################################################

    def get_risk_factor_return(self):

        sub_path = os.path.join(self.path, 'risk_factor_return')
        risk_factor_return = pd.read_csv(os.path.join(sub_path, 'RiskFactorReturn.csv'), index_col=[0], encoding='gbk')
        risk_factor_return.index = risk_factor_return.index.map(str)

        return risk_factor_return

    def get_risk_factor_exposure(self, date):

        sub_path = os.path.join(self.path, 'stock_risk_exposure')
        exposure = pd.read_csv(os.path.join(sub_path, 'StockRiskExposure_%s.csv' % date), index_col=[0], encoding='gbk')
        return exposure

    def cal_fmp(self, fmp_name, type="Equal"):

        """
        type = 'Equal' 对角线全为1
        type = 'FreeMvSqrt' 对角线为自由流通市值的平方根
        type = 'BarraStockCov' 对角线为Barra估计的股票协方差矩阵
        """

        for i_date in range(len(self.change_date_series) - 1):

            # read alpha data
            ####################################################################################################
            date = self.change_date_series[i_date]
            alpha_date, industry_dummy_date, barra_style_date, free_mv_date = self.get_data_date(date)
            alpha_date = alpha_date.dropna()
            alpha_date = FactorPreProcess().remove_extreme_value_mad(alpha_date)
            alpha_date = FactorPreProcess().standardization(alpha_date)
            code_list = list(alpha_date.index)
            code_list.sort()
            alpha_date = alpha_date.loc[code_list, :]

            # data
            ####################################################################################################
            if type == 'BarraStockCov':

                stock_cov = Barra().get_stock_covariance(date)
                code_list = list(set(alpha_date.index) & set(stock_cov.index))
                code_list.sort()
                alpha_date = alpha_date.loc[code_list, :]
                stock_cov = stock_cov.loc[code_list, code_list]
                alpha_date = FactorPreProcess().remove_extreme_value_mad(alpha_date)
                alpha_date = FactorPreProcess().standardization(alpha_date)

            if len(alpha_date) > self.min_stock_num:

                if type == 'Equal':
                    P = np.diag(np.ones(shape=(1, len(alpha_date)))[0])
                elif type == 'BarraStockCov':
                    P = stock_cov.values

                Q = np.zeros(shape=(P.shape[0], 1))
                A = np.column_stack(alpha_date.values)
                A_add = np.ones(shape=(1, P.shape[0]))
                A = np.row_stack((A, A_add))
                b = np.array([[1.0], [0.0]])
                try:
                    P = matrix(P)
                    Q = matrix(Q)
                    A = matrix(A)
                    b = matrix(b)
                    result = sol.qp(P, q=Q, A=A, b=b)
                    fmp_raw_alpha = pd.DataFrame(np.array(result['x'][0:]), columns=[date], index=code_list).T
                    print("########## factor mimicking portfolio At %s ##########" % date)
                    concat_data = pd.concat([fmp_raw_alpha.T, alpha_date], axis=1)
                    concat_data = concat_data.dropna()
                    print(concat_data.corr().values[0][0])
                except Exception as e:
                    fmp_raw_alpha = pd.DataFrame([], columns=[date], index=code_list).T
                    print("########## Quadratic Programming FMP is InCorrect %s ##########" % date)

            # concat
            ####################################################################################################
            if i_date == 0:
                fmp_raw_alpha_all = fmp_raw_alpha
            else:
                fmp_raw_alpha_all = pd.concat([fmp_raw_alpha_all, fmp_raw_alpha], axis=0)

        # write data
        ####################################################################################################
        sub_path = os.path.join(self.path, 'fmp')
        file = os.path.join(sub_path, '%s_%s_%s.csv' % (self.alpha_factor_name, fmp_name, type))
        fmp_raw_alpha_all = fmp_raw_alpha_all.T
        fmp_raw_alpha_all.to_csv(file)
        ####################################################################################################

    def get_fmp(self, fmp_name, type):

        sub_path = os.path.join(self.path, 'fmp')
        file = os.path.join(sub_path, '%s_%s_%s.csv' % (self.alpha_factor_name, fmp_name, type))
        fmp_alpha = pd.read_csv(file, index_col=[0], encoding='gbk')

        return fmp_alpha

    def alpha_contribution(self, fmp_name, type):

        """
        risk factor return multiply risk factor exposure_return of fmp
        can contribute alpha return on risk factor
        """

        for i_date in range(len(self.change_date_series)-1):

            # date
            ####################################################################################################
            date = self.change_date_series[i_date]
            next_date = self.change_date_series[i_date + 1]
            change_date = Date().get_trade_date_offset(date, 1)
            next_change_date = Date().get_trade_date_offset(next_date, 1)

            # data
            ####################################################################################################
            stock_return = self.get_stock_return(change_date, next_change_date)

            fmp = self.get_fmp(fmp_name, type)
            fmp_date = pd.DataFrame(fmp[date])
            fmp_date.columns = ['FmpWeight']
            fmp_date = fmp_date.dropna()

            exposure_date = self.get_risk_factor_exposure(date)
            risk_return = self.get_risk_factor_return().T
            risk_return_date = pd.DataFrame(risk_return[date])

            code_list = list(set(exposure_date.index) & set(fmp_date.index) & set(stock_return.index))
            code_list.sort()

            exposure_date = exposure_date.loc[code_list, :]
            fmp_date = fmp_date.loc[code_list, :]
            stock_return = stock_return.loc[code_list, :]

            if len(fmp_date) > self.min_stock_num:

                # risk factor return multiply alpha exposure_return on risk factor
                ####################################################################################################
                fmp_exposure = np.dot(fmp_date.T, exposure_date)
                fmp_exposure = pd.DataFrame(fmp_exposure, index=[date], columns=exposure_date.columns)

                fmp_risk_factor = fmp_exposure.mul(risk_return_date.T)
                fmp_alpha_factor = np.dot(fmp_date.T, stock_return)

                col = list(fmp_risk_factor.columns)

                fmp_risk_factor.loc[date, 'Res_Alpha'] = fmp_alpha_factor[0][0] - fmp_risk_factor.sum().sum()
                fmp_risk_factor.loc[date, 'Industry'] = fmp_risk_factor[self.industry_factor_name].sum().sum()
                fmp_risk_factor.loc[date, 'Style'] = fmp_risk_factor[self.style_factor_name].sum().sum()
                fmp_risk_factor.loc[date, 'Raw_Alpha'] = fmp_alpha_factor[0][0]

                col.insert(0, 'Res_Alpha')
                col.insert(0, 'Industry')
                col.insert(0, 'Style')
                col.insert(0, 'Raw_Alpha')
                fmp_risk_factor = fmp_risk_factor[col]
                print("Contribution for %s %s %s %s" % (self.alpha_factor_name, fmp_name, type, date))

                # 4 concat
                ####################################################################################################
                if i_date == 0:
                    fmp_risk_factor_all = fmp_risk_factor
                    fmp_exposure_all = fmp_exposure
                else:
                    fmp_risk_factor_all = pd.concat([fmp_risk_factor_all, fmp_risk_factor], axis=0)
                    fmp_exposure_all = pd.concat([fmp_exposure_all, fmp_exposure], axis=0)

        # summary
        ####################################################################################################
        sub_path = os.path.join(self.path, 'summary')
        fmp_risk_summary = pd.DataFrame()
        fmp_risk_summary['Contribution'] = fmp_risk_factor_all.mean() * self.annual_number
        fmp_risk_summary['IR'] = fmp_risk_factor_all.mean() / fmp_risk_factor_all.std() * np.sqrt(self.annual_number)

        risk_return = risk_return.T
        risk_return_mean = pd.DataFrame(risk_return.mean()) * self.annual_number
        risk_return_mean.columns = ['Factor Return']

        exposure_mean = pd.DataFrame(fmp_exposure_all.mean())
        exposure_mean.columns = ['Avg Exposure']

        exposure = pd.concat([risk_return_mean, exposure_mean], axis=1)

        # write excel
        ####################################################################################################
        filename = os.path.join(sub_path, '%s_%s_%s_Summary.xlsx' % (self.alpha_factor_name, fmp_name, type))
        sheet_name = "Contribution"

        we = WriteExcel(filename)
        ws = we.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=fmp_risk_summary.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.ix['format', 'IR'] = '0.00'
        we.write_pandas(fmp_risk_summary, ws, begin_row_number=0, begin_col_number=1,
                        num_format_pd=num_format_pd, color="blue", fillna=True)

        num_format_pd = pd.DataFrame([], columns=exposure.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.ix['format', 'Avg Exposure'] = '0.000'
        we.write_pandas(exposure, ws, begin_row_number=4, begin_col_number=2 + len(fmp_risk_summary.columns),
                        num_format_pd=num_format_pd, color="blue", fillna=True)
        we.close()

        # Write Csv
        ####################################################################################################
        sub_path = os.path.join(self.path, 'fmp_risk_factor')
        filename = os.path.join(sub_path, '%s_%s_%s_RiskContributionFMP.csv' % (self.alpha_factor_name, fmp_name, type))
        fmp_risk_factor_all.to_csv(filename)
        sub_path = os.path.join(self.path, 'fmp_exposure')
        filename = os.path.join(sub_path, '%s_%s_%s_RiskExposureFMP.csv' % (self.alpha_factor_name, fmp_name, type))
        fmp_exposure_all.to_csv(filename)
        ###################################################################################################


if __name__ == '__main__':

    self = TransferSignalToFMP()
    alpha_factor_name = "IncomeYOYDaily"
    beg_date = "20150630"
    end_date = "20180909"
    periods = "W"
    self.get_data(alpha_factor_name, beg_date, end_date, periods)
    self.cal_risk_factor_return()
    fmp_name = 'Raw'
    type = 'Equal'
    # self.cal_fmp(fmp_name, type)
    self.alpha_contribution(fmp_name, type)

