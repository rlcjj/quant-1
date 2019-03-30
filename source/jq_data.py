from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.code_format import CodeFormat

import os
import pandas as pd
from datetime import datetime
from jqdatasdk import auth, get_all_securities


class JQData(Data):

    """ JQ接口下载和读取数据 """

    def __init__(self):

        Data.__init__(self)
        self.log_in()

    def log_in(self):

        """ 登陆 """

        user = '18810515636'
        pass_wd = 'dfc19921208'
        auth(user, pass_wd)

    def change_code_format_from_jq(self, code):

        code = code.replace("XSHE", "SZ")
        code = code.replace("XSHG", "SH")
        return code

    def change_code_format_to_jq(self, code):

        code = code.replace("SZ", "XSHE")
        code = code.replace("SH", "XSHG")
        return code

    def load_all_stock_code(self):

        data = get_all_securities(types=['multi_factor'], date=datetime.today())
        data.index = data.index.map(self.change_code_format_from_jq)

        file = os.path.join(self.primary_data_path, r"stock_data\stock_basic_data\jq_all_code.csv")
        data.to_csv(file)

if __name__ == '__main__':

    self = JQData()
    self.load_all_stock_code()


