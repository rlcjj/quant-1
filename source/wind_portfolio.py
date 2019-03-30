from quant.data.data import Data
from quant.stock.date import Date

import pandas as pd
import os
from WindPy import w
w.start()


class WindPortUpLoad(Data):

    """ 上传wind组合 """

    def __init__(self):

        Data.__init__(self)
        self.owner = "W6964909132"
        self.path = os.path.join(self.primary_data_path, r'portfolio\wind_portfolio')

    @staticmethod
    def detect_error(res, action, port_name, date):

        """ 检查上传是否有错误 """

        if res.ErrorCode == 0:
            print(" %s %s At %s is OK " % (action, port_name, date))
        else:
            print(" %s %s At %s is Error " % (action, port_name, date))
            print(res)

    def upload_cash(self, port_name, date, cash="1000000000"):

        """ 上传wind组合期初现金 """

        change_date = Date().get_trade_date_offset(date, -1)
        res = w.wupf(port_name, change_date, "CNY", cash, "1",
                     "Owner=%s;Direction=Long;CreditTrading=No;HedgeType=Spec;" % self.owner)
        self.detect_error(res, "Upload Cash", port_name, date)

    def upload_weight_date(self, port_name, date):

        """
        上传wind组合权重
        将现金项去掉
        价格都为空 而不是0
        """

        # 参数 第二天上传
        #########################################################################################################
        file = os.path.join(self.path, port_name, port_name + '_' + date + '.csv')
        print(file)
        data_pd = pd.read_csv(file, encoding='gbk')
        data_pd = data_pd[data_pd.Code != 'Cash']
        data_pd = data_pd[~data_pd.Code.duplicated()]

        change_date = Date().get_trade_date_offset(date, 1)
        data_pd.Weight = data_pd.Weight.round(4)
        # data_pd = data_pd[data_pd.Weight >= 0.003]
        data_pd = data_pd.astype(str)

        data_pd["Price"] = ""

        # from quant.multi_factor.multi_factor import Stock
        # price = Stock().read_factor_h5("PriceCloseUnadjust")
        # try:
        #     price_date = pd.DataFrame(price[date])
        #     price_date.columns = ["PriceClose"]
        #     data = data_pd
        #     data.index = data_pd.Code
        #     data = pd.concat([data, price_date], axis=1)
        #     data = data.dropna()
        #     data.Price = data.PriceClose
        #     data_pd = data
        #     data_pd = data_pd.astype(str)
        #
        # except Exception as e:
        #     print(" Date %s Price is None " % date)

        # 整理字符串
        ##########################################################
        code_str = ','.join(list(data_pd.Code.values))
        weight_str = ','.join(list(data_pd.Weight.values))
        price_str = ','.join(list(data_pd.Price.values))
        direction_str = ','.join(list(data_pd.Direction.values))
        credit_str = ','.join(list(data_pd.CreditTrading.values))

        # 上传组合
        ##########################################################
        print("Direction=%s;CreditTrading=%s;Owner=%s;type=%s" %
              (direction_str, credit_str, self.owner, "weight"))
        print(port_name, change_date, code_str, weight_str, price_str)

        res = w.wupf(port_name, change_date, code_str, weight_str, price_str,
                     "Direction=%s;CreditTrading=%s;Owner=%s;type=%s" %
                     (direction_str, credit_str, self.owner, "weight"))

        self.detect_error(res, "UpLoad Weight ", port_name, change_date)

    def upload_weight_period(self, port_name):

        """ 上传 组合期初现金 和一段时间内wind组合权重 """

        sub_path = os.path.join(self.path, port_name)
        file_list = list(os.listdir(sub_path))
        date_list = list(map(lambda x: x[len(x)-12:len(x)-4], file_list))
        date_list.sort()

        self.upload_cash(port_name, date_list[0])

        for date in date_list:
            self.upload_weight_date(port_name, date)


if __name__ == "__main__":

    # WindPortUpLoad().upload_weight_date("东方红精选", "20180731")
    # WindPortUpLoad().upload_weight_date("东方红精选", "20180831")
    # WindPortUpLoad().upload_weight_date("东方红产业升级", "20180731")
    # WindPortUpLoad().upload_weight_date("东方红产业升级", "20180831")

    # WindPortUpLoad().upload_weight_period("东方红产业升级lasso")
    # WindPortUpLoad().upload_weight_period("优质基金池")

    # self = WindPortUpLoad()
    # self.upload_weight_period("超预期30")

    WindPortUpLoad().upload_weight_date("公募股票基金季报满仓", "20051031")
    WindPortUpLoad().upload_weight_date("公募股票基金季报满仓", "20060125")
