import pandas as pd
import os
import statsmodels.api as sm
from quant.utility.factor_preprocess import FactorPreProcess


def TestFundAlphaFactor(name):

    # 参数 shift_name 为后置一期
    ###########################################################################################
    path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    shift_name = 1
    group_number = 10

    # 读取基金每个季度的数据
    ###########################################################################################
    file = "FundReturnAfter.csv"
    file = os.path.join(path, "FundReturn", file)
    fund_pct = pd.read_csv(file, index_col=[0], encoding='gbk')

    # 基金 alpha factor 因子值
    ###########################################################################################
    file = os.path.join(path, "FundAlphaFactor", name + '.csv')
    values = pd.read_csv(file, index_col=[0], encoding='gbk')
    values = FactorPreProcess().remove_extreme_value_mad(values)
    values = FactorPreProcess().standardization(values)
    label = ["Group_" + str(x) for x in range(1, 1 + group_number)]
    result = pd.DataFrame([], index=values.columns, columns=label)

    # 每期做截面回归 并分组
    ###########################################################################################
    for i in range(len(values.columns) - shift_name - 1):

        # 确定日期
        ###########################################################################################
        date = values.columns[i]
        date_later = values.columns[i + shift_name]
        val = values[date]
        pct = fund_pct[date_later]

        # 合并数据
        ###########################################################################################
        data = pd.concat([val, pct], axis=1)
        data.columns = ['val', 'pct']
        data = data.dropna()

        if len(data) > 50:

            # 取得数据
            ###########################################################################################
            x = data['val']
            y = data['pct']

            # 回归求取因子收益率 IC
            ###########################################################################################
            x_add = sm.add_constant(x)
            model = sm.OLS(y, x_add).fit()
            beta = model.params[1]
            result.loc[date_later, 'AlphaFactor'] = beta
            result.loc[date_later, "IC"] = data.corr().iloc[0, 1]

            # 按照因子值排序 求分组平均收益
            ###########################################################################################
            data = data.sort_values(by=['val'], ascending=False)
            data['group'] = pd.qcut(data['val'], group_number, labels=label)
            gb = data.groupby(by=["group"]).mean()["pct"]
            result.loc[date_later, label] = gb
            mean = gb.mean()
            result.loc[date_later, "G1ExcessReturn"] = gb.loc["Group_1"] - mean
            result.loc[date_later, "G10ExcessReturn"] = gb.loc["Group_10"] - mean
            ###########################################################################################
        else:
            pass

    # 计算累计收益率
    ###########################################################################################
    for i_col in range(len(result.columns)):
        col = result.columns[i_col]
        result['Cum' + col] = result[col].cumsum()

    # 输出 FactorReturn & ICIR
    ###########################################################################################
    print(name)
    print(result['AlphaFactor'].mean() * 4)
    print(result['IC'].mean() / result['IC'].std() * 2)

    # 存储数据
    ###########################################################################################
    file = name + "BackTestReturn.csv"
    file = os.path.join(path, "FundAlphaBackTest", file)
    result.to_csv(file)
    ###########################################################################################


def TestFundAlphaFactorAll(name):

    factor = name
    TestFundAlphaFactor(factor)

    factor = name + "ZScore"
    TestFundAlphaFactor(factor)
    factor = name + "ZScoreMean"
    TestFundAlphaFactor(factor)
    factor = name + "ZScoreIR"
    TestFundAlphaFactor(factor)

    factor = name + "Percent"
    TestFundAlphaFactor(factor)
    # factor = name + "PercentMean"
    # TestFundAlphaFactor(factor)
    # factor = name + "PercentIR"
    # TestFundAlphaFactor(factor)


if __name__ == '__main__':

    TestFundAlphaFactorAll("FundAlphaReturnQuarter")
    TestFundAlphaFactorAll("FundStyleReturnQuarter")
    TestFundAlphaFactorAll("FundAllReturnQuarter")
    TestFundAlphaFactorAll("FundIndustryReturnQuarter")
    TestFundAlphaFactorAll("FundPctReturnQuarter")


