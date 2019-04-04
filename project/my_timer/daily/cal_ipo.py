from quant.project.my_timer.daily.cal_ipo_buy import CalIPOBuy
from quant.project.my_timer.daily.cal_ipo_sell import CalIPOSell
from datetime import datetime
import os


if __name__ == '__main__':

    self = CalIPOBuy()
    today = datetime.today().strftime("%Y%m%d")
    # self.load_param_file(today)
    self.ipo_buy_online(today)
    self.ipo_buy_outline(today)

    self = CalIPOSell()
    today = datetime.today().strftime("%Y%m%d")
    self.ipo_sell(today)

    os.system("pause")
