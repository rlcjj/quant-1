import os
import pandas as pd

from quant.data.data import Data
from quant.stock.date import Date
from quant.source.fin_db import FinDb
from quant.fund.fund_static import FundStatic
from quant.utility.factor_operate import FactorOperate


class FundFactor(Data):

    """
    下载、读取基金因子数据
    load_fund_factor()
    load_fund_factor_all()
    get_fund_factor()
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_factor_data'
        self.data_path_factor = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_fund_factor(self, factor_name, beg_date, end_date):

        """ 财汇数据库下载基金因子数据（增量更新） """

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        print("Loading Fund Factor %s From %s To %s" % (factor_name, beg_date, end_date))
        new_data = FinDb().load_raw_data_filter_period(factor_name, beg_date, end_date)
        fund_info_data = FundStatic().get_findb_fund_info()
        table_name, field_en, filter_field, field_ch, val_name = FinDb().get_load_findb_param(factor_name)

        new_data = pd.merge(new_data, fund_info_data, on="证券内码", how='inner')
        new_data = pd.DataFrame(new_data[val_name].values,
                                index=[list(new_data['基金代码'].values), list(new_data['日期'].values)])
        new_data = new_data.sort_index()
        new_data = new_data[~new_data.index.duplicated()]
        new_data = new_data.unstack()

        new_data.columns = new_data.columns.droplevel(level=0)
        new_data = new_data.T
        new_data = new_data.dropna(how='all')
        new_data.index = new_data.index.map(str)

        out_file = os.path.join(self.data_path_factor, factor_name + '.csv')

        if os.path.exists(out_file):
            data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
            data.index = data.index.map(str)
            data = FactorOperate().pandas_add_row(data, new_data)
        else:
            print(" File No Exist ", factor_name)
            data = new_data

        data = data.dropna(how='all')
        data.to_csv(out_file)

    def get_fund_factor(self, factor_name, date_list=None, fund_pool=None):

        """ 得到基金因子数据 """

        out_file = os.path.join(self.data_path_factor, factor_name + '.csv')
        data = pd.read_csv(out_file, index_col=[0], encoding='gbk')
        data = FactorOperate().drop_duplicated(data)
        data.index = data.index.map(str)
        data.columns = data.columns.map(str)

        if date_list is not None:
            data = data.ix[date_list, :]
        if fund_pool is not None:
            data = data.ix[:, fund_pool]

        return data

    def load_fund_factor_all(self, beg_date, end_date):

        """ 更新所有基金因子数据 """

        data = pd.read_excel(FinDb().load_param_file)
        data = data[data.TYPE == 'Fund_Data']
        data = data[data.SUB_TYPE == 'Factor']
        factor_name_list = list(data.NAME.values)

        for i_factor in range(len(factor_name_list)):
            factor_name = factor_name_list[i_factor]
            self.load_fund_factor(factor_name, beg_date, end_date)


if __name__ == '__main__':

    # load factor
    FundFactor().load_fund_factor("Fund_Bench_Pct", "19991231", "20190307")
    FundFactor().load_fund_factor_all(beg_date="20181231", end_date="20190307")

    # get factor
    data = FundFactor().get_fund_factor("Fund_Bench_Pct")
    print(data)


