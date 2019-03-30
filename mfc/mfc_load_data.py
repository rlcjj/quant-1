import os
import shutil
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.factor_operate import FactorOperate
from quant.mfc.mfc_get_data import MfcGetData
from quant.source.my_ftp import MyFtp


class MfcLoadData(Data):

    """
    下载FTP上的持仓文件和股票库文件

    1、日文件
    load_holding_date()
    change_holding_date()
    load_stock_pool_date()

    2、历史文件
    load_his_data()
    change_his_data_file()

    3、分红文件 并计算复权净值数据

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.ftp_path = r'\holdingdata'
        self.network_path = r'\\10.1.0.7\内外网文档交换\内网转外网\金融工程部\窦福成\holdingdata'

    def load_ftp_holding_date(self, date):

        """ 从FTP外网转内网文件夹 下载持仓信息 """

        load_file_list = ['01AfterTA.ok', '01BeforeTA.ok',
                          '01HIS成交回报.xls', '01HIS委托流水.xls', '01TODAY单元资产.xls',
                          '01TODAY基金证券.xls', '01TODAY基金资产.xls', '01TODAY组合证券.xls',
                          '01HIS流水查询.xls']

        local_path = os.path.join(self.data_path, r"mfc_holding_raw\201806_now\raw_file")

        date_int = Date().change_to_str(date)
        local_sub_path = os.path.join(local_path, date_int)
        ftp_sub_path = os.path.join(self.ftp_path, date_int)

        if not os.path.exists(local_sub_path):
            os.mkdir(local_sub_path)

        ftp = MyFtp()
        ftp.connect()
        print("####### Loading Ftp Holding File ############")
        ftp.load_file_folder_change_name(ftp_sub_path, local_sub_path, load_file_list, load_file_list)
        ftp.close()

    def load_network_holding_date(self, date):

        """ 从网盘内网转外网文件夹 下载持仓信息 """

        load_file_list = ['01Jijinzichan.ok', '01GuPiaoChi.ok',
                          '01HIS成交回报.xls', '01TODAY单元资产.xls',
                          '01TODAY基金证券.xls', '01TODAY基金资产.xls', '01TODAY组合证券.xls']
        #  '01HIS委托流水.xls', '01HIS流水查询.xls'

        local_path = os.path.join(self.data_path, r"mfc_holding_raw\201806_now\raw_file")

        local_sub_path = os.path.join(local_path, Date().change_to_str(date))
        network_sub_path = os.path.join(self.network_path, Date().change_to_str(date))

        if not os.path.exists(local_sub_path):
            os.mkdir(local_sub_path)

        print("####### Loading NetWork Holding File ############")

        for i_file in range(len(load_file_list)):

            file = load_file_list[i_file]
            local_file = os.path.join(local_sub_path, file)
            network_file = os.path.join(network_sub_path, file)
            print(local_file)
            shutil.copyfile(network_file, local_file)

    def load_ftp_stock_pool_date(self, date):

        """ 从FTP外网转内网文件夹 下载股票池 同时修改名字 """

        pool_file = os.path.join(self.data_path, "static_data", "Stock_Pool_Ftp.xlsx")
        pool_data = pd.read_excel(pool_file, encoding='gbk')
        pool_data = pool_data.dropna(subset=['Pool_Ch', 'Pool_Ftp'])
        pool_ch = list(pool_data['Pool_Ch'].values)
        pool_ftp = list(pool_data['Pool_Ftp'].values)

        local_path = os.path.join(self.data_path, r"mfc_holding_raw\201806_now\raw_file")

        date_int = Date().change_to_str(date)
        local_sub_path = os.path.join(local_path, date_int)
        ftp_sub_path = os.path.join(self.ftp_path, date_int)

        if not os.path.exists(local_sub_path):
            os.mkdir(local_sub_path)

        ftp = MyFtp()
        ftp.connect()
        print("####### Loading Ftp Stock Pool File ############")
        ftp.load_file_folder_change_name(ftp_sub_path, local_sub_path, pool_ftp, pool_ch)
        ftp.close()

    def load_network_stock_pool_date(self, date):

        """ 从网盘内网转外网文件夹 下载股票池 同时修改名字 """

        pool_file = os.path.join(self.data_path, "static_data", "Stock_Pool_Ftp.xlsx")
        pool_data = pd.read_excel(pool_file, encoding='gbk')
        pool_data = pool_data.dropna(subset=['Pool_Ch', 'Pool_Ftp'])
        pool_ch = list(pool_data['Pool_Ch'].values)
        pool_network = list(pool_data['Pool_Ftp'].values)

        local_path = os.path.join(self.data_path, r"mfc_holding_raw\201806_now\raw_file")

        local_sub_path = os.path.join(local_path, Date().change_to_str(date))
        network_sub_path = os.path.join(self.network_path, Date().change_to_str(date))

        if not os.path.exists(local_sub_path):
            os.mkdir(local_sub_path)

        print("####### Loading NetWork Stock Pool File ############")
        for i_file in range(len(pool_ch)):

            local_file = os.path.join(local_sub_path, pool_ch[i_file])
            network_file = os.path.join(network_sub_path, pool_network[i_file])
            try:
                shutil.copyfile(network_file, local_file)
                print(local_file)
            except Exception as e:
                print(local_file, "loading fail")

    def change_holding_date(self, date):

        """ 将持仓信息存储到另外一个位置 """

        date_before = Date().get_trade_date_offset(date, -1)
        local_path = os.path.join(self.data_path, r"mfc_holding_raw\201806_now\raw_file")

        date_int = Date().change_to_str(date)
        date_before = Date().change_to_str(date_before)
        before_path = os.path.join(local_path, date_int)
        after_path = os.path.join(self.data_path, "mfc_holding")

        change_file_dick = {'01HIS成交回报.xls': "成交回报\\成交回报_",
                            '01TODAY单元资产.xls': "单元资产\\单元资产_",
                            '01TODAY基金证券.xls': "基金证券\\基金证券_",
                            '01TODAY基金资产.xls': "基金资产\\基金资产_",
                            '01TODAY组合证券.xls': "组合证券\\组合证券_"}

        print("####### Change Holding File Position ############")

        for b_file, a_file in change_file_dick.items():
            before_file = os.path.join(before_path, b_file)
            if os.path.exists(before_file):
                print(before_file)
                data = pd.read_excel(before_file, index_col=[0], encoding='gbk')
                after_file = os.path.join(after_path, a_file + date_before + '.csv')
                print("Change File into ", after_file)
                data.to_csv(after_file)
            else:
                print("Tne File At ", date_int, " is No Exist. ")

    def load_mfc_fund_div(self):

        """ 下载泰达基金的分红文件 """

        in_file = '\\\\10.3.12.202\\fe\\fe_public\\业绩归因\\input\\dividend.csv'
        out_file = os.path.join(self.data_path, "static_data", "dividend.csv")
        shutil.copy(in_file, out_file)

    @staticmethod
    def get_file_tradedate(sub_path, begin_date_int, end_date_int):

        """ 利用文件夹的名字得到交易日序列 """

        begin_date_int = Date().change_to_str(begin_date_int)
        end_date_int = Date().change_to_str(end_date_int)
        dir_list = os.listdir(sub_path)
        date_list = list(map(lambda x: str(x)[5:13], dir_list))
        date_list_pd = pd.DataFrame(date_list, index=date_list, columns=['trade_date'])
        date_period = list(date_list_pd.ix[begin_date_int:end_date_int, 'trade_date'].values)
        return date_period

    def cal_mfc_private_fund_nav(self, fund_name, begin_date_int, end_date_int):

        """ 分红信息 和基金资产 计算泰达专户基金的复权净值（由专户投资经理给出）"""

        self.load_mfc_fund_div()
        file = os.path.join(self.data_path, "static_data", "dividend.csv")
        did_file = pd.read_csv(file, index_col=[0], encoding='gbk')

        did_file['DATETIME'] = did_file['DATETIME'].map(str)
        did_data = did_file[did_file.index == fund_name]
        sub_path = os.path.join(self.data_path, 'mfc_holding\\基金资产')

        date_list = self.get_file_tradedate(sub_path, begin_date_int, end_date_int)
        trade_date_list = Date().get_trade_date_series(begin_date_int, end_date_int)
        date_list = list(set(date_list) & set(trade_date_list))
        date_list.sort()
        cum_nav_period = pd.DataFrame([], index=date_list, columns=['单位净值', '基金份额', '净值'])

        for i in range(len(date_list)):

            date_int = date_list[i]
            try:
                asset = MfcGetData().get_fund_asset(date_int)
                asset.index = asset['基金名称']
                cum_nav_period.ix[date_int, '基金份额'] = asset.ix[fund_name, '基金份额']
                cum_nav_period.ix[date_int, '净值'] = asset.ix[fund_name, '净值']
                cum_nav_period['单位净值'] = cum_nav_period['净值'] / cum_nav_period['基金份额']
            except Exception as e:
                pass

        did_date = pd.DataFrame(did_data['DIVD_ASSET'].values, index=did_data['DATETIME'], columns=['分红资产'])
        all_data = pd.concat([cum_nav_period, did_date], axis=1)
        all_data['分红资产'] = all_data['分红资产'].fillna(0.0)

        all_data['分红净值'] = all_data['分红资产'] / all_data['基金份额']
        all_data['累计分红净值'] = all_data['分红净值'].cumsum()
        all_data['累计净值'] = all_data['累计分红净值'] + all_data['单位净值']
        all_data['累计净值涨跌幅'] = all_data['累计净值'].pct_change()
        all_data['累计复权分红净值'] = (all_data['累计分红净值'] * all_data['累计净值涨跌幅']).cumsum()
        all_data['累计复权净值'] = all_data['累计净值'] + all_data['累计复权分红净值']
        all_data = all_data.dropna(subset=["单位净值"])
        all_data[['累计复权净值', '累计净值']] = all_data[['累计复权净值', '累计净值']].fillna(1.0)
        all_data['累计净值涨跌幅'] = all_data['累计净值涨跌幅'].fillna(0.0)

        print("Cal Mfc fund %s Nav " % fund_name)
        file = os.path.join(self.data_path, "nav\private_fund", fund_name + "_Nav.csv")
        all_data.to_csv(file)

    def cal_mfc_private_fund_nav_all(self):

        """ 计算所有泰达专户基金的复权净值（全部更新） """

        begin_date_int = "20130101"
        end_date_int = datetime.today().strftime("%Y%m%d")

        data = MfcGetData().get_mfc_fund_info()
        data = data[data.Type == "专户"]

        for fund_name in data.Name:
            self.cal_mfc_private_fund_nav(fund_name, begin_date_int, end_date_int)

    def load_mfc_public_fund_nav(self, beg_date=None, end_date=None):

        """ wind下载多有泰达公募基金的复权净值 增量更新（默认更新最近两个月） """

        if end_date is None:
            end_date = Date().change_to_str(datetime.today())
        if beg_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -40)

        from WindPy import w
        w.start()

        data = MfcGetData().get_mfc_fund_info()
        data = data[data.Type == "公募"]

        for i_code in range(len(data)):

            fund_code = data.Code.values[i_code]
            nav_data = w.wsd(fund_code, "nav,NAV_adj,NAV_acc,NAV_adj_return1", beg_date, end_date, "")
            nav_data = pd.DataFrame(nav_data.Data, index=nav_data.Fields, columns=nav_data.Times).T
            nav_data.index = nav_data.index.map(lambda x: x.strftime('%Y%m%d'))
            new_data = nav_data.dropna(subset=['NAV_ADJ'])
            print(" Load Mfc Public Fund %s Nav " % fund_code)

            # 合并存储数据
            file = os.path.join(self.data_path, "nav\public_fund", fund_code + "_Nav.csv")
            if os.path.exists(file):
                old_data = pd.read_csv(file, index_col=[0], encoding='gbk')
                old_data.index = old_data.index.map(str)
                nav_data = FactorOperate().pandas_add_row(old_data, new_data)
            else:
                nav_data = new_data

            nav_data.to_csv(file)


if __name__ == '__main__':

    date = datetime.today()

    """ 早晨下载持仓文件和股票池 """
    MfcLoadData().load_network_holding_date(date)
    MfcLoadData().load_network_stock_pool_date(date)
    MfcLoadData().change_holding_date(date)

    """ 计算公募和专户的基金复权净值 """
    MfcLoadData().load_mfc_fund_div()
    MfcLoadData().cal_mfc_private_fund_nav_all()
    MfcLoadData().load_mfc_public_fund_nav()

