from datetime import datetime
import pandas as pd
import numpy as np
import os

from quant.data.data import Data
from quant.stock.date import Date
from quant.source.fin_db import FinDb
from quant.utility.code_format import CodeFormat

from WindPy import w
w.start()


class FundStatic(Data):

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_basic_info'
        self.data_path_static = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_wind_fund_info(self):

        """ 下载基金基本信息 成立日 到期日 基金简称 基金基准 基金管理人等等 """

        date = Date().get_normal_date_series(period='Q')[-1]
        date = "20181231"

        print("######## Loading Fund Info ########")
        from quant.fund.fund_pool import FundPool
        code = FundPool().get_fund_pool_code(date, "全部开放式基金")

        code1 = code[0:3500]
        code_str = ','.join(list(code1))
        data = w.wss(code_str, "fund_setupdate,fund_maturitydate,fund_fullname,fund_investtype,"
                               "fund_structuredfundornot,fund_benchmark,sec_name,fund_corp_fundmanagementcompany")
        data1 = pd.DataFrame(data.Data, columns=data.Codes, index=data.Fields).T

        code2 = code[3500:len(code)-1]
        code_str = ','.join(list(code2))
        data = w.wss(code_str, "fund_setupdate,fund_maturitydate,fund_fullname,fund_investtype,"
                               "fund_structuredfundornot,fund_benchmark,sec_name,fund_corp_fundmanagementcompany")
        data2 = pd.DataFrame(data.Data, columns=data.Codes, index=data.Fields).T

        data = pd.concat([data1, data2], axis=0)
        data.columns = ['SetupDate', 'MaturityDate', 'FullName', 'InvestType', 'IfStructed',
                        'BenchMark', 'Name', 'Corp']
        data['SetupDate'] = data['SetupDate'].map(Date().change_to_str)
        data['MaturityDate'] = data['MaturityDate'].map(Date().change_to_str)
        file = os.path.join(self.data_path_static, 'FundInfoWind.csv')
        data.to_csv(file)

    def get_wind_fund_info(self):

        """ 得到基金基本信息 成立日 到期日 基金简称 基金基准 基金管理人等等 """

        file = os.path.join(self.data_path_static, 'FundInfoWind.csv')
        data = pd.read_csv(file, encoding='gbk', index_col=[0])
        data['SetupDate'] = data['SetupDate'].map(Date().change_to_str)
        data['MaturityDate'] = data['MaturityDate'].map(Date().change_to_str)

        return data

    def load_findb_sec_info(self, pool_name=101):

        """ 下载财汇数据库股票基本信息表 """

        data = FinDb().load_raw_data_filter("Sec_Basic_Info", pool_name)
        data['证券代码'] = data['证券代码'].map(CodeFormat().stock_code_add_postfix)
        out_file = os.path.join(self.data_path_static, 'Sec_Basic_Info.csv')
        print(" Loading Security Basic InFo " + out_file)
        data.to_csv(out_file)

    def load_findb_fund_info(self):

        """ 下载财汇数据库基金基本信息表 """

        data = FinDb().load_raw_data("Fund_Basic_Info")
        out_file = os.path.join(self.data_path_static, 'Fund_Basic_Info.csv')
        data['基金代码'] = data['基金代码'].map(CodeFormat().fund_code_add_postfix)
        print(" Loading Fund Basic InFo " + out_file)
        data.to_csv(out_file)

    def get_findb_sec_info(self):

        """ 得到财汇数据库股票基本信息表 """

        file = os.path.join(self.data_path_static, 'Sec_Basic_Info.csv')
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data = data.astype(np.str)
        return data

    def get_findb_fund_info(self):

        """ 得到财汇数据库基金基本信息表 """

        file = os.path.join(self.data_path_static, 'Fund_Basic_Info.csv')
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data = data.astype(np.str)
        return data

    def get_fund_name(self, fund_code):

        """ 数据来源于wind数据浏览器 得到现任基金经理的名称 """

        file = os.path.join(self.data_path_static, 'FundManager.xlsx')
        data = pd.read_excel(file, index_col=[0])
        data = data.dropna()
        try:
            manager_str = data.loc[fund_code, "证券简称"]
        except Exception as e:
            manager_str = ""

        return manager_str

    def get_fund_manager(self, date, fund_code):

        """ 数据来源于wind数据浏览器 得到现任基金经理的名称 """

        file = os.path.join(self.data_path_static, 'FundManager.xlsx')
        data = pd.read_excel(file, index_col=[0])
        data = data.dropna()
        manager_str = data.loc[fund_code, "基金经理(历任)"]

        manager_list = manager_str.split("\r\n")
        manager_pd = pd.DataFrame([], columns=["beg_date", "end_date"])

        for i in range(len(manager_list)):

            text = manager_list[i]
            manager_name = text[0:text.index("(")]

            if "-" in text:
                beg_date = text[text.index("(") + 1:text.index("-")]
                end_date = text[text.index("-") + 1:text.index(")")]
            else:
                beg_date = text[text.index("(") + 1:text.index("至")]
                end_date = datetime.today().strftime("%Y%m%d")
            manager_pd.loc[manager_name, "beg_date"] = beg_date
            manager_pd.loc[manager_name, "end_date"] = end_date

        manager_pd = manager_pd[manager_pd['end_date'] >= date]
        return ",".join(manager_pd.index)

    def get_fund_manager_change_info(self, bg_date, ed_date, fund_code):

        """ 数据来源于wind数据浏览器 一段时间内有无基金经理变更（包括新任、新增、离职等等） """

        file = os.path.join(self.data_path_static, 'FundManager.xlsx')
        data = pd.read_excel(file, index_col=[0])
        data = data.dropna()
        manager_str = data.loc[fund_code, "基金经理(历任)"]

        manager_list = manager_str.split("\r\n")
        manager_pd = pd.DataFrame([], columns=["beg_date", "end_date"])

        for i in range(len(manager_list)):

            text = manager_list[i]
            manager_name = text[0:text.index("(")]

            if "-" in text:
                beg_date = text[text.index("(") + 1:text.index("-")]
                end_date = text[text.index("-") + 1:text.index(")")]
            else:
                beg_date = text[text.index("(") + 1:text.index("至")]
                end_date = datetime.today().strftime("%Y%m%d")
            manager_pd.loc[manager_name, "beg_date"] = beg_date
            manager_pd.loc[manager_name, "end_date"] = end_date

        manager_add = manager_pd[manager_pd['end_date'] >= bg_date]
        manager_add = manager_add[manager_add['end_date'] < ed_date]

        manager_del = manager_pd[manager_pd['beg_date'] >= bg_date]
        manager_del = manager_del[manager_del['beg_date'] < ed_date]

        manager_pd = pd.concat([manager_add, manager_del], axis=0)
        print(manager_pd)

        if len(manager_pd) > 0:
            val = True
        else:
            val = False
        return val


if __name__ == '__main__':

    self = FundStatic()

    # self.load_findb_fund_info()
    # self.load_findb_sec_info()
    # self.load_wind_fund_info()

    date = "20181231"
    bg_date = "20180101"
    ed_date = "20190101"
    fund_code = "000001.OF"

    print(self.get_fund_manager(date, fund_code))
    print(self.get_fund_manager_change_info(bg_date, ed_date, fund_code))
    print(self.get_fund_name(fund_code))
    print(self.get_fund_name_all())

