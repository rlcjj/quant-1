import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from quant.data.data import Data
from quant.stock.stock import Stock
from quant.stock.stock_static import StockStatic
from quant.utility.write_excel import WriteExcel
from quant.utility.factor_operate import FactorOperate

from WindPy import w
w.start()


class NewStock(Data):

    """
    计算最近新股收益（这里只计算增量）
    配合Excel表计算 未完成全部自动化
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\new_stock'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def get_new_stock_list(self, beg_date='20170101'):

        """ 当前所有新股池 """

        Stock().load_all_stock_code_now()
        Stock().load_ipo_date()
        data = StockStatic().get_ipo_date()
        data.columns = ['ipo_date', 'delist_date']

        data = data[data['ipo_date'] >= beg_date]
        data = data.sort_values(by=['ipo_date'], ascending=True)
        return data

    def get_open_date_pct(self, code, ipo_date):

        """ 计算新股什么时候开板 及开板收益等等 """

        print(code, ipo_date)
        end_date = (datetime.strptime(ipo_date, '%Y-%m-%d') + timedelta(days=40)).strftime('%Y-%m-%d')
        to_date = datetime.today().strftime('%Y-%m-%d')
        date = min(end_date, to_date)
        pct = w.wsd(code, "close,pct_chg", ipo_date, date, "PriceAdj=B")
        pct = pd.DataFrame(pct.Data, index=pct.Fields, columns=pct.Times).T
        pct.index = pct.index.map(lambda x: x.strftime('%Y-%m-%d'))
        pct = pct.dropna()
        open_pct = 0.0
        open_date = np.nan
        open_price = np.nan

        for i_date in range(len(pct)):

            pct_day = pct.ix[i_date, "PCT_CHG"]
            open_pct = (open_pct + 1.0) * (pct_day / 100.0 + 1.0) - 1.0
            if pct_day < 9:
                open_date = pct.index.values[i_date]
                open_price = pct.ix[i_date, 'CLOSE']
                break

        return open_date, open_pct, open_price

    def load_ipo_data(self, beg_date):

        """ 下载IPO数据 上市日期 发行价 中签率 申购上限 等等"""

        data = self.get_new_stock_list(beg_date)
        code_str = ','.join(data.index.values)

        data = w.wss(code_str,
                     "sec_name,ipo_date,ipo_price,ipo_cashratio,ipo_lotteryrate_abc,ipo_otc_cash_pct,ipo_op_uplimit",
                     "instituteType=1")

        data_pd = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        data_pd["IPO_DATE"] = data_pd["IPO_DATE"].map(lambda x: x.strftime('%Y-%m-%d'))
        data_pd.columns = ['股票名称', '上市日期', '发行价格', '网上中签率(%)',
                           '网下A类中签率(%)', '网下总计中签率(%)', '申购上限数量(万股)']
        data_pd['申购上限金额(万元)'] = data_pd["申购上限数量(万股)"] * data_pd['发行价格']

        data_pd = data_pd.dropna()
        data_pd = data_pd.sort_values(by=['上市日期'], ascending=True)

        for i_code in range(0, len(data_pd)):

            code = data_pd.index.values[i_code]
            ipo_date = data_pd.ix[i_code, '上市日期']
            open_date, open_pct, open_price = self.get_open_date_pct(code, ipo_date)
            data_pd.ix[i_code, '开板日期'] = open_date
            data_pd.ix[i_code, '开板价格'] = open_price
            data_pd.ix[i_code, '开板收益'] = open_pct

        print(data_pd)
        file = os.path.join(self.data_path, 'ipo_data.xlsx')
        data = pd.read_excel(file, index_col=[1])
        data = data.T.dropna(how='all').T

        concat_data = FactorOperate().pandas_add_row(data, data_pd)
        concat_data = concat_data.sort_values(by=['上市日期'], ascending=True)
        excel = WriteExcel(file)
        worksheet = excel.add_worksheet("新股检测")
        excel.write_pandas(concat_data, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=None, color="orange", fillna=True)
        excel.close()


if __name__ == '__main__':

    beg_date = '20180101'

    # 从这个时间开始计算新股 会合并之前的数据
    self = NewStock()
    self.load_ipo_data(beg_date)
