import pandas as pd
from WindPy import w
w.start()
import os
from datetime import datetime
from quant.stock.date import Date


def load_inside_fund():

    """
    场内基金筛选标准

    成立日期大于1年
    基金净资产超过2个亿
    非分级基金
    日均成交额大于200万

    data['IfSetupDate'] = data['SetupDate'] < date_before_1y
    data['IFTotalAsset'] = data['TotalAsset'] > 2.0
    data['NotStructedFund'] = data['IfStructedFund'] == '否'
    data['IFAvgAmtPer'] = data['AvgAmtPer'] > 20000000

    """

    output_path = r'E:\Data\fund_data\fof_pool'
    fund_file = "全部场内基金_raw.csv"
    today = datetime.today()
    report_date = Date().get_last_fund_quarter_date(today)

    date_before_3m = Date().get_normal_date_offset(report_date, -91)
    date_before_1y = Date().get_normal_date_offset(report_date, -365)
    print(report_date, date_before_3m, date_before_1y)

    file = os.path.join(output_path, fund_file)
    data = pd.read_csv(file, index_col=[0], encoding='gbk')
    fund_code_str = ','.join(list(data['wind_code'].values))
    load_factor_str = "fund_setupdate,prt_fundnetasset_total,fund_structuredfundornot"

    data = w.wss(fund_code_str, load_factor_str, "unit=1;rptDate=" + report_date)
    data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
    data.columns = ['SetupDate', 'TotalAsset', 'IfStructedFund']

    data['SetupDate'] = data['SetupDate'].map(lambda x:x.strftime('%Y%m%d'))
    data['TotalAsset'] /= 100000000.0

    avg_amt_per = w.wss(fund_code_str, "avg_amt_per", "unit=1;startDate=" + date_before_3m + ";endDate=" + report_date)
    avg_amt_per = pd.DataFrame(avg_amt_per.Data, index=['AvgAmtPer'], columns=avg_amt_per.Codes).T
    data = pd.concat([data, avg_amt_per], axis=1)

    data['IfSetupDate'] = data['SetupDate'] < date_before_1y
    data['IFTotalAsset'] = data['TotalAsset'] > 2.0
    data['NotStructedFund'] = data['IfStructedFund'] == '否'
    data['IFAvgAmtPer'] = data['AvgAmtPer'] > 20000000

    data.to_csv(os.path.join(output_path, '全部场内基金性质.csv'))
    return True


def get_diff_inside_fund():

    """
    主要检查投资库和单独入库当中有无禁止库基金
    """

    output_path = r'E:\SoftWare\anaconda\anaconda\Lib\site-packages\quant\project\fund_project\fof_fund_pool\data'
    inside_file = '全部场内基金性质.csv'
    fof_file = '基金库20180930.xlsx'

    data = pd.read_csv(os.path.join(output_path, inside_file), index_col=[0], encoding='gbk')
    data_filter = data[data['IfSetupDate'] & data['IFTotalAsset'] & data['NotStructedFund'] & data['IFAvgAmtPer']]
    my_filter_fund = set(data_filter.index)
    fof_data = pd.read_excel(os.path.join(output_path, fof_file), encoding='gbk')
    investment_fund = set(list(filter(lambda x: x[-2:] in ['SH', 'SZ'], list(fof_data['投资库'].dropna().values))))
    special_fund = set(list(filter(lambda x: x[-2:] in ['SH', 'SZ'], list(fof_data['单独入库'].dropna().values))))
    input_filter_fund = investment_fund | special_fund

    print(" My Filter Fund - Input Filter Fund ")
    print(list(set(my_filter_fund) - set(input_filter_fund)))
    print(' ##################################### ')
    print(" Input Filter Fund - My Filter Fund ")
    print(list(set(input_filter_fund) - set(my_filter_fund)))
    print(' ##################################### ')


if __name__ == '__main__':

    # load_inside_fund()
    get_diff_inside_fund()
