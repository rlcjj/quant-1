import os
import pandas as pd
from quant.data.data import Data
from quant.stock.date import Date
from quant.fund.fund_factor import FundFactor

from WindPy import w
w.start()


class FundPool(Data):

    """
    下载\获取基金池
    load_fund_pool()
    get_fund_pool()
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_pool'
        self.data_path_pool = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_fund_pool_all(self, date):

        """ 下载所有基金池 更新所有基金池及相关属性（每季度更新一次）"""

        date = Date().get_last_fund_quarter_date(date)

        fund_pool_pd = pd.DataFrame([
                                     ["港股通基金", 1000024255000000],
                                     ["量化基金", 1000023322000000],
                                     ["全部开放式基金", "a201010400000000"],
                                     ["被动指数型基金", 2001010102000000],
                                     ["指数增强型基金", 2001010103000000],
                                     ["普通股票型基金", 2001010101000000],
                                     ["偏股混合型基金", 2001010201000000],
                                     ["灵活配置型基金", 1000011486000000],
                                     ["偏债混合型基金", 2001010203000000]
                                     ], columns=["PoolName", "PoolNumber"])

        for i_pool in range(len(fund_pool_pd)):

            name = fund_pool_pd.loc[fund_pool_pd.index[i_pool], "PoolName"]
            pool_number = fund_pool_pd.loc[fund_pool_pd.index[i_pool], "PoolNumber"]
            self.load_fund_pool(date, name, pool_number)
            self.fund_pool_add_attribute(date, name)

        # 将已有基金池拆分合并成为新的基金池

        self.concat_fund_pool(["被动指数型基金", "指数增强型基金"], date, "指数型基金")
        self.concat_fund_pool(["普通股票型基金", "偏股混合型基金"], date, "股票型基金")
        self.concat_fund_pool(["指数型基金", "量化基金"], date, "指数+量化基金")
        self.concat_fund_pool(["指数型基金", "普通股票型基金", '偏股混合型基金'], date, "指数+主动股票型基金")
        self.split_fund_pool_300_500(date)
        self.split_flexible_fund_pool(date)
        self.concat_fund_pool(["股票型基金", "灵活配置型基金_60"], date, "股票+灵活配置60型基金")
        self.concat_fund_pool(["指数型基金", "普通股票型基金",
                               '偏股混合型基金', '灵活配置型基金_60'], date, "指数+主动股票+灵活配置60基金")
        self.cal_active_stock_fund_pool(date)

    def load_fund_pool(self, date, name, pool_number):

        """ 下载基金池 为了便于比较每个类型加了 部门几个基金 """

        date = Date.change_to_str(date)
        data = w.wset("sectorconstituent", "date=%s;sectorid=%s" % (date, pool_number))
        data = pd.DataFrame(data.Data, index=data.Fields).T
        data.date = data.date.map(Date.change_to_str)
        data['Type'] = name

        if name == "指数增强型基金":
            d = pd.DataFrame([['001733.OF', "泰达宏利量化"],
                              ['004484.OF', '泰达宏利业绩驱动']],
                             columns=['wind_code', 'sec_name'])
            data = data.append(d)
            data = data.reset_index(drop=True)

        if name == "被动指数型基金":
            d = pd.DataFrame([['162213.OF', "泰达宏利沪深300"]],
                             columns=['wind_code', 'sec_name'])
            data = data.append(d)
            data = data.reset_index(drop=True)

        if name == "偏债混合型基金":
            d = pd.DataFrame([['003912.OF', "泰达宏利启富"],
                              ['004000.OF', '泰达宏利睿选稳健'],
                              ['003501.OF', '泰达宏利睿智稳健'],
                              ['162211.OF', '泰达宏利品质生活'],
                              ['001419.OF', '泰达宏利新思路']])
            d.columns = ['wind_code', 'sec_name']
            data = data.append(d)
            data = data.reset_index(drop=True)

        if name == "偏股混合型基金":
            d = pd.DataFrame([['001017.OF', "泰达宏利改革动力"],
                              ['002263.OF', '泰达宏利同顺大数据']])
            d.columns = ['wind_code', 'sec_name']
            data = data.append(d)
            data = data.reset_index(drop=True)

        out_sub_path = os.path.join(self.data_path_pool, name)
        if not os.path.exists(out_sub_path):
            os.makedirs(out_sub_path)

        print(" Loading Fund Pool %s At %s" % (name, date))
        out_file = os.path.join(out_sub_path, name + '_' + date + '.csv')
        data.to_csv(out_file)
        print(data.head())

    def cal_active_stock_fund_pool(self, date):

        """ 用来计算基金持仓基准的股票池 """

        ptgp = self.get_fund_pool_all(date, "普通股票型基金")
        pghh = self.get_fund_pool_all(date, "偏股混合型基金")
        ggt = self.get_fund_pool_all(date, "港股通基金")
        lh = self.get_fund_pool_all(date, "量化基金")

        fund_pool = set(ptgp['wind_code'].values) | set(pghh['wind_code'].values)
        fund_pool = set(fund_pool) - set(ggt['wind_code'].values) - set(lh['wind_code'].values)

        data = pd.concat([ptgp, pghh], axis=0)
        data = data.reset_index(drop=True)

        data_final = data[data['wind_code'].map(lambda x: x in fund_pool)]
        data_final['if_A'] = data_final['sec_name'].map(self.if_a_fund)
        data_final = data_final[data_final['if_A'] == 'A类基金']
        data = data_final.reset_index(drop=True)

        name = "基金持仓基准基金池"
        file = name + '_' + str(date) + '.csv'
        out_file = os.path.join(self.data_path_pool, name, file)
        data.to_csv(out_file)
        self.fund_pool_add_attribute(date, name="基金持仓基准基金池")

    def get_fund_pool_code(self, date=None, name=None):

        """ 得到基金池代码 """

        if name is None:
            name = '基金持仓基准基金池'
        if date is None:
            date = Date().get_normal_date_series(period='Q')[-2]

        date = Date.change_to_str(date)
        print(" Get Fund Pool Code %s %s " % (name, date))
        out_file = os.path.join(self.data_path_pool, name, name + '_' + str(date) + '.csv')
        data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
        data = data.sort_values(by=['wind_code'], ascending=True)
        data = list(data['wind_code'].values)
        return data

    def get_fund_pool_name(self, date=None, name=None):

        """ 下载基金池名称 """

        if name is None:
            name = '基金持仓基准基金池'
        if date is None:
            date = Date().get_normal_date_series(period='Q')[-2]

        date = Date.change_to_str(date)
        print(" Get Fund Pool Name %s %s " % (name, date))
        out_file = os.path.join(self.data_path_pool, name, name + '_' + str(date) + '.csv')
        data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
        data = data.sort_values(by=['wind_code'], ascending=True)
        data = list(data['sec_name'].values)
        return data

    def get_fund_pool_all(self, date=None, name=None):

        """ 得到基金池信息 """

        if name is None:
            name = '基金持仓基准基金池'
        if date is None:
            date = Date().get_normal_date_series(period='Q')[-1]

        date = Date.change_to_str(date)
        print(" Get Fund Pool %s %s " % (name, date))
        out_file = os.path.join(self.data_path_pool, name, name + '_' + str(date) + '.csv')
        data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
        data = data.sort_values(by=['wind_code'], ascending=True)

        if 'setupdate' in data.columns:
            data['setupdate'] = data['setupdate'].map(Date().change_to_str)

        data.index = data['wind_code']
        data = data[~data.index.duplicated()]
        return data

    def concat_fund_pool(self, pool_list, date, save_name):

        """ 基金池合并 """

        for i in range(len(pool_list)):
            fund_pool = pool_list[i]

            if i == 0:
                data = self.get_fund_pool_all(date, fund_pool)
            else:
                add_data = self.get_fund_pool_all(date, fund_pool)
                data = pd.concat([data, add_data], axis=0)
                data = data.reset_index(drop=True)

        data.index = data['wind_code']
        data = data.loc[~data.index.duplicated(), :]
        data = data.reset_index(drop=True)

        name = save_name
        out_sub_path = os.path.join(self.data_path_pool, name)
        if not os.path.exists(out_sub_path):
            os.makedirs(out_sub_path)
        print(" Concat Fund Pool %s At %s" % (save_name, date))
        file = name + '_' + date + '.csv'
        out_file = os.path.join(out_sub_path, file)
        data.to_csv(out_file)

    def split_flexible_fund_pool(self, date):

        """ 分离灵活配置基金池 """

        data = self.get_fund_pool_all(date=date, name="灵活配置型基金")
        data.index = data['wind_code']

        report_date = Date().get_last_fund_quarter_date(date)
        ratio = FundFactor().get_fund_factor("Stock_Ratio", [report_date], fund_pool=list(data['wind_code']))
        ratio = ratio.T
        ratio.columns = ['stock_ratio']
        data = pd.concat([data, ratio], axis=1)

        data['stock_ratio'] = ratio
        data_60 = data[data['stock_ratio'] > 60]
        add_fund = ['003501.OF', '004000.OF']
        try:

            d = data.loc[add_fund, :]
            data_60 = data_60.append(d)
            data_60 = data_60.reset_index(drop=True)
        except Exception as e:
            print(e)
            print(add_fund, "is not in Fund Pool")

        name = "灵活配置型基金_60"
        print(" Split Flexible Fund Pool %s At %s" % (name, date))
        file = name + '_' + date + '.csv'
        out_file = os.path.join(self.data_path_pool, name,  file)
        data_60 = data_60.reset_index(drop=True)
        data_60.to_csv(out_file)

        data_30 = data[data['stock_ratio'] < 32]

        name = "灵活配置型基金_30"
        file = name + '_' + date + '.csv'
        out_file = os.path.join(self.data_path_pool, name,  file)
        data_30 = data_30.reset_index(drop=True)
        data_30.to_csv(out_file)

    def split_fund_pool_300_500(self, date):

        data = self.get_fund_pool_all(date=date, name="指数型基金")
        data.index = data['wind_code']

        data['if_300_fund'] = data['sec_name'].map(lambda x: "沪深300" in x)
        data_hs300 = data[data['if_300_fund']]
        data_hs300 = data_hs300[(data_hs300['if_connect'] == '非联接基金') &
                                (data_hs300['if_hk'] == '非港股基金') &
                                (data_hs300['if_a'] == 'A类基金')]

        name = "沪深300基金"
        print(" Split 300 Fund Pool %s At %s" % (name, date))
        file = name + '_' + date + '.csv'
        out_file = os.path.join(self.data_path_pool, name, file)
        data_hs300 = data_hs300.reset_index(drop=True)
        data_hs300.to_csv(out_file)

        data['if_500_fund'] = data['sec_name'].map(lambda x: "中证500" in x)
        data_zz500 = data[data['if_500_fund']]
        data_zz500 = data_zz500[(data_zz500['if_connect'] == '非联接基金') &
                                (data_zz500['if_hk'] == '非港股基金') &
                                (data_zz500['if_a'] == 'A类基金')]

        name = "中证500基金"
        print(" Split 500 Fund Pool %s At %s" % (name, date))
        file = name + '_' + date + '.csv'
        out_file = os.path.join(self.data_path_pool, name, file)
        data_zz500 = data_zz500.reset_index(drop=True)
        data_zz500.to_csv(out_file)

    @staticmethod
    def if_connected_fund(x):

        """ 是否是ETF联接基金 """

        if '联接' in x:
            return '联接基金'
        else:
            return '非联接基金'

    @staticmethod
    def if_etf_fund(x):

        """ 是否是ETF基金 """

        if 'ETF' in x:
            return 'ETF基金'
        else:
            return '非ETF基金'

    @staticmethod
    def if_hongkong_fund(x):

        """ 是否是港股基金 """

        if ('恒生' in x) or ('港股' in x):
            return '港股基金'
        else:
            return '非港股基金'

    @staticmethod
    def if_a_fund(x):

        """ 是否是A类基金(注意ETF基金有E) """

        if ('C' in x) or ('O' in x) or ('H' in x) or ('I' in x) or \
                ('B' in x) or ('D' in x) or ('R' in x):
            return '非A类基金'
        else:
            return 'A类基金'

    def fund_pool_add_attribute(self, date, name):

        """ 给基金池添加属性列（是否是ETF基金，成立日期等等） """

        data = self.get_fund_pool_all(date, name)
        data['if_a'] = data["sec_name"].map(self.if_a_fund)
        data['if_etf'] = data["sec_name"].map(self.if_etf_fund)
        data['if_connect'] = data["sec_name"].map(self.if_connected_fund)
        data['if_hk'] = data["sec_name"].map(self.if_hongkong_fund)

        data.index = data['wind_code']
        data = data.dropna(subset=['sec_name'])
        data = data[~data.index.duplicated()]

        data_code_str = ','.join(data["wind_code"].values)
        fund_setupdate = w.wss(data_code_str, "fund_setupdate", "")
        fund_setupdate = pd.DataFrame(fund_setupdate.Data, index=['setupdate'], columns=fund_setupdate.Codes).T
        fund_setupdate['setupdate'] = fund_setupdate['setupdate'].map(Date().change_to_str)
        data = pd.concat([data, fund_setupdate], axis=1)
        data = data.reset_index(drop=True)

        out_sub_path = os.path.join(self.data_path_pool, name)
        if not os.path.exists(out_sub_path):
            os.makedirs(out_sub_path)

        print(" Add Fund Attribute %s At %s" % (name, date))
        file = name + '_' + date + '.csv'
        out_file = os.path.join(out_sub_path, file)
        data.to_csv(out_file)


if __name__ == '__main__':

    date = '20181231'
    self = FundPool()

    # FundPool().load_fund_pool_all(date)
    # print(FundPool().get_fund_pool_code())
