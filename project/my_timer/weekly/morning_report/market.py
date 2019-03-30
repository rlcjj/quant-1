from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel

import pandas as pd
import numpy as np
import os


class Market(Data):

    """ 晨会内容 年报和半年报中 各个机构所占市值比例（基金、保险、社保、QFII） """

    def __init__(self):

        """ 数据存储位置 """
        Data.__init__(self)
        self.sub_data_path = r'stock_data\morning_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self):

        """ 更新数据 """

        Stock().load_h5_primary_factor()

    def get_all_data(self, beg_date, end_date):

        """ 得到数据 （这里只取年报和半年报数据在，注意区分二季报和四季报）"""

        share_fund = Stock().read_factor_h5("HolderTotalByFund")  # 基金
        share_inst = Stock().read_factor_h5("HolderTotalByInst")  # 机构
        share_general_corp = Stock().read_factor_h5("HolderTotalByGeneralCorp")  # 一般法人
        share_hf = Stock().read_factor_h5("HolderTotalByHF")  # 私募
        share_qfii = Stock().read_factor_h5("HolderTotalByQFII")  # Qfii
        share_social_security = Stock().read_factor_h5("HolderTotalBySocialSecurity")  # 社保
        share_insurance = Stock().read_factor_h5("HolderTotalByInsurance")  # 保险

        halfyear_date = Date().get_last_fund_halfyear_date(end_date)
        date_series = Date().get_normal_date_series(Date().get_trade_date_offset(beg_date, -200), halfyear_date, "S")
        print(date_series)
        share_fund = share_fund[date_series]
        share_inst = share_inst[date_series]
        share_general_corp = share_general_corp[date_series]
        share_hf = share_hf[date_series]
        share_qfii = share_qfii[date_series]
        share_social_security = share_social_security[date_series]
        share_insurance = share_insurance[date_series]

        share_hk = Stock().read_factor_h5("HK2CHoldShare") / 1000000  # 陆股通
        share_hk = share_hk.T.fillna(method="pad", limit=3).T

        share_all = Stock().read_factor_h5("Share_TotalA") / 100000000  # 全A
        price_unadjust = Stock().read_factor_h5("PriceCloseUnadjust")  # 不复权价格
        share_free = Stock().read_factor_h5("Free_FloatShare")/ 100000000
        print(share_all.columns)
        result = pd.DataFrame([])

        date_series_data = Date().get_normal_date_series(beg_date, end_date, "M")

        for i_date in range(len(date_series_data)):

            date = date_series_data[i_date]
            price_date = price_unadjust.columns[price_unadjust.columns <= date][-1]
            share_date = share_fund.columns[share_fund.columns <= date][-1]
            print(date, price_date, share_date)

            try:
                share_hk[price_date]
            except Exception as e:
                share_hk.loc[:, price_date] = np.nan

            data = pd.concat([share_fund[share_date], share_inst[share_date], share_general_corp[share_date],
                              share_hf[share_date], share_qfii[share_date], share_social_security[share_date],
                              share_insurance[share_date], share_hk[price_date],
                              share_all[price_date], share_free[price_date], price_unadjust[price_date]], axis=1)

            data.columns = ['公募基金', '机构', '一般法人', '私募', 'QFII', '社保', '保险', '陆股通', '全A', "流通", '价格']
            col = ['公募基金', '机构', '一般法人', '私募', 'QFII', '社保', '保险', '陆股通', '全A', "流通"]
            data_mv = data[col].mul(data['价格'], axis='index')
            data_mv_sum = pd.DataFrame(data_mv.sum())
            data_mv_sum.columns = [date]

            data_mv_sum = data_mv_sum.T
            result = pd.concat([result, data_mv_sum], axis=0)

        result["总和"] = result[['公募基金', 'QFII', '社保', '保险', '陆股通']].sum(axis=1)
        result["总和(剔除保险)"] = result[['公募基金', 'QFII', '社保', '陆股通']].sum(axis=1)
        ratio = result.div(result['全A'], axis='index')

        ratio_free = result.div(result['流通'], axis='index')

        return result, ratio, ratio_free

    def generate_excel(self, end_date):

        """ 大股东增减持信息 输出到Excel """

        beg_date = "20050101"

        # 一段时间内市值占比时间序列
        result, ratio, ratio_free = self.get_all_data(beg_date, end_date)

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, '市场整体占比.xlsx')
        excel = WriteExcel(filename)
        sheet_name = "市场整体占比"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        num_format_pd = pd.DataFrame([], columns=ratio.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(ratio, worksheet, begin_row_number=0, begin_col_number=15,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        num_format_pd = pd.DataFrame([], columns=ratio_free.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(ratio_free, worksheet, begin_row_number=0, begin_col_number=30,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        summary = pd.concat([result.T[result.index[-1]], ratio.T[ratio.index[-1]],
                             ratio_free.T[ratio_free.index[-1]]], axis=1)
        summary.columns = ["市值", 'A股总市值占比', 'A股流通市值占比']
        num_format_pd = pd.DataFrame([], columns=summary.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.ix['format', ['市值']] = '0.00'
        excel.write_pandas(summary, worksheet, begin_row_number=0, begin_col_number=46,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        excel.close()

if __name__ == '__main__':

    beg_date = "20050101"
    end_date = "20190214"
    self = Market()
    self.generate_excel(end_date)

