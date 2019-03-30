import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel


class RiskFactor(Data):

    """
    所有风险因子的父类

    风险模型的作用
    1、给出股票协方差矩阵，风险因子对模型的解释力（R2）越强，给出的股票协方差矩阵越好
    2、识别和控制风险：对那些对股票有显著影响的单因子波动率不是剧烈的因子，可以考虑放宽或者不做限制
    3、组合绩效分析

    可参考文档
    1、东方证券 东方A股风险模型
    2、Barra USE4
    3、

    测试单个风险因子的具体指标
    一般按照月频率测试
    1、横截面上对股票收益率有显著影响：风险因子单独回归,T值绝对值大于2的比例>60%或者T值绝对值的均值>2
    2、时间序列上因子波动率波动剧烈：年化波动率>5%
       Barra 模型中有很多波动率不是很高的因子，例如流动性因子、残差波动率因子，其被选为风险因子是因为1
    3、因子暴露稳定：因子暴露值前后相关系数>0.85

    测试整个风险模型的具体指标
    1、风险因子共同回归时,调整后的R2
    2、模型中，因子对其他风险因子相关性不高：方差膨胀因子VIF<3
    3、加入因子后，有没有提升整体模型的解释能力

    注意不管是风险模型、还是alpha模型，其模型的构造都和股票池相关

    """

    def __init__(self):

        """ 数据存储位置 """

        Data.__init__(self)
        self.sub_data_path = r'stock_data\risk_model'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.exposure_hdf_path = os.path.join(self.data_path, r'factor\hdf')
        self.exposure_csv_path = os.path.join(self.data_path, r'factor\csv')
        self.factor_performance_path = os.path.join(self.data_path, r'factor_performance')

    def get_risk_factor_exposure(self, factor_name):

        """ 取得风险因子的暴露 """

        data = Stock().read_factor_h5(factor_name, self.exposure_hdf_path)
        return data

    def save_risk_factor_exposure(self, data, factor_name):

        """ 存储成为 CSV 和 HDF 两份 """

        Stock().write_factor_h5(data, factor_name, self.exposure_hdf_path)
        data = self.get_risk_factor_exposure(factor_name)
        data.to_csv(os.path.join(self.exposure_csv_path, '%s.csv' % factor_name))

    def generate_patch_file(self, factor_name, beg_date, end_date):

        """ 将因子生成邮件 patch 格式 """

        data = self.get_risk_factor_exposure(factor_name, beg_date, end_date).T
        data = data.loc[beg_date:end_date, :]
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(data.index))

        for date in date_series:
            data_date = data.loc[date, :]

    def update_risk_factor_exposure(self, factor_name, beg_date, end_date, force=False):

        """
        决定更新因子的时间区间
        1、如果因子不存在 则更新全部区间
        2、如果强制更新因子 更新区间和所给的一致
        """

        file = os.path.join(self.exposure_hdf_path, factor_name + '.h5')
        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        if not os.path.exists(file):
            print("Factor Not Exist %s" % factor_name)
            update_beg_date = min(beg_date, "20050101")
            update_end_date = datetime.today().strftime("%Y%m%d")
            state = "Date NoExist Update All"
        else:
            data = self.get_risk_factor_exposure(factor_name)
            data_beg_date = data.index[0]
            data_end_date = data.index[-1]
            if force:
                update_beg_date = beg_date
                update_end_date = end_date
                state = "Force Update Data Period"
            else:

                if data_beg_date < beg_date and data_end_date > end_date:
                    update_beg_date = beg_date
                    update_end_date = end_date
                    state = "Data Already Calculated"
                elif data_beg_date > beg_date and data_end_date > end_date:
                    update_beg_date = beg_date
                    update_end_date = data_beg_date
                    state = "Update Data Previous"
                elif data_beg_date < beg_date and data_end_date < end_date:
                    update_beg_date = data_end_date
                    update_end_date = end_date
                    state = "Update Data Latest"
                elif data_beg_date > beg_date and data_end_date < end_date:
                    update_beg_date = beg_date
                    update_end_date = end_date
                    state = "Update Data Period"
                else:
                    update_beg_date = beg_date
                    update_end_date = end_date
                    state = "Update Data Period"

        return update_beg_date, update_end_date, state

    def risk_factor_performance(self,
                                factor_name,
                                stock_pool_name="AllChinaStockFilter",
                                beg_date=None,
                                end_date=None,
                                period='M'):

        """ 计算单风险因子的因子收益率波动率、自相关性、T值大于2的比例等等 找到有定价能力的风险因子 """

        exposure = self.get_risk_factor_exposure(factor_name)
        price = Stock().read_factor_h5("Price_Unadjust")
        num = Date().get_period_number_for_year(period)

        if beg_date is None:
            beg_date = exposure.columns[0]
        if end_date is None:
            end_date = exposure.columns[-1]

        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        date_series = list(set(date_series) & set(exposure.columns) & set(price.columns))
        date_series.sort()

        factor_return = pd.DataFrame([], index=date_series, columns=['因子收益率'])

        for i_date in range(0, len(date_series)-1):

            cur_date = date_series[i_date]
            buy_date = cur_date
            sell_date = date_series[i_date + 1]
            stock_list = Stock().get_invest_stock_pool(stock_pool_name, cur_date)
            stock_pct = price[sell_date] / price[buy_date] - 1.0
            exposure_date = exposure[cur_date]
            exposure_next = exposure[sell_date]

            data = pd.concat([exposure_date, exposure_next], axis=1)
            data = data.dropna()
            stock_list_finally = list(set(stock_list) & set(data.index))
            stock_list_finally.sort()
            data = data.loc[stock_list_finally, :]
            auto_corr = data.corr().iloc[0, 1]

            data = pd.concat([exposure_date, stock_pct], axis=1)
            stock_list_finally = list(set(stock_list) & set(data.index))
            stock_list_finally.sort()
            data = data.loc[stock_list_finally, :]
            data.columns = ['x', 'y']
            data = data.dropna()

            if len(data) > 0:

                print("Risk Factor  %s %s %s" % (factor_name, stock_pool_name, cur_date))
                y = data['y'].values
                x = data['x'].values
                x_add = sm.add_constant(x)
                model = sm.OLS(y, x_add).fit()

                factor_return_date = model.params[1]
                rank_corr = data.corr(method="spearman").iloc[0, 1]
                t_value = model.tvalues[1]
                r2 = model.rsquared_adj

                factor_return.loc[cur_date, '因子收益率'] = factor_return_date
                factor_return.loc[cur_date, 'IC'] = rank_corr
                factor_return.loc[cur_date, 'T值'] = t_value
                factor_return.loc[cur_date, '自相关系数'] = auto_corr
                factor_return.loc[cur_date, 'R2'] = r2
            else:
                print("Risk Factor is Null %s %s %s" % (factor_name, stock_pool_name, cur_date))

        factor_return = factor_return.dropna(subset=['因子收益率', 'T值'])
        factor_return['因子累计收益率'] = factor_return['因子收益率'].cumsum()

        factor_return_mean = factor_return['因子收益率'].mean() * num
        factor_return_std = factor_return['因子收益率'].std() * np.sqrt(num)

        rank_ic_mean = factor_return['IC'].mean()
        rank_ic_ir = rank_ic_mean / factor_return['IC'].std() * np.sqrt(num)

        if len(factor_return) > 0:

            abs_t_2_ratio = len(factor_return[factor_return['T值'].abs() > 2]) / len(factor_return)
            data_beg_date = factor_return.index[0]
            data_end_date = factor_return.index[-1]
            abs_t_mean = factor_return['T值'].abs().mean()
            auto_corr_mean = factor_return['自相关系数'].mean()
            r2_mean = factor_return['R2'].mean()

            summary = pd.DataFrame([], columns=['因子表现'])
            summary.loc['因子年化收益率', "因子表现"] = factor_return_mean
            summary.loc['因子年化波动率', "因子表现"] = factor_return_std
            summary.loc['IC均值', "因子表现"] = rank_ic_mean
            summary.loc['ICIR', "因子表现"] = rank_ic_ir
            summary.loc['平均R2', "因子表现"] = r2_mean
            summary.loc['T值绝对值大于2的比率', "因子表现"] = abs_t_2_ratio
            summary.loc['T值绝对值平均数', "因子表现"] = abs_t_mean
            summary.loc['自相关系数平均', "因子表现"] = auto_corr_mean
            summary.loc['期数', "因子表现"] = str(len(factor_return))
            summary.loc['开始日期', "因子表现"] = data_beg_date
            summary.loc['结束日期', "因子表现"] = data_end_date

            path = os.path.join(self.factor_performance_path, stock_pool_name)
            if not os.path.exists(path):
                os.makedirs(path)
            file = os.path.join(path, 'Summary_%s.xlsx' % factor_name)

            excel = WriteExcel(file)
            num_format_pd = pd.DataFrame([], columns=summary.columns, index=['format'])
            num_format_pd.loc['format', :] = '0.00%'

            worksheet = excel.add_worksheet(factor_name)
            excel.write_pandas(summary, worksheet, begin_row_number=0, begin_col_number=1,
                               num_format_pd=num_format_pd, color="red", fillna=True)

            num_format_pd = pd.DataFrame([], columns=factor_return.columns, index=['format'])
            num_format_pd.loc['format', :] = '0.00%'
            excel.write_pandas(factor_return, worksheet, begin_row_number=0, begin_col_number=4,
                               num_format_pd=num_format_pd, color="red", fillna=True)
            excel.close()

        else:
            print("Risk Factor %s is Null in %s" % (factor_name, stock_pool_name))

if __name__ == '__main__':

    self = RiskFactor()
    period = 'M'
    beg_date = "20101010"
    end_date = "20180101"
    stock_pool_name = "AllChinaStockFilter"
    factor_name = "cne5_normal_bp"
    self.risk_factor_performance("risk_normal_fund_etf_holder", period=period, stock_pool_name=stock_pool_name)
    self.risk_factor_performance("risk_raw_gem", period=period, stock_pool_name=stock_pool_name)

    # 测试多个 Risk Factor
    from quant.project.multi_factor.risk_model.model.risk_model import RiskModel
    rm = RiskModel()
    rm.set_model_name("cne5")
    risk_factor_list = rm.get_risk_factor_list()

    for factor_name in risk_factor_list:
        self.risk_factor_performance(factor_name, period=period, stock_pool_name=stock_pool_name)
