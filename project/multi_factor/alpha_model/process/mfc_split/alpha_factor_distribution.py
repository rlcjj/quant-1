import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from quant.stock.barra import Barra
from quant.stock.stock import Stock
from quant.utility.hdf_mfc import HdfMfc
from quant.utility.factor_preprocess import FactorPreProcess


class AlphaFactorDescribe(object):

    """
    从各个方面描述 原始因子值

    1、某天的分布
    1、1 在某天的分布是否正太
    1、2 在某天的因子值在行业上的均值
    1、3 在某天在因子值随着市值变化

    2、历史上在风格和行业回归后的暴露值 的均值（需要取因子值取残差之后的数据）

    3、原始因子和取残差之后的因子值对比

    """

    def __init__(self):
        pass

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

    def get_free_mv(self):
        free_mv = Stock().read_factor_h5("Mkt_freeshares")
        return free_mv

    def get_total_ln_mv(self):
        total_ln_mv = Stock().read_factor_h5("TotalMarketValueLn", Stock().get_h5_path("my_alpha"))
        return total_ln_mv

    def get_risk_citic1_industry_file(self):
        industry_path = r'E:\New Portfolio Construction Programs\New Portfolio Construction Programs_LTT'
        industry_path += r'\InputData\WindData\IndustryData'
        industry_file = pd.read_csv(os.path.join(industry_path, "CiticCodeList1.csv"), encoding='gbk', index_col=[0])
        industry_file = industry_file[['Alias', 'WindCode', 'Name']]
        return industry_file

    def plot_distribution(self, factor_name, date):

        # 参数
        #####################################################################################
        need_alpha_standardization = True
        need_normal_inv = False

        # 读取Alpha数据
        #####################################################################################
        alpha_exposure = self.get_alpha_exposure(factor_name)
        if need_alpha_standardization:
            alpha_exposure = FactorPreProcess().standardization(alpha_exposure)
        if need_normal_inv:
            alpha_exposure = FactorPreProcess().inv_normalization(alpha_exposure)
        alpha_exposure_date = pd.DataFrame(alpha_exposure[date])

        # 其他数据
        #####################################################################################
        industry_expposure = self.get_risk_citic1_industry_exposure()
        industry_expposure_date = pd.DataFrame(industry_expposure[date])
        industry_file = self.get_risk_citic1_industry_file()
        total_ln_mv = self.get_total_ln_mv()
        total_ln_mv_date = pd.DataFrame(total_ln_mv[date])

        # 计算图所需数据
        #####################################################################################
        # 1、alpha分布
        alpha_exposure_values = alpha_exposure[date].dropna().values
        print("有效数值个数", len(alpha_exposure_values))
        print("平均数", np.mean(alpha_exposure_values))
        print("中位数", np.mean(alpha_exposure_values))
        print("最大数", np.max(alpha_exposure_values))
        print("最小数", np.min(alpha_exposure_values))

        #####################################################################################
        # 2、不同行业下alpha中位数
        data = pd.concat([alpha_exposure_date, industry_expposure_date], axis=1)
        data = data.dropna()
        data.columns = ["Alpha", 'Industry']
        gb_industry = data.groupby(by=['Industry']).median()
        gb_industry.index = gb_industry.index.map(lambda x: industry_file[industry_file.Alias == x].Name.values[0])
        gb_industry.index = gb_industry.index.map(lambda x: x[0:-4])
        gb_industry = gb_industry.sort_values(by=['Alpha'], ascending=False)

        #####################################################################################
        # 2、不同市值对数下alpha中位数
        data = pd.concat([alpha_exposure_date, total_ln_mv_date], axis=1)
        data = data.dropna()
        data.columns = ["Alpha", 'lnmv']
        data['lnmv'] = data['lnmv'].round(2)
        data['lnmvGroup'] = pd.qcut(data['lnmv'], q=10)
        gb_lnmv = data.groupby(by=['lnmvGroup']).median()
        #####################################################################################

        # 画图
        #####################################################################################
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

        #####################################################################################
        # 1、alpha分布
        fig = plt.figure(12)
        ax1 = fig.add_subplot(311)
        ax1.hist(alpha_exposure_values, bins=40, facecolor='blue', edgecolor='black')
        ax1.set_xlabel("标准化后因子中分布", fontsize=8)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)

        # 2、不同行业下alpha中位数
        #####################################################################################
        ax2 = fig.add_subplot(312)
        x_number = np.arange(len(gb_industry)) + 1
        alpha_median = gb_industry['Alpha'].values
        x_index = gb_industry.index.values
        ax2.bar(x_number, alpha_median, width=1, facecolor='blue', edgecolor='black')
        ticks = ax2.set_xticks(x_number)
        labels = ax2.set_xticklabels(x_index, rotation=90, fontsize='small')
        ax2.set_xlabel("不同行业下因子中位数", fontsize=8)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)

        # 2、不同市值对数下alpha中位数
        #####################################################################################
        ax3 = fig.add_subplot(313)

        x_number = np.arange(len(gb_lnmv)) + 1
        alpha_median = gb_lnmv['Alpha'].values
        x_index = gb_lnmv.index.values
        ax3.bar(x_number, alpha_median, width=1, facecolor='blue', edgecolor='black')
        ticks = ax3.set_xticks(x_number)
        labels = ax3.set_xticklabels(x_index, rotation=30, fontsize='small')
        ax3.set_xlabel("不同总指数对数下因子中位数", fontsize=8)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)

        plt.tight_layout(pad=0.15, h_pad=None, w_pad=None, rect=None)
        plt.show()
        #####################################################################################

    def plot_exposure_history(self, factor_name):

        # 数据
        #####################################################################################
        data = Stock().read_factor_h5(factor_name + 'StyleIndustryExposure', Stock().get_h5_path("my_alpha"))
        data = pd.DataFrame(data.mean(axis=1), columns=["MeanExposure"])
        style_name = list(Barra().get_factor_name(type_list=['STYLE'])['NAME_EN'].values)
        data_style = data.loc[style_name, :]
        industry_name = list(filter(lambda x: "Industry" in x, list(data.index)))
        data_insudtry = data.loc[industry_name, :]
        industry_name = list(map(lambda x: int(x[9:]), industry_name))
        industry_file = self.get_risk_citic1_industry_file()
        industry_name = list(map(lambda x: industry_file[industry_file.Alias == x].Name.values[0], industry_name))
        data_insudtry.index = list(map(lambda x: x[0:-4], industry_name))
        data_insudtry = data_insudtry.sort_values(by=["MeanExposure"], ascending=False)
        #####################################################################################

        # 画图 风格
        #####################################################################################
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        fig = plt.figure(12)
        ax1 = fig.add_subplot(211)
        x_number = np.arange(len(data_style)) + 1
        alpha_median = data_style['MeanExposure'].values
        x_index = data_style.index.values
        ax1.bar(x_number, alpha_median, width=1, facecolor='blue', edgecolor='black')
        ticks = ax1.set_xticks(x_number)
        labels = ax1.set_xticklabels(x_index, rotation=30, fontsize='small')
        ax1.set_xlabel("Alpha因子在暴露在风格因子上的历史均值", fontsize=8)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)

        # 画图 行业
        #####################################################################################
        ax2 = fig.add_subplot(212)
        x_number = np.arange(len(data_insudtry)) + 1
        alpha_median = data_insudtry['MeanExposure'].values
        x_index = data_insudtry.index.values
        ax2.bar(x_number, alpha_median, width=1, facecolor='blue', edgecolor='black')
        ticks = ax2.set_xticks(x_number)
        labels = ax2.set_xticklabels(x_index, rotation=90, fontsize='small')

        ax2.set_xlabel("Alpha因子在暴露在行业因子上的历史均值", fontsize=8)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)

        #####################################################################################
        plt.tight_layout(pad=0.15, h_pad=None, w_pad=None, rect=None)
        plt.show()
        #####################################################################################

    def cal_factor_raw_res_diff(self):

        """
        对比因子原始值和因子残差值
        """

        path = r'E:\New Portfolio Construction Programs\New Portfolio Construction Programs\OutputData\Split Factors'
        raw_factor_name = 'HolderBySFNumberFill'
        res_factor_name = 'HolderBySFNumberFill_res'
        date = '20180914'

        raw_file = os.path.join(path, raw_factor_name + '.h5')
        res_file = os.path.join(path, res_factor_name + '.h5')

        raw_data = HdfMfc(raw_file).read_hdf_factor(raw_factor_name)
        res_data = HdfMfc(res_file).read_hdf_factor(res_factor_name)

        diff_data = pd.concat([raw_data[date], res_data[date]], axis=1)
        diff_data = diff_data.dropna()
        diff_data.to_csv(os.path.join(path, raw_factor_name + 'Diff.csv'))


if __name__ == '__main__':

    factor_name = 'ROERankYOY'
    date = '20171229'
    self = AlphaFactorDescribe()

    # AlphaFactorDescribe().plot_distribution(factor_name, date)
    # AlphaFactorDescribe().plot_exposure_history(factor_name)
    AlphaFactorDescribe().cal_factor_raw_res_diff()

