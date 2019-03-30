import pandas as pd
import os
import statsmodels.api as sm
from quant.source.wind_portfolio import WindPortUpLoad
from quant.source.backtest import PortBackTestStock
from quant.fund.fund import Fund
from quant.stock.date import Date
from datetime import datetime


def GenerateWindStockPorfolio(name, port_name, freq="M"):

    # 参数 shift_name 为后置一期
    ###########################################################################################
    path = r'E:\3_Data\4_fund_data\2_fund_factor'
    port_path = r'E:\3_Data\5_stock_data\4_portfolio_wind'
    min_number = 5
    max_number = 150
    ratio = 0.20

    # 基金 alpha factor 因子值
    ###########################################################################################
    file = os.path.join(path, "exposure", name + '.csv')
    values = pd.read_csv(file, index_col=[0], encoding='gbk')
    values.columns = values.columns.map(lambda x: Date().get_trade_date_offset(x, 0))
    date_series = Date().get_trade_date_series("20040101", datetime.today(), freq)
    values_date_series = list(values.columns)

    use_date_series = list(set(values_date_series) & set(date_series))
    use_date_series.sort()

    sub_path = os.path.join(port_path, port_name)
    if not os.path.exists(sub_path):
        os.makedirs(sub_path)

    # 每期做截面回归 并分组
    ###########################################################################################
    for i in range(0, len(use_date_series)):

        # 确定日期
        ###########################################################################################
        date = use_date_series[i]
        data = pd.DataFrame(values[date])
        data = data.dropna()
        data = data.sort_values(by=[date], ascending=False)

        position = min(max(min_number, int(len(data)*ratio)), max_number)
        data = data.iloc[0:position, :]

        data.columns = ["Alpha"]
        data['Rank'] = data['Alpha'].rank()
        data['RankRatio'] = data['Rank'] / len(data)

        quarter_date = Date().get_last_fund_quarter_date(date)
        print(date, quarter_date)

        stock_data = pd.DataFrame([])

        # 确定基金
        ###########################################################################################
        for i_fund in range(len(data)):

            fund = data.index[i_fund]
            fund_weight = data.loc[fund, "RankRatio"]
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

        stock_data = stock_data.dropna(how='all')
        stock_data_weight = pd.DataFrame(stock_data.sum(axis=1))
        stock_data_weight.columns = ["Weight"]
        stock_data_weight["Weight"] = stock_data_weight["Weight"] / stock_data_weight["Weight"].sum()

        if len(stock_data_weight) > 0:

            stock_data_weight["Code"] = stock_data_weight.index
            stock_data_weight["Price"] = 0.0
            stock_data_weight["Direction"] = "Long"
            stock_data_weight["CreditTrading"] = "No"
            stock_data_weight["Date"] = date

            file = port_name + "_" + date + '.csv'
            file = os.path.join(sub_path, file)
            stock_data_weight.to_csv(file, index=False)


def GenerateWindFundPorfolioAndBackTest(name, port_name):

    GenerateWindStockPorfolio(name, port_name)
    # WindPortUpLoad().upload_weight_period(port_name)

    backtest = PortBackTestStock()
    backtest.set_info(port_name, "PublicQuarter")
    backtest.set_weight_at_all_change_date()
    backtest.cal_turnover()
    backtest.set_weight_at_all_daily()
    backtest.cal_port_return()
    backtest.cal_summary()


if __name__ == "__main__":

    # name = "FundRegressionStyle_AlphaReturnIR_240"
    # port_name = "季报AlphaIR1200"

    GenerateWindFundPorfolioAndBackTest("FundRegressionStyle_AlphaReturnIR_240", "风格AlphaIR240_TopFund")
