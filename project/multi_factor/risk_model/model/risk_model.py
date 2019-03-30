import os
import numpy as np
import pandas as pd
from cvxopt import matrix
import cvxopt.solvers as sol
import statsmodels.api as sm
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskModel(Data):

    """
    所有风险模型的母类

    1、包含哪些风险因子
    2、计算每日股票在风险因子上的暴露
    3、计算每日因子的协方差矩阵
    4、计算每日股票的残差收益率
    5、计算每日股票的协方差矩阵

    测试整个风险模型的能力
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\risk_model\model'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.model_performance_path = os.path.join(self.primary_data_path, r'stock_data\risk_model\model_performance')
        self.model_path = ""
        self.risk_model_name = ""
        self.exposure_path = ""
        self.factor_return_path = ""
        self.res_return_path = ""
        self.factor_cov_path = ""
        self.stock_res_cov_path = ""
        self.stock_cov_path = ""

        self.pct_chg = None
        self.free_mv_data = None
        self.trade_status = None
        self.industry = None
        self.style_factor_name = None
        self.change_style_factor_name = None
        self.style_factor_data = None
        self.industry_factor_name = None
        self.date_series = None

    def set_model_name(self, risk_model_name="cne5"):

        """ 确定风险模型 并创建文件路径 """

        self.risk_model_name = risk_model_name
        self.model_path = os.path.join(self.data_path, self.risk_model_name)
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)

        self.exposure_path = os.path.join(self.model_path, "exposure")
        if not os.path.exists(self.exposure_path):
            os.makedirs(self.exposure_path)

        self.factor_return_path = os.path.join(self.model_path, "factor_return")
        if not os.path.exists(self.factor_return_path):
            os.makedirs(self.factor_return_path)

        self.res_return_path = os.path.join(self.model_path, "stock_residual_return")
        if not os.path.exists(self.res_return_path):
            os.makedirs(self.res_return_path)

        self.factor_cov_path = os.path.join(self.model_path, "factor_cov")
        if not os.path.exists(self.factor_cov_path):
            os.makedirs(self.factor_cov_path)

        self.stock_res_cov_path = os.path.join(self.model_path, "stock_res_cov")
        if not os.path.exists(self.stock_res_cov_path):
            os.makedirs(self.stock_res_cov_path)

        self.stock_cov_path = os.path.join(self.model_path, "stock_cov")
        if not os.path.exists(self.stock_cov_path):
            os.makedirs(self.stock_cov_path)

    def get_risk_factor_list(self):

        """ 模型包含哪些风险因子 """

        file = os.path.join(self.data_path, 'param', 'RiskModel.xlsx')
        data = pd.read_excel(file)
        data_model = pd.DataFrame(data[self.risk_model_name])
        data_model = data_model.dropna()
        risk_factor_name = list(data_model[self.risk_model_name].values)
        return risk_factor_name

    def get_stock_pool(self, stock_pool_name="AllChinaStockFilter", date="20181231"):

        """ 风险因子股票池 """

        stock_pool = Stock().get_invest_stock_pool(stock_pool_name, date)
        return stock_pool

    def get_data_all(self, risk_model_name):

        """ 得到所有需要的数据 """

        self.set_model_name(risk_model_name)
        self.style_factor_name = self.get_risk_factor_list()
        self.industry_factor_name = Stock().get_industry_citic1_en_name()
        self.pct_chg = Stock().read_factor_h5("Pct_chg")
        self.free_mv_data = Stock().read_factor_h5("Mkt_freeshares") / 100000000.0
        self.trade_status = Stock().read_factor_h5("TradingStatus")
        self.industry = Stock().read_factor_h5("industry_citic1")
        self.style_factor_data = pd.Panel()

        for i_style in range(len(self.style_factor_name)):

            factor_name = self.style_factor_name[i_style]
            data = RiskFactor().get_risk_factor_exposure(factor_name)
            self.style_factor_data = pd.concat([self.style_factor_data, data], axis=0)

        self.style_factor_data.items = self.style_factor_name

    def get_data_date(self, date):

        """ 当日回归所需数据  """

        before_date = Date().get_trade_date_offset(date, -1)
        print("Get data At %s %s " % (before_date, date))

        # 前一天风格、行业暴露、自由流通市值
        industry_date = self.industry[before_date]
        industry_dummy_date = pd.get_dummies(industry_date)
        industry_columns = list(map(Stock().get_industry_citic1_name, list(industry_dummy_date.columns)))
        industry_dummy_date.columns = industry_columns
        style_date = pd.DataFrame(self.style_factor_data[:, :, before_date])
        style_date = style_date.T.dropna(how='all').T
        style_date = style_date.dropna(how='all')

        self.style_factor_name = list(style_date.columns)

        free_mv_date = pd.DataFrame(self.free_mv_data[before_date])
        free_mv_date.columns = ['FreeMv']

        # 去掉全部缺失的因子和全部缺失的股票
        exposure_date = pd.concat([style_date, industry_dummy_date], axis=1)
        exposure_date = exposure_date.T.dropna(how='all').T
        exposure_date = exposure_date.dropna(how='all')

        # 当日收益率、停牌信息
        pct_data = pd.DataFrame(self.pct_chg[date])
        pct_data.columns = ['Pct']
        trade_status = pd.DataFrame(self.trade_status[date])
        trade_status.columns = ['TradeStatus']

        # 去除停牌股票
        data = pd.concat([pct_data, trade_status, exposure_date], axis=1)
        data = data.dropna(subset=["Pct", 'TradeStatus'], how='all')
        data = data[data['TradeStatus'] == 0.0]
        del data['TradeStatus']

        # 加入市场
        data['ChinaEquity'] = 1.0

        # 补全缺失值
        data_median = data.median()
        data = data.fillna(data_median)

        # 去除没有股票的行业 风格里面也有GEM这种类似行业因子的情况
        data = data[data.columns[data.sum() != 0]]
        self.industry_factor_name = list(filter(lambda x: x in data.columns, self.industry_factor_name))
        self.style_factor_name = list(filter(lambda x: x in data.columns, self.style_factor_name))

        # 风格需要市值加权平均值标准化
        result = Stock().standardization_cross_free_mv(data[self.style_factor_name], self.free_mv_data, before_date)
        data[self.style_factor_name] = result

        # 得到行业市值权重
        concat_data = pd.concat([data[self.industry_factor_name], free_mv_date], axis=1)
        concat_data = concat_data.dropna(subset=[self.industry_factor_name], how='all')
        industry_data = concat_data[self.industry_factor_name].T
        free_mv = pd.DataFrame(concat_data['FreeMv'])
        free_mv = free_mv.fillna(0.0)

        industry_weight = industry_data.dot(free_mv)
        industry_weight = industry_weight / industry_weight.sum()
        industry_weight.columns = ['Weight']
        return data, industry_weight

    def cal_return_date(self, date):

        """
        计算每日的因子收益率、因子暴露、股票的残差收益率
        这是一个有限制条件的 OLS
        行业部分有约束 市值加权的因子收益率为0
        """

        data, industry_weight = self.get_data_date(date)

        factor_return_up = 8.0
        factor_return_low = -8.0
        min_period = 50

        y = data['Pct'].values
        x = data.iloc[:, 1:].values

        if len(data) > min_period:

            P = 2 * np.dot(x.T, x)
            Q = -2 * np.dot(x.T, y)

            # 收益率上下限为

            G_up = np.diag(np.ones(x.shape[1]))
            G_low = - np.diag(np.ones(x.shape[1]))
            G = np.row_stack((G_up, G_low))
            h_up = np.row_stack(np.ones((x.shape[1], 1))) * factor_return_up
            h_low = - np.row_stack(np.ones((x.shape[1], 1))) * factor_return_low
            h = np.row_stack((h_up, h_low))

            # 行业约束
            A = np.column_stack(np.zeros((1, x.shape[1])))
            A_pd = pd.DataFrame(A, index=data.columns[1:], columns=['Weight'])
            A_pd.loc[self.industry_factor_name, "Weight"] = industry_weight.loc[self.industry_factor_name, "Weight"]
            A = A_pd.T.values
            b = np.array([0.0])

            # 开始规划求解因子收益率
            try:
                P = matrix(P)
                Q = matrix(Q)
                G = matrix(G)
                h = matrix(h)
                A = matrix(A)
                b = matrix(b)
                result = sol.qp(P, Q, G, h, A, b)
                factor_return_date = pd.DataFrame(np.array(result['x'][0:]), columns=[date], index=data.columns[1:])
                print("Risk Regression Factor Return %s %s" % (date, self.risk_model_name))
            except Exception as e:
                factor_return_date = pd.DataFrame([], columns=[date], index=data.columns[1:])
                print("Risk Regression Factor Return is Error %s %s" % (date, self.risk_model_name))
        else:
            factor_return_date = pd.DataFrame([])

        # 残差收益
        exposure_before_date = pd.DataFrame(data.iloc[:, 1:])
        stock_return = pd.DataFrame(data['Pct'])
        risk_factor_return = pd.DataFrame(exposure_before_date.dot(factor_return_date))
        risk_factor_return.columns = ['RiskFactorPct']
        stock_residual = pd.concat([stock_return, risk_factor_return], axis=1)
        stock_residual['ResReturn'] = stock_residual['Pct'] - stock_residual['RiskFactorPct']
        res_return_date = pd.DataFrame(stock_residual['ResReturn'])
        res_return_date.columns = [date]

        return factor_return_date, exposure_before_date, res_return_date

    def cal_return_all(self, beg_date, end_date, risk_model_name, period='D'):

        """ 计算每天的因子收益率、因子暴露、股票的残差收益率 """

        self.set_model_name(risk_model_name)
        self.get_data_all(risk_model_name)

        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        date_series = list(set(date_series) & set(self.pct_chg.columns) & set(self.free_mv_data.columns) &
                           set(self.trade_status.columns) & set(self.industry.columns))
        date_series.sort()

        factor_return = pd.DataFrame()
        res_return = pd.DataFrame()

        # 因子暴露文件
        for i_date in range(len(date_series)):

            date = date_series[i_date]
            before_date = Date().get_trade_date_offset(date, -1)
            factor_return_date, exposure_before_date, res_return_date = self.cal_return_date(date)
            exposure_file = os.path.join(self.exposure_path, "exposure_%s.csv" % before_date)
            exposure_before_date.to_csv(exposure_file)
            factor_return = pd.concat([factor_return, factor_return_date], axis=1)
            res_return = pd.concat([res_return, res_return_date], axis=1)

        # 因子收益率文件
        factor_return = factor_return.T
        factor_return_file = os.path.join(self.factor_return_path, "factor_return.csv")
        if os.path.exists(factor_return_file):
            old_data = self.get_factor_return()
            factor_return = Stock().pandas_add_row(old_data, factor_return)
        factor_return.to_csv(factor_return_file)
        factor_return_cum = factor_return.cumsum()
        factor_return_file = os.path.join(self.factor_return_path, "factor_return_cum.csv")
        factor_return_cum.to_csv(factor_return_file)

        # 股票残差率文件
        res_return = res_return.T
        res_return_file = os.path.join(self.res_return_path, "stock_residual_return.csv")
        if os.path.exists(res_return_file):
            old_data = self.get_stock_residual_return()
            res_return = Stock().pandas_add_row(old_data, res_return)
        res_return.to_csv(res_return_file)

    def get_factor_exposure(self, date, risk_model_name="cne5"):

        """ 得到因子暴露值 """

        self.set_model_name(risk_model_name)
        exposure_file = os.path.join(self.exposure_path, "exposure_%s.csv" % date)
        if os.path.exists(exposure_file):
            old_data = pd.read_csv(exposure_file, index_col=[0], encoding='gbk')
            old_data.index = old_data.index.map(str)
        else:
            print("File is not Exist")
            old_data = pd.DataFrame([])
        return old_data

    def get_factor_return(self, risk_model_name="cne5"):

        """ 得到因子收益率 """

        self.set_model_name(risk_model_name)
        factor_return_file = os.path.join(self.factor_return_path, "factor_return.csv")
        if os.path.exists(factor_return_file):
            old_data = pd.read_csv(factor_return_file, index_col=[0], encoding='gbk')
            old_data.index = old_data.index.map(str)
        else:
            print("File is not Exist")
            old_data = pd.DataFrame([])
        return old_data

    def cal_factor_cum_return(self,
                              risk_model_name="cne5",
                              beg_date="20040101",
                              end_date=datetime.today().strftime("%Y%m%d")):

        """ 计算和得到因子累计收益率 """
        self.set_model_name(risk_model_name)
        data = self.get_factor_return()
        data_cum = data.loc[beg_date:end_date, :].cumsum()
        factor_return_file = os.path.join(self.factor_return_path, "factor_return_cum.csv")
        data_cum.to_csv(factor_return_file)
        return data_cum

    def get_stock_residual_return(self, risk_model_name="cne5"):

        """ 得到股票残差收益率 """

        self.set_model_name(risk_model_name)
        res_return_file = os.path.join(self.res_return_path, "stock_residual_return.csv")
        if os.path.exists(res_return_file):
            old_data = pd.read_csv(res_return_file, index_col=[0], encoding='gbk')
            old_data.index = old_data.index.map(str)
        else:
            print("File is not Exist")
            old_data = pd.DataFrame([])
        return old_data

    def cal_factor_cov_date(self, date, risk_model_name="cne5"):

        """
        因子协方差 (USE4)
        1、利用因子日度收益率来估算因子的协方差矩阵 采用指数加权的办法
           因子方差采用 half_life=252 协方差采用half_life=504
        2、EM算法处理缺失的因子收益率的数值
        3、Newey-West Approach
        4、Factor Regime Adjustment

        这里只采用1
        """

        var_half_life = 252
        cov_half_life = 504
        self.set_model_name(risk_model_name)
        data = self.get_factor_return(risk_model_name)
        var_beg_date = Date().get_trade_date_offset(date, -var_half_life)
        cov_beg_date = Date().get_trade_date_offset(date, -cov_half_life)

        data_date = data.loc[var_beg_date:date, :]
        var = data_date.ewm(halflife=var_half_life).std() * np.sqrt(252)
        var_date = var.loc[date, :]

        data_date = data.loc[cov_beg_date:date, :]
        cov = data_date.ewm(halflife=cov_half_life).cov() * np.sqrt(252)
        cov_date = cov[date, :, :]

        for i_factor in range(len(var_date.index)):
            factor_name = var_date.index[i_factor]
            cov_date.loc[factor_name, factor_name] = var_date[factor_name]

        file = os.path.join(self.factor_cov_path, 'factor_cov_%s.csv' % date)
        cov_date.to_csv(file)

    def cal_stock_residual_vol_date(self, date, risk_model_name="cne5"):

        """
        股票残差收益率波动率估计 (USE4)
        1、利用因子日度收益率来估算因子的协方差矩阵 采用指数加权的办法
           因子方差采用 half_life=252
        2、贝叶斯压缩估计
        3、Newey-West Approach
        4、Factor Regime Adjustment

        这里只采用1
        """

        var_half_life = 252
        self.set_model_name(risk_model_name)
        data = self.get_stock_residual_return(risk_model_name)
        var_beg_date = Date().get_trade_date_offset(date, -var_half_life)

        data_date = data.loc[var_beg_date:date, :]
        var = data_date.ewm(halflife=var_half_life).std() * np.sqrt(252)
        var_date = var.loc[date, :]
        cov_date = pd.DataFrame([], index=var_date.index, columns=var_date.index)
        cov_date = cov_date.fillna(0.0)

        for i_factor in range(len(var_date.index)):
            factor_name = var_date.index[i_factor]
            cov_date.loc[factor_name, factor_name] = var_date[factor_name]

        file = os.path.join(self.stock_res_cov_path, 'stock_res_cov_%s.csv' % date)
        cov_date.to_csv(file)

    def cal_stock_vol_date(self, date, risk_model_name="cne5"):

        """ 股票收益率波动率估计 """

        self.set_model_name(risk_model_name)
        stock_exposure = self.get_factor_exposure(date, risk_model_name)
        factor_cov = self.get_factor_cov(date, risk_model_name)
        stock_res_vol = self.get_stock_residual_vol(date, risk_model_name)

        stock_cov = stock_exposure.dot(factor_cov.dot(stock_exposure.T)).add(stock_res_vol)
        # stock_cov_mean = stock_cov.mean().mean()
        # stock_cov = stock_cov.fillna(stock_cov_mean)

        file = os.path.join(self.stock_cov_path, 'stock_cov_%s.csv' % date)
        stock_cov.to_csv(file)

    def cal_vol_all(self, beg_date, end_date, risk_model_name, period='W'):

        """ 计算每天的因子波动率、股票残差波动率、股票波动率（时间较长，一般只计算周度数据） """

        self.set_model_name(risk_model_name)
        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print("Risk Factor and Stock Cov %s %s" % (date, self.risk_model_name))
            self.cal_factor_cov_date(date, risk_model_name)
            self.cal_stock_residual_vol_date(date, risk_model_name)
            self.cal_stock_vol_date(date, risk_model_name)

    def get_factor_cov(self, date, risk_model_name="cne5"):

        """ 因子协方差矩阵 """

        self.set_model_name(risk_model_name)
        factor_cov_file = os.path.join(self.factor_cov_path, 'factor_cov_%s.csv' % date)
        if os.path.exists(factor_cov_file):
            old_data = pd.read_csv(factor_cov_file, index_col=[0], encoding='gbk')
            old_data.index = old_data.index.map(str)
        else:
            print("File is not Exist")
            old_data = pd.DataFrame([])
        return old_data

    def get_stock_residual_vol(self, date, risk_model_name="cne5"):

        """ 股票残差收益率波动率估计 """

        self.set_model_name(risk_model_name)
        factor_cov_file = os.path.join(self.stock_res_cov_path, 'stock_res_cov_%s.csv' % date)
        if os.path.exists(factor_cov_file):
            old_data = pd.read_csv(factor_cov_file, index_col=[0], encoding='gbk')
            old_data.index = old_data.index.map(str)
        else:
            print("File is not Exist")
            old_data = pd.DataFrame([])
        return old_data

    def get_stock_vol_date(self, date, risk_model_name="cne5"):

        """ 股票收益率波动率估计  """

        self.set_model_name(risk_model_name)
        factor_cov_file = os.path.join(self.stock_cov_path, 'stock_cov_%s.csv' % date)
        if os.path.exists(factor_cov_file):
            old_data = pd.read_csv(factor_cov_file, index_col=[0], encoding='gbk')
            old_data.index = old_data.index.map(str)
        else:
            print("File is not Exist")
            old_data = pd.DataFrame([])
        return old_data

    def risk_model_performance(self, risk_model_name="cne5", period='M'):

        """ 检验模型当中的因子对收益率的解释能力 主要计算 R2 """

        self.set_model_name(risk_model_name)
        self.get_data_all(risk_model_name)
        price = Stock().read_factor_h5("Price_Unadjust")
        num = Date().get_period_number_for_year(period)

        print("Test Risk Model %s From %s To %s" % (risk_model_name, beg_date, end_date))

        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        date_series = list(set(date_series) & set(self.style_factor_data.minor_axis) & set(price.columns))
        date_series.sort()
        factor_return_total = pd.DataFrame()
        t_value_total = pd.DataFrame()
        r_square = pd.DataFrame([], columns=['R2'])

        # 因子暴露文件
        for i_date in range(0, len(date_series) - 1):

            cur_date = date_series[i_date]
            next_date = Date().get_trade_date_offset(cur_date, 1)
            exposure_date, industry_data = self.get_data_date(next_date)

            buy_date = cur_date
            sell_date = date_series[i_date + 1]
            stock_pct = price[sell_date] / price[buy_date] - 1.0
            exposure_date['Pct'] = stock_pct
            data = exposure_date
            data = data.dropna()
            data = data.drop(labels=['ChinaEquity'], axis=1)

            y = data['Pct'].values
            x = data.iloc[:, 1:].values
            model = sm.OLS(y, x).fit()

            factor_return = pd.DataFrame(model.params[:], index=data.columns[1:], columns=[cur_date])
            t_value = pd.DataFrame(model.tvalues[:], index=data.columns[1:], columns=[cur_date])
            factor_return_total = pd.concat([factor_return_total, factor_return], axis=1)
            t_value_total = pd.concat([t_value_total, t_value], axis=1)

            r_square.loc[cur_date, 'R2'] = model.rsquared_adj

        # 去掉行业因子
        factor_return_total = factor_return_total.T
        factor_return_total = factor_return_total[self.get_risk_factor_list()]
        t_value_total = t_value_total.T
        t_value_total = t_value_total[self.get_risk_factor_list()]

        t_value_ratio = (t_value_total.abs() > 2).sum(axis=0) / t_value_total.count(axis=0)
        t_value_abs_mean = t_value_total.abs().mean()
        factor_return_std = factor_return_total.std(axis=0) * np.sqrt(num)
        summary = pd.concat([t_value_ratio, t_value_abs_mean, factor_return_std], axis=1)
        summary = summary.dropna()
        summary.columns = ["T值绝对值大于2的比率", 'T值绝对值均值', '因子年化波动率']
        summary['模型平均R2'] = r_square['R2'].mean()
        summary = summary.sort_values(by=['T值绝对值大于2的比率'], ascending=True)

        file = os.path.join(self.model_performance_path, 'Summary_%s.xlsx' % risk_model_name)

        excel = WriteExcel(file)
        num_format_pd = pd.DataFrame([], columns=summary.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        num_format_pd.loc['format', ['T值绝对值均值']] = '0.00'

        worksheet = excel.add_worksheet(risk_model_name)
        excel.write_pandas(summary, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        num_format_pd = pd.DataFrame([], columns=r_square.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        excel.write_pandas(r_square, worksheet, begin_row_number=0, begin_col_number=8,
                           num_format_pd=num_format_pd, color="red", fillna=True)
        excel.close()


if __name__ == '__main__':

    from datetime import datetime
    beg_date = "20060105"
    end_date = datetime.today().strftime("%Y%m%d")
    risk_model_name = "cne5"
    date = "20190104"
    period = 'M'

    self = RiskModel()
    # self.cal_return_all(beg_date, end_date, risk_model_name)
    # self.cal_vol_all(beg_date, end_date, risk_model_name)

    self.risk_model_performance("cne5")
    self.risk_model_performance("risk_model")
