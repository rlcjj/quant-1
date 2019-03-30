import pandas as pd
from WindPy import w
from quant.stock.date import Date
w.start()
from datetime import datetime
import os


def load_outside_fund(date):

    # 全部场外基金
    # 公募基金 基金市场类(净值) 全部基金
    data = w.wset("sectorconstituent","date=" + str(date) + ";sectorid=a201010700000000")
    data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
    output_path = r'E:\Data\fund_data\fof_pool'
    data.to_csv(os.path.join(output_path, "全部场外基金_raw.csv"))
    return True


def load_inside_fund(date):

    # 全部场内基金
    # 公募基金 基金市场类(行情) 全部基金
    data = w.wset("sectorconstituent","date=" + str(date) + ";sectorid=1000019786000000")
    data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
    output_path = r'E:\Data\fund_data\fof_pool'
    data.to_csv(os.path.join(output_path, "全部场内基金_raw.csv"))
    return True


if __name__ == '__main__':

    today = datetime.today()
    Date().load_trade_date_series("Q")
    date = Date().get_last_fund_quarter_date(today)
    # date = '20180930'
    print(date)
    load_outside_fund(date)
    load_inside_fund(date)
