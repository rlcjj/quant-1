import pandas as pd
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'
import cx_Oracle

from quant.data.data import Data


class FinDb(Data):

    """
    Oracle 数据库下载数据（财汇数据库属于Oracle数据库）
    数据库 http://edm.finchina.com/datadict/login.jsp

    connect()
    close()
    load_raw_data()
    load_raw_data_filter()
    load_raw_data_filter_period()
    """

    def __init__(self):

        Data.__init__(self)

        self.ip = '10.1.0.34'
        self.port = '1526'
        self.db_name = 'FINDDATA'
        self.usr_name = 'findb'
        self.usr_password = 'findb2017!!'
        self.tns_name = None
        self.conn = None
        self.cursor = None
        self.load_param_file = os.path.join(self.primary_data_path, 'paramter_file\load_findb_param.xlsx')

    def connect(self):

        """ 联接数据库 """

        self.tns_name = cx_Oracle.makedsn(self.ip, self.port, self.db_name)
        self.conn = cx_Oracle.connect(self.usr_name, self.usr_password, self.tns_name)
        self.cursor = self.conn.cursor()

    def close(self):

        """ 关闭数据库 """

        self.cursor.close()
        self.conn.close()

    def change_str_to_list(self, in_str):

        """ 分离字符串 """

        in_str = in_str.replace('[', '')
        in_str = in_str.replace(']', '')
        in_str = in_str.replace(' ', '')
        in_str = in_str.replace('\'', '')
        in_str = in_str.replace("\"", "")
        in_str = in_str.replace("\n", "")
        str_list = in_str.split(',')
        return str_list

    def get_load_findb_param(self, name):

        """ 得到下载参数 """

        data = pd.read_excel(self.load_param_file, encoding='gbk')
        data = data.fillna("")
        if len(data[data.NAME == name].index) != 0:
            index = data[data.NAME == name].index.tolist()[0]
            table = data.ix[index, 'LOAD_TABLE']
            val_name = data.ix[index, 'VAL_NAME']
            val_name = self.change_str_to_list(val_name)[0]
            fileds_list_en = self.change_str_to_list(data.ix[index, 'LOAD_FIELD_EN'])
            fileds_list_ch = self.change_str_to_list(data.ix[index, 'LOAD_FIELD_CH'])
            filter_field = data.ix[index, "FILTER_FIELD"]
        else:
            table, fileds_list_en, filter_field, fileds_list_ch = "", "", "", ""
            print(" The Input Name is no exist, Please Confirm Your Name.")
        return table, fileds_list_en, filter_field, fileds_list_ch, val_name

    def load_raw_data(self, factor_name):

        """ 下载数据 """

        table_name, field_en, filter_field, field_ch, val_name = self.get_load_findb_param(factor_name)
        field_en_str = ','.join(field_en)
        self.connect()
        self.cursor.execute('SELECT ' + field_en_str + ' FROM ' + table_name)

        rows = self.cursor.fetchall()
        data_df = pd.DataFrame(rows, columns=field_ch)
        self.close()

        return data_df

    def load_raw_data_filter(self, factor_name, filter_val):

        """ 下载数据 filter_val=val """

        table_name, field_en, filter_field, field_ch, val_name = self.get_load_findb_param(factor_name)
        self.connect()

        field_en_str = ','.join(field_en)
        self.cursor.execute('SELECT ' + field_en_str + ' FROM ' + table_name +
                            ' WHERE ' + filter_field + '=' + str(filter_val))

        rows = self.cursor.fetchall()
        data_df = pd.DataFrame(rows, columns=field_ch)
        self.close()
        return data_df

    def load_raw_data_filter_period(self, factor_name, beg_val, end_val):

        """ 下载数据  min_val < filter_val < max_val """

        table_name, field_en, filter_field, field_ch, val_name = self.get_load_findb_param(factor_name)
        self.connect()

        field_en_str = ','.join(field_en)
        print(table_name, field_en, filter_field, field_ch)
        print('SELECT ' + field_en_str + ' FROM ' + table_name +
                            ' WHERE ' + filter_field + '<' + end_val + " AND " + filter_field + '>' + beg_val)
        self.cursor.execute('SELECT ' + field_en_str + ' FROM ' + table_name +
                            ' WHERE ' + filter_field + '<' + end_val + " AND " + filter_field + '>' + beg_val)

        rows = self.cursor.fetchall()
        data_df = pd.DataFrame(rows, columns=field_ch)
        self.close()
        return data_df


if __name__ == '__main__':

    from datetime import datetime
    from quant.stock.date import Date

    print(FinDb().load_raw_data("Fund_Basic_Info"))
    print(FinDb().load_raw_data_filter("Sec_Basic_Info", 101))

    today = Date().change_to_str(datetime.today())
    print(FinDb().load_raw_data_filter_period("Exchange_Share", "20040101", today))
