import pandas as pd
import os
import statsmodels.api as sm
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.utility.factor_preprocess import FactorPreProcess
from datetime import datetime
import numpy as np


def TestFundAlphaFactor(name, periods="Q"):

    # 参数 shift_name 为后置一期
    ###########################################################################################
    # name = "FundHolderQuarter_AlphaReturnMean_480"
    # periods = "Q"
    path = r'E:\3_Data\4_fund_data\2_fund_factor'
    group_number = 10

    # 读取基金每个季度的数据
    ###########################################################################################
    fund_nav = Fund().get_fund_factor("Repair_Nav", None, None).T

    # 基金 alpha factor 因子值
    ###########################################################################################
    file = os.path.join(path, "exposure", name + '.csv')
    values = pd.read_csv(file, index_col=[0], encoding='gbk')
    values.columns = values.columns.map(str)
    values.columns = values.columns.map(lambda x: Date().get_trade_date_offset(x, 0))
    values = FactorPreProcess().remove_extreme_value_mad(values)
    values = FactorPreProcess().standardization(values)
    label = ["Group_" + str(x) for x in range(1, 1 + group_number)]
    result = pd.DataFrame([], index=values.columns, columns=label)

    # 回测日期
    ###########################################################################################
    backtest_date_series = Date().get_trade_date_series("20040101", datetime.today(), periods)
    values_date_series = list(map(str, list(values.columns)))
    nav_date_series = list(map(str, list(fund_nav.columns)))

    date_series = list(set(backtest_date_series) & set(values_date_series) & set(nav_date_series))
    date_series.sort()

    # 每期做截面回归 并分组
    ###########################################################################################
    for i in range(len(date_series)-1):

        # 确定日期
        ###########################################################################################
        date = date_series[i]
        next_date = date_series[i + 1]
        val = pd.DataFrame(values[date])
        val_next = pd.DataFrame(values[next_date])
        pct = pd.DataFrame(fund_nav[next_date] / fund_nav[date] - 1.0)

        # 合并数据
        ###########################################################################################
        data = pd.concat([val, pct], axis=1)
        data = data.loc[~data.index.duplicated(), :]
        data.columns = ['val', 'pct']
        data = data.dropna()
        data['rank_val'] = data['val'].rank()
        data['rank_pct'] = data['pct'].rank()

        if len(data) > 10:

            try:
                print(name, date)
                # 取得数据
                ###########################################################################################
                x = data['val']
                y = data['pct']

                # 回归求取因子收益率 IC
                ###########################################################################################
                x_add = sm.add_constant(x)
                model = sm.OLS(y, x_add).fit()
                beta = model.params[1]
                result.loc[date, 'AlphaFactor'] = beta
                result.loc[date, "IC"] = data.corr().iloc[0, 1]
                result.loc[date, "RankIC"] = data["rank_val"].corr(data["rank_pct"])

                # 按照因子值排序 求分组平均收益
                ###########################################################################################
                data = data.sort_values(by=['val'], ascending=False)
                data['group'] = pd.qcut(data['val'], group_number, labels=label)
                gb = data.groupby(by=["group"]).mean()["pct"]
                result.loc[date, label] = gb
                mean = gb.mean()
                result.loc[date, "G1ExcessReturn"] = gb.loc["Group_1"] - mean
                result.loc[date, "G10ExcessReturn"] = gb.loc["Group_10"] - mean
                corr_data = pd.concat([val, val_next], axis=1)
                result.loc[date, "AutoCorr"] = corr_data.corr().iloc[0, 1]
            except Exception as e:
                pass
            ###########################################################################################
        else:
            pass

    ###########################################################################################
    result = result.dropna()

    # 计算累计收益率
    ###########################################################################################
    for i_col in range(len(result.columns)):
        col = result.columns[i_col]
        result['Cum' + col] = result[col].cumsum()

    # 存储数据
    ###########################################################################################
    file = name + "BackTestReturn_" + str(periods) + ".csv"
    file = os.path.join(path, "alpha_factor_test_result", file)
    result.to_csv(file)
    ###########################################################################################


def TestAllFundAlphaFactor():

    path = r'E:\3_Data\4_fund_data\2_fund_factor'
    sub_path = os.path.join(path, "alpha_factor_test_result")
    file_list = os.listdir(sub_path)
    file_list.remove("AllBackTestReturn.csv")

    result = pd.DataFrame([], index=file_list)

    for i_file in range(len(file_list)):

        file = file_list[i_file]
        print(file)
        file_name = os.path.join(path, "alpha_factor_test_result", file)
        data = pd.read_csv(file_name, index_col=[0], encoding='gbk')
        result.loc[file, "beg_date"] = data.index[0]
        result.loc[file, "end_date"] = data.index[-1]

        if file[-6:] == "_M.csv":
            f = 12
        else:
            f = 4

        result.loc[file, "alphafactor_median"] = data["AlphaFactor"].median() * f
        result.loc[file, "G1_median"] = data["G1ExcessReturn"].median() * f
        result.loc[file, "G10_median"] = data["G10ExcessReturn"].median() * f
        result.loc[file, "G10_IR"] = data["G10ExcessReturn"].median() / data["G10ExcessReturn"].std() * np.sqrt(f)
        result.loc[file, "IC_median"] = data["IC"].median()
        result.loc[file, "RankIC_median"] = data["RankIC"].median()
        result.loc[file, "RankIC_IR"] = data["RankIC"].median() / data["RankIC"].std() * np.sqrt(f)
        try:
            result.loc[file, "AutoCorr_Mean"] = data["AutoCorr"].mean()
        except Exception as e:
            result.loc[file, "AutoCorr_Mean"] = np.nan

    file = "AllBackTestReturn.csv"
    file = os.path.join(path, "alpha_factor_test_result", file)
    result.to_csv(file)


def TestAllFundAlphaFactorCorr():

    path = r'E:\3_Data\4_fund_data\2_fund_factor'
    sub_path = os.path.join(path, "exposure")
    file_list = os.listdir(sub_path)
    date = "20180630"
    file_list.remove("Corr.csv")

    for i_file in range(len(file_list)):

        file = file_list[i_file]
        print(file)
        file_name = os.path.join(path, "exposure", file)
        data = pd.read_csv(file_name, index_col=[0], encoding='gbk')
        data_date = data[date]
        if i_file == 0:
            result = pd.DataFrame(data_date)
        else:
            result = pd.concat([result, data_date], axis=1)

    result.columns = file_list
    result = result.corr()
    file = os.path.join(path, "exposure", "Corr.csv")
    result.to_csv(file)

if __name__ == '__main__':

    # TestFundAlphaFactor("FundHolderHalfYear_AlphaReturnMean_120")
    # TestFundAlphaFactor("FundHolderHalfYear_AlphaReturnIR_120")
    #
    # TestFundAlphaFactor("FundHolderQuarter_AlphaReturnMean_120")
    # TestFundAlphaFactor("FundHolderQuarter_AlphaReturnIR_120")
    #
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnMean_120")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnIR_120")
    #
    # TestFundAlphaFactor("FundHolderHalfYear_AlphaReturnMean_480")
    # TestFundAlphaFactor("FundHolderHalfYear_AlphaReturnIR_480")

    # TestFundAlphaFactor("FundHolderQuarter_AlphaReturnMean_480")
    # TestFundAlphaFactor("FundHolderQuarter_AlphaReturnIR_480")
    #
    # TestFundAlphaFactor("FundHolderQuarter_FundReturnMean_120")
    # TestFundAlphaFactor("FundHolderQuarter_FundReturnIR_120")
    #
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnIR_120")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnMean_120")
    #
    # TestFundAlphaFactor("MorningStar_MRAR_2_12")
    #
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnIR_480")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnMean_480")
    #
    # TestFundAlphaFactor("FundHolderQuarter_FundReturnMean_240")
    # TestFundAlphaFactor("FundHolderQuarter_FundReturnIR_240")
    #
    # TestFundAlphaFactor("FundHolderQuarter_AlphaReturnMean_1200")
    # TestFundAlphaFactor("FundHolderQuarter_AlphaReturnIR_1200")
    #
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnIR_480")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnMean_480")
    #
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnIR_240")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnMean_240")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnIR_480")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnMean_480")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnIR_720")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnMean_720")
    #
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnIR_240", "M")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnMean_240", "M")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnIR_480", "M")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnMean_480", "M")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnIR_720", "M")
    # TestFundAlphaFactor("FundRegressionStyle_AlphaReturnMean_720", "M")
    #
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnIR_240")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnMean_240")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnIR_480")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnMean_480")
    #
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnIR_240", "M")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnMean_240", "M")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnIR_480", "M")
    # TestFundAlphaFactor("FundRegressionIndex_AlphaReturnMean_480", "M")
    #
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnIR_240", "Q")
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnMean_240", "Q")
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnIR_480", "Q")
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnMean_480", "Q")
    #
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnIR_240", "M")
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnMean_240", "M")
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnIR_480", "M")
    # TestFundAlphaFactor("FundRegressionIndex_FundReturnMean_480", "M")
    #
    # TestFundAlphaFactor("FundHolderQuarter_AlphaReturnMean_480", "M")

    TestAllFundAlphaFactor()
    # TestAllFundAlphaFactorCorr()
