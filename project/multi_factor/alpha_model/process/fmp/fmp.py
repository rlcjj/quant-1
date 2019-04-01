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


class FMP(object):

    """
    Transfer Alpha Signal to Factor Mimicking Portfolio
    1 Quadratic Programming for Solution
    2 Need to Know What Risk Factor to Neutral
       2.1 The Factor has a large negative return
       2.2 The Factor has a negative or positive exposure_return in history

    Source: Axioma Research Paper No.45 -- Alpha Construction in a Consistent Investment Process
    """

    def __init__(self):

        self.alpha_data = None
        self.style_data = None
        self.industry_data = None
        self.price_data = None
        self.free_mv_data = None
        self.trade_status = None

        self.use_date_series = None
        self.change_date_series = None
        self.alpha_factor_name = None
        self.style_factor_name = None
        self.industry_factor_name = None
        self.risk_factor_name = None
        self.min_stock_num = 30
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

    def get_data_date(self, date, stock_pool='Astock'):

        # alpha data date
        ####################################################################################################
        alpha_date_list = list(self.alpha_data.columns)
        alpha_date_list = list(filter(lambda x: x <= date, alpha_date_list))

        alpha_date = pd.DataFrame(self.alpha_data[max(alpha_date_list)])
        alpha_date.columns = [self.alpha_factor_name]

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

        # free mv date
        ####################################################################################################
        free_mv_date = pd.DataFrame(self.free_mv_data[date])
        free_mv_date.columns = ['FreeMv']

        # ipo date
        ####################################################################################################
        ipo_date = Stock().get_ipo_date()
        ipo_date_new = Date().get_trade_date_offset(date, -120)
        ipo_date = ipo_date[ipo_date['IPO_DATE'] < ipo_date_new]
        ipo_date = ipo_date[ipo_date['DELIST_DATE'] > date]

        # trade status date
        ####################################################################################################
        trade_status_date = pd.DataFrame(self.trade_status[date])
        trade_status_date.columns = ['TradeStatus']

        code_trade = pd.concat([ipo_date, trade_status_date], axis=1)
        code_trade = code_trade.dropna()
        code_trade = code_trade[code_trade['TradeStatus'] == 0.0]

        if stock_pool != 'Astock':
            from quant.stock.index import Index
            index_weight = Index().get_weight(stock_pool, date)
            if index_weight is not None:
                code_trade = pd.concat([code_trade, index_weight], axis=1)
                code_trade = code_trade.dropna()
            else:
                code_trade = pd.DataFrame([])

        all_data = pd.concat([alpha_date, barra_industry_date, barra_style_date, free_mv_date, code_trade], axis=1)
        all_data = all_data.dropna()

        alpha_date = pd.DataFrame(all_data[self.alpha_factor_name])
        alpha_date = FactorPreProcess().remove_extreme_value_mad(alpha_date)
        alpha_date = FactorPreProcess().standardization(alpha_date)

        barra_industry_date = pd.DataFrame(all_data[self.industry_factor_name])
        columns = barra_industry_date.columns[barra_industry_date.sum() > 10.0]
        barra_industry_date = barra_industry_date[columns]

        barra_style_date = pd.DataFrame(all_data[self.style_factor_name])
        barra_style_date = FactorPreProcess().standardization(barra_style_date)

        free_mv_date = pd.DataFrame(all_data['FreeMv'])
        code_trade = pd.DataFrame(all_data['TradeStatus'])

        return alpha_date, barra_industry_date, barra_style_date, free_mv_date, code_trade

    def cal_fmp(self, neutralize='Raw', W_mat="Equal", stock_pool='Astock'):

        """
        min h'Wh
        s.t. h'*a = 1.0
             h'*B = 0.0

        :param W_mat
        W_mat = 'Equal' 对角线全为1
        W_mat = 'FreeMvSqrt' 对角线为自由流通市值的平方根
        W_mat = 'BarraStockCov' 对角线为Barra估计的股票协方差矩阵

        :param neutralize
        neutralize = 'Raw' 不限制对风险因子约束
        neutralize = 'Res' 限制对风险因子约束 具体约束见参数文件

        :param stock_pool
        multi_factor pool 股票池

        在计算FMP的时候 还可以加入其他的约束条件
        """

        params_file = r'E:\3_Data\5_stock_data\3_alpha_model\fmp\input_file\neutral_list.xlsx'
        params = pd.read_excel(params_file)

        for i_date in range(len(self.change_date_series) - 1):

            # read alpha data and concat multi_factor list
            ####################################################################################################
            date = self.change_date_series[i_date]
            data = self.get_data_date(date, stock_pool)
            alpha_date, industry_dummy_date, barra_style_date, free_mv_date, code_trade = data

            code_list = list(alpha_date.index)

            # W 矩阵
            ####################################################################################################
            if W_mat == 'BarraStockCov':

                stock_cov = Barra().get_stock_covariance(date)
                alpha_date = alpha_date.loc[code_list, :]
                stock_cov = stock_cov.loc[code_list, code_list]
                alpha_date = FactorPreProcess().remove_extreme_value_mad(alpha_date)
                alpha_date = FactorPreProcess().standardization(alpha_date)

            elif W_mat == 'FreeMvSqrt':
                free_mv_date = free_mv_date.dropna()
                free_mv_date['FreeMv2'] = free_mv_date['FreeMv'].map(lambda x: 1 / (x ** (1 / 2)))
                free_mv_date = pd.DataFrame(free_mv_date['FreeMv2'])

            else:
                pass
            ####################################################################################################

            if len(alpha_date) > self.min_stock_num:

                if W_mat == 'Equal':
                    P = np.diag(np.ones(shape=(1, len(alpha_date)))[0])
                elif W_mat == 'FreeMvSqrt':
                    P = np.diag(np.column_stack(free_mv_date.values)[0])
                elif W_mat == 'BarraStockCov':
                    P = stock_cov.values
                else:
                    P = np.diag(np.ones(shape=(1, len(alpha_date)))[0])

                Q = np.zeros(shape=(P.shape[0], 1))

                A = np.column_stack(alpha_date.values)
                A_add = np.ones(shape=(1, P.shape[0]))
                A = np.row_stack((A, A_add))
                b = np.array([[1.0], [0.0]])

                if neutralize == 'Res':

                    params = params[params.name == self.alpha_factor_name]
                    params = params[params.market == stock_pool]
                    params.index = ['index']

                    if params.loc['index', 'Industry'] == 1.0:

                        A_add = industry_dummy_date.T.values
                        A = np.row_stack((A, A_add))
                        b_add = np.row_stack((np.zeros(shape=(len(industry_dummy_date.columns), 1))))
                        b = np.row_stack((b, b_add))

                    params_style = params.loc[:, self.style_factor_name].T
                    params_style = params_style[params_style == 1.0]
                    params_style = params_style.dropna()

                    if len(params_style) > 0:

                        barra_style_date = barra_style_date[params_style.index]
                        A_add = barra_style_date.T.values
                        A = np.row_stack((A, A_add))
                        b_add = np.row_stack((np.zeros(shape=(len(barra_style_date.columns), 1))))
                        b = np.row_stack((b, b_add))

                print(A.shape)
                try:
                    P = matrix(P)
                    Q = matrix(Q)
                    A = matrix(A)
                    b = matrix(b)
                    result = sol.qp(P, q=Q, A=A, b=b)
                    fmp_raw_alpha = pd.DataFrame(np.array(result['x'][0:]), columns=[date], index=code_list).T
                    print("Cal FMP %s %s %s %s " % (date, stock_pool, neutralize, self.alpha_factor_name))
                    concat_data = pd.concat([fmp_raw_alpha.T, alpha_date], axis=1)
                    concat_data = concat_data.dropna()
                    print(concat_data.corr().values[0][0])
                except Exception as e:
                    fmp_raw_alpha = pd.DataFrame([], columns=[date], index=code_list).T
                    print("QP FMP is InCorrect  %s %s %s %s " % (date, stock_pool, neutralize, self.alpha_factor_name))
            else:
                fmp_raw_alpha = pd.DataFrame([], columns=[date], index=code_list).T
                print("The Length of Data is Zero %s %s %s %s " % (date, stock_pool, neutralize, self.alpha_factor_name))

            # concat
            ####################################################################################################
            if i_date == 0:
                fmp_raw_alpha_all = fmp_raw_alpha
            else:
                fmp_raw_alpha_all = pd.concat([fmp_raw_alpha_all, fmp_raw_alpha], axis=0)

        # write data
        ####################################################################################################
        sub_path = os.path.join(self.path, 'fmp')
        file = os.path.join(sub_path, '%s_%s_%s_%s.csv' % (self.alpha_factor_name, neutralize, W_mat, stock_pool))
        fmp_raw_alpha_all = fmp_raw_alpha_all.T
        fmp_raw_alpha_all.to_csv(file)
        ####################################################################################################

    def get_fmp(self, neutralize='Raw', W_mat="Equal", stock_pool='Astock'):

        sub_path = os.path.join(self.path, 'fmp')
        file = os.path.join(sub_path, '%s_%s_%s_%s.csv' % (self.alpha_factor_name, neutralize, W_mat, stock_pool))
        fmp_alpha = pd.read_csv(file, index_col=[0], encoding='gbk')
        return fmp_alpha

    def alpha_contribution(self, neutralize='Raw', W_mat="Equal", stock_pool='Astock'):

        """
        利用Barra风险模型对alpha因子进行归因
        严格的，对于不同股票池的风险因子的因子收益率应该重新计算
        但是这里暂时用的还是全市场的风险因子收益率
        """

        type_list = ['COUNTRY', 'STYLE', 'INDUSTRY']
        stock_return = Barra().get_stock_return().T
        risk_return = Barra().get_factor_return(type_list=type_list)

        for i_date in range(len(self.change_date_series)-1):

            # date
            ####################################################################################################
            date = self.change_date_series[i_date]
            bg_date = Date().get_trade_date_offset(date, 1)
            ed_date = self.change_date_series[i_date + 1]

            # data
            ####################################################################################################
            stock_return_period = stock_return.loc[bg_date:ed_date, :]
            stock_return_period = stock_return_period.T.dropna().T
            stock_return_period = pd.DataFrame(stock_return_period.sum(skipna=True))
            stock_return_period.columns = ['Pct']

            risk_return_period = risk_return.loc[bg_date:ed_date, :]
            risk_return_period = pd.DataFrame(risk_return_period.sum(skipna=True))
            risk_return_period.columns = [date]

            exposure_date = Barra().get_factor_exposure_date(date, type_list)

            fmp = self.get_fmp(neutralize, W_mat, stock_pool)
            fmp_date = pd.DataFrame(fmp[date])
            fmp_date.columns = ['FmpWeight']
            fmp_date = fmp_date.dropna()

            code_list = list(set(exposure_date.index) & set(fmp_date.index) & set(stock_return_period.index))
            code_list.sort()

            exposure_date = exposure_date.loc[code_list, :]
            fmp_date = fmp_date.loc[code_list, :]
            stock_return_period = stock_return_period.loc[code_list, :]

            if len(fmp_date) > self.min_stock_num:

                # risk factor return multiply alpha exposure_return on risk factor
                ####################################################################################################
                fmp_exposure = np.dot(fmp_date.T, exposure_date)
                fmp_exposure = pd.DataFrame(fmp_exposure, index=[date], columns=exposure_date.columns)

                fmp_risk_factor = fmp_exposure.mul(risk_return_period.T)
                fmp_alpha_factor = np.dot(fmp_date.T, stock_return_period)

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
                print("Contribution for %s %s %s %s %s" % (self.alpha_factor_name, neutralize, W_mat, date, stock_pool))

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

        risk_return_mean = pd.DataFrame(risk_return.mean()) * 250
        risk_return_mean.columns = ['Factor Return']

        exposure_mean = pd.DataFrame(fmp_exposure_all.mean())
        exposure_mean.columns = ['Avg Exposure']

        exposure = pd.concat([risk_return_mean, exposure_mean], axis=1)

        # write excel
        ####################################################################################################
        filename = os.path.join(sub_path, '%s_%s_%s_%s_Summary.xlsx' % (self.alpha_factor_name, neutralize, W_mat, stock_pool))
        sheet_name = "Contribution"

        we = WriteExcel(filename)
        ws = we.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=fmp_risk_summary.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        we.write_pandas(fmp_risk_summary, ws, begin_row_number=0, begin_col_number=1,
                        num_format_pd=num_format_pd, color="blue", fillna=True)

        num_format_pd = pd.DataFrame([], columns=exposure.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        num_format_pd.ix['format', 'Avg Exposure'] = '0.00%'
        we.write_pandas(exposure, ws, begin_row_number=4, begin_col_number=2 + len(fmp_risk_summary.columns),
                        num_format_pd=num_format_pd, color="blue", fillna=True)
        we.close()

        # Write Csv
        ####################################################################################################
        sub_path = os.path.join(self.path, 'fmp_risk_factor')
        filename = os.path.join(sub_path, '%s_%s_%s_%s_RiskContributionFMP.csv' % (self.alpha_factor_name, neutralize, W_mat, stock_pool))
        fmp_risk_factor_all.to_csv(filename)
        sub_path = os.path.join(self.path, 'fmp_exposure')
        filename = os.path.join(sub_path, '%s_%s_%s_%s_RiskExposureFMP.csv' % (self.alpha_factor_name, neutralize, W_mat, stock_pool))
        fmp_exposure_all.to_csv(filename)
        ###################################################################################################

    def cal_real_portfolio(self, neutralize='Raw', W_mat="Equal", stock_pool='Astock'):

        for i_date in range(len(self.change_date_series)-1):

            lamb = 1000.0

            # date
            ####################################################################################################
            date = self.change_date_series[i_date]
            data = self.get_data_date(date, stock_pool)
            alpha_date, industry_dummy_date, barra_style_date, free_mv_date, code_trade = data

            fmp = self.get_fmp(neutralize, W_mat, stock_pool)
            fmp_date = pd.DataFrame(fmp[date])
            fmp_date.columns = ['FmpWeight']
            fmp_date = fmp_date.dropna()

            code_list = list(fmp_date.index)

            # Barra().cal_stock_covariance(date)
            stock_covriance = Barra().get_stock_covariance(date)
            stock_covriance = stock_covriance.loc[code_list, code_list].values
            stock_covriance = np.zeros(shape=(len(code_list), len(code_list)))

            alpha_signal = np.dot(stock_covriance, fmp_date)
            alpha_signal = fmp_date.values * 2

            P = stock_covriance * lamb
            Q = - np.row_stack(alpha_signal)

            from quant.stock.index import Index
            index_weight = Index().get_weight(index_code=stock_pool, date=date)
            index_weight = index_weight.loc[code_list, :]
            index_weight = index_weight.fillna(0.0)
            index_weight['Max'] = 0.03
            index_weight['Min'] = -index_weight['WEIGHT']

            G_positive = np.diag(np.ones(shape=(len(index_weight))))
            G_negative = - np.diag(np.ones(shape=(len(index_weight))))
            G = np.row_stack((G_positive, G_negative))

            h_positive = np.row_stack(index_weight['Max'].values)
            h_negative = np.row_stack(index_weight['Min'].values)
            h = np.row_stack((h_positive, h_negative))

            A = np.ones(shape=(1, len(index_weight)))
            b = np.array([[0.0]])

            try:
                P = matrix(P)
                Q = matrix(Q)
                G = matrix(G)
                h = matrix(h)
                A = matrix(A)
                b = matrix(b)

                result = sol.qp(P, q=Q, G=G, h=h, A=A, b=b)
                result = sol.qp(P, q=Q)
                stock_weight_active = pd.DataFrame(np.array(result['x'][0:]), columns=['Active'], index=code_list).T
                weight = pd.concat([index_weight, stock_weight_active.T, fmp_date], axis=1)
                weight['PortWeight'] = weight['WEIGHT'] + weight['Active']
                weight['ImplyWeight'] = weight['WEIGHT'] + weight['FmpWeight']
                print((weight['WEIGHT'] - weight['PortWeight']).abs().sum())
                print(weight['Active'].sum())
                print("Cal Portfolio %s %s %s %s " % (date, stock_pool, neutralize, self.alpha_factor_name))
            except Exception as e:
                stock_weight = pd.DataFrame([], columns=[date], index=code_list).T
                index_weight = pd.concat([index_weight, stock_weight.T], axis=1)
                print("QP Portfolio is InCorrect  %s %s %s %s " % (date, stock_pool, neutralize, self.alpha_factor_name))


if __name__ == '__main__':

    # params
    ###################################################################################################
    self = FMP()
    alpha_factor_name = "ROERankYOY"
    beg_date = "20070105"
    end_date = "20181009"
    periods = "W"
    stock_pool = '000905.SH'
    W_mat = 'Equal'
    neutralize = 'Raw'

    # cal
    ###################################################################################################
    self.get_data(alpha_factor_name, beg_date, end_date, periods)
    self.cal_fmp(neutralize, W_mat, stock_pool)
    self.alpha_contribution(neutralize, W_mat, stock_pool)
    ###################################################################################################

