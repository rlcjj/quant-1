import pandas as pd
import numpy as np
import os


def sub_diff_fund():

    """
    输入 张晓龙 生成的投资库、单独入库、禁止库文件
    输入 风控的禁止库文件
    需要把在风控的禁止库的基金从 投资库、单独入库当中 剔除
    """

    # 参数
    ######################################################################################################
    output_path = r'E:\Data\fund_data\fof_pool'
    fof_file = '基金库20180930.xlsx'
    forbid_file = 'FOF禁止库差异.xlsx'
    out_file = '基金库最终20180930.xlsx'
    ######################################################################################################

    # 读取数据
    ######################################################################################################
    fof_data = pd.read_excel(os.path.join(output_path, fof_file), encoding='gbk')
    forbid_data = pd.read_excel(os.path.join(output_path, forbid_file), encoding='gbk')
    ######################################################################################################

    # 计算
    ######################################################################################################
    fof_investment_fund = set(fof_data['投资库'].dropna().values)
    fof_special_fund = set(fof_data['单独入库'].dropna().values)
    fof_forbid_fund = set(fof_data['禁止库'].dropna().values)
    risk_forbid_fund = set(forbid_data['禁止库'].dropna().values)
    print(len(fof_data['禁止库'].dropna().values), len(forbid_data['禁止库'].dropna().values))

    fund_list = list(fof_investment_fund - risk_forbid_fund)
    fund_list.sort()
    fof_investment_fund_pd = pd.DataFrame(fund_list, columns=['投资库'])

    fund_list = list(fof_special_fund - risk_forbid_fund)
    fund_list.sort()
    fof_special_fund_pd = pd.DataFrame(fund_list, columns=['单独入库'])

    fund_list = list(fof_forbid_fund | risk_forbid_fund)
    fund_list.sort()
    print(len(fof_forbid_fund), len(risk_forbid_fund), len(fund_list))
    fof_forbid_fund_pd = pd.DataFrame(fund_list, columns=['禁止库'])
    ######################################################################################

    # 输出
    ######################################################################################
    result = pd.concat([fof_investment_fund_pd, fof_special_fund_pd, fof_forbid_fund_pd], axis=1)
    result.to_excel(os.path.join(output_path, out_file))
    ######################################################################################


if __name__ == '__main__':

    sub_diff_fund()
