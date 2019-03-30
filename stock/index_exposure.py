from datetime import datetime
import pandas as pd
import os

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.barra import Barra
from quant.stock.index_weight import IndexWeight
from quant.utility.factor_operate import FactorOperate


class IndexBarraExposure(Data):

    """
    利用指数的持仓来计算指数 barra_exposure 满仓
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'index_data\index_barra_exposure'
        self.data_path_exposure = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_index_exposure_date(self, index_code, date):

        """ 计算某个时间点的BARRA暴露 """

        type_list = ["STYLE", "COUNTRY", "INDUSTRY"]
        print("Calculating Index %s Barra Exposure at %s" % (index_code, date))
        try:
            weight = IndexWeight().get_weight_date(index_code, date)
            exposure = Barra().get_factor_exposure_date(date, type_list)

            data = pd.concat([weight, exposure], axis=1)
            data = data.dropna(subset=["WEIGHT"])

            res = pd.DataFrame([], columns=exposure.columns, index=[date])

            for i_col in range(len(exposure.columns)):
                risk_factor_name = exposure.columns[i_col]
                res.ix[date, risk_factor_name] = (data["WEIGHT"] * data[risk_factor_name]).sum() / data['WEIGHT'].sum()

            data = pd.concat([weight, exposure], axis=1)
            data = data.dropna(subset=["WEIGHT"])

            res = pd.DataFrame([], columns=exposure.columns, index=[date])

            for i_col in range(len(exposure.columns)):
                risk_factor_name = exposure.columns[i_col]
                res.ix[date, risk_factor_name] = (data["WEIGHT"] * data[risk_factor_name]).sum() / data['WEIGHT'].sum()
        except Exception as e:
            res = pd.DataFrame([])
        return res

    def cal_index_exposure(self,
                           index_code="000300.SH",
                           beg_date="20031231",
                           end_date=datetime.today().strftime("%Y%m%d"),
                           period="D"):

        """ 计算一段时间的BARRA暴露 """

        date_series_daily = Date().get_trade_date_series(beg_date, end_date, period=period)

        for i_date in range(len(date_series_daily)):
            date = date_series_daily[i_date]
            res = self.cal_index_exposure_date(index_code, date)
            if i_date == 0:
                new_data = res
            else:
                new_data = pd.concat([new_data, res], axis=0)

        out_file = os.path.join(self.data_path_exposure,  "Index_Barra_Exposure_" + index_code + '.csv')
        if os.path.exists(out_file):
            data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
            data.index = data.index.map(str)
            data = FactorOperate().pandas_add_row(data, new_data)
        else:
            data = new_data
        data.to_csv(out_file)

    def get_index_exposure_date(self, index_code, date, type_list=["STYLE"]):

        """ 得到某个时间点的BARRA暴露 """

        try:
            date = Date().get_trade_date_offset(date, 0)
            out_file = os.path.join(self.data_path_exposure, "Index_Barra_Exposure_" + index_code + '.csv')
            data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
            data.index = data.index.map(str)
            factor_name = Barra().get_factor_name(type_list=type_list)
            factor_name = list(factor_name["NAME_EN"].values)
            exposure_date = data.ix[date, factor_name]
            exposure_date = pd.DataFrame(exposure_date.values, index=exposure_date.index, columns=[index_code]).T
        except Exception as e:
            print("读取出现问题")
            exposure_date = pd.DataFrame([])

        return exposure_date

    def get_index_exposure(self, index_code, beg_date, end_date, type_list=["STYLE"]):

        """ 得到一段时间的BARRA暴露 """

        try:
            out_file = os.path.join(self.data_path_exposure, "Index_Barra_Exposure_" + index_code + '.csv')
            data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
            data.index = data.index.map(str)
            factor_name = Barra().get_factor_name(type_list=type_list)
            factor_name = list(factor_name["NAME_EN"].values)
            exposure = data.ix[beg_date:end_date, factor_name]
        except Exception as e:
            print("读取出现问题")
            exposure = pd.DataFrame([])

        return exposure


if __name__ == "__main__":

    self = IndexBarraExposure()
    index_code = "000300.SH"
    date = "20171229"

    """ 计算 """
    # self.cal_index_exposure("000016.SH", beg_date="20171231", end_date="20180819")
    # self.cal_index_exposure("000300.SH", beg_date="20050101", end_date="20170819")
    # self.cal_index_exposure("000905.SH", beg_date="20171231", end_date="20180819")
    # self.cal_index_exposure("881001.WI", beg_date="20040101", end_date="20180831")
    # self.cal_index_exposure("公募股票基金季报平均",  beg_date="20051231", end_date="20180831")

    """ 得到 """
    # print(self.get_index_exposure_date("000300.SH", "20180718"))
    # print(self.get_index_exposure("881001.WI", "20180909", "20181010"))


