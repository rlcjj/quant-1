import pandas as pd
import numpy as np
import os
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.barra import Barra
from quant.utility.factor_preprocess import FactorPreProcess


class AlphaRegressionSplit(object):

    """
    将收益率拆分 拆分到行业因子上 和 Style 因子上
    将Alpha因子进行拆分 拆分到行业因子上 和 Style 因子上
    """

    def __init__(self):
        pass

    def get_pct_data(self):

        stock_pct = Stock().read_factor_h5("Pct_chg")
        # stock_pct *= 100.0
        return stock_pct

    def get_alpha_exposure(self, factor_name):

        alpha_exposure = Stock().read_factor_h5(factor_name, Stock().get_h5_path("my_alpha"))
        return alpha_exposure

    def get_risk_barra_style_exposure_date(self, date):

        type_list = ['STYLE']
        risk_barra_style_exposure = Barra().get_factor_exposure_date(date=date, type_list=type_list)
        return risk_barra_style_exposure

    def get_risk_barra_country_exposure_date(self, date):

        type_list = ['COUNTRY']
        risk_barra_country_exposure = Barra().get_factor_exposure_date(date=date, type_list=type_list)
        return risk_barra_country_exposure

    def get_risk_barra_industry_country_exposure_date(self, date):

        type_list = ["INDUSTRY"]
        risk_barra_industry_country_exposure = Barra().get_factor_exposure_date(date=date, type_list=type_list)
        return risk_barra_industry_country_exposure

    def get_risk_citic1_industry_exposure(self):

        industry = Stock().read_factor_h5("industry_citic1")
        return industry

    def get_risk_citic1_industry_file(self):
        industry_path = r'E:\New Portfolio Construction Programs\New Portfolio Construction Programs_LTT'
        industry_path += r'\InputData\WindData\IndustryData'
        industry_file = pd.read_csv(os.path.join(industry_path, "CiticCodeList1.csv"), encoding='gbk', index_col=[0])
        industry_file = industry_file[['Alias', 'WindCode', 'Name']]
        return industry_file

    def get_free_mv(self):

        free_mv = Stock().read_factor_h5("Mkt_freeshares")
        return free_mv

    def regression_split_alpha(self, beg_date, end_date, factor_name,
                               need_barra_style=True,  need_citic1_industry=True,
                               need_alpha_rorminv=True, need_wls_free_mv=True):

        """
        Alpha因子 和 风险因子做回归
        1、计算剔除风险因子之后的Alpha因子值
        2、计算Alpha因子暴露在在风险因子上的值
        3、风险因子默认是 Barra风格因子、中信一级行业因子
        """

        # 默认参数
        ##################################################################################
        # need_barra_style = True  # 需要回归掉 Barra Style Factor
        # need_citic1_industry = True  # 需要回归掉 中信一级行业因子
        # need_alpha_rorminv = True  # alpha需要逆正态化
        # need_wls_free_mv = True  # 需要利用根号流通市值做加权做小二乘
        #
        # beg_date = "20040101"
        # end_date = '20180930'
        # factor_name = 'HolderRatioByFund'
        ##################################################################################

        # 因子值的读取和预处理
        # 1、去掉重复行列
        # 2、横截面去极值并标准化、或者直接逆正态化
        ##################################################################################
        alpha_exposure = self.get_alpha_exposure(factor_name)
        alpha_exposure = FactorPreProcess().drop_duplicated(alpha_exposure)
        alpha_exposure = alpha_exposure.T.dropna(how='all').T
        alpha_date_series = list(alpha_exposure.columns)
        if need_alpha_rorminv:
            alpha_exposure = FactorPreProcess().inv_normalization(alpha_exposure)
        else:
            # 根据因子的
            # alpha_exposure = FactorPreProcess().remove_extreme_value_mad(alpha_exposure)
            alpha_exposure = FactorPreProcess().standardization(alpha_exposure)
        ##################################################################################

        # 读取 CITIC Industry
        ##################################################################################
        if need_citic1_industry:
            risk_citic1_industry_exposure = self.get_risk_citic1_industry_exposure()
            industry_date_series = list(risk_citic1_industry_exposure.columns)
        else:
            industry_date_series = Date().get_trade_date_series(beg_date, end_date, 'D')
        ##################################################################################

        # 读取 自由流通市值
        ##################################################################################
        free_mv = self.get_free_mv()
        free_mv /= 100000000.0
        free_mv_date_series = list(free_mv.columns)
        ##################################################################################

        # 日期序列
        ##################################################################################
        date_series = Date().get_trade_date_series(beg_date, end_date, 'D')
        use_date_series = list(set(alpha_date_series) & set(date_series) &
                               set(industry_date_series) & set(free_mv_date_series))
        use_date_series.sort()
        ##################################################################################

        # 开始剥离
        ##################################################################################
        for i_date in range(len(use_date_series)):

            # 日期
            ##################################################################################
            date = use_date_series[i_date]
            print(" Regression And Split Alpha %s At Date %s " % (factor_name, date))

            # 读取 alpha
            ##################################################################################
            alpha_exposure_date = pd.DataFrame(alpha_exposure[date])
            alpha_exposure_date.columns = [factor_name]

            # free_mv
            ##################################################################################
            free_mv_date = pd.DataFrame(free_mv[date])
            free_mv_date.columns = ["FreeMV"]
            risk_factor_name = []
            ##################################################################################

            # 行业数据
            ##################################################################################
            if need_citic1_industry:
                industry_exposure_date = risk_citic1_industry_exposure[date]
                industry_dummy_date = pd.get_dummies(industry_exposure_date)
                industry_columns = list(map(lambda x: 'Industry_' + str(int(x)), list(industry_dummy_date.columns)))
                # fun = lambda x: industry_file[industry_file.Alias == x].Name.values[0]
                # industry_columns = list(map(fun, list(industry_dummy_date.columns)))
                industry_dummy_date.columns = industry_columns
                risk_factor_name.extend(industry_columns)
            else:
                industry_dummy_date = pd.DataFrame([])
            ##################################################################################

            # 读取 style barra factor exposure_return
            # 原来是市值加权平均数为0 转化为简单平均为0
            ##################################################################################
            if need_barra_style:
                style_exposure_raw_date = self.get_risk_barra_style_exposure_date(date)
                style_columns = style_exposure_raw_date.columns
                risk_factor_name.extend(style_columns)

                if need_wls_free_mv:
                    style_exposure_date = FactorPreProcess().remove_extreme_value_mad(style_exposure_raw_date)
                    style_mv = pd.concat([style_exposure_date, free_mv_date], axis=1)
                    style_mv = style_mv.dropna()
                    style_exposure_date = style_exposure_date.loc[style_mv.index, :]
                    free_mv_date_weight = free_mv_date.loc[style_mv.index, "FreeMV"]
                    free_mv_date_weight = free_mv_date_weight / free_mv_date_weight.sum()
                    weight_mean = style_exposure_date.mul(free_mv_date_weight, axis='index').sum()
                    style_exposure_date = style_exposure_date.sub(weight_mean, axis='columns')
                    style_exposure_date_std = style_exposure_date.std()
                    style_exposure_date = style_exposure_date.div(style_exposure_date_std, axis='columns')
                else:
                    style_exposure_date = FactorPreProcess().remove_extreme_value_mad(style_exposure_raw_date)
                    style_exposure_date = FactorPreProcess().standardization(style_exposure_date)
            else:
                style_exposure_date = pd.DataFrame([])
            ##################################################################################

            # 合并数据 并添加市场因子 去除全是0的列
            ##################################################################################
            data_exposure = pd.concat([alpha_exposure_date, free_mv_date,
                                       style_exposure_date, industry_dummy_date], axis=1)
            print(data_exposure.head())
            data_exposure = data_exposure.dropna()
            allzero_columns = data_exposure.applymap(lambda x: x == 0).sum() == len(data_exposure)
            allzero_columns = list(allzero_columns[allzero_columns].index)

            for i_allzero in range(len(allzero_columns)):
                col = allzero_columns[i_allzero]
                risk_factor_name.remove(col)
                industry_columns.remove(col)

            data_exposure['ChinaEquity'] = 1.0
            risk_factor_name.insert(0, 'ChinaEquity')
            ##################################################################################

            # 数据准备
            ##################################################################################
            alpha_stock = data_exposure[factor_name].values
            risk_factor_stock = data_exposure[risk_factor_name].values
            free_mv_stock = data_exposure['FreeMV'].values

            if need_citic1_industry:
                industry_mv_weight = data_exposure[industry_columns].mul(data_exposure['FreeMV'], axis='index').sum()
                industry_mv_weight /= industry_mv_weight.sum()
                industry_mv_weight = industry_mv_weight.values
            ##################################################################################

            ##################################################################################
            # 回归所需数据 这里做的其实是一个有约束的WLS或OLS
            # 有两种方法 一种是转化为二次规划 一种是直接用矩阵的方法
            ##################################################################################

            ##################################################################################
            # 方法1 矩阵的方法 MATLAB程序一致
            # 1、1 如果是利用市值做加权最小二乘回归的话 需要调整XY矩阵
            # 残差的方差和市值的平方根成反比
            ##################################################################################
            if need_wls_free_mv:
                D_inv = np.diag(free_mv_stock**(1/4))
                X = np.dot(D_inv, risk_factor_stock)
                Y = np.dot(D_inv, alpha_stock)
            else:
                X = risk_factor_stock
                Y = alpha_stock
            ##################################################################################

            # 1、2如果有行业因子 则需要加上约束矩阵
            ##################################################################################
            if need_citic1_industry:

                risk_number = len(risk_factor_name)
                weight_factor = pd.DataFrame(np.zeros(shape=(risk_number, 1)), index=risk_factor_name, columns=['Col'])

                if need_wls_free_mv:
                    weight_factor.loc[industry_columns, "Col"] = industry_mv_weight
                else:
                    weight_factor.loc[industry_columns, 'Col'] = 1.0
                weight_factor['Col'] /= weight_factor['Col'].sum()

                # 约束矩阵
                Wf = np.zeros(shape=(risk_number, risk_number - 1))
                Wf[0, 0] = 1.0

                style_beg_number = 1 + len(industry_columns)
                style_end_number = risk_number
                industry_beg_number = 1
                industry_end_number = style_beg_number

                for i_style in range(style_beg_number, style_end_number):
                    Wf[i_style, i_style - 1] = 1.0

                for i_industry in range(industry_beg_number, industry_end_number - 1):
                    industry_w = weight_factor.loc[weight_factor.index[i_industry], 'Col']
                    Wf[i_industry + 1, i_industry] = industry_w
                    industry_w_n = weight_factor.loc[weight_factor.index[i_industry + 1], 'Col']
                    Wf[i_industry, i_industry] = - industry_w_n
            ##################################################################################

            # 1、3矩阵求解系数 和 回归残差项
            ##################################################################################
            if need_citic1_industry:
                Wf_t = np.transpose(Wf)
                X_t = np.transpose(X)
                A = np.dot(np.dot(np.dot(Wf_t, X_t), X), Wf)
                A_inv = np.linalg.inv(A)
                B = np.dot(np.dot(Wf_t, X_t), Y)
                coeff = np.dot(Wf, np.dot(A_inv, B))
                coeff_pd = pd.DataFrame(coeff, index=risk_factor_name, columns=[date])
                risk_part_exposure = np.dot(risk_factor_stock, coeff)
                risk_part_exposure_pd = pd.DataFrame(risk_part_exposure, index=data_exposure.index, columns=[date])
                residual = alpha_stock - np.dot(risk_factor_stock, coeff)
                residual_pd = pd.DataFrame(residual, index=data_exposure.index, columns=[date])
            else:
                X_t = np.transpose(X)
                A_inv = np.linalg.inv(np.dot(X_t, X))
                B = np.dot(X_t, Y)
                coeff = np.dot(A_inv, B)
                coeff_pd = pd.DataFrame(coeff, index=risk_factor_name, columns=[date])
                risk_part_exposure = np.dot(risk_factor_stock, coeff)
                risk_part_exposure_pd = pd.DataFrame(risk_part_exposure, index=data_exposure.index, columns=[date])
                residual = alpha_stock - np.dot(risk_factor_stock, coeff)
                residual_pd = pd.DataFrame(residual, index=data_exposure.index, columns=[date])
            ##################################################################################

            # 1、4 合并每天的数据
            ##################################################################################
            if i_date == 0:
                coeff_all_date = coeff_pd
                residual_all_date = residual_pd
                risk_part_all_date = risk_part_exposure_pd
            else:
                coeff_all_date = pd.concat([coeff_all_date, coeff_pd], axis=1)
                residual_all_date = pd.concat([residual_all_date, residual_pd], axis=1)
                risk_part_all_date = pd.concat([risk_part_all_date, risk_part_exposure_pd], axis=1)
            ##################################################################################

        # 存储数据
        ##################################################################################
        Stock().write_factor_h5(coeff_all_date, factor_name + 'StyleIndustryExposure', 'my_alpha')
        Stock().write_factor_h5(residual_all_date, factor_name + 'Res', 'my_alpha')
        Stock().write_factor_h5(risk_part_all_date, factor_name + 'StyleIndustry', 'my_alpha')
        ##################################################################################

    def regression_split_return(self, beg_date, end_date,
                               need_barra_style=True, need_citic1_industry=True,
                               need_wls_free_mv=True):

        """
        当天股票收益率 和 前一天风险因子做回归 （注意和Alpha剥离不一样）
        1、计算剔除风险因子之后的残差收益率
        2、计算收益率暴露在在风险因子上的值，即因子收益率
        3、风险因子默认是 Barra风格因子、中信一级行业因子
        """

        # 默认参数
        ##################################################################################
        # need_barra_style = True  # 需要回归掉 Barra Style Factor
        # need_citic1_industry = True  # 需要回归掉 中信一级行业因子
        # need_wls_free_mv = True  # 需要利用根号流通市值做加权做小二乘
        #
        # beg_date = "20040101"
        # end_date = '20180930'
        ##################################################################################

        # 因子值的读取和预处理
        # 1、去掉重复行列
        # 2、横截面去极值并标准化、或者直接逆正态化
        ##################################################################################
        beg_date = Date().get_trade_date_offset(beg_date, -1)
        stock_return = self.get_pct_data()
        stock_return = FactorPreProcess().drop_duplicated(stock_return)
        stock_return = stock_return.T.dropna(how='all').T
        return_date_series = list(stock_return.columns)
        ##################################################################################

        # 读取 CITIC Industry
        ##################################################################################
        if need_citic1_industry:
            risk_citic1_industry_exposure = self.get_risk_citic1_industry_exposure()
            industry_date_series = list(risk_citic1_industry_exposure.columns)

            industry_path = r'E:\New Portfolio Construction Programs\New Portfolio Construction Programs_LTT\InputData\WindData\IndustryData'
            industry_file = pd.read_csv(os.path.join(industry_path, "CiticCodeList1.csv"), encoding='gbk', index_col=[0])
            industry_file = industry_file[['Alias', 'WindCode', 'Name']]
        else:
            industry_date_series = Date().get_trade_date_series(beg_date, end_date, 'D')
        ##################################################################################

        # 读取 自由流通市值
        ##################################################################################
        free_mv = self.get_free_mv()
        free_mv /= 1000000000.0
        free_mv_date_series = list(free_mv.columns)
        ##################################################################################

        # 日期序列
        ##################################################################################
        date_series = Date().get_trade_date_series(beg_date, end_date, 'D')
        use_date_series = list(set(return_date_series) & set(date_series) &
                               set(industry_date_series) & set(free_mv_date_series))
        use_date_series.sort()
        print(use_date_series[0], use_date_series[-1])
        print(stock_return)
        ##################################################################################

        # 开始剥离
        ##################################################################################
        for i_date in range(len(use_date_series) - 1):

            # 日期
            ##################################################################################
            date = use_date_series[i_date]
            next_date = use_date_series[i_date + 1]
            print(" Regression And Split StockReturn At Date %s " % date)

            # 读取 alpha
            ##################################################################################
            stock_return_date = pd.DataFrame(stock_return[next_date])
            stock_return_date.columns = ["Pct"]

            # free_mv
            ##################################################################################
            free_mv_date = pd.DataFrame(free_mv[date])
            free_mv_date.columns = ["FreeMV"]
            risk_factor_name = []
            ##################################################################################

            # 行业数据
            ##################################################################################
            if need_citic1_industry:
                industry_exposure_date = risk_citic1_industry_exposure[date]
                industry_dummy_date = pd.get_dummies(industry_exposure_date)
                industry_columns = list(map(lambda x: 'Industry_' + str(int(x)), list(industry_dummy_date.columns)))
                # fun = lambda x: industry_file[industry_file.Alias == x].Name.values[0]
                # industry_columns = list(map(fun, list(industry_dummy_date.columns)))
                industry_dummy_date.columns = industry_columns
                risk_factor_name.extend(industry_columns)
            else:
                industry_dummy_date = pd.DataFrame([])
            ##################################################################################

            # 读取 style barra factor exposure_return
            # 原来是市值加权平均数为0 转化为简单平均为0
            ##################################################################################
            if need_barra_style:
                style_exposure_raw_date = self.get_risk_barra_style_exposure_date(date)
                style_columns = style_exposure_raw_date.columns
                risk_factor_name.extend(style_columns)

                if need_wls_free_mv:
                    style_exposure_date = FactorPreProcess().remove_extreme_value_mad(style_exposure_raw_date)
                    style_mv = pd.concat([style_exposure_date, free_mv_date], axis=1)
                    style_mv = style_mv.dropna()
                    style_exposure_date = style_exposure_date.loc[style_mv.index, :]
                    free_mv_date_weight = free_mv_date.loc[style_mv.index, "FreeMV"]
                    free_mv_date_weight = free_mv_date_weight / free_mv_date_weight.sum()
                    weight_mean = style_exposure_date.mul(free_mv_date_weight, axis='index').sum()
                    style_exposure_date = style_exposure_date.sub(weight_mean, axis='columns')
                    style_exposure_date_std = style_exposure_date.std()
                    style_exposure_date = style_exposure_date.div(style_exposure_date_std, axis='columns')
                else:
                    style_exposure_date = FactorPreProcess().remove_extreme_value_mad(style_exposure_raw_date)
                    style_exposure_date = FactorPreProcess().standardization(style_exposure_date)
            else:
                style_exposure_date = pd.DataFrame([])
            ##################################################################################

            # 合并数据 并添加市场因子 去除全是0的列
            ##################################################################################
            data_exposure = pd.concat([stock_return_date, free_mv_date,
                                       style_exposure_date, industry_dummy_date], axis=1)
            data_exposure = data_exposure.dropna()
            allzero_columns = data_exposure.applymap(lambda x: x == 0).sum() == len(data_exposure)
            allzero_columns = list(allzero_columns[allzero_columns].index)

            for i_allzero in range(len(allzero_columns)):
                col = allzero_columns[i_allzero]
                risk_factor_name.remove(col)
                industry_columns.remove(col)
            data_exposure['ChinaEquity'] = 1.0
            risk_factor_name.insert(0, 'ChinaEquity')
            ##################################################################################

            # 数据准备
            ##################################################################################
            alpha_stock = data_exposure["Pct"].values
            risk_factor_stock = data_exposure[risk_factor_name].values
            free_mv_stock = data_exposure['FreeMV'].values

            if need_citic1_industry:
                industry_mv_weight = data_exposure[industry_columns].mul(data_exposure['FreeMV'], axis='index').sum()
                industry_mv_weight /= industry_mv_weight.sum()
                industry_mv_weight = industry_mv_weight.values
            ##################################################################################

            ##################################################################################
            # 回归所需数据 这里做的其实是一个有约束的WLS或OLS
            # 有两种方法 一种是转化为二次规划 一种是直接用矩阵的方法
            ##################################################################################

            ##################################################################################
            # 方法1 矩阵的方法 MATLAB程序一致
            # 1、1 如果是利用市值做加权最小二乘回归的话 需要调整XY矩阵
            # 残差的方差和市值的平方根成反比
            ##################################################################################
            if need_wls_free_mv:
                D_inv = np.diag(free_mv_stock ** (1 / 4))
                X = np.dot(D_inv, risk_factor_stock)
                Y = np.dot(D_inv, alpha_stock)
            else:
                X = risk_factor_stock
                Y = alpha_stock
            ##################################################################################

            # 1、2如果有行业因子 则需要加上约束矩阵
            ##################################################################################
            if need_citic1_industry:

                risk_number = len(risk_factor_name)
                weight_factor = pd.DataFrame(np.zeros(shape=(risk_number, 1)), index=risk_factor_name, columns=['Col'])

                if need_wls_free_mv:
                    weight_factor.loc[industry_columns, "Col"] = industry_mv_weight
                else:
                    weight_factor.loc[industry_columns, 'Col'] = 1.0
                weight_factor['Col'] /= weight_factor['Col'].sum()

                # 约束矩阵
                Wf = np.zeros(shape=(risk_number, risk_number - 1))
                Wf[0, 0] = 1.0

                style_beg_number = 1 + len(industry_columns)
                style_end_number = risk_number
                industry_beg_number = 1
                industry_end_number = style_beg_number

                for i_style in range(style_beg_number, style_end_number):
                    Wf[i_style, i_style - 1] = 1.0

                for i_industry in range(industry_beg_number, industry_end_number - 1):
                    industry_w = weight_factor.loc[weight_factor.index[i_industry], 'Col']
                    Wf[i_industry + 1, i_industry] = industry_w
                    industry_w_n = weight_factor.loc[weight_factor.index[i_industry + 1], 'Col']
                    Wf[i_industry, i_industry] = - industry_w_n
            ##################################################################################

            # 1、3矩阵求解系数 和 回归残差项
            ##################################################################################
            if need_citic1_industry:
                Wf_t = np.transpose(Wf)
                X_t = np.transpose(X)
                A = np.dot(np.dot(np.dot(Wf_t, X_t), X), Wf)
                A_inv = np.linalg.inv(A)
                B = np.dot(np.dot(Wf_t, X_t), Y)
                coeff = np.dot(Wf, np.dot(A_inv, B))
                coeff_pd = pd.DataFrame(coeff, index=risk_factor_name, columns=[next_date])
                risk_part_exposure = np.dot(risk_factor_stock, coeff)
                risk_part_exposure_pd = pd.DataFrame(risk_part_exposure, index=data_exposure.index, columns=[date])
                residual = alpha_stock - np.dot(risk_factor_stock, coeff)
                residual_pd = pd.DataFrame(residual, index=data_exposure.index, columns=[next_date])
            else:
                X_t = np.transpose(X)
                A_inv = np.linalg.inv(np.dot(X_t, X))
                B = np.dot(X_t, Y)
                coeff = np.dot(A_inv, B)
                coeff_pd = pd.DataFrame(coeff, index=risk_factor_name, columns=[next_date])
                risk_part_exposure = np.dot(risk_factor_stock, coeff)
                risk_part_exposure_pd = pd.DataFrame(risk_part_exposure, index=data_exposure.index, columns=[date])
                residual = alpha_stock - np.dot(risk_factor_stock, coeff)
                residual_pd = pd.DataFrame(residual, index=data_exposure.index, columns=[date])
            ##################################################################################

            # 1、4 合并每天的数据
            ##################################################################################
            if i_date == 0:
                coeff_all_date = coeff_pd
                residual_all_date = residual_pd
                risk_part_all_date = risk_part_exposure_pd
            else:
                coeff_all_date = pd.concat([coeff_all_date, coeff_pd], axis=1)
                residual_all_date = pd.concat([residual_all_date, residual_pd], axis=1)
                risk_part_all_date = pd.concat([risk_part_all_date, risk_part_exposure_pd], axis=1)
            ##################################################################################

        # 存储数据
        ##################################################################################
        Stock().write_factor_h5(coeff_all_date, 'PctStyleIndustryFactor', 'my_alpha')
        Stock().write_factor_h5(residual_all_date, 'PctRes', 'my_alpha')
        Stock().write_factor_h5(risk_part_all_date, 'PctStyleIndustry', 'my_alpha')
        ##################################################################################

if __name__ == '__main__':

    # 参数
    ##################################################################################
    beg_date = "20060104"
    end_date = '20180930'
    factor_name = 'HolderBySFIf'
    self = AlphaRegressionSplit()

    # 拆分Alpha\Return
    ##################################################################################
    # AlphaRegressionSplit().regression_split_return(beg_date, end_date,
    #                                                need_barra_style=True, need_citic1_industry=True,
    #                                                need_wls_free_mv=True)
    AlphaRegressionSplit().regression_split_alpha(beg_date, end_date, factor_name,
                                                  need_barra_style=True, need_citic1_industry=True,
                                                  need_alpha_rorminv=False, need_wls_free_mv=True)
    ##################################################################################

