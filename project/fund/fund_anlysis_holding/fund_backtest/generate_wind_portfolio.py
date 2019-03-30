import pandas as pd
import os
import statsmodels.api as sm


def TestFundAlphaFactor(name):

    # 参数 shift_name 为后置一期
    ###########################################################################################
    path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    min_number = 5
    ratio = 0.10
    name = "FundAlphaReturnQuarter"

    # 基金 alpha factor 因子值
    ###########################################################################################
    file = os.path.join(path, "FundAlphaFactor", name + '.csv')
    values = pd.read_csv(file, index_col=[0], encoding='gbk')

    # 每期生成wind组合
    ###########################################################################################
    for i in range(len(values.columns)):

        # 确定日期
        ###########################################################################################
        date = values.columns[i]
        val = values[date]
        data = pd.DataFrame(val)
        data.columns = ['val']
        data = data.dropna()
        position = max(min_number, int(len(data)*ratio))
        data = data.sort_values(by=['val'], ascending=False)
        data = data.iloc[0:position, :]

    file = name + "BackTestReturn.csv"
    file = os.path.join(path, "FundAlphaBackTest", file)
    data.to_csv(file)


if __name__ == "__main__":

    TestFundAlphaFactor()

