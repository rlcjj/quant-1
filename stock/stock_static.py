from quant.data.data import Data
from quant.stock.date import Date

import os
import numpy as np
import pandas as pd
from datetime import datetime, time
from WindPy import w
w.start()


class StockStatic(Data):

    """
    下载、得到一些股票常用的性质
    （所有股票池、上市退市日、交易状态、自由流通市值）为了交易使用 所以每天更新

    load_all_stock_code_now
    get_all_stock_code_now

    load_ipo_date()
    get_ipo_date()

    load_trade_status_today()
    get_trade_status_date()

    load_free_market_value_date()
    get_free_market_value_date()

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\stock_basic_data'
        self.data_path_static = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_all_stock_code_now(self):

        """ 下载当前A股的股票池 包含之前所有退市的股票的最大集合"""

        print("###### Loading All Stock Code ######")
        today = datetime.today().strftime('%Y-%m-%d')
        data = w.wset("sectorconstituent", "date=" + today + ";sectorid=a001010100000000")
        data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        now_wind_list = list(data['wind_code'].values)

        data = w.wset("sectorconstituent", "date=" + today + ";sectorid=a001010m00000000")
        data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        delist_list = list(data['wind_code'].values)

        now_list = self.get_all_stock_code_now()
        update_list = list(set(now_list) | set(now_wind_list) | set(delist_list))
        update_list.sort()
        update_code = pd.DataFrame(update_list, columns=['code'])
        file = os.path.join(self.data_path_static, 'All_Stock_Code.csv')
        update_code.to_csv(file)

    def get_all_stock_code_now(self):

        """ 得到当前A股的股票池 包含之前所有退市的股票的最大集合"""

        file = os.path.join(self.data_path_static, 'All_Stock_Code.csv')

        if os.path.exists(file):
            code = pd.read_csv(file, encoding='gbk', index_col=[0])
            now_list = list(code['code'].values)
        else:
            now_list = []
        return now_list

    def load_ipo_date(self):

        """ 下载股票上市时间和退市时间 """

        print("######### Loading IPO date ##########")
        file = os.path.join(self.data_path_static, "Ipo_Date.csv")
        code_list = self.get_all_stock_code_now()
        code_list_str = ','.join(code_list)
        data = w.wss(code_list_str, "ipo_date, delist_date")
        data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        data["IPO_DATE"] = data["IPO_DATE"].map(lambda x: x.strftime("%Y%m%d"))
        data["DELIST_DATE"] = data["DELIST_DATE"].map(lambda x: x.strftime("%Y%m%d"))
        data["DELIST_DATE"] = data["DELIST_DATE"].map(lambda x: "21000101" if x == "18991230" else x)
        data.to_csv(file)

    def get_ipo_date(self):

        """ 得到股票上市时间和退市时间 """

        file = os.path.join(self.data_path_static, "Ipo_Date.csv")
        ipo_date = pd.read_csv(file, encoding='gbk', index_col=[0])
        ipo_date = ipo_date.astype(np.str)
        return ipo_date

    def load_trade_status_today(self):

        """
        下载股票交易状态
        超过9：15 就用今天的数据
        不超过9：15 就用昨天的数据
         """

        today = datetime.today()
        today_str = Date.change_to_str(today)
        before_date = Date().get_trade_date_offset(today, -1)

        out_path = os.path.join(self.data_path_static, "trade_status")
        out_file = os.path.join(out_path, 'trade_status_' + today_str + '.csv')

        code_list = self.get_all_stock_code_now()
        code_list_str = ','.join(code_list)

        if today.time() > time(9, 15):

            print("######### Loading Trade Status At %s #########" % today_str)
            trade_status = w.wsq(code_list_str, "rt_trade_status")
            trade_status_pd = pd.DataFrame(trade_status.Data, index=['Trade_Status'], columns=trade_status.Codes).T
            trade_status_pd = trade_status_pd[(trade_status_pd['Trade_Status'] != 1.0)
                                              & (trade_status_pd['Trade_Status'] != 4.0)]

            if len(trade_status_pd) > 1000:
                trade_status = w.wss(code_list_str, "trade_status", "tradeDate=" + today_str)
                trade_status_pd = pd.DataFrame(trade_status.Data, index=['Trade_Status'], columns=trade_status.Codes).T
                trade_status_pd = trade_status_pd[trade_status_pd['Trade_Status'] != "交易"]
                trade_status_pd.to_csv(out_file)
            else:
                trade_status_pd.to_csv(out_file)

        else:
            print("######### Loading Trade Status At %s #########" % before_date)
            trade_status = w.wss(code_list_str, "trade_status", "tradeDate=" + before_date)
            trade_status_pd = pd.DataFrame(trade_status.Data, index=['Trade_Status'], columns=trade_status.Codes).T
            trade_status_pd = trade_status_pd[trade_status_pd['Trade_Status'] != "交易"]
            trade_status_pd.to_csv(out_file)

    def get_trade_status_date(self, date):

        """ 得到股票交易状态 """

        date = Date.change_to_str(date)
        out_path = os.path.join(self.data_path_static, "trade_status")
        out_file = os.path.join(out_path, 'trade_status_' + date + '.csv')
        trade_status = pd.read_csv(out_file, index_col=[0], encoding='gbk')
        return trade_status

    def load_free_market_value_date(self, date):

        """ 下载股票自由流通市值 """

        print("######### Loading FreeMarketValue At %s #########" % date)
        date = Date.change_to_str(date)
        out_path = os.path.join(self.data_path_static, "Free_Market_Value")
        code_list = self.get_all_stock_code_now()
        code_list_str = ','.join(code_list)
        data = w.wss(code_list_str,  "mkt_freeshares", "unit=1;tradeDate=" + date)
        data = pd.DataFrame(data.Data, index=['Free_Market_Value'], columns=data.Codes).T
        out_file = os.path.join(out_path, "Free_Market_Value_" + date + '.csv')
        data.to_csv(out_file)

    def get_free_market_value_date(self, date):

        """ 得到股票自由流通市值 """

        date = Date.change_to_str(date)
        out_path = os.path.join(self.data_path_static, "Free_Market_Value")
        out_file = os.path.join(out_path, 'Free_Market_Value_' + date + '.csv')
        free_market_value = pd.read_csv(out_file, index_col=[0], encoding='gbk')
        return free_market_value

    def get_industry_citic1(self):

        """ 得到中信一级股票行业对应表 """

        file = os.path.join(self.data_path_static, "CiticCodeList1.csv")
        industry_citic1 = pd.read_csv(file, index_col=[0], encoding='gbk')
        return industry_citic1

    def get_industry_citic1_cn_name(self):

        """ 得到中信一级股票行业对应表中文 """

        industry_citic1 = self.get_industry_citic1()
        industry_citic1 = industry_citic1['Ch'].values
        return industry_citic1

    def get_industry_citic1_en_name(self):

        """ 得到中信一级股票行业对应表英文 """

        industry_citic1 = self.get_industry_citic1()
        industry_citic1 = industry_citic1['En'].values
        return industry_citic1

    def get_industry_citic1_name(self, number):

        """ 得到中信一级股票行业数字转英文 """

        number = int(number)
        industry_citic1 = self.get_industry_citic1()
        industry_citic1 = industry_citic1[industry_citic1['Alias'] == number]
        name = industry_citic1['En'].values[0]
        return name

    def get_industry_citic1_name_ch(self, number):

        """ 得到中信一级股票行业数字转中文 """

        number = int(number)
        industry_citic1 = self.get_industry_citic1()
        industry_citic1 = industry_citic1[industry_citic1['Alias'] == number]
        name = industry_citic1['Ch'].values[0]
        return name

    def load_st_info(self):

        """ 下载股票ST信息 """

        print("######### Loading ST date ##########")
        file = os.path.join(self.data_path_static, "st.csv")
        code_list = self.get_all_stock_code_now()
        code_list_str = ','.join(code_list)
        data = w.wss(code_list_str, "riskadmonition_date")
        data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        data.to_csv(file)

    def get_st_info(self):

        """ 得到股票ST信息 """

        file = os.path.join(self.data_path_static, "ST.csv")
        st = pd.read_csv(file, index_col=[0], encoding='gbk')
        return st

    def load_nature_info(self):

        """ 下载股票公司属性信息 """

        print("######### Loading Type of Company date ##########")
        file = os.path.join(self.data_path_static, "nature.csv")
        code_list = self.get_all_stock_code_now()
        code_list_str = ','.join(code_list)
        data = w.wss(code_list_str, "nature")
        data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        data.to_csv(file)

    def get_nature_info(self):

        """ 得到股票公司属性信息 """

        file = os.path.join(self.data_path_static, "nature.csv")
        st = pd.read_csv(file, index_col=[0], encoding='gbk')
        return st

    def load_stock_pledge(self, beg_date, end_date):

        """ 下载 股票质押情况"""

        index_col = ['wind_code', 'pledged_shares',  'pledge_start_date',
                     'pledge_end_date', 'pledge_termination_date', 'pledge_party']
        new_data = w.wset("sharepledge", "startdate=%s;enddate=%s;sectorid=a001010100000000" % (beg_date, end_date))
        new_data = pd.DataFrame(new_data.Data, index=new_data.Fields, columns=new_data.Codes).T
        new_data['pledge_start_date'] = new_data['pledge_start_date'].map(Date().change_to_str)
        new_data['pledge_end_date'] = new_data['pledge_end_date'].map(Date().change_to_str)
        new_data['pledge_termination_date'] = new_data['pledge_termination_date'].map(Date().change_to_str)
        new_data = new_data.set_index(index_col)
        new_data = new_data.sort_index()

        file = os.path.join(self.data_path_static, "pledge.csv")

        if os.path.exists(file):
            old_data = pd.read_csv(file, encoding='gbk')
            old_data['pledge_start_date'] = old_data['pledge_start_date'].map(str)
            old_data['pledge_end_date'] = old_data['pledge_end_date'].map(str)
            old_data['pledge_termination_date'] = old_data['pledge_termination_date'].map(str)
            old_data = old_data.set_index(index_col)

            data = pd.concat([old_data, new_data], axis=0)
            data = data[~data.index.duplicated()]
            data = data.sort_index()
        else:
            data = new_data

        data.to_csv(file)

    def get_stock_pledge(self):

        """ 得到 股票质押情况"""

        file = os.path.join(self.data_path_static, "pledge.csv")
        data = pd.read_csv(file, encoding='gbk')
        data['pledge_start_date'] = data['pledge_start_date'].map(str)
        data['pledge_end_date'] = data['pledge_end_date'].map(str)
        data['pledge_termination_date'] = data['pledge_termination_date'].map(str)
        return data

    def load_major_holder_deal(self, beg_date, end_date):

        """ 下载 大股东增持减详表 """

        new_data = w.wset("majorholderdealrecord",
                          "startdate=%s;enddate=%s;sectorid=a001010100000000;type=announcedate" % (beg_date, end_date))
        new_data = pd.DataFrame(new_data.Data, index=new_data.Fields, columns=new_data.Codes).T
        new_data['announcement_date'] = new_data['announcement_date'].map(Date().change_to_str)
        new_data['change_start_date'] = new_data['change_start_date'].map(Date().change_to_str)
        new_data['change_end_date'] = new_data['change_end_date'].map(Date().change_to_str)
        index_col = ['wind_code', 'announcement_date',  'shareholder_name']

        new_data = new_data.set_index(index_col)
        new_data = new_data.sort_index()
        print(new_data)

        file = os.path.join(self.data_path_static, "major_holder_deal.csv")

        if os.path.exists(file):
            old_data = pd.read_csv(file, encoding='gbk')
            old_data['announcement_date'] = old_data['announcement_date'].map(str)
            old_data['change_start_date'] = old_data['change_start_date'].map(str)
            old_data['change_end_date'] = old_data['change_end_date'].map(str)
            old_data = old_data.set_index(index_col)

            data = pd.concat([old_data, new_data], axis=0)
            data = data[~data.index.duplicated()]
            data = data.sort_index()
        else:
            data = new_data
        data.to_csv(file)

    def get_major_holder_deal(self):

        """ 得到 大股东增持减详表 """

        file = os.path.join(self.data_path_static, "major_holder_deal.csv")
        old_data = pd.read_csv(file, encoding='gbk')
        old_data['announcement_date'] = old_data['announcement_date'].map(str)
        old_data['change_start_date'] = old_data['change_start_date'].map(str)
        old_data['change_end_date'] = old_data['change_end_date'].map(str)
        return old_data

    def load_stock_illegality(self, beg_date, end_date):

        """ 下载 公司违规处罚情况 只下载了对象为公司的类型"""

        new_data = w.wset("illegality",
                          "startdate=%s;enddate=%s;sectorid=a001010100000000;maintype=company" % (beg_date, end_date))
        new_data = pd.DataFrame(new_data.Data, index=new_data.Fields, columns=new_data.Codes).T
        new_data['announce_date'] = new_data['announce_date'].map(Date().change_to_str)

        index_col = ['wind_code', 'announce_date',  'breach_type',
                     'penalty_object', 'penalty_type', 'processor']

        new_data = new_data.set_index(index_col)
        new_data = new_data.sort_index()

        file = os.path.join(self.data_path_static, "illegality.csv")

        if os.path.exists(file):
            old_data = pd.read_csv(file, encoding='gbk')
            old_data['announce_date'] = old_data['announce_date'].map(str)
            old_data = old_data.set_index(index_col)

            data = pd.concat([old_data, new_data], axis=0)
            data = data[~data.index.duplicated()]
            data = data.sort_index()
        else:
            data = new_data
        data.to_csv(file)

    def get_stock_illegality(self):

        """ 得到 公司违规处罚情况 """

        file = os.path.join(self.data_path_static, "illegality.csv")
        data = pd.read_csv(file, encoding='gbk')
        data['announce_date'] = data['announce_date'].map(Date().change_to_str)
        return data

    def load_stock_change_name(self, beg_date, end_date):

        """ 下载更改股票名称信息 """

        print("######### Loading Stock Name ##########")
        new_data = w.wset("stockchangename",
                          "startdate=%s;enddate=%s;sectorid=a001010100000000" % (beg_date, end_date))
        new_data = pd.DataFrame(new_data.Data, index=new_data.Fields, columns=new_data.Codes).T
        new_data['name_change_date'] = new_data['name_change_date'].map(Date().change_to_str)

        index_col = ['wind_code', 'sec_name', 'name_change_date']

        new_data = new_data.set_index(index_col)
        new_data = new_data.sort_index()

        file = os.path.join(self.data_path_static, "stockchangename.csv")

        if os.path.exists(file):
            old_data = pd.read_csv(file, encoding='gbk')
            old_data['name_change_date'] = old_data['name_change_date'].map(str)
            old_data = old_data.set_index(index_col)

            data = pd.concat([old_data, new_data], axis=0)
            data = data[~data.index.duplicated()]
            data = data.sort_index()
        else:
            data = new_data

        data.to_csv(file)

    def load_stock_name_now(self):

        """ 下载 股票当前名称 """

        file = os.path.join(self.data_path_static, "sec_name.csv")
        code_list = self.get_all_stock_code_now()
        code_list_str = ','.join(code_list)
        data = w.wss(code_list_str, "sec_name")
        data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        data.to_csv(file)

    def get_stock_change_name(self):

        """ 得到更改股票名称信息 """

        file = os.path.join(self.data_path_static, "stockchangename.csv")
        data = pd.read_csv(file, encoding='gbk')
        data['name_change_date'] = data['name_change_date'].map(Date().change_to_str)
        return data

    def get_stock_name_now(self):

        """ 得到股票当前名称 """

        file = os.path.join(self.data_path_static, "sec_name.csv")
        data = pd.read_csv(file, encoding='gbk', index_col=[0])
        return data

    def get_stock_name_date(self, stock_code="000001.SZ", date="20171229"):

        """ 某只股票 某日的股票名称 """

        data = self.get_stock_change_name()
        data_now = self.get_stock_name_now()
        try:
            data_code = data[data['wind_code'] == stock_code]
            data_code = data_code.sort_values(by=['name_change_date'])

            data_date = data_code[data_code['name_change_date'] <= date]

            if len(data_date) == 0 and len(data_code) != 0:
                name = data_code.loc[data_code.index[0], "sec_name_before"]
            elif len(data_date) != 0:
                name = data_date.loc[data_date.index[-1], "sec_name_after"]
            else:
                name = data_now.loc[stock_code, "SEC_NAME"]
        except Exception as e:
            name = ""
        return name

    def load_audit_category_date(self, date):

        """ 下载 最近年报审计意见 """

        year_date = Date().get_last_stock_year_report_date(date)
        file = os.path.join(self.data_path_static, "stmnote_audit_category.csv")
        code_list = self.get_all_stock_code_now()
        code_list_str = ','.join(code_list)
        new_data = w.wss(code_list_str, "stmnote_audit_category", "rptDate=%s;zoneType=1" % year_date)
        new_data = pd.DataFrame(new_data.Data, index=new_data.Fields, columns=new_data.Codes).T
        new_data.columns = [year_date]

        if os.path.exists(file):
            old_data = pd.read_csv(file, encoding='gbk', index_col=[0])
            data = pd.concat([old_data, new_data], axis=1)
            data = data.T.sort_index().T
        else:
            data = new_data

        data.to_csv(file)

    def get_audit_category_date(self, date):

        """ 下载 最近年报审计意见 """

        year_date = Date().get_last_stock_year_report_date(date)
        file = os.path.join(self.data_path_static, "stmnote_audit_category.csv")
        data = pd.read_csv(file, encoding='gbk', index_col=[0])
        data_date = pd.DataFrame(data[year_date])
        return data_date

    def load_stock_static_data_all(self, beg_date=None, end_date=None):

        """ 下载所有不是每天早晨下载的那些股票基本信息 """

        if end_date is None:
            end_date = datetime.today().strftime("%Y%m%d")
        if beg_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -20)

        # 整体
        self.load_all_stock_code_now()
        self.load_ipo_date()
        self.load_stock_name_now()
        self.load_st_info()
        self.load_stock_change_name(beg_date, end_date)

        # 股票池
        self.load_stock_pledge(beg_date, end_date)  # 股票质押情况
        self.load_audit_category_date(end_date)  # 最近1期年报审计意见
        self.load_nature_info()  # 企业属性
        self.load_stock_illegality(beg_date, end_date)  # 违法违规情况

        # 晨报需要
        self.load_major_holder_deal(beg_date, end_date)  # 重要股东二级市场交易


if __name__ == '__main__':

    """ 下载数据 """

    self = StockStatic()
    date = datetime(2018, 7, 6)

    # StockStatic().load_all_stock_code_now()
    # print(StockStatic().get_all_stock_code_now())
    #
    # StockStatic().load_ipo_date()
    # print(StockStatic().get_ipo_date())
    #
    # StockStatic().load_trade_status_today()
    # print(StockStatic().get_trade_status_date(date))
    #
    # StockStatic().load_free_market_value_date(date)
    # print(StockStatic().get_free_market_value_date(date))

    # StockStatic().load_st_info()
    # StockStatic().load_nature_info()

    beg_date = "20181220"
    end_date = "20190115"
    # StockStatic().load_stock_pledge(beg_date, end_date)
    # StockStatic().load_stock_illegality(beg_date, end_date)
    # print(StockStatic().get_stock_illegality())
    # StockStatic().load_stock_change_name(beg_date, end_date)
    # print(StockStatic().get_stock_change_name())

    # stock_code = "000003.SZ"
    # date = "20021229"
    # print(StockStatic().get_stock_name_date(stock_code, date))

    # StockStatic().load_audit_category_date("20031231")
    # StockStatic().load_major_holder_deal("20181220", datetime.today().strftime("%Y%m%d"))
    # print(StockStatic().get_major_holder_deal())
    # self.load_stock_static_data_all()

