import os
from datetime import datetime

from quant.stock.date import Date
from quant.fund.fund import Fund
from quant.stock.stock import Stock
from quant.stock.barra import Barra
from quant.stock.index import Index


def load_data():

    """ 更新数据 """

    print(" 更新本周数据 ")

    # 参数
    today = datetime.today().strftime("%Y%m%d")

    # 更新日期(早晨已经更新日期序列)
    Date().load_trade_date_series_all()

    # 股票因子数据（网盘h5下载数据）
    Stock().load_h5_primary_factor()

    # 更新 Barra数据
    beg_date = Date().get_trade_date_offset(today, -5)
    Barra().update_barra(beg_date, today)

    # 更新Fund（基础数据、因子数据、持仓数据）
    beg_date = Date().get_trade_date_offset(today, -90)
    Fund().update_fund_data(beg_date, today)

    # 更新Index(因为IndexWeight每天更新，这里不用更新)
    # 需要wind流量
    beg_date = Date().get_trade_date_offset(today, -8)
    Index().load_index_factor_all(beg_date, today)

    # Stock静态数据，例如股票池、成立日期等等
    # 需要wind流量
    beg_date = Date().get_trade_date_offset(today, -6)
    Stock().load_stock_static_data_all(beg_date, today)

    os.system("pause")


if __name__ == '__main__':

    load_data()

