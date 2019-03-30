import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.factor_operate import FactorOperate


class IndexFactor(Data):

    """
    指数的不同属性CLOSE\PE\PCT时间序列的下载和获取
    默认为wind终端下载
    指数收益率会有缺失的情况 需要指数收盘价格相除计算

    load_index_factor()
    load_index_factor_all()
    get_index_factor()
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'index_data\index_factor'
        self.data_data_factor = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_index_factor(self,
                          index_code="000300.SH",
                          beg_date=None,
                          end_date=datetime.today().strftime("%Y%m%d"),
                          primary=False):

        """ 下载一个指数 最近的Factor """

        from WindPy import w
        w.start()

        out_file = os.path.join(self.data_data_factor, index_code + '.csv')
        if beg_date is None and os.path.exists(out_file):
            beg_date = Date().get_trade_date_offset(end_date, -20)

        if beg_date is None and not os.path.exists(out_file):
            try:
                base_data = w.wsd(index_code, "basedate")
                beg_date = base_data.Data[0][0].strftime("%Y%m%d")
            except Exception as e:
                beg_date = '19991231'

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)
        print(beg_date, end_date, index_code, primary)

        # 下载数据
        ##############################################################################

        if primary:
            index_data = w.wsd(index_code, "close,pe_ttm,pb_lf", beg_date, end_date, "Fill=Previous")
        else:
            index_data = w.wsd(index_code, "close", beg_date, end_date, "Fill=Previous")

        new_data = pd.DataFrame(index_data.Data, index=index_data.Fields, columns=index_data.Times).T
        new_data.index = new_data.index.map(lambda x: x.strftime('%Y%m%d'))
        print(new_data)

        try:
            new_data['PCT'] = new_data['CLOSE'].pct_change()
            print(" Loading Index Factor ", index_code)

            if os.path.exists(out_file):
                data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
                data.index = data.index.map(str)
                data = FactorOperate().pandas_add_row(data, new_data)
            else:
                print(" File No Exist ", index_code)
                data = new_data
            data = data.dropna(how='all')
            data.to_csv(out_file)
        except Exception as e:
            print(e)
            print(" Loading Index Factor Error", index_code)

    def load_index_factor_all(self,
                              beg_date=None,
                              end_date=datetime.today().strftime("%Y%m%d")):

        """ 下载所有指数 最近的Factor """

        file = os.path.join(self.data_data_factor, "index_pool.xlsx")
        index_pool = pd.read_excel(file, index_col=[0])
        for i in range(len(index_pool)):
            index_code = index_pool.index[i]
            primary = index_pool.loc[index_code, "Primary"]
            self.load_index_factor(index_code=index_code, beg_date=beg_date,
                                   end_date=end_date, primary=primary)

        self.make_index_mixed()

    def get_index_factor(self,
                         index_code="000300.SH",
                         beg_date='19991231',
                         end_date=datetime.today().strftime("%Y%m%d"),
                         attr=['CLOSE', 'PCT']):

        """ 得到单个指数 最近的Factor """

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        file = os.path.join(self.data_data_factor, index_code + '.csv')

        if os.path.exists(file):
            data = pd.read_csv(file, index_col=[0], encoding='gbk', parse_dates=[0])
            data.index = data.index.map(lambda x: x.strftime('%Y%m%d'))
            data = data.ix[beg_date: end_date, attr]
        else:
            print(" File No Exist ", index_code)
            data = None
        return data

    def make_index_mixed(self, index_code_list=["000905.SH", "399101.SZ", "399102.SZ"],
                         index_ratio_list=[1/3, 1/3, 1/3],
                         index_name="中证500+创业板综+中小板综"):

        """ 幾個指數相加 """
        result = pd.DataFrame([])

        for i in range(len(index_code_list)):
            index_code = index_code_list[i]
            index_ratio = index_ratio_list[i]
            index_data = self.get_index_factor(index_code, attr=["CLOSE"])
            index_data['CLOSE'] = index_data['CLOSE'].pct_change() * index_ratio
            index_data.columns = [index_code]
            result = pd.concat([result, index_data], axis=1)

        result = result.dropna()
        result['PCT'] = result.sum(axis=1)
        result['CLOSE'] = (result['PCT'] + 1.0).cumprod()
        out_file = os.path.join(self.data_data_factor, index_name + '.csv')
        result.to_csv(out_file)

    def make_index_with_fixed(self, fix_return, index_ratio, index_code, make_index_name):

        """ 得到指数+固定收益指数 """

        index_data = self.get_index_factor(index_code, attr=["CLOSE"])
        index_data['return_index'] = index_data.pct_change()
        index_data['return_make_index'] = index_data['return_index'] * index_ratio + fix_return / 250.0
        index_data[make_index_name] = (index_data['return_make_index'] + 1.0).cumprod()
        data = pd.DataFrame(index_data[make_index_name])
        data.columns = ["CLOSE"]
        print(" Making Index %s " % make_index_name)
        out_file = os.path.join(self.data_data_factor, make_index_name + '.csv')
        data.to_csv(out_file)

    def get_index_cross_factor(self, factor_name):

        """ 得到一个Index 某个Factor的二维数据 """

        file_list = os.listdir(self.data_data_factor)
        file_list.remove("index_pool.xlsx")
        index_list = list(map(lambda x: x[0:-4], file_list))
        data = pd.DataFrame([])

        for i in range(len(file_list)):
            index = index_list[i]
            data_add = self.get_index_factor(index_code=index, attr=[factor_name])
            data = pd.concat([data, data_add], axis=1)
        data.columns = index_list
        data = data.dropna(how='all')
        return data


if __name__ == "__main__":

    # Index Factor
    #############################################################################
    self = IndexFactor()
    index = IndexFactor()
    today = datetime.today().strftime("%Y%m%d")
    # self.load_index_factor_all(beg_date="20190101")
    self.make_index_mixed()

    # index.load_index_factor("000300.SH", "20180531", today)
    # index.load_index_factor_all("20180701", today)
    # index.load_index_factor("HSI.HI")
    #
    # print(index.get_index_factor("000905.SH", "20180601", today))
    # print(index.get_index_factor("881001.WI", "20180601", today))
    #
    # index_code = "000905.SH"
    # index_ratio = 0.8
    # fix_return = 0.01
    # make_index_name = "中证500指数80%+固定收益1%"
    # index.make_index_with_fixed(fix_return, index_ratio, index_code, make_index_name)
    # print(index.get_index_factor("中证500全收益指数80%+固定收益1%", attr=["CLOSE"]))
    #
    # print(index.get_index_cross_factor("PCT"))
