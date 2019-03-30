from quant.project.my_timer.weekly.morning_report.market import Market
from quant.project.my_timer.weekly.morning_report.etf_fund import ETFFund
from quant.project.my_timer.weekly.morning_report.hk_inflow import HKInflow
from quant.project.my_timer.weekly.morning_report.major_holder_deal import MajorHolderDeal
from quant.project.my_timer.weekly.morning_report.fund_holder_inflow import FundHolderInflow
from quant.project.my_timer.weekly.morning_report.fund_style_position import FundStylePosition

from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.index import Index
from datetime import datetime


def update_data():

    """ 更新需要的数据 """

    end_date = datetime.today()
    Date().load_trade_date_series("D")
    beg_date = Date().get_trade_date_offset(end_date, -10)

    # 股票基金数据
    # Stock().load_h5_primary_factor()
    # Fund().load_fund_factor_all(beg_date, end_date)

    # 需要消耗 wind 流量（重要股东二级市场交易、指数涨跌幅）
    Stock().load_major_holder_deal(beg_date, end_date)
    Index().load_index_factor_all(beg_date, end_date)


def main(end_date, quarter_date, quarter_last_date):

    """ 生成晨报需要excel"""

    ETFFund().generate_excel(end_date)
    FundHolderInflow().generate_excel(end_date, quarter_date, quarter_last_date)

    MajorHolderDeal().generate_excel(end_date)
    Market().generate_excel(end_date)

    FundStylePosition().cal_fund_style_position()
    FundStylePosition().generate_excel(end_date)
    HKInflow().generate_excel(end_date)


if __name__ == '__main__':

    end_date = "20190321"
    quarter_date = "20181231"
    quarter_last_date = "20180930"

    update_data()
    main(end_date, quarter_date, quarter_last_date)

