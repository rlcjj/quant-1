import pandas as pd
import os
from quant.utility.factor_preprocess import FactorPreProcess


def fund_factor_change(name):

    """
    将原始的alpha因子转换成为多种alpha形式
    标准化、标准化值的时间序列IR 百分位数、百分位数的时间序列IR
    """

    # 参数
    ######################################################################################
    T = 6
    path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    # name = "FundAlphaReturnQuarter"

    # 读取原始数值
    ######################################################################################
    file = os.path.join(path, "FundAlphaFactor", name + '.csv')
    data = pd.read_csv(file, index_col=[0], encoding='gbk')

    # 截面排序百分比
    ######################################################################################
    data_rank = data.rank() / data.count()
    file = os.path.join(path, "FundAlphaFactor", name + 'Percent.csv')
    data_rank.to_csv(file)

    # 截面排序百分比 的均值
    ######################################################################################
    data_rank = data.rank() / data.count()
    data_rank_mean = data_rank.T.rolling(window=T).mean().T
    file = os.path.join(path, "FundAlphaFactor", name + 'PercentMean.csv')
    data_rank_mean.to_csv(file)

    # 截面排序百分比IR
    ######################################################################################
    score_mean = data_rank.T.rolling(window=T).mean()
    score_std = data_rank.T.rolling(window=T).std()
    score_ir = score_mean.div(score_std)
    score_ir = score_ir.T

    file = os.path.join(path, "FundAlphaFactor", name + 'PercentIR.csv')
    score_ir.to_csv(file)

    # Zscore
    ######################################################################################
    data = FactorPreProcess().remove_extreme_value_mad(data)
    data = FactorPreProcess().standardization(data)

    file = os.path.join(path, "FundAlphaFactor", name + 'ZScore.csv')
    data.to_csv(file)

    # 截面排序百分比 的均值
    ######################################################################################
    score_mean = data.T.rolling(window=T).mean().T
    file = os.path.join(path, "FundAlphaFactor", name + 'ZScoreMean.csv')
    score_mean.to_csv(file)

    # Zscore IR
    ######################################################################################
    score_mean = data.T.rolling(window=T).mean()
    score_std = data.T.rolling(window=T).std()
    score_ir = score_mean.div(score_std)
    score_ir = score_ir.T
    score_ir = FactorPreProcess().remove_extreme_value_mad(score_ir)
    score_ir = FactorPreProcess().standardization(score_ir)

    file = os.path.join(path, "FundAlphaFactor", name + 'ZScoreIR.csv')
    score_ir.to_csv(file)
    ######################################################################################


if __name__ == '__main__':

    fund_factor_change("FundAlphaReturnQuarter")
    fund_factor_change("FundStyleReturnQuarter")
    fund_factor_change("FundAllReturnQuarter")
    fund_factor_change("FundIndustryReturnQuarter")
    fund_factor_change("FundPctReturnQuarter")
