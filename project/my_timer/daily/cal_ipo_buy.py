import os
import shutil
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.source.my_ftp import MyFtp
from quant.mfc.mfc_data import MfcData
from quant.utility.code_format import CodeFormat

from WindPy import w
w.start()


class CalIPOBuy(Data):

    """
    新股申购
    由杨帆 整理好新股申购文件（每个基金一个文件）
    下载 整理 为每位基金经理生成一个新股申购文件（线上、线下分开）
    一般来说 线下会先于线上
    沪市新股申购代码 和 股票代码不一致

    """

    def __init__(self):

        """ 初始化数据存储位置和参数 """

        Data.__init__(self)
        self.sub_data_path = 'mfcteda_data\cal_ipo_buy'
        self.network_path = r'\\10.1.0.7\rd\※※金融工程部数据产品※※\新股申购文件'
        self.ftp_path = "\\ipo_stock_buy\\"
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_param_file(self, today=datetime.today().strftime("%Y%m%d")):

        """ 下载打新参数文件 """

        network_path = os.path.join(self.network_path, today)
        local_path = os.path.join(self.data_path, today, "新股原始文件")
        print("下载打新文件#######################################")
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        if not os.path.exists(network_path):
            print("文件夹不存在，今日无打新，可以再次确认")
        else:
            dir_list = os.listdir(network_path)
            if len(dir_list) == 0:
                print("文件夹存在，但是文件夹为空，可以再次确认")
            else:
                print("文件夹存在，且文件夹不为空，下载参数文件")
                for file in dir_list:
                    network_file = os.path.join(network_path, file)
                    local_file = os.path.join(local_path, file)
                    print(network_file)
                    shutil.copyfile(network_file, local_file)

    def ipo_buy_online(self, today=datetime.today().strftime("%Y%m%d")):

        """ 线上打新 （股票总市值不够1000万 或者不够单只股票打新下限 或者 专户产品）"""

        fund_info = MfcData().get_mfc_fund_info()
        fund_info.index = fund_info.ShortName
        fund_info = fund_info[['Name', 'StockGroupId', 'Id']]
        fund_info = fund_info.dropna()

        print("开始计算网上打新############################################")

        # New FTP Folder
        ftp = MyFtp()
        ftp.connect()
        ftp_folder = os.path.join(self.ftp_path, today)
        ftp.upload_folder(ftp_folder)
        ftp.close()
        manager_info = MfcData().get_manager_fund()

        for i_manager in range(len(manager_info.columns)):

            manager_name = manager_info.columns[i_manager]
            manager_fund = pd.DataFrame(manager_info[manager_name])
            manager_fund = manager_fund.dropna()
            manager_fund.index = manager_fund[manager_name]

            # 新思路和集利债 固收负责 在刘洋产品中去掉
            if manager_name == "liuyang":
                manager_fund = manager_fund.drop("泰达新思路")
                manager_fund = manager_fund.drop("泰达宏利集利债券")

            if manager_name == "caolongjie":
                manager_fund = manager_fund.drop("建行中国人寿固收组合管理计划")

            manager_fund_info = fund_info[fund_info['Name'].map(lambda x: x in manager_fund.values)]

            local_path = os.path.join(self.data_path, today, "新股原始文件")
            dir_list = os.listdir(local_path)

            result = pd.DataFrame([])

            for i_file in range(len(dir_list)):

                file = dir_list[i_file]
                local_file = os.path.join(local_path, file)
                try:
                    data = pd.read_excel(local_file, index_col=[0], sheetname='2网上')
                except Exception as e:
                    print(e)
                    data = pd.read_excel(local_file, index_col=[0])

                if data.index.name == "泰达宏利基金管理有限公司":

                    print(file, "有网上新股")

                    """ 一种是只有网上发行的 一种是网下发行完成后再网上发行的"""

                    try:
                        stock_code = CodeFormat().change_normal_to_ipo_apply_code(data.iloc[2, 9])[0:6]
                        stock_price = data.iloc[2, 11]
                        print("之前问询过网下，现在网上新股")
                        """ 当日拿不出来当日申购上限数据 就用Excel中的数据 """
                        stock_code_normal = CodeFormat().change_ipo_apply_code_to_normal(data.iloc[2, 9])[0:6]
                        stock_code_normal = CodeFormat().stock_code_add_postfix(stock_code_normal)
                        num = w.wss(stock_code_normal, "ipo_SShares_uplimit", "unit=1")
                        stock_number_up = num.Data[0][0]

                        if np.isnan(stock_number_up) or stock_number_up == 0:
                            stock_number_up = data.iloc[2, 13]

                        print(stock_code, stock_number_up, stock_price)

                        fund1 = data.iloc[4:6, :].T
                        fund1.index = fund1['基金名称']
                        fund1 = fund1.dropna()
                        fund1 = fund1[fund1.iloc[:, 1] == "是"]

                        fund2 = data.iloc[10:12, :].T
                        fund2.index = fund2['基金名称']
                        fund2 = fund2.dropna()
                        fund2 = fund2[fund2.iloc[:, 1] == "是"]

                        fund3 = data.iloc[17:19, :].T
                        fund3.index = fund3['基金名称']
                        fund3 = fund3.dropna()
                        fund3 = fund3[fund3.iloc[:, 1] == "是"]

                    except Exception as e:
                        print(e)
                        stock_code = CodeFormat().change_normal_to_ipo_apply_code(data.iloc[4, 0])[0:6]
                        stock_price = data.iloc[4, 6]
                        print("只有网上新股")

                        """ 当日拿不出来当日申购上限数据 就用Excel中的数据 """

                        stock_code_normal = CodeFormat().change_ipo_apply_code_to_normal(data.iloc[4, 0])[0:6]
                        stock_code_normal = CodeFormat().stock_code_add_postfix(stock_code_normal)
                        num = w.wss(stock_code_normal, "ipo_SShares_uplimit", "unit=1")
                        stock_number_up = num.Data[0][0]

                        if np.isnan(stock_number_up) or stock_number_up == 0:
                            stock_number_up = data.iloc[4, 7]

                        print(stock_code, stock_number_up, stock_price)

                        fund1 = data.iloc[7:9, :].T
                        fund1.index = fund1['基金名称']
                        fund1 = fund1.dropna()
                        fund1 = fund1[fund1.iloc[:, 1] == "是"]

                        fund2 = data.iloc[13:15, :].T
                        fund2.index = fund2['基金名称']
                        fund2 = fund2.dropna()
                        fund2 = fund2[fund2.iloc[:, 1] == "是"]

                        fund3 = data.iloc[19:21, :].T
                        fund3.index = fund3['基金名称']
                        fund3 = fund3.dropna()
                        fund3 = fund3[fund3.iloc[:, 1] == "是"]

                    fund = pd.concat([fund1, fund2, fund3], axis=0)
                    online_fund = pd.concat([fund, manager_fund_info], axis=1)
                    online_fund = online_fund.dropna()

                    online_fund['证券代码'] = stock_code
                    online_fund['委托方向'] = "C"
                    online_fund['指令数量'] = stock_number_up
                    online_fund['指令价格'] = stock_price
                    online_fund['价格模式'] = ""
                    online_fund['交易市场内部编号'] = CodeFormat().get_stcok_market(stock_code)
                    online_fund['交易市场内部编号'] = online_fund['交易市场内部编号'].map(lambda x: 1 if x == 'SH' else 2)
                    online_fund['当前指令市值/净值（%）'] = ""
                    online_fund['目标市值/净值（%）'] = ""
                    online_fund['基金编号（序号）'] = online_fund['Id']
                    online_fund['基金名称'] = online_fund['Name']
                    online_fund["组合编号"] = online_fund['StockGroupId']

                    result = pd.concat([online_fund, result], axis=0)
                else:
                    print(file, "没有网上新股")
                    continue

            if len(result):
                local_path = os.path.join(self.data_path, today, "申购单")
                if not os.path.exists(local_path):
                    os.makedirs(local_path)

                file = '网上_%s.xls' % manager_name
                out_file = os.path.join(local_path, file)
                col = ['证券代码', '委托方向', '指令数量', '指令价格', '价格模式',
                       '交易市场内部编号', '当前指令市值/净值（%）', '目标市值/净值（%）',
                       '基金编号（序号）', '基金名称', '组合编号']
                result = result[col]
                print("今日有网上新股%s %s %s" % (manager_name, today, len(result)))
                result.to_excel(out_file, index=None)

                ftp = MyFtp()
                ftp.connect()
                ftp_file = os.path.join(self.ftp_path, today, file)
                ftp.upload_file(ftp_file, out_file)
                ftp.close()
            else:
                print("今日无网上新股%s %s %s" % (manager_name, today, len(result)))

    def ipo_buy_outline(self, today=datetime.today().strftime("%Y%m%d")):

        """ 线下打新 （股票总市值大于600万， 公募）"""

        print("开始计算网下打新############################################")

        fund_info = MfcData().get_mfc_fund_info()
        fund_info.index = fund_info.ShortName
        fund_info = fund_info[['Name', 'StockGroupId', 'Id', 'FundId']]
        fund_info = fund_info.dropna()
        fund_info['Id'] = fund_info['Id']
        fund_info['FundId'] = fund_info['FundId'].map(CodeFormat.stock_code_add_postfix)
        fund_info['FundId'] = fund_info['FundId'].map(lambda x: x[0:6])

        # New FTP Folder
        ftp = MyFtp()
        ftp.connect()
        ftp_folder = os.path.join(self.ftp_path, today)
        ftp.upload_folder(ftp_folder)
        ftp.close()
        manager_info = MfcData().get_manager_fund()
        manager_list = ['liuxin', 'liuyang']

        for i_manager in range(len(manager_list)):

            manager_name = manager_list[i_manager]
            manager_fund = pd.DataFrame(manager_info[manager_name])
            manager_fund = manager_fund.dropna()
            manager_fund.index = manager_fund[manager_name]

            # 新思路和集利债 固收负责 在刘洋产品中去掉
            if manager_name == "liuyang":
                manager_fund = manager_fund.drop("泰达新思路")
                manager_fund = manager_fund.drop("泰达宏利集利债券")

            if manager_name == "caolongjie":
                manager_fund = manager_fund.drop("建行中国人寿固收组合管理计划")

            manager_fund_info = fund_info[fund_info['Name'].map(lambda x: x in manager_fund.values)]

            local_path = os.path.join(self.data_path, today, "新股原始文件")
            dir_list = os.listdir(local_path)

            result = pd.DataFrame([])

            for i_file in range(len(dir_list)):

                file = dir_list[i_file]
                local_file = os.path.join(local_path, file)
                data = pd.read_excel(local_file, index_col=[0])

                if data.index.name == "新股发行网下申购审批表":

                    stock_code = CodeFormat().change_normal_to_ipo_apply_code(data.iloc[1, 3])[0:6]
                    stock_price = data.iloc[6, 1]

                    """ 网下问询时间和当日不一致的话 那么说明之前已经网下申购完成 当日应该是网上问询 """

                    ask_date = Date().change_to_str(data.iloc[3, 0])

                    if ask_date == today:

                        print("有网下新股", file)
                        fund = data.iloc[34:, 0:3]
                        fund.columns = ['Number', 'Blank', 'Vol']
                        fund = fund[['Number', 'Vol']]
                        fund = fund.dropna()

                        online_fund = pd.concat([fund, manager_fund_info], axis=1)
                        online_fund = online_fund.dropna()

                        online_fund['基金代码'] = online_fund['FundId']
                        online_fund["组合编号"] = online_fund['StockGroupId']
                        online_fund['交易市场内部编号'] = CodeFormat().get_stcok_market(stock_code)
                        online_fund['交易市场内部编号'] = online_fund['交易市场内部编号'].map(lambda x: 1 if x == 'SH' else 2)
                        online_fund['证券代码'] = stock_code
                        online_fund['申购价格1'] = stock_price
                        online_fund['申购数量1'] = online_fund['Number'] * 10000.0
                        online_fund['申购价格2'] = ""
                        online_fund['申购数量2'] = ""
                        online_fund['申购价格3'] = ""
                        online_fund['申购数量3'] = ""
                        online_fund['其他要求'] = ""
                        online_fund['基金名称'] = online_fund['Name']
                        online_fund['组合名称'] = ""

                        result = pd.concat([online_fund, result], axis=0)

                    else:
                        print("网下问询日期和当日不匹配，之前已经问询过", file)
                        continue
                else:
                    print("没有网下", file)
                    continue

            if len(result):
                local_path = os.path.join(self.data_path, today, "申购单")
                if not os.path.exists(local_path):
                    os.makedirs(local_path)

                file = '网下_%s.xls' % manager_name
                out_file = os.path.join(local_path, file)
                col = ['基金代码', '组合编号', '交易市场内部编号', '证券代码',
                       '申购价格1', '申购数量1', '申购价格2', '申购数量2', '申购价格3', '申购数量3',
                       "其他要求", '基金名称', '组合名称']
                result = result[col]
                print("今日有网下新股%s %s %s" % (manager_name, today, len(result)))
                result.to_excel(out_file, index=None)

                ftp = MyFtp()
                ftp.connect()
                ftp_file = os.path.join(self.ftp_path, today, file)
                ftp.upload_file(ftp_file, out_file)
                ftp.close()
            else:
                print("今日无网下新股%s %s %s" % (manager_name, today, len(result)))

if __name__ == '__main__':

    self = CalIPOBuy()
    today = datetime.today().strftime("%Y%m%d")
    self.load_param_file(today)
    self.ipo_buy_online(today)
    self.ipo_buy_outline(today)

    os.system("pause")
