from quant.data.data import Data
from quant.stock.date import Date
from quant.source.fin_db import FinDb
from quant.fund.fund_pool import FundPool
from quant.fund.fund_static import FundStatic

import os
import pandas as pd
from datetime import datetime


class FundHolder(Data):

    """
    1、下载基金持仓
    load_fund_holding_stock()
    load_fund_holding_industry()

    2、得到基金持仓
    get_fund_holding_stock_all()
    get_fund_holding_industry_all()
    get_fund_holding_stock_date()
    get_fund_top10_stock_date()
    get_fund_all_stock_date()

    3、将每个基金的各期的股票权重存储成为一个文件 有很多地方方便读取
    cal_fund_stock_weight_halfyear()
    cal_fund_stock_weight_quarter()
    get_fund_stock_weight_halfyear()
    get_fund_stock_weight_quarter()
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_holding_data'
        self.data_path_holder = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_fund_holding_industry(self, beg_date=None, end_date=None):

        """ 下载所有基金行业持仓 """

        if beg_date is None:
            beg_date = "19991231"
        if end_date is None:
            end_date = datetime.today()

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        new_data = FinDb().load_raw_data_filter_period("Fund_Industry_Holding", beg_date, end_date)

        fund_info_data = FundStatic().get_findb_fund_info()
        fund_info_data = fund_info_data.rename(columns={"证券内码": "基金内码", "证券代码": "基金代码"})

        new_data = pd.merge(new_data, fund_info_data, on="基金内码", how='inner')
        new_data = new_data[["发布日期", "截至日期", "基金代码", "基金简称",
                             "行业代码", "行业名称", "占净值比", "持仓市值"]]
        new_data = new_data.sort_values(by=["截至日期", "基金代码", "行业代码"], ascending=True)
        Index = pd.MultiIndex.from_arrays(new_data[["截至日期", "基金代码", "行业代码"]].T.values,
                                          names=["截至日期", "基金代码", "行业代码"])
        data = pd.DataFrame(new_data[["发布日期", "基金简称", "行业名称",
                                      "占净值比", "持仓市值"]].values, index=Index,
                                columns=["发布日期", "基金简称", "行业名称",
                                        "占净值比", "持仓市值"])

        data.index.names = ["ReportDate", "FundCode", "IndustryCode"]
        data.columns = ["PublishDate", "FundName", "IndustryName", "Weight", "MarketValue"]
        out_file = os.path.join(self.data_path_holder, "Fund_Industry_Holding.csv")
        data.to_csv(out_file)

    def load_fund_holding_stock(self, beg_date=None, end_date=None):

        """ 下载所有基金股票持仓 """

        if beg_date is None:
            beg_date = "19991231"
        if end_date is None:
            end_date = datetime.today()

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        new_data = FinDb().load_raw_data_filter_period("Fund_Stock_Holding", beg_date, end_date)

        fund_info_data = FundStatic().get_findb_fund_info()
        fund_info_data = fund_info_data.rename(columns={"证券内码": "基金内码", "证券代码": "基金代码"})

        stock_info_data = FundStatic().get_findb_sec_info()
        stock_info_data = stock_info_data.rename(columns={"证券内码": "股票内码", "证券代码": "股票代码"})
        stock_info_data = stock_info_data.ix[:, ["股票内码", "股票代码"]]

        new_data = pd.merge(new_data, fund_info_data, on="基金内码", how='inner')
        new_data = pd.merge(new_data, stock_info_data, on="股票内码", how='inner')
        new_data = new_data[["发布日期", "截至日期", "基金代码", "基金简称",
                             "股票代码", "股票名称", "占净值比", "持仓股数", "持仓市值"]]
        new_data = new_data.sort_values(by=["截至日期", "基金代码", "股票代码"], ascending=True)
        Index = pd.MultiIndex.from_arrays(new_data[["截至日期", "基金代码", "股票代码"]].T.values,
                                          names=["截至日期", "基金代码", "股票代码"])
        data = pd.DataFrame(new_data[["发布日期", "基金简称", "股票名称",
                                      "占净值比", "持仓股数", "持仓市值"]].values, index=Index,
                                columns=["发布日期", "基金简称", "股票名称",
                                        "占净值比", "持仓股数", "持仓市值"])

        data.index.names = ["ReportDate", "FundCode", "StockCode"]
        data.columns = ["PublishDate", "FundName", "StockName", "Weight", "Share", "MarketValue"]
        out_file = os.path.join(self.data_path_holder, "Fund_Stock_Holding.csv")
        data.to_csv(out_file)

    def get_fund_holding_stock_all(self):

        """ 得到全部基金股票持仓 """

        file = os.path.join(self.data_path_holder, "Fund_Stock_Holding.csv")
        fund_holding = pd.read_csv(file, encoding='gbk')
        fund_holding['ReportDate'] = fund_holding['ReportDate'].map(str)
        fund_holding['PublishDate'] = fund_holding['PublishDate'].map(str)
        fund_holding = fund_holding.dropna()
        fund_holding = fund_holding.reset_index(drop=True)

        return fund_holding

    def get_fund_holding_industry_all(self):

        """ 得到全部基金行业持仓 """

        file = os.path.join(self.data_path_holder, "Fund_Industry_Holding.csv")
        fund_holding = pd.read_csv(file, encoding='gbk')
        fund_holding['ReportDate'] = fund_holding['ReportDate'].map(str)
        fund_holding = fund_holding.dropna()
        fund_holding = fund_holding.reset_index(drop=True)

        return fund_holding

    def get_fund_holding_stock_date(self, report_date):

        """ 得到所有基金在某个报告期的股票持仓 """

        data = self.get_fund_holding_stock_all()
        data = data[data['ReportDate'] == report_date]
        data = data.reset_index(drop=True)
        return data

    def get_fund_top10_stock_date(self, fund_code, quarter_date):

        """ 得到某个基金某个报告期 的前十大重仓股 """

        data = self.get_fund_holding_stock_all()
        data_date = data[data.ReportDate == quarter_date]
        data_date_fund = data_date[data_date.FundCode == fund_code]
        fund_top10_stock = pd.DataFrame(data_date_fund.Weight.values,
                                        index=data_date_fund.StockCode, columns=['Weight'])
        fund_top10_stock = fund_top10_stock.sort_values(by=['Weight'], ascending=False)
        fund_top10_stock = fund_top10_stock.dropna()
        fund_top10_stock = fund_top10_stock.iloc[0:10, :]

        return fund_top10_stock

    def get_fund_all_stock_date(self, fund_code, halfyaer_date):

        """ 得到某个基金某个报告期 的所有股票 """

        data = self.get_fund_holding_stock_all()
        data_date = data[data.ReportDate == halfyaer_date]
        data_date_fund = data_date[data_date.FundCode == fund_code]
        fund_all_stock = pd.DataFrame(data_date_fund.Weight.values,
                                        index=data_date_fund.StockCode, columns=['Weight'])
        fund_all_stock = fund_all_stock.sort_values(by=['Weight'], ascending=False)
        fund_all_stock = fund_all_stock.dropna()
        return fund_all_stock

    def cal_fund_stock_weight_halfyear(self):

        """
        将半年报基金持仓分离（权重信息）
        每次都重新计算
        每只基金一张表，每张表示基金不同日期半年报全部持仓权重(需要计算所有基金)
        """

        # 基金持仓信息
        file = os.path.join(self.data_path_holder, "Fund_Stock_Holding.csv")
        data = pd.read_csv(file, usecols=[0, 1, 2, 6], encoding='gbk')

        fund_list = list(set(data['FundCode'].values))
        # fund_pool = FundPool().get_fund_pool_code()
        # fund_list = list(set(fund_list) & set(fund_pool))
        fund_list.sort()

        today = datetime.today()
        date_halfyear_series = Date().get_normal_date_series("19991231", today, "S")
        print(date_halfyear_series)

        for i_fund in range(len(fund_list)):

            fund = fund_list[i_fund]
            print(" Split Fund %s HalfYear Holding Stock" % fund)
            data_fund = data[data.FundCode == fund]
            data_gb = data_fund.groupby(by=["ReportDate", "StockCode"]).mean()
            data_gb = data_gb.sort_index()
            data_gb = data_gb[~data_gb.index.duplicated()]
            data_gb = data_gb.unstack()
            data_gb.columns = data_gb.columns.droplevel(level=0)
            data_gb = data_gb.T
            data_gb.columns = data_gb.columns.map(str)
            col = list(set(data_gb.columns) & set(date_halfyear_series))
            col.sort()
            data_gb = data_gb[col]
            file = os.path.join(self.data_path_holder, "fund_holding_halfyear", "FundHoldingHalfYear_" + fund + '.csv')
            data_gb.to_csv(file)

    def cal_fund_stock_weight_quarter(self):

        """
        将半年报基金持仓分离（权重信息）
        每次都重新计算
        每只基金一张表，每张表示基金不同日期季报重仓持股权重
        """

        file = os.path.join(self.data_path_holder, "Fund_Stock_Holding.csv")
        data = pd.read_csv(file, usecols=[0, 1, 2, 6], encoding='gbk')

        fund_list = list(set(data['FundCode'].values))
        # fund_pool = FundPool().get_fund_pool_code()
        # fund_list = list(set(fund_list) & set(fund_pool))
        fund_list.sort()

        today = datetime.today()
        date_quarter_series = Date().get_normal_date_series("19991231", today, "S")
        print(date_quarter_series)

        for i_fund in range(len(fund_list)):

            fund = fund_list[i_fund]
            print(" Split Fund %s Quarter Holding Stock" % fund)
            data_fund = data[data.FundCode == fund]
            data_gb = data_fund.groupby(by=["ReportDate", "StockCode"]).mean()
            data_gb = data_gb.sort_index()
            data_gb = data_gb[~data_gb.index.duplicated()]
            data_gb = data_gb.unstack()
            data_gb.columns = data_gb.columns.droplevel(level=0)
            data_gb = data_gb.T
            data_gb.columns = data_gb.columns.map(str)
            col = list(set(data_gb.columns) & set(date_quarter_series))
            col.sort()
            data_gb = data_gb[col]

            for i_date in range(len(data_gb.columns)):
                date = data_gb.columns[i_date]
                data_gb[date] = data_gb[date].sort_values(ascending=False)[0:10]

            file = os.path.join(self.data_path_holder, "fund_holding_quarter", "FundHoldingQuarter_" + fund + '.csv')
            data_gb.to_csv(file)

    def get_fund_stock_weight_halfyear(self, fund):

        """ 得到基金半年报持仓 """

        file = os.path.join(self.data_path_holder, "fund_holding_halfyear", "FundHoldingHalfYear_" + fund + '.csv')
        try:
            data = pd.read_csv(file, index_col=[0], encoding='gbk')
            data.columns = data.columns.map(str)
        except Exception as e:
            data = None
        return data

    def get_fund_stock_weight_quarter(self, fund):

        """ 得到基金季报持仓 """

        file = os.path.join(self.data_path_holder, "fund_holding_quarter", "FundHoldingQuarter_" + fund + '.csv')
        try:
            data = pd.read_csv(file, index_col=[0], encoding='gbk')
            data.columns = data.columns.map(str)
        except Exception as e:
            data = None
        return data

    def update_fund_holding(self):

        """ 更新数据 """

        self.load_fund_holding_stock()
        self.load_fund_holding_industry()
        self.cal_fund_stock_weight_halfyear()
        self.cal_fund_stock_weight_quarter()

if __name__ == '__main__':

    self = FundHolder()
    fund_code = '000001.OF'
    quarter_date = "20190331"
    # self.update_fund_holding()
    # print(self.get_fund_top10_stock_date(fund_code, quarter_date))
    # print(self.get_fund_holding_industry_all())
    self.cal_fund_stock_weight_halfyear()
    self.cal_fund_stock_weight_quarter()
    data = self.get_fund_holding_stock_all()
