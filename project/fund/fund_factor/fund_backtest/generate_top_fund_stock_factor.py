import pandas as pd
import os
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.stock import Stock
from datetime import datetime


def GenerateStockFactor(name, factor_name, freq="M"):

    # 参数
    ###########################################################################################
    path = r'E:\3_Data\4_fund_data\2_fund_factor'
    min_number = 5
    max_number = 200
    ratio = 0.15
    save_path = r'E:\3_Data\4_fund_data\2_fund_factor\fund_stock_alpha_factor'

    # 读取全部基金Alpha因子值
    ###########################################################################################
    file = os.path.join(path, "exposure", name + '.csv')
    values = pd.read_csv(file, index_col=[0], encoding='gbk')
    values.columns = values.columns.map(str)
    values.columns = values.columns.map(lambda x: Date().get_trade_date_offset(x, 0))
    date_series = Date().get_trade_date_series("20040101", datetime.today(), freq)
    values_date_seris = list(values.columns)

    use_date_series = list(set(values_date_seris) & set(date_series))
    use_date_series.sort()

    # 每期计算股票Alpha因子值
    ###########################################################################################
    for i in range(0, len(use_date_series)):

        # 日期
        ###########################################################################################
        date = use_date_series[i]
        data = pd.DataFrame(values[date])
        data = data.dropna()
        position = min(max(min_number, int(len(data)*ratio)), max_number)
        data = data.sort_values(by=[date], ascending=False)
        data = data.iloc[0:position, :]
        data.columns = ["Alpha"]
        data['Rank'] = data['Alpha'].rank()
        data['RankRatio'] = data['Rank'] / len(data)

        quarter_date = Date().get_last_fund_quarter_date(date)
        print(date, quarter_date)

        stock_data = pd.DataFrame([])

        # 所有基金当期季报股票综合
        ###########################################################################################
        for i_fund in range(len(data)):

            fund = data.index[i_fund]
            fund_weight = data.loc[fund, "RankRatio"]
            # fund_weight = 1
            try:
                fund_holding = Fund().get_fund_holding_quarter(fund=fund)
                fund_holding_date = pd.DataFrame(fund_holding[quarter_date])
                fund_holding_date = fund_holding_date.dropna()
                fund_holding_date *= fund_weight
                fund_holding_date.columns = [fund]
            except Exception as e:
                fund_holding_date = pd.DataFrame([], columns=[fund])
            if i_fund == 0:
                stock_data = fund_holding_date
            else:
                stock_data = pd.concat([stock_data, fund_holding_date], axis=1)

        ###########################################################################################
        stock_data = stock_data.dropna(how='all')
        stock_data_weight = pd.DataFrame(stock_data.sum(axis=1))
        stock_data_weight.columns = [date]

        # 每期股票Alpha合并
        ###########################################################################################
        if i == 0:
            result = stock_data_weight
        else:
            result = pd.concat([result, stock_data_weight], axis=1)

    # 转换成日频率数据
    ####################################################################################################
    result = result.T
    date_series = Date().get_normal_date_series(result.index[0], result.index[-1])

    result_daily = pd.DataFrame([], columns=result.columns)

    for i_date in range(len(date_series)):

        print(date)
        date = date_series[i_date]
        lastly_factor_date = result.index[result.index <= date][-1]
        result_daily.loc[date, :] = result.loc[lastly_factor_date, :]

    result_daily = result_daily.T

    # 股票Alpha数据存储
    ####################################################################################################
    file = os.path.join(save_path, factor_name + "_" + str(freq) + '_TopFund.csv')
    result_daily.to_csv(file)
    result_daily = pd.read_csv(file, index_col=[0], encoding='gbk')
    result_daily.columns = result_daily.columns.map(str)
    Stock().write_factor_h5(result_daily, factor_name + "_" + str(freq) + '_TopFund', "my_alpha")
    ####################################################################################################


if __name__ == "__main__":

    # name = "FundRegressionStyle_AlphaReturnMean_240"
    # factor_name = "FundRegressionStyle_AlphaReturnMean_240"
    # GenerateStockFactor(name, factor_name)
    name = "FundRegressionStyle_AlphaReturnIR_240"
    factor_name = name
    GenerateStockFactor(name, factor_name, "M")