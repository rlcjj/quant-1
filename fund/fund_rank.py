from quant.stock.date import Date
from quant.data.data import Data
from quant.fund.fund import Fund
import pandas as pd
import numpy as np
import os

from WindPy import w
w.start()


class FundRank(Data):

    """ 计算基金排名 利用 wind 提取数据 """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\performance\FundRank'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def rank_fund(self, fund_code, rank_pool, beg_date, end_date, new_fund_date=None, excess=False):

        """
        计算某只基金在基金池的排名
        三种排名方式
        1、直接获取wind接口结果
        2、自己给定基金池，从wind接口获取基金绝对收益
        3、基金给定基金池，从wind接口获取基金超额收益
        """

        if new_fund_date is None:
            new_fund_date = beg_date

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)
        new_fund_date = Date().change_to_str(new_fund_date)

        print(" 正在计算基金排名 %s 在基金池 %s 从 %s 到 %s " % (fund_code, rank_pool, beg_date, end_date))

        # 分类获取排名
        if rank_pool == 'wind':

            # Wind 三级分类
            date_str = "startDate=%s;endDate=%s;fundType=3" % (beg_date, end_date)
            data = w.wss(fund_code, "peer_fund_return_rank_per", date_str)
            val = str(data.Data[0][0])
            data = w.wss(fund_code, "peer_fund_return_rank_prop_per", date_str)

            try:
                pct = np.round(data.Data[0][0] / 100.0, 3)
            except Exception as e:
                print(e)
                print("wind返回基金排名百分比非数字")
                pct = "None"
            return val, pct

        else:

            # 获取基金池
            pool = Fund().get_fund_pool_all(date="20181231", name=rank_pool)
            bool_series = (pool['if_connect'] == '非联接基金') & (pool['if_hk'] == '非港股基金')
            bool_series &= (pool['if_a'] == 'A类基金')
            pool = pool[bool_series]
            fund_code_str = ','.join(pool.index.values)

            if not excess:

                # 区间总收益排名
                data = w.wss(fund_code_str, "NAV_adj_return", "startDate=%s;endDate=%s" % (beg_date, end_date))
                data = pd.DataFrame(data.Data, columns=data.Codes, index=['NAV_adj_return']).T
                data = data[~data.index.duplicated()]
                data = pd.concat([data, pool], axis=1)
                data = data[data["setupdate"] <= new_fund_date]
                data = data.dropna(subset=['NAV_adj_return'])
                data = data.sort_values(by='NAV_adj_return', ascending=False)

                data['range'] = range(len(data))
                data["rank"] = data['range'].map(lambda x: str(x + 1) + "/" + str(len(data)))
                data['rank_pct'] = data['range'].map((lambda x: (x + 1) / len(data)))
                try:
                    val = data.loc[fund_code, "rank"]
                    pct = data.loc[fund_code, "rank_pct"]
                    pct = np.round(pct, 3)
                    file = "%s_%s_%s_%s.csv" % (fund_code, rank_pool, beg_date, end_date)
                    file = os.path.join(self.data_path, file)
                    data.to_csv(file)
                except Exception as e:
                    print(e)
                    val = "None"
                    pct = "None"
                return val, pct
            else:

                # 区间超额收益排名
                date_str = "startDate=%s;endDate=%s" % (beg_date, end_date)
                data = w.wss(fund_code_str, "NAV_over_bench_return_per", date_str)
                data = pd.DataFrame(data.Data, columns=data.Codes, index=['NAV_over_bench_return_per']).T
                data = pd.concat([data, pool], axis=1)
                data = data[data["setupdate"] <= new_fund_date]
                data = data.dropna(subset=['NAV_over_bench_return_per'])
                data = data.sort_values(by='NAV_over_bench_return_per', ascending=False)

                data['range'] = range(len(data))
                data["rank"] = data['range'].map(lambda x: str(x + 1) + "/" + str(len(data)))
                data['rank_pct'] = data['range'].map((lambda x: (x + 1) / len(data)))

                try:
                    val = data.loc[fund_code, "rank"]
                    pct = data.loc[fund_code, "rank_pct"]
                    pct = np.round(pct, 3)
                    file = "%s_%s_%s_%s.csv" % (fund_code, rank_pool, beg_date, end_date)
                    file = os.path.join(self.data_path, file)
                    data.to_csv(file)
                except Exception as e:
                    print(e)
                    val = "None"
                    pct = "None"
                return val, pct

    def rank_fund2(self, fund_pct, bench_pct,
                   fund_code, rank_pool, beg_date, end_date, new_fund_date=None, excess=False):

        """
        计算某只基金在基金池的排名
        三种排名方式
        1、直接获取wind接口结果
        2、自己给定基金池，本地基金数据取得基金绝对收益
        3、基金给定基金池，本地基金数据获取基金超额收益
        """

        if new_fund_date is None:
            new_fund_date = beg_date

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)
        new_fund_date = Date().change_to_str(new_fund_date)

        print(" 正在计算基金排名 %s 在基金池 %s 从 %s 到 %s " % (fund_code, rank_pool, beg_date, end_date))

        # 分类获取排名
        if rank_pool == 'wind':

            # Wind 三级分类
            date_str = "startDate=%s;endDate=%s;fundType=3" % (beg_date, end_date)
            data = w.wss(fund_code, "peer_fund_return_rank_per", date_str)
            val = str(data.Data[0][0])
            data = w.wss(fund_code, "peer_fund_return_rank_prop_per", date_str)

            try:
                pct = np.round(data.Data[0][0] / 100.0, 3)
            except Exception as e:
                print(e)
                print("wind返回基金排名百分比非数字")
                pct = "None"
            return val, pct

        else:

            # 获取基金池
            pool = Fund().get_fund_pool_all(date="20181231", name=rank_pool)
            bool_series = (pool['if_connect'] == '非联接基金') & (pool['if_hk'] == '非港股基金')
            bool_series &= (pool['if_a'] == 'A类基金')
            pool = pool[bool_series]

            if not excess:

                # 区间总收益排名
                # fund_pct = Fund().get_fund_factor("Repair_Nav_Pct")
                fund_pct = fund_pct.loc[beg_date:end_date, pool.index]
                fund_pct = fund_pct.dropna(how='all')
                data = (fund_pct / 100.0 + 1.0).cumprod() - 1.0
                data = pd.DataFrame(data.iloc[-1, :])
                data.columns = ['Pct']
                data = data[~data.index.duplicated()]
                data = data.dropna()

                data = pd.concat([data, pool], axis=1)
                data = data[data["setupdate"] <= new_fund_date]
                data = data.dropna(subset=['Pct'])
                data = data.sort_values(by='Pct', ascending=False)

                data['range'] = range(len(data))
                data["rank"] = data['range'].map(lambda x: str(x + 1) + "/" + str(len(data)))
                data['rank_pct'] = data['range'].map((lambda x: (x + 1) / len(data)))
                try:
                    val = data.loc[fund_code, "rank"]
                    pct = data.loc[fund_code, "rank_pct"]
                    pct = np.round(pct, 3)
                    file = "%s_%s_%s_%s.csv" % (fund_code, rank_pool, beg_date, end_date)
                    file = os.path.join(self.data_path, file)
                    data.to_csv(file)
                except Exception as e:
                    print(e)
                    val = "None"
                    pct = "None"
                return val, pct
            else:

                # 区间超额收益排名
                # fund_pct = Fund().get_fund_factor("Repair_Nav_Pct")
                # bench_pct = Fund().get_fund_factor("Fund_Bench_Pct") * 100
                excess_pct = fund_pct.sub(bench_pct)
                excess_pct = excess_pct.loc[beg_date:end_date, pool.index]
                excess_pct = excess_pct.dropna(how='all')
                data = (excess_pct / 100.0 + 1.0).cumprod() - 1.0
                data = pd.DataFrame(data.iloc[-1, :])
                data.columns = ['Pct']
                data = data[~data.index.duplicated()]
                data = data.dropna()

                data = pd.concat([data, pool], axis=1)
                data = data[data["setupdate"] <= new_fund_date]
                data = data.dropna(subset=['Pct'])
                data = data.sort_values(by='Pct', ascending=False)

                data['range'] = range(len(data))
                data["rank"] = data['range'].map(lambda x: str(x + 1) + "/" + str(len(data)))
                data['rank_pct'] = data['range'].map((lambda x: (x + 1) / len(data)))

                try:
                    val = data.loc[fund_code, "rank"]
                    pct = data.loc[fund_code, "rank_pct"]
                    pct = np.round(pct, 3)
                    file = "%s_%s_%s_%s.csv" % (fund_code, rank_pool, beg_date, end_date)
                    file = os.path.join(self.data_path, file)
                    data.to_csv(file)
                except Exception as e:
                    print(e)
                    val = "None"
                    pct = "None"
                return val, pct

    def rank_fund_array(self, fund_code, date_array, rank_pool, excess):

        """ 基金在不同区间段的排名 """

        performance_table = pd.DataFrame([], columns=date_array[:, 0])

        for i_date in range(date_array.shape[0]):
            label = date_array[i_date, 0]
            beg_date = date_array[i_date, 1]
            end_date = date_array[i_date, 2]
            new_fund_date = date_array[i_date, 3]
            rank_str, pct = self.rank_fund(fund_code, rank_pool, beg_date, end_date, new_fund_date, excess)
            performance_table.ix[rank_pool + "_排名", label] = rank_str
            performance_table.ix[rank_pool + "_百分比", label] = pct

        return performance_table

    def rank_fund_array2(self, fund_pct, bench_pct, fund_code, date_array, rank_pool, excess):

        """ 基金在不同区间段的排名 """

        performance_table = pd.DataFrame([], columns=date_array[:, 0])

        for i_date in range(date_array.shape[0]):
            label = date_array[i_date, 0]
            beg_date = date_array[i_date, 1]
            end_date = date_array[i_date, 2]
            new_fund_date = date_array[i_date, 3]
            rank_str, pct = self.rank_fund2(fund_pct, bench_pct,
                                            fund_code, rank_pool, beg_date, end_date, new_fund_date, excess)
            performance_table.ix[rank_pool + "_排名", label] = rank_str
            performance_table.ix[rank_pool + "_百分比", label] = pct

        return performance_table

    def example(self):

        """ 举例 """

        setup_date = '20150101'
        beg_date = "20161231"
        new_fund_date = beg_date
        end_date = '20171130'
        fund_code = '229002.OF'
        excess = False
        rank_pool = "股票型基金"

        date_array = np.array([["2017年以来", '20170101', end_date, "20170101"],
                               ["2016年", '20160101', '20161231', "20160101"],
                               ["2015年", setup_date, '20151231', setup_date],
                               ["成立以来", setup_date, end_date, setup_date]])
        fund_pct = Fund().get_fund_factor("Repair_Nav_Pct")
        bench_pct = Fund().get_fund_factor("Fund_Bench_Pct") * 100
        print(self.rank_fund_array2(fund_pct, bench_pct, fund_code, date_array, rank_pool, excess))

if __name__ == '__main__':

    self = FundRank()
    self.example()