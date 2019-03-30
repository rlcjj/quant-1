import os
import pandas as pd
from datetime import datetime

from quant.fund.fund import Fund
from quant.stock.date import Date


def equal_allstock_halfyear_date(report_date):

    report_date = Date().change_to_str(report_date)
    data = Fund().get_fund_holding_stock_date(report_date)
    data = data[['FundCode', 'Weight', 'StockCode']]

    pool = Fund().get_fund_pool_code(report_date, "基金持仓基准基金池")
    fund_code = list(set(pool))
    fund_code.sort()

    for i_fund in range(len(fund_code)):

        fund = fund_code[i_fund]
        data_fund = data[data['FundCode'] == fund]
        data_fund = data_fund.dropna(subset=['Weight'])
        data_fund = data_fund.sort_values(by=['Weight'], ascending=False)

        if i_fund == 0:
            data_fund_all = data_fund.copy()
            all_weight = data_fund_all['Weight'].sum()
            if all_weight < 60:
                data_fund_all = pd.DataFrame([], columns=data_fund.columns)
        else:
            data_fund_add = data_fund.copy()
            all_weight = data_fund['Weight'].sum()
            if all_weight < 60:
                data_fund_add = pd.DataFrame([], columns=data_fund.columns)
            data_fund_all = pd.concat([data_fund_all, data_fund_add], axis=0)

    stock_code = list(set(data_fund_all['StockCode'].values))
    stock_code.sort()
    weight_sum = data_fund_all['Weight'].sum()
    weight_code = pd.DataFrame([], index=stock_code, columns=['Weight'])

    for i_stock in range(len(stock_code)):
        stock = stock_code[i_stock]
        data_stock = data_fund_all[data_fund_all['StockCode'] == stock]
        stock_weight_sum = data_stock['Weight'].sum()
        weight_code.ix[stock, 'Weight'] = stock_weight_sum / weight_sum

    weight_code.index = weight_code.index.map(lambda x: x[0:6] + '-CN')

    out_path = os.path.join(Fund().data_path_holder, "fund_holding_benchmark")
    out_path = os.path.join(out_path, "equal_halfyear_all")
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    out_file = os.path.join(out_path, "equal_halfyear_all_" + report_date + '.csv')
    print(out_file)
    weight_code.to_csv(out_file, header=None)


def equal_allstock_halfyear_all():

    date_series = Date().get_normal_date_series("20040101", datetime.today(), period="S")
    for i_date in range(26, len(date_series) - 1):
        report_date = date_series[i_date]
        equal_allstock_halfyear_date(report_date)
        print(report_date)

if __name__ == "__main__":

    report_date = '20181231'
    equal_allstock_halfyear_date(report_date)
    # equal_allstock_halfyear_all()
