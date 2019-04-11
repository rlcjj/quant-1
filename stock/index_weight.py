import pandas as pd
import numpy as np
import shutil
import os

from quant.data.data import Data
from quant.stock.date import Date
from quant.source.my_ftp import MyFtp
from quant.utility.hdf_mfc import HdfMfc
from quant.utility.zip_file import ZipFile
from quant.utility.code_format import CodeFormat
from quant.stock.stock_static import StockStatic
from quant.utility.factor_operate import FactorOperate
from quant.stock.stock_factor_data import StockFactorData


class IndexWeight(Data):

    """
    指数每日权重的下载和获取 网盘\ftp\wind\自己计算

    load_weight_from_ftp_date()
    load_weight_from_wind_date()
    load_weight_china_index_date()

    load_weight_period()

    get_weight()
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'index_data\index_weight'
        self.data_path_weight = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_weight_from_network(self):

        """ 从网盘拿到 Index Weight h5文件 并生成csv """

        sub_path = os.path.join(self.data_path_weight)
        load_path = r"\\10.3.12.202\fe\primary_data\hdf\primary_data\weight"
        file_list = ["SH000300.h5", 'SH000905.h5']
        change_list = ['000300.SH', '000905.SH']

        for i_file in range(len(file_list)):

            file = file_list[i_file]
            change_name = change_list[i_file]
            old_file = os.path.join(load_path, file)
            new_file = os.path.join(sub_path, file)
            print("Loading Index Weight From NetWork %s " % change_name)
            shutil.copyfile(old_file, new_file)
            data = HdfMfc().read_hdf_factor(new_file)
            data.to_csv(os.path.join(sub_path, change_name + '.csv'))
            os.remove(new_file)

    def write_index_weight(self, index_code, new_data):

        """  合并新老权重数据 """

        old_file = os.path.join(self.data_path_weight, index_code + '.csv')
        if os.path.exists(old_file):

            old_data = self.get_weight(index_code)
            old_data = old_data.T
            new_data = new_data.T
            data = FactorOperate().pandas_add_row(old_data, new_data).T
        else:
            data = new_data
        data = data.dropna(how='all')
        data = data.T.dropna(how='all').T
        data.to_csv(old_file)

    def load_weight_from_ftp_date(self, index_code, date):

        """
        从中证公司的FTP上下载原始指数权重 解压缩 并改变原始文件的位置
        """

        date = Date().change_to_str(date)
        code = CodeFormat().stock_code_drop_postfix(index_code)

        # ftp load
        ftp = MyFtp(ip="124.74.243.125", port=21, user_name="csitd", user_password="26266119")
        ftp.connect()
        file_name = "%sweightnextday%s.zip" % (code, date)
        ftp_file = "/idxdata/data/asharedata/%s/weight_for_next_trading_day/%s" % (code, file_name)
        local_file = os.path.join(self.data_path_weight, file_name)
        ftp.load_file(ftp_file, local_file)
        ftp.close()

        print("Loading Index Weight From NetWork %s % s" % (index_code, date))

        # unzip
        ZipFile().unzip_file(local_file, self.data_path_weight)
        unzip_file_name = code + "weightnextday" + date + ".xls"
        unzip_file_name = os.path.join(self.data_path_weight, unzip_file_name)
        new_data = pd.read_excel(unzip_file_name, encoding='gbk')
        new_data = new_data.iloc[:, [4, 16]]
        new_data.columns = ['CODE', 'WEIGHT']
        new_data.CODE = new_data.CODE.map(CodeFormat().stock_code_add_postfix)
        new_data.WEIGHT = new_data.WEIGHT.astype(np.float) / 100.0
        new_data.index = new_data.CODE
        new_data = new_data.drop(['CODE'], axis=1)
        new_data.columns = [date]
        os.remove(os.path.join(self.data_path_weight, code + "weightnextday" + date + ".xls"))
        os.remove(os.path.join(self.data_path_weight, code + "weightnextday" + date + ".zip"))
        os.remove(os.path.join(self.data_path_weight, code + "weightnextday" + date + ".flg"))

        self.write_index_weight(index_code, new_data)

    def load_weight_from_wind_date(self, index_code, date):

        """
        从wind客户终端下载指数权重
        注意：未付费的指数只能获得月频的权重数据
        """

        from WindPy import w
        w.start()

        date = Date().change_to_str(date)
        last_date = Date().get_trade_date_offset(date, -1)

        print('Loading Index Weight Form Wind %s %s' % (index_code, date))

        data = w.wset("indexconstituent", "date=%s;windcode=%s;field=wind_code,i_weight" % (last_date, index_code))
        new_data = pd.DataFrame(data.Data, index=['CODE', 'WEIGHT'], columns=data.Codes).T
        new_data.index = new_data.CODE
        print(new_data)
        new_data.WEIGHT /= 100.0
        new_data = new_data.drop(['CODE'], axis=1)
        new_data.columns = [date]

        if len(new_data.dropna()) < len(new_data):
            diff = len(new_data) - len(new_data.dropna())
            print('The number of nan is %s' % diff)
            new_data = new_data.dropna()
        if len(new_data) < 20:
            print('The number of code is %s' % len(new_data.dropna()))

        self.write_index_weight(index_code, new_data)

    def load_weight_windqa_date(self, date):

        """
        利用自由流通市值作为指数权重
        计算wind全A 剔除新股和次新股
        """

        date = Date().change_to_str(date)
        date_halfyear = Date().get_normal_date_offset(date, -120)
        index_code = "881001.WI"

        print('Loading Index Weight By FreeMarketValue %s %s' % (index_code, date))

        if date > "20181101":
            StockStatic().load_free_market_value_date(date)
            data = StockStatic().get_free_market_value_date(date)
        else:
            data = StockFactorData().read_factor_h5("Mkt_freeshares")
            data = pd.DataFrame(data[date])
            data.columns = ["Free_Market_Value"]

        ipo_data = StockStatic().get_ipo_date()
        data = pd.concat([data, ipo_data], axis=1)
        data = data[data['IPO_DATE'] <= date_halfyear]
        data = data[data['DELIST_DATE'] >= date]

        data = data.dropna()
        free_mv_sum = data['Free_Market_Value'].sum()
        weight = pd.DataFrame(data['Free_Market_Value'].values / free_mv_sum, index=data.index, columns=[date])
        weight.index.name = "CODE"

        print(len(weight))
        self.write_index_weight(index_code, weight.copy())

    def load_weight_period(self, index_code, beg_date, end_date):

        """ 下载一段时间内 每个交易日的指数权重 """

        date_list = Date().get_trade_date_series(beg_date, end_date)

        if index_code in ['000300.SH', '000905.SH', '000940.SH']:
            for date in date_list:
                self.load_weight_from_ftp_date(index_code, date)

        elif index_code in ["China_Index_Benchmark", '881001.WI']:
            for date in date_list:
                self.load_weight_china_index_date(date)
        else:
            for date in date_list:
                self.load_weight_from_wind_date(index_code, date)

    def get_weight(self, index_code="000300.SH"):

        """ 从文件得到所有日期权重 """

        file = os.path.join(self.data_path_weight, index_code + '.csv')
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data.columns = data.columns.map(str)
        return data

    def get_weight_date(self, index_code, date):

        """ 从文件得到特定日期权重 """

        data = self.get_weight(index_code)
        data_date = pd.DataFrame(data[date])
        data_date = data_date.dropna()
        data_date.columns = ['WEIGHT']
        data_date.index.name = 'CODE'
        return data_date

    def make_weight_mixed(self,
                          date,
                          index_code_list=["000905.SH", "399101.SZ", "399102.SZ"],
                          index_ratio_list=[1/3, 1/3, 1/3],
                          index_name="中证500+创业板综+中小板综"):

        """ 指数权重合并 """

        result = pd.DataFrame([])

        for i in range(len(index_code_list)):
            index_code = index_code_list[i]
            index_ratio = index_ratio_list[i]
            index_data = self.get_weight_date(index_code, date) * index_ratio
            index_data.columns = [index_code]
            result = pd.concat([result, index_data], axis=0)

        result = result.fillna(0.0)
        result[date] = result.sum(axis=1)
        self.write_index_weight(index_name, pd.DataFrame(result[date]))


if __name__ == "__main__":

    from datetime import datetime
    date = datetime.today()
    date = Date().get_trade_date_offset(date, -1)
    self = IndexWeight()
    index_code = "881001.WI"

    date_series = Date().get_trade_date_series("20190101", "20190301")
    # for date in date_series:
    #     self.make_weight_mixed(date)

    """ Load Index Weight """

    # self.load_weight_from_ftp_date("000905.SH", date)
    # self.load_weight_from_wind_date("000016.SH", date)
    # self.load_weight_china_index_date(date)
    #
    # self.load_weight_period("000905.SH", "20181216", date)
    self.load_weight_period("000852.SH", "20181227", "20190104")
    self.load_weight_period("399101.SZ", "20181227", "20190104")
    self.load_weight_period("399102.SZ", "20181227", "20190104")

    # self.load_weight_from_network()

    """ Get Index Weight """

    # print(self.get_weight("000300.SH"))
    # print(self.get_weight_date("China_Index_Benchmark", date))
    # self.load_weight_from_network()
    # self.load_weight_from_ftp_date("000905.SH", "20190201")
    # self.load_weight_from_ftp_date("000300.SH", "20190201")
