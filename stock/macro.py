from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.factor_operate import FactorOperate

from datetime import datetime
import pandas as pd
import os


class Macro(Data):

    def __init__(self):

        """ 宏观数据的下载 和获取 """

        Data.__init__(self)
        self.sub_data_path = r'macro_data\data'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_macro_data_wind(self,
                             macro_code="M0000545",
                             beg_date="19900101",
                             end_date=datetime.today().strftime("%Y%m%d")):

        """ 下载宏观数据 """

        from WindPy import w
        w.start()

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        # 下载数据
        ##############################################################################
        data = w.edb(macro_code, beg_date, end_date, "Fill=Previous")
        new_data = pd.DataFrame(data.Data, columns=data.Times, index=data.Codes).T
        new_data = new_data.dropna()
        new_data.index = new_data.index.map(lambda x: x.strftime('%Y%m%d'))

        print(" Loading Macro Data %s From %s To %s " % (macro_code, beg_date, end_date))
        out_file = os.path.join(self.data_path, macro_code + '.csv')

        if os.path.exists(out_file):
            data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
            data.index = data.index.map(str)
            data = FactorOperate().pandas_add_row(data, new_data)
        else:
            print(" File No Exist ", macro_code)
            data = new_data

        data = data.dropna(how='all')
        data.to_csv(out_file)

    def get_macro_data(self,
                       macro_code="M0000545",
                       beg_date="19900101",
                       end_date=datetime.today().strftime("%Y%m%d")):

        """ 得到宏观数据 """

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        file = os.path.join(self.data_path, macro_code + '.csv')
        print(file)

        if os.path.exists(file):
            data = pd.read_csv(file, index_col=[0], encoding='gbk', parse_dates=[0])
            data.index = data.index.map(lambda x: x.strftime('%Y%m%d'))
            data = data.ix[beg_date:end_date, :]
            data = data.dropna()
        else:
            print(" File No Exist ", macro_code)
            data = pd.DataFrame([])
        return data

    def get_daily_risk_free_rate(self,
                                 beg_date="19900101",
                                 end_date=datetime.today().strftime("%Y%m%d")):

        """ 利用十年期国债收益率利率代表为无风险利率 2002年开始 """

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        data = self.get_macro_data("S0059749", beg_date, end_date)
        data.columns = ["RiskFreeRate"]

        data["RiskFreeRate"] /= 250
        return data

    def load_daily_risk_free_rate(self,
                                  beg_date="19900101",
                                  end_date=datetime.today().strftime("%Y%m%d")):

        """ 利用十年期国债收益率利率代表为无风险利率 2002年开始 下载"""

        self.load_macro_data_wind("S0059749", beg_date, end_date)

    def load_all_macro_data_wind(self, beg_date, end_date):

        """ 下载所有宏观数据 """

        params = [

            # 月频率数据
            ["宏观基本面-产出视角-工业增加值-当月同比", "M0000545"],
            ["宏观基本面-产出视角-出口交货值-当月同比", "M0007454"],
            ["宏观基本面-产出视角-发电量-当月同比", "S0027013"],
            ["宏观基本面-产出视角-货运量-当月同比", "S0036033"],
            ["宏观基本面-消费视角-消费-社会消费品零售总额-当月同比", "M0001428"],
            ["宏观基本面-消费视角-进出口金额-当月同比", "M0000605"],
            ["宏观基本面-市场预期-PMI", "M0017126"],
            ["物价指数-PPI-全部工业品-当月同比", "M0001227"],
            ["物价指数-CPI-当月同比", "M0000612"],
            ["物价指数-CGPI(企业商品价格指数)-当月同比", "M0001375"],
            ["物价指数-RPI(商品零售价格指数)-当月同比", "M0001022"],
            ["M0-当月同比", "M0001381"],
            ["M1-当月同比", "M0001383"],
            ["M2-当月同比", "M0001385"],
            ["社会融资规模-当月值", "M5206730"],
            ["社会融资规模-累计值", "M5201630"],
            ["社会融资规模存量-当月同比", "M5525763"],

            # 日频率数据
            ["SHIBOR-隔夜", "M0017138"],
            ["SHIBOR-1月", "M0017141"],
            ["SHIBOR-1年", "M0017145"],
            ["中债国债到期收益率-1年", "S0059744"],
            ["中债国债到期收益率-5年", "S0059747"],
            ["中债国债到期收益率-10年", "S0059749"],
            ["中债国开债到期收益率-1年", "M1004263"],
            ["中债国开债到期收益率-5年", "M1004267"],
            ["中债国开债到期收益率-10年", "M1004271"],
        ]

        for i in range(len(params)):

            macro_name = params[i][0]
            macro_code = params[i][1]
            print("Loading Macro Data %s Close From %s To %s " % (macro_name, beg_date, end_date))
            self.load_macro_data_wind(macro_code, beg_date, end_date)

if __name__ == '__main__':

    self = Macro()
    # self.load_macro_data_wind("M0000545", "19950101", "20171114")
    # print(self.get_macro_data("M0000545", "20080101", "20121231"))
    beg_date = "20190101"
    end_date = datetime.today().strftime("%Y%m%d")
    self.load_all_macro_data_wind(beg_date, end_date)
