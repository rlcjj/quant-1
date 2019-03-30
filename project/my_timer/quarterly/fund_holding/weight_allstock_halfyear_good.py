import pandas as pd
import numpy as np
from quant.fund.fund import Fund
from quant.stock.date import Date

import os
from datetime import datetime
from WindPy import w
w.start()


def weight_all_stock_good_date(report_date):

    report_date = Date().change_to_str(report_date)
    data = Fund().get_fund_holding_stock_date(report_date)
    data = data[['FundCode', 'Weight', 'StockCode']]

    pool = Fund().get_fund_pool_code(report_date, "基金持仓基准基金池")
    fund_code = list(set(pool))
    fund_code.sort()

    weight = Fund().get_fund_factor("Total_Asset", date_list=[report_date]).T
    weight = weight.dropna()

    # 根据业绩 筛选股票池 其他还和原来一样
    ###############################################################################################
    end_0 = int(report_date)
    begin_0 = int(report_date) - 10000
    end_1 = int(report_date) - 10000
    begin_1 = int(report_date) - 20000
    end_2 = int(report_date) - 20000
    begin_2 = int(report_date) - 30000
    print(end_0, end_1, end_2)

    code_str = ','.join(fund_code)

    data0 = w.wss(code_str, "NAV_adj_return", "startDate=" + str(begin_0) + ";endDate=" + str(end_0))
    data0 = pd.DataFrame(data0.Data, columns=data0.Codes, index=[str(end_0)]).T

    data1 = w.wss(code_str, "NAV_adj_return", "startDate=" + str(begin_1) + ";endDate=" + str(end_1))
    data1 = pd.DataFrame(data1.Data, columns=data1.Codes, index=[str(end_1)]).T

    data2 = w.wss(code_str, "NAV_adj_return", "startDate=" + str(begin_2) + ";endDate=" + str(end_2))
    data2 = pd.DataFrame(data2.Data, columns=data2.Codes, index=[str(end_2)]).T

    performance = pd.concat([data0, data1, data2], axis=1)
    performance = performance.dropna()
    rank = performance.rank(ascending=False)

    rank = rank.dropna()
    rank /= len(rank)

    rank['rank_mean'] = rank[[str(end_0), str(end_1), str(end_2)]].mean(axis=1)
    rank['rank_std'] = rank[[str(end_0), str(end_1), str(end_2)]].std(axis=1)

    rank['rank_mean_plus_std'] = rank['rank_mean'] + rank['rank_std']
    rank = rank.sort_values(by=['rank_mean_plus_std'], ascending=True)

    size = max(2, np.ceil(0.15*len(rank)))
    rank_good = rank[0:int(size)]
    rank_good = pd.concat([performance, rank_good], axis=1)
    rank_good = rank_good.dropna()
    rank_good = rank_good.sort_values(by=['rank_mean_plus_std'])
    fund_code = list(rank_good.index)

    if len(fund_code) == 0:
        pass

    else:
        for i_fund in range(len(fund_code)):

            fund = fund_code[i_fund]
            data_fund = data[data['FundCode'] == fund]
            data_fund = data_fund.dropna(subset=['Weight'])
            data_fund = data_fund.sort_values(by=['Weight'], ascending=False)

            try:
                asset = weight.ix[fund, report_date] / 100000000.0
            except Exception as e:
                asset = 1.0

            if i_fund == 0:
                data_fund_all = data_fund.copy()
                data_fund_all["Asset_Weight"] = data_fund_all['Weight'] * asset
                all_weight = data_fund_all['Weight'].sum()
                if all_weight < 60:
                    data_fund_all = pd.DataFrame([], columns=data_fund.columns)
            else:
                data_fund_all_add = data_fund.copy()
                data_fund_all_add["Asset_Weight"] = data_fund_all_add['Weight'] * asset
                all_weight = data_fund_all_add['Weight'].sum()
                if all_weight < 60:
                    data_fund_all_add = pd.DataFrame([], columns=data_fund.columns)
                data_fund_all = pd.concat([data_fund_all, data_fund_all_add], axis=0)

        stock_code = list(set(data_fund_all['StockCode'].values))
        stock_code.sort()
        weight_sum = data_fund_all['Asset_Weight'].sum()
        weight_code = pd.DataFrame([], index=stock_code, columns=['Asset_Weight'])

        for i_stock in range(len(stock_code)):
            stock = stock_code[i_stock]
            data_stock = data_fund_all[data_fund_all['StockCode'] == stock]
            stock_weight_sum = data_stock['Asset_Weight'].sum()
            weight_code.ix[stock, 'Asset_Weight'] = stock_weight_sum / weight_sum

        weight_code.index = weight_code.index.map(lambda x: x[0:6] + '-CN')
        out_path = os.path.join(Fund().data_path_holder, "fund_holding_benchmark")
        out_path = os.path.join(out_path, "weight_halfyear_all_good")
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        out_file = os.path.join(out_path, "weight_halfyear_all_good_" + report_date + '.csv')
        print(out_file)
        weight_code.to_csv(out_file, header=None)


def weight_all_stock_good_all():

    date_series = Date().get_normal_date_series("20040101", datetime.today(), period="S")
    for i_date in range(0, len(date_series) - 2):
        report_date = date_series[i_date]
        weight_all_stock_good_date(report_date)
        print(report_date)

if __name__ == "__main__":

    weight_all_stock_good_date("20181231")
    # weight_all_stock_good_all()
