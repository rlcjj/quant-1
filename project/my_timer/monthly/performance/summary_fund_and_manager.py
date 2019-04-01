import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.fund.fund_rank import FundRank
from quant.mfc.mfc_data import MfcData
from quant.stock.index import Index
from quant.stock.date import Date
from quant.utility.financial_series import FinancialSeries
from quant.utility.write_excel import WriteExcel

""" 戴博需要的整理数据 每月更新 """
""" 泰达宏利所有股票基金及基金经理任职及每年表现 """


def update_data():

    """ 更新净值数据"""
    MfcData().load_mfc_public_fund_nav()
    Index().load_index_factor_all()


def rank_fund_self(end_date, fund_code, rank_pool, fund_name, mage_date):

    """ 某个基金排名 """
    today = datetime.strptime(end_date, "%Y%m%d")
    before_1y = datetime(year=today.year - 1, month=today.month, day=today.day).strftime("%Y%m%d")
    before_2y = datetime(year=today.year - 2, month=today.month, day=today.day).strftime("%Y%m%d")
    before_3y = datetime(year=today.year - 3, month=today.month, day=today.day).strftime("%Y%m%d")
    before_5y = datetime(year=today.year - 5, month=today.month, day=today.day).strftime("%Y%m%d")

    date_array = np.array([
        ["2019年", "20190101", end_date, '20180930'],
        ["2018年", '20180101', "20181231", '20170930'],
        ["2017年", "20170101", '20171231', "20160930"],
        ["2016年", "20160101", '20161231', "20150930"],
        ["2015年", "20150101", '20151231', "20140930"],
        ["成立以来", mage_date, end_date, mage_date],
        ["过去1年", before_1y, end_date, before_1y],
        ["过去2年", before_2y, end_date, before_2y],
        ["过去3年", before_3y, end_date, before_3y],
        ["过去5年", before_5y, end_date, before_3y]])

    rank_percent = pd.DataFrame([], index=[fund_name])
    rank_str = pd.DataFrame([], index=[fund_name])
    for i_date in range(len(date_array)):
        label = date_array[i_date, 0]
        beg_date = date_array[i_date, 1]
        end_date = date_array[i_date, 2]
        new_fund_date = date_array[i_date, 3]
        if beg_date >= str(int(mage_date)):
            str_rank, pct = FundRank().rank_fund(fund_code, rank_pool, beg_date, end_date, new_fund_date, excess=False)
            rank_percent.loc[fund_name, label] = pct
            rank_str.loc[fund_name, label] = str_rank
        else:
            rank_percent.loc[fund_name, label] = "NAN"
            rank_str.loc[fund_name, label] = "NAN"
    print(rank_percent)
    print(rank_str)
    return rank_percent, rank_str


def rank_fund_manager(end_date, fund_code, rank_pool, fund_name, mage_date):

    """ 某个基金经理管理以来排名 """
    today = datetime.strptime(end_date, "%Y%m%d")
    before_1y = datetime(year=today.year - 1, month=today.month, day=today.day).strftime("%Y%m%d")
    before_2y = datetime(year=today.year - 2, month=today.month, day=today.day).strftime("%Y%m%d")
    before_3y = datetime(year=today.year - 3, month=today.month, day=today.day).strftime("%Y%m%d")
    before_5y = datetime(year=today.year - 5, month=today.month, day=today.day).strftime("%Y%m%d")

    date_array = np.array([
        ["2019年", "20190101", end_date, '20180930'],
        ["2018年", '20180101', "20181231", '20170930'],
        ["2017年", "20170101", '20171231', "20160930"],
        ["2016年", "20160101", '20161231', "20150930"],
        ["2015年", "20150101", '20151231', "20140930"],
        ["管理以来", mage_date, end_date, mage_date],
        ["过去1年", before_1y, end_date, before_1y],
        ["过去2年", before_2y, end_date, before_2y],
        ["过去3年", before_3y, end_date, before_3y],
        ["过去5年", before_5y, end_date, before_3y]])

    rank_percent = pd.DataFrame([], index=[fund_name])
    rank_str = pd.DataFrame([], index=[fund_name])
    for i_date in range(len(date_array)):
        label = date_array[i_date, 0]
        beg_date = date_array[i_date, 1]
        end_date = date_array[i_date, 2]
        new_fund_date = date_array[i_date, 3]
        if beg_date >= str(int(mage_date)):

            # if fund_code in ["162201.OF"]:
            #     str_rank, pct = MfcManagerMoney().cal_fund_index(
            #         rank_pool, "FTSE成长", fund_code, beg_date, end_date, "超额收益")
            # elif fund_code in ["162202.OF"]:
            #     str_rank, pct = MfcManagerMoney().cal_fund_index(
            #         rank_pool, "FTSE周期", fund_code, beg_date, end_date, "超额收益")
            # elif fund_code in ["162203.OF"]:
            #     str_rank, pct = MfcManagerMoney().cal_fund_index(
            #         rank_pool, "FTSE稳定", fund_code, beg_date, end_date, "超额收益")
            # else:
            #     str_rank, pct = FundRank().rank_fund(fund_code, rank_pool, beg_date, end_date, new_fund_date,
            #                                          excess=False)
            str_rank, pct = FundRank().rank_fund(fund_code, rank_pool, beg_date, end_date, new_fund_date, excess=False)
            rank_percent.loc[fund_name, label] = pct
            rank_str.loc[fund_name, label] = str_rank
        else:
            rank_percent.loc[fund_name, label] = "NAN"
            rank_str.loc[fund_name, label] = "NAN"
    print(rank_percent)
    print(rank_str)
    return rank_percent, rank_str


def return_fund(end_date, fund_code, fund_name, mage_date):

    """ 某个基金收益率 """

    today = datetime.strptime(end_date, "%Y%m%d")
    before_1y = datetime(year=today.year - 1, month=today.month, day=today.day).strftime("%Y%m%d")
    before_2y = datetime(year=today.year - 2, month=today.month, day=today.day).strftime("%Y%m%d")
    before_3y = datetime(year=today.year - 3, month=today.month, day=today.day).strftime("%Y%m%d")
    before_5y = datetime(year=today.year - 5, month=today.month, day=today.day).strftime("%Y%m%d")

    date_array = np.array([
        ["2019年", "20190101", end_date, '20180930'],
        ["2018年", '20180101', "20181231", '20170930'],
        ["2017年", "20170101", '20171231', "20160930"],
        ["2016年", "20160101", '20161231', "20150930"],
        ["2015年", "20150101", '20151231', "20140930"],
        ["管理以来", mage_date, end_date, mage_date],
        ["过去1年", before_1y, end_date, before_1y],
        ["过去2年", before_2y, end_date, before_2y],
        ["过去3年", before_3y, end_date, before_3y],
        ["过去5年", before_5y, end_date, before_3y]])

    performance_table = pd.DataFrame([], index=[fund_name])
    for i_date in range(len(date_array)):
        label = date_array[i_date, 0]
        beg_date = date_array[i_date, 1]
        end_date = date_array[i_date, 2]
        if beg_date >= str(int(mage_date)):
            fund_nav = MfcData().get_mfc_public_fund_nav(fund_code)
            fs = FinancialSeries(pd.DataFrame(fund_nav['NAV_ADJ']))
            performance_table.ix[fund_name, label] = fs.get_interval_return(beg_date, end_date)
        else:
            performance_table.ix[fund_name, label] = "NAN"
    print(performance_table)
    return performance_table


def return_index(end_date, index_code, index_name, index_ratio, mage_date):

    """ 某个指数收益率 """

    today = datetime.strptime(end_date, "%Y%m%d")
    before_1y = datetime(year=today.year - 1, month=today.month, day=today.day).strftime("%Y%m%d")
    before_2y = datetime(year=today.year - 2, month=today.month, day=today.day).strftime("%Y%m%d")
    before_3y = datetime(year=today.year - 3, month=today.month, day=today.day).strftime("%Y%m%d")
    before_5y = datetime(year=today.year - 5, month=today.month, day=today.day).strftime("%Y%m%d")

    date_array = np.array([
        ["2019年", "20190101", end_date, '20180930'],
        ["2018年", '20180101', "20181231", '20170930'],
        ["2017年", "20170101", '20171231', "20160930"],
        ["2016年", "20160101", '20161231', "20150930"],
        ["2015年", "20150101", '20151231', "20140930"],
        ["过去1年", before_1y, end_date, before_1y],
        ["过去2年", before_2y, end_date, before_2y],
        ["过去3年", before_3y, end_date, before_3y],
        ["过去5年", before_5y, end_date, before_3y]])

    performance_table = pd.DataFrame([], index=[index_name])
    for i_date in range(len(date_array)):
        label = date_array[i_date, 0]
        beg_date = date_array[i_date, 1]
        end_date = date_array[i_date, 2]
        if beg_date >= str(int(mage_date)):
            index_close = Index().get_index_factor(index_code, attr=['CLOSE'])
            print(index_close.tail())
            fs = FinancialSeries(pd.DataFrame(index_close))
            pct = fs.get_interval_return(beg_date, end_date)
            print(pct, index_name)
            if type(pct) == np.float64:
                pct *= float(index_ratio)
            performance_table.loc[index_name, label] = pct
        else:
            performance_table.ix[index_name, label] = "NAN"

    print(performance_table)
    return performance_table


def rank_all_manager(end_date):

    """ 所有基金经理业绩 """

    path = r'E:\Data\mfcteda_data\基金经理'
    param_file = os.path.join(path, '泰达宏利基金经理排名.xlsx')
    data = pd.read_excel(param_file, index_col=[0])
    data = data.iloc[0:19, :]
    performance = pd.DataFrame()

    for i in range(len(data)):
        index = data.index[i]
        manager = data.loc[index, "基金经理"]
        mage_date = str(int(data.loc[index, "管理开始日"]))
        fund_name = data.loc[index, "名称"]
        fund_code = data.loc[index, "代码"]
        rank_pool = data.loc[index, '公司分类']
        print(manager, fund_name)
        rank_percent, rank_str = rank_fund_manager(end_date, fund_code, rank_pool, fund_name, mage_date)
        performance = pd.concat([performance, rank_percent], axis=0)

    file = os.path.join(path, '泰达宏利基金经理排名%s.xlsx' % end_date)
    we = WriteExcel(file)

    # write pandas
    sheet_name = "泰达宏利基金经理排名百分比"
    num_format_pd = pd.DataFrame([], columns=performance.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    worksheet = we.add_worksheet(sheet_name)
    we.write_pandas(performance, worksheet, begin_row_number=0, begin_col_number=1,
                    num_format_pd=num_format_pd, color="blue", fillna=True)
    we.conditional_format(worksheet, 0, 1, len(performance), len(performance.columns) + 1,
                          reverse=True)
    we.close()


def rank_all_fund(end_date):

    """ 所有基金业绩 """

    path = r'E:\Data\mfcteda_data\基金经理'
    param_file = os.path.join(path, '泰达宏利基金排名.xlsx')
    data = pd.read_excel(param_file, index_col=[0], sheetname="基金排名百分比")
    data['基金成立日'] = data['基金成立日'].map(lambda x:Date().change_to_str(x))
    data = data.iloc[0:, :]
    performance_rank_str = pd.DataFrame()
    performance_rank_pct = pd.DataFrame()
    performance_return_pct = pd.DataFrame()

    for i in range(len(data)):
        index = data.index[i]
        manager = data.loc[index, "基金经理"]
        mage_date = str(int(data.loc[index, "基金成立日"]))
        fund_name = data.loc[index, "名称"]
        fund_code = data.loc[index, "代码"]
        rank_pool = data.loc[index, '公司分类']
        print(manager, fund_name)
        rank_percent, rank_str = rank_fund_self(end_date, fund_code, rank_pool, fund_name, mage_date)
        return_pct = return_fund(end_date, fund_code, fund_name, mage_date)
        performance_rank_pct = pd.concat([performance_rank_pct, rank_percent], axis=0)
        performance_rank_str = pd.concat([performance_rank_str, rank_str], axis=0)
        performance_return_pct = pd.concat([performance_return_pct, return_pct], axis=0)

    index_array = np.array([["沪深300*80%", '000300.SH', 0.8, "20050101"],
                           ["中证500*80%", '000905.SH', 0.8, "20050101"],
                           ["万德全A*80%", '881001.WI', 0.8, "20050101"],
                           ["FTSE成长*80%", "FTSE成长", 0.8, "20131008"],
                           ["FTSE周期*80%", "FTSE周期", 0.8, "20131008"],
                           ["FTSE稳定*80%", "FTSE稳定", 0.8, "20131008"]])

    index_return_pct = pd.DataFrame()
    for i in range(len(index_array)):
        index_name = index_array[i][0]
        index_code = index_array[i][1]
        ratio = index_array[i][2]
        mg_date = index_array[i][3]
        print(fund_code, fund_name)
        return_i = return_index(end_date, index_code, index_name, ratio, mg_date)
        index_return_pct = pd.concat([index_return_pct, return_i], axis=0)

    performance_return_pct = pd.concat([performance_return_pct, index_return_pct], axis=0)
    date_index = ["2019年", "2018年", "2017年", "2016年", "2015年", "管理以来", "过去1年", "过去2年", "过去3年", "过去5年"]
    performance_return_pct = performance_return_pct[date_index]

    file = os.path.join(path, '泰达宏利基金排名%s.xlsx' % end_date)
    we = WriteExcel(file)

    # write pandas
    sheet_name = "泰达宏利基金排名百分比"
    num_format_pd = pd.DataFrame([], columns=performance_rank_pct.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    worksheet = we.add_worksheet(sheet_name)
    we.write_pandas(performance_rank_pct, worksheet, begin_row_number=0, begin_col_number=1,
                    num_format_pd=num_format_pd, color="blue", fillna=True)
    we.conditional_format(worksheet, 0, 1, len(performance_rank_pct), len(performance_rank_pct.columns) + 1,
                          reverse=True)

    sheet_name = "泰达宏利基金排名字符串"
    num_format_pd = pd.DataFrame([], columns=performance_rank_str.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00'
    worksheet = we.add_worksheet(sheet_name)
    we.write_pandas(performance_rank_str, worksheet, begin_row_number=0, begin_col_number=1,
                    num_format_pd=num_format_pd, color="blue", fillna=True)

    sheet_name = "泰达宏利基金收益率"
    num_format_pd = pd.DataFrame([], columns=performance_return_pct.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    worksheet = we.add_worksheet(sheet_name)
    we.write_pandas(performance_return_pct, worksheet, begin_row_number=0, begin_col_number=1,
                    num_format_pd=num_format_pd, color="blue", fillna=True)
    we.conditional_format(worksheet, 0, 1, len(performance_return_pct), len(performance_return_pct.columns) + 1)
    we.close()

if __name__ == '__main__':

    end_date = Date().get_normal_date_last_month_end_day(datetime.today())
    print(end_date)

    """ 需要更新富时指数收益 """
    update_data()
    rank_all_manager(end_date)
    rank_all_fund(end_date)
