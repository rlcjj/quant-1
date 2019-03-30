import pandas as pd
import os

from quant.stock.date import Date
from quant.fund.fund import Fund


def FundBarraDecomposeReturnQuarter(fund_holding_date, report_date, path, fund_code):

    """
    计算在给定时间点前后一个月 一个基金 拆分的 特异收益 风格收益 行业收益 和 市场收益
    """

    # 参数
    ###################################################################################################
    # report_date = '20171231'
    # fund_code = '000001.OF'
    # path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    #
    # fund_holding_all = Fund().get_fund_holding_all()
    # fund_holding_date = fund_holding_all[fund_holding_all['Date'] == report_date]

    # 持仓信息
    ######################################################################################################
    fund_holding = fund_holding_date[fund_holding_date['FundCode'] == fund_code]
    fund_holding.index = fund_holding['StockCode']
    fund_holding = fund_holding.ix[~fund_holding.index.duplicated(), :]
    fund_holding = fund_holding.dropna(subset=['Weight'])
    fund_holding = fund_holding.sort_values(by=['Weight'], ascending=False)

    # 股票各部分收益
    #####################################################################################################
    file = "StockBarraDecomposeReturnQuarter" + report_date + '.csv'
    file = os.path.join(path, "StockBarraDecomposeReturnQuarter", file)
    stock_decompose_return = pd.read_csv(file, index_col=[0], encoding='gbk')

    # 数据合并
    ######################################################################################################
    all_data = pd.concat([fund_holding, stock_decompose_return], axis=1)
    all_data = all_data.dropna()
    all_data = all_data.sort_values(by=['Weight'], ascending=False)
    all_data = all_data.iloc[0:10, :]

    # 计算结果
    ######################################################################################################
    result = pd.DataFrame([], columns=stock_decompose_return.columns, index=[fund_code])

    if all_data['Weight'].sum() > 0:
        for i in range(len(stock_decompose_return.columns)):
            col = stock_decompose_return.columns[i]
            result.loc[fund_code, col] = (all_data['Weight'] * all_data[col]).sum() / all_data['Weight'].sum()

    print(" FundBarraDecomposeReturnQuarter %s %s " % (fund_code, report_date))
    #######################################################################################################
    return result


def AllFundBarraDecomposeReturnQuarter(fund_holding_all, path, report_date):

    """
    计算一个季报时间点 前后一个月 所有基金 拆分的 特异收益 风格收益 行业收益 和 市场收益
    """
    # 参数
    ######################################################################################################
    # report_date = '20171231'
    # path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    # fund_holding_all = Fund().get_fund_holding_all()

    # 持仓信息
    ######################################################################################################
    fund_holding_date = fund_holding_all[fund_holding_all['Date'] == report_date]

    # 基金池信息
    ######################################################################################################
    fund_code_list = Fund().get_fund_pool_code(date=report_date, name="基金持仓基准基金池")
    fund_code_list3 = Fund().get_fund_pool_code(date=report_date, name="量化基金")
    fund_code_list2 = Fund().get_fund_pool_code(date="20180630", name="东方红基金")
    fund_code_list.extend(fund_code_list2)
    fund_code_list.extend(fund_code_list3)
    fund_code_list = list(set(fund_code_list))
    fund_code_list.sort()

    # cal fund alpha on style
    ######################################################################################################
    for i in range(0, len(fund_code_list)):

        fund_code = fund_code_list[i]
        if i == 0:
            result = FundBarraDecomposeReturnQuarter(fund_holding_date, report_date, path, fund_code)
        else:
            res = FundBarraDecomposeReturnQuarter(fund_holding_date, report_date, path, fund_code)
            result = pd.concat([result, res], axis=0)

    ######################################################################################################
    file = "FundBarraDecomposeReturnQuarter" + report_date + '.csv'
    file = os.path.join(path, "FundBarraDecomposeReturnQuarter", file)
    result.to_csv(file)
    ######################################################################################################


def AllFundBarraDecomposeReturnAllQuarter():

    """
    计算所有季报时间点 前后一个月 所有基金 拆分的 特异收益 风格收益 行业收益 和 市场收益
    """
    ################################################################################
    path = 'E:\\3_Data\\4_fund_data\\7_fund_select_stock\\'
    fund_holding_all = Fund().get_fund_holding_all()
    beg_date = "20040101"
    end_date = "20180815"
    ################################################################################
    date_series = Date().get_normal_date_series(beg_date, end_date, "Q")

    for i in range(len(date_series)):
        report_date = date_series[i]
        AllFundBarraDecomposeReturnQuarter(fund_holding_all, path, report_date)
        print(" FundBarraDecomposeReturnQuarter %s" % report_date)

    return True


if __name__ == "__main__":

    AllFundBarraDecomposeReturnAllQuarter()
