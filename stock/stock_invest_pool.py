from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index_weight import IndexWeight
from quant.stock.stock_forbid_pool import StockForbidPool

from datetime import datetime
import pandas as pd
import os


class StockInvestPool(Data):

    """
    股票可投资池 = 所有股票 - 某些禁投库

    AStock: A股所有企业 - 未上市或已退市 - 次新股 - ST股
    AStockFilter: A股所有企业 - 未上市或已退市 - 次新股 - ST股 - 自由流通市值后20% - 交易额后20% -
                  净资产为负 - 净利润为负 - 营收为负 - 最近半年被处罚
    hs300: 沪深300
    zz500: 中证500

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\stock_pool\invest_stock_pool'
        self.data_path_invest_pool = os.path.join(self.primary_data_path, self.sub_data_path)

    def generate_A_stock_pool(self,
                              beg_date="20040101",
                              end_date=datetime.today().strftime("%Y%m%d"),
                              period="W"):

        """   AStock: A股所有企业 - 未上市或已退市 - 次新股 - ST股 """

        stock_pool_name = "AllChinaStock"
        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        sub_path = os.path.join(self.data_path_invest_pool, stock_pool_name)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print("Generate %s Stock Invest Pool %s" % (stock_pool_name, date))
            all_stock_code_now = StockForbidPool().get_all_stock_code_now()
            all_stock_pd = pd.DataFrame([], index=all_stock_code_now)
            delist_code = StockForbidPool().get_forbid_pool("DelistStockPool", date)
            sub_new_code = StockForbidPool().get_forbid_pool("NewStockPool", date)
            st_code = StockForbidPool().get_forbid_pool("STStockPool", date)

            all_stock_pd = pd.concat([all_stock_pd, delist_code, sub_new_code, st_code], axis=1)
            file = os.path.join(sub_path, "%s_%s.csv" % (stock_pool_name, date))
            all_stock_pd.to_csv(file)

    def generate_A_stock_pool_filter(self,
                                     beg_date="20040101",
                                     end_date=datetime.today().strftime("%Y%m%d"),
                                     period="W"):

        """  AStockFilter: A股所有企业 - 未上市或已退市 - 次新股 - ST股 - 自由流通市值后20% - 交易额后20% -
             净资产为负 - 净利润为负 - 营收为负 - 最近半年被处罚 """

        stock_pool_name = "AllChinaStockFilter"
        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        sub_path = os.path.join(self.data_path_invest_pool, stock_pool_name)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print("Generate %s Stock Invest Pool %s" % (stock_pool_name, date))
            all_stock_code_now = StockForbidPool().get_all_stock_code_now()
            all_stock_pd = pd.DataFrame([], index=all_stock_code_now)

            delist_code = StockForbidPool().get_forbid_pool("DelistStockPool", date)
            sub_new_code = StockForbidPool().get_forbid_pool("NewStockPool", date)
            st_code = StockForbidPool().get_forbid_pool("STStockPool", date)

            negative_netprofit = StockForbidPool().get_forbid_pool("NegativeNeProfitStockPool", date)
            negative_income = StockForbidPool().get_forbid_pool("NegativeIncomeTTMStockPool", date)
            negative_net_asset = StockForbidPool().get_forbid_pool("NegativeNetAssetStockPool", date)

            trade_amount_ratio = StockForbidPool().get_forbid_pool("SmallTradeAmountRatioStockPool", date)
            free_mv_ratio = StockForbidPool().get_forbid_pool("SmallFreeMVRatioStockPool", date)

            bad_account = StockForbidPool().get_forbid_pool("BadAccountsReceivableStockPool", date)
            bad_goodwill_ratio = StockForbidPool().get_forbid_pool("BadGoodwillRatioStockPool", date)
            bad_audit_actegory = StockForbidPool().get_forbid_pool("BadAuditCategoryStockPool", date)

            illegality = StockForbidPool().get_forbid_pool("IllegalityStockPool", date)

            all_stock_pd = pd.concat([all_stock_pd, delist_code, sub_new_code, st_code,
                                      negative_netprofit, negative_net_asset, negative_income,
                                      free_mv_ratio, trade_amount_ratio,
                                      bad_account, bad_goodwill_ratio, bad_audit_actegory,
                                      illegality], axis=1)

            file = os.path.join(sub_path, "%s_%s.csv" % (stock_pool_name, date))
            all_stock_pd.to_csv(file)

    def generate_hs300_stock_pool(self,
                                  beg_date="20050101",
                                  end_date=datetime.today().strftime("%Y%m%d"),
                                  period="W"):

        """ 沪深300股票池 """

        stock_pool_name = "hs300"
        index_code = "000300.SH"
        sub_path = os.path.join(self.data_path_invest_pool, stock_pool_name)
        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        filter_stock = IndexWeight().get_weight(index_code)
        filter_stock.columns = filter_stock.columns.map(str)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            file = os.path.join(sub_path, "%s_%s.csv" % (stock_pool_name, date))
            last_date_list = filter_stock.columns[filter_stock.columns <= date]

            if len(last_date_list) != 0:
                last_date = last_date_list[-1]
            else:
                last_date = filter_stock.columns[0]

            print("Generate %s Stock Invest Pool %s" % (stock_pool_name, last_date))
            stock_date = pd.DataFrame(filter_stock[last_date])
            stock_date = stock_date.dropna()

            filter_stock_pd = pd.DataFrame([], index=stock_date.index, columns=["成分股"])
            filter_stock_pd.to_csv(file)

    def generate_zz500_stock_pool(self,
                                  beg_date="20050101",
                                  end_date=datetime.today().strftime("%Y%m%d"),
                                  period="W"):

        """ 中证500股票池 """

        stock_pool_name = "zz500"
        index_code = "000905.SH"
        sub_path = os.path.join(self.data_path_invest_pool, stock_pool_name)
        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        filter_stock = IndexWeight().get_weight(index_code)
        filter_stock.columns = filter_stock.columns.map(str)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            file = os.path.join(sub_path, "%s_%s.csv" % (stock_pool_name, date))

            last_date_list = filter_stock.columns[filter_stock.columns <= date]

            if len(last_date_list) != 0:
                last_date = last_date_list[-1]
            else:
                last_date = filter_stock.columns[0]
            print("Generate %s Stock Invest Pool %s" % (stock_pool_name, last_date))

            stock_date = pd.DataFrame(filter_stock[last_date])
            stock_date = stock_date.dropna()

            filter_stock_pd = pd.DataFrame([], index=stock_date.index, columns=["成分股"])
            filter_stock_pd.to_csv(file)

    def get_invest_stock_pool(self,
                              stock_pool_name="AllChinaStockFilter",
                              date="20171229"):

        """ 取最近交易日的股票投资池 """

        sub_path = os.path.join(self.data_path_invest_pool, stock_pool_name)

        file_list = os.listdir(sub_path)
        date_list = list(map(lambda x: x[-12:-4], file_list))
        date_list.sort()
        date_list_pd = pd.DataFrame(date_list, index=date_list, columns=["date"])
        date_list_pd = date_list_pd[date_list_pd['date'] <= date]

        if len(date_list_pd) != 0:
            last_trade_days = date_list_pd.index[-1]
        else:
            last_trade_days = date_list[0]

        file = os.path.join(sub_path, "%s_%s.csv" % (stock_pool_name, last_trade_days))
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data_filter = list(data.index[data.count(axis=1) == 0].values)

        return data_filter

    def update_stock_pool(self, beg_date, end_date, period):

        """ 更新最近股票禁投库和股票投资库 """

        StockForbidPool().cal_forbid_pool_all(beg_date, end_date, period)
        self.generate_A_stock_pool(beg_date, end_date, period)
        self.generate_A_stock_pool_filter(beg_date, end_date, period)
        self.generate_hs300_stock_pool(beg_date, end_date, period)
        self.generate_zz500_stock_pool(beg_date, end_date, period)


if __name__ == '__main__':

    # StockInvestPool
    self = StockInvestPool()

    # self.generate_A_stock_pool()
    # self.generate_A_stock_pool_filter()
    self.generate_hs300_stock_pool()
    self.generate_zz500_stock_pool()

    print(self.get_invest_stock_pool("AllChinaStockFilter", date="20180101"))
    print(self.get_invest_stock_pool("hs300"))

