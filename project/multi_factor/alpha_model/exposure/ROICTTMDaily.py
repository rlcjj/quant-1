import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def ROICTTMDaily(beg_date, end_date):

    """
    因子说明：（营业收入TTM - 营业成本TTM） / 全部投入资本
    TTM 为不同一财报期 最近可以得到的最新财报
    若有一个为负值 结果为负值
    """

    # param
    #################################################################################
    factor_name = "ROICTTMDaily"
    ipo_num = 90

    # read data
    #################################################################################
    cost = Stock().read_factor_h5("OperatingCost")
    income = Stock().read_factor_h5("OperatingIncome")
    investcapital = Stock().read_factor_h5("Investcapital")

    cost = StockFactorOperate().change_single_quarter_to_ttm_quarter(cost)
    income = StockFactorOperate().change_single_quarter_to_ttm_quarter(income)
    investcapital = StockFactorOperate().change_single_quarter_to_ttm_quarter(investcapital)
    investcapital /= 4.0

    report_data = Stock().read_factor_h5("ReportDateDaily")
    cost = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(cost, report_data, beg_date, end_date)
    income = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(income, report_data, beg_date, end_date)
    investcapital = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(investcapital, report_data, beg_date, end_date)



    # data precessing
    #################################################################################
    [cost, income, investcapital] = Stock().make_same_index_columns([cost, income, investcapital])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)

    for i in range(0, len(date_series)):

        current_date = date_series[i]

        if current_date in cost.columns:

            cost_date = cost[current_date]
            income_date = income[current_date]
            investcapital_date = investcapital[current_date]
            print('Calculating factor %s at date %s' % (factor_name, current_date))

            data_date = pd.concat([cost_date, income_date, investcapital_date], axis=1)
            data_date.columns = ['cost', 'income', 'investcapital']

            """ 这里本来应该对行业做一些调整
            filename = in_path[0:len(in_path)-13] + "DataSet\\industry_citic.txt"
            industry = pd.read_table(filename, index_col=[0], encoding='gbk', header=None)
            cost_industry = pd.concat([operating_cost_ttm, industry], axis=1)
            cost_industry.columns = ['value', 'industry']
            filter1 = cost_industry['industry'].map(lambda x: x in ['银行', '非银行金融'])
            filter2 = cost_industry['industry'].map(lambda x: x is np.nan)
            filter_total = filter1 & filter2
            cost_industry.ix[filter_total, 'value'] = 0.0
            operating_cost_ttm = pd.DataFrame(cost_industry['value'].values,
            index=cost_industry.index, columns=[curent_date])
            """

            data_date['diff'] = data_date['income'] - data_date['cost']
            data_date = data_date.dropna()
            data_date = data_date[data_date['investcapital'] != 0.0]
            data_date['ratio'] = data_date['diff'] / data_date['investcapital']

            # 只要有一个是负数 比例为负数
            mimus_index = (data_date['diff'] < 0.0) | (data_date['investcapital'] < 0.0)
            data_date.loc[mimus_index, 'ratio'] = - data_date.loc[mimus_index, 'ratio'].abs()
        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            data_date = pd.DataFrame([], columns=["ratio"], index=cost.index)

        if i == 0:
            res = pd.DataFrame(data_date['ratio'].values, columns=[current_date], index=data_date.index)
        else:
            res_add = pd.DataFrame(data_date['ratio'].values, columns=[current_date], index=data_date.index)
            res = pd.concat([res, res_add], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = ROICTTMDaily(beg_date, end_date)
    print(data)

