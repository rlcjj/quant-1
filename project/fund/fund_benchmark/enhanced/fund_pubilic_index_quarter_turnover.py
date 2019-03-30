from quant.fund.fund_holder import FundHolder
from quant.fund.fund_pool import FundPool
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.stock import Stock
import pandas as pd
from datetime import datetime
import os
import numpy as np


class FundPublicIndexQuarterTurnOver(object):

    """
    利用每天可得到的基金季报合成指数
    基金是经过筛选的 例如 低换手 持股集中的基金
    """

    def __init__(self):

        self.name = "PublicQuarterTurnOver"
        self.data_weight_path = r"E:\3_Data\2_index_data\2_index_weight\weight"
        self.data_factor_path = r"E:\3_Data\2_index_data\1_index_price_volumn"

    def cal_quarter_holding_allfund_quarter(self, quarter_date):

        """
        计算 季报日 普通股票+偏股混合基金 基金平均持仓
        """

        fund_pool = FundPool().get_fund_pool_code(name="基金持仓基准基金池", date=quarter_date)
        halfyear_date = Date().get_last_fund_halfyear_date(Date().get_trade_date_offset(quarter_date, 15))
        fund_turnover = Fund().get_fund_turnover()
        fund_turnover = fund_turnover.loc[fund_pool, :]
        fund_turnover[fund_turnover < 15] = np.nan
        fund_turnover_date = pd.DataFrame(fund_turnover[halfyear_date])
        fund_turnover_date = fund_turnover_date.dropna()
        fund_turnover_date = fund_turnover_date.sort_values(by=[halfyear_date], ascending=True)
        fund_pool = list(fund_turnover_date.index[0:int(len(fund_turnover_date)/2)])

        for i_fund in range(len(fund_pool)):
            fund = fund_pool[i_fund]
            try:
                fund_holding = FundHolder().get_fund_holding_quarter(fund=fund)
                fund_holding_date = pd.DataFrame(fund_holding[quarter_date])
                fund_holding_date = fund_holding_date.dropna()
                fund_holding_date *= 1.0
                fund_holding_date.columns = [fund]
            except Exception as e:
                fund_holding_date = pd.DataFrame([], columns=[fund])
            if i_fund == 0:
                stock_data = fund_holding_date
            else:
                stock_data = pd.concat([stock_data, fund_holding_date], axis=1)

        stock_data = stock_data.dropna(how='all')
        stock_data_weight = pd.DataFrame(stock_data.sum(axis=1))
        stock_data_weight.columns = ["WEIGHT"]
        stock_data_weight /= stock_data_weight.sum()
        stock_data_weight.index.name = "CODE"

        sub_path = os.path.join(self.data_weight_path, self.name)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        file = os.path.join(sub_path, quarter_date + '_QuarterHolding.csv')
        stock_data_weight.to_csv(file)

    def cal_quarter_holding_allfund_allquarter(self):

        """
        计算 季报日 普通股票+偏股混合基金 基金平均持仓
        """
        date_series = Date().get_normal_date_series("20040101", datetime.today(), "Q")
        for i_date in range(len(date_series)):
            quarter_date = date_series[i_date]
            self.cal_quarter_holding_allfund_quarter(quarter_date)

    def get_quarter_holding_allfund_quarter(self, date):

        sub_path = os.path.join(self.data_weight_path, self.name)
        file = os.path.join(sub_path, date + '_QuarterHolding.csv')
        stock_data_weight = pd.read_csv(file, index_col=[0])
        return stock_data_weight

    def cal_quarter_holding_allfund_daily(self, date):

        quarter_date = Date().get_last_fund_quarter_date(date)
        stock_data_weight = self.get_quarter_holding_allfund_quarter(quarter_date)
        sub_path = os.path.join(self.data_weight_path, self.name)
        file = os.path.join(sub_path, date + '.csv')
        stock_data_weight.to_csv(file)

    def cal_quarter_holding_allfund_alldaily(self):

        date_series = Date().get_normal_date_series("20040501", datetime.today(), "D")
        for i_date in range(len(date_series)):
            date = date_series[i_date]
            self.cal_quarter_holding_allfund_daily(date)

    def get_quarter_holding_allfund_daily(self, date):

        sub_path = os.path.join(self.data_weight_path, self.name)
        file = os.path.join(sub_path, date + '.csv')
        stock_data_weight = pd.read_csv(file, index_col=[0])
        return stock_data_weight

    def cal_return_daily(self):

        stock_return = Stock().read_factor_h5("Pct_chg")
        date_series = Date().get_trade_date_series("20040501", datetime.today(), "D")
        return_date_series = list(stock_return.columns)
        date_series = list(set(return_date_series) & set(date_series))
        date_series.sort()

        result = pd.DataFrame([], index=date_series, columns=["PCT"])

        for i_date in range(len(date_series)):
            date = date_series[i_date]
            weight = self.get_quarter_holding_allfund_daily(date)
            all_data = pd.concat([weight, stock_return[date]], axis=1)
            all_data.columns = ["Weight", "Return"]
            all_data = all_data.dropna()
            pct = (all_data["Weight"] * all_data["Return"]).sum()
            result.loc[date, "PCT"] = pct / 100

        result = result.dropna()
        result["CLOSE"] = (result["PCT"] + 1.0).cumprod() * 1000
        file = os.path.join(self.data_factor_path, self.name + '.csv')
        result.to_csv(file)


if __name__ == '__main__':

    self = FundPublicIndexQuarterTurnOver()
    date = "20171229"
    # FundPublicIndexQuarterTurnOver().cal_quarter_holding_allfund_allquarter()
    # FundPublicIndexQuarterTurnOver().cal_quarter_holding_allfund_alldaily()
    # FundPublicIndexQuarterTurnOver().cal_return_daily()

    from quant.stock.index import Index
    beg_date = "20100102"
    end_date = datetime.today()

    name_list = ["偏股基金总指数", "跟随股票基金指数", "跟随低换手基金", "沪深300", "中证500"]
    code_list = ["885001.WI", "PublicQuarter", 'PublicQuarterTurnOver', "000300.SH", "000905.SH"]

    for i in range(len(code_list)):
        code = code_list[i]
        index_data = Index().get_index_factor(code, beg_date, end_date, ["PCT"])
        if i == 0:
            all_data = index_data
        else:
            all_data = pd.concat([all_data, index_data], axis=1)

    all_data.columns = name_list
    all_data["偏股基金总指数_满仓"] = all_data['偏股基金总指数'] / 0.90
    all_data = all_data.dropna()

    all_data = (all_data + 1.0).cumprod() - 1.0
    all_data.to_csv(r"C:\Users\doufucheng\OneDrive\Desktop\index.csv")



