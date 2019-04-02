from datetime import datetime
from quant.fund.fund import Fund
from quant.stock.date import Date


def test_fund_position_update(date):

    data = Fund().get_fund_holding_stock_all()
    report_date_list = list(set(data['ReportDate'].values))
    report_date_list.sort()

    data_report = data[data['ReportDate'] == date]
    fund_list = list(set(data_report['FundCode'].values))
    fund_list.sort()
    i = 0

    for fund_code in fund_list:
        data_fund = data_report[data_report['FundCode'] == fund_code]
        if len(data_fund) > 10:
            i += 1

    print("在 " + date + " 有" + str(len(fund_list)) + "只基金更新持仓")
    print("其中持仓超过10只的基金组合有", str(i) + "只")


def fund_holding_update():

    print("##########    参数    ###############")
    date = '20181231'
    last_date = "20180930"

    print("########## 更新日期 ###############")
    # Date().load_trade_date_series_all()

    print("########## 更新股票池 基金规模 ###############")
    # Fund().load_fund_pool_all(date)
    Fund().load_fund_factor("Total_Asset", "20180101", datetime.today())

    print("########## 基金持仓股票 ###############")
    Fund().load_fund_holding_stock("19991231", datetime.today())
    Fund().load_fund_holding_industry("19991231", datetime.today())
    # Fund().cal_fund_stock_weight_halfyear()
    # Fund().cal_fund_stock_weight_quarter()

    print("########## 检查持仓更新情况 ###############")
    test_fund_position_update(last_date)
    test_fund_position_update(date)

    print("########## 计算加权基金基准 ###############")
    from quant.project.my_timer.quarterly.fund_holding.weight_allstock_halfyear_good import weight_all_stock_good_date
    from quant.project.my_timer.quarterly.fund_holding.weight_allstock_halfyear_holding import \
        weight_allstock_holding_date
    from quant.project.my_timer.quarterly.fund_holding.equal_halfyear_holding import equal_allstock_halfyear_date
    from quant.project.my_timer.quarterly.fund_holding.equal_top10stock_holding import equal_top10stock_holding_date
    from quant.project.my_timer.quarterly.fund_holding.weight_top10stock_good import weight_top10stock_good_date
    from quant.project.my_timer.quarterly.fund_holding.weight_top10stock_holding import weight_top10stock_holding_date
    weight_all_stock_good_date(date)
    weight_allstock_holding_date(date)
    equal_allstock_halfyear_date(date)
    equal_top10stock_holding_date(date)
    weight_top10stock_good_date(date)
    weight_top10stock_holding_date(date)

if __name__ == '__main__':

    fund_holding_update()
