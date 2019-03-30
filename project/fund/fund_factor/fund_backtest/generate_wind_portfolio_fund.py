import pandas as pd
import os
import statsmodels.api as sm
from quant.source.wind_portfolio import WindPortUpLoad
from quant.source.backtest_fund import PortBackTestFund


def GenerateWindFundPorfolio(name, port_name):

    # 参数 shift_name 为后置一期
    ###########################################################################################
    path = r'E:\3_Data\4_fund_data\2_fund_factor'
    min_number = 5
    max_number = 300
    ratio = 0.20
    port_path = r'E:\3_Data\5_stock_data\4_portfolio_wind'

    # 基金 alpha factor 因子值
    ###########################################################################################
    file = os.path.join(path, "exposure", name + '.csv')
    values = pd.read_csv(file, index_col=[0], encoding='gbk')

    sub_path = os.path.join(port_path, port_name)
    if not os.path.exists(sub_path):
        os.makedirs(sub_path)

    # 每期做截面回归 并分组
    ###########################################################################################
    for i in range(len(values.columns)):

        # 确定日期
        ###########################################################################################
        date = values.columns[i]
        data = pd.DataFrame(values[date])
        data = data.dropna()
        position = min(max(min_number, int(len(data)*ratio)), max_number)
        data = data.sort_values(by=[date], ascending=False)
        data = data.iloc[0:position, :]
        data.columns = ["Alpha"]
        if len(data) > 0:

            data["Code"] = data.index
            data["Weight"] = 1 / len(data)
            data["Price"] = 0.0
            data["Direction"] = "Long"
            data["CreditTrading"] = "No"
            data["Date"] = date

            file = port_name + "_" + date + '.csv'
            file = os.path.join(sub_path, file)
            data.to_csv(file, index=False)


def GenerateWindFundPorfolioAndBackTest(name, port_name):

    GenerateWindFundPorfolio(name, port_name)
    # WindPortUpLoad().upload_weight_period(port_name)

    backtest = PortBackTestFund()
    backtest.set_info(port_name, "885012.WI")
    backtest.set_weight_at_all_change_date()
    backtest.cal_turnover()
    backtest.set_weight_at_all_daily()
    backtest.cal_port_return()
    backtest.cal_summary()


if __name__ == "__main__":

    # GenerateWindFundPorfolioAndBackTest("FundRegressionIndex_AlphaReturnMean_120", "回归IndexAlphaMean120")
    # GenerateWindFundPorfolioAndBackTest("MorningStar_MRAR_2_12", "晨星核心指标")
    # GenerateWindFundPorfolioAndBackTest("FundHolderQuarter_AlphaReturnMean_480", "季报AlphaMean480")
    # GenerateWindFundPorfolioAndBackTest("FundHolderQuarter_AlphaReturnMean_480", "季报AlphaMean480")
    # GenerateWindFundPorfolioAndBackTest("FundRegressionIndex_AlphaReturnMean_480", "回归IndexAlphaMean480")

    GenerateWindFundPorfolioAndBackTest("FundHolderQuarter_AlphaReturnIR_1200", "季报AlphaIR1200")
    GenerateWindFundPorfolioAndBackTest("FundHolderQuarter_AlphaReturnMean_1200", "季报AlphaMean1200")
