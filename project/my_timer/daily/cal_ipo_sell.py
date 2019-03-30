import os
import warnings
import pandas as pd
from datetime import datetime
from datetime import timedelta

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.source.my_ftp import MyFtp
from quant.mfc.mfc_data import MfcData
from quant.utility.code_format import CodeFormat

from WindPy import w
w.start()


class CalIPOSell(Data):

    """
    卖出新股
    1、每天上午10点计算
    2、部门所有基金持有新股当天有没有开板，若开板，则卖出，生成恒生交易单，上传至FTP内网转外网文件夹下
    3、交易量>0 并且 收益率<9% 则视为开板
    4、所有基金都没有新股卖出，则为空文件夹

    之前是每个基金一个文件 现在是每个基金经理一个文件
    """

    def __init__(self):

        """ 初始化数据存储位置和参数 """

        Data.__init__(self)
        self.sub_data_path = 'mfcteda_data\cal_ipo_sell'
        self.ftp_path = "\\ipo_stock_sell\\"
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.new_days = 60  # 60自然日

    def ipo_sell(self,
                 today=datetime.today().strftime("%Y%m%d")):

        """ 计算所有基金新股是否打开 """

        before_trade_data = Date().get_trade_date_offset(today, -1)

        # get holding data
        data = MfcData().get_group_security(before_trade_data)
        data = data.dropna(subset=['基金名称'])
        data = data[['基金名称', '基金编号', '组合名称', '组合编号', '证券代码', '持仓', '证券类别']]
        data.columns = [['基金名称', '基金编号（序号）', '组合名称', '组合编号', '证券代码', '指令数量', '证券类别']]

        data = data[data['证券类别'] == '股票']
        data['证券代码'] = data['证券代码'].map(CodeFormat().stock_code_add_postfix)
        data["交易市场内部编号"] = data['证券代码'].map(CodeFormat().get_stcok_market)

        fund_info = MfcData().get_mfc_fund_info()
        fund_info = fund_info.dropna(subset=['FundId'])
        fund_info['FundId'] = fund_info['FundId'].map(CodeFormat.stock_code_add_postfix)
        fund_info['FundId'] = fund_info['FundId'].map(lambda x: x[0:6])

        # get ipo data
        Stock().load_all_stock_code_now()
        Stock().load_ipo_date()
        stock = Stock().get_ipo_date()
        stock.columns = ['IpoDate', 'DelistDate']
        stock['证券代码'] = stock.index
        stock['IpoDate'] = stock['IpoDate'].map(lambda x: str(int(x)))

        # get New Stock
        new_stock_date = datetime.today() - timedelta(days=self.new_days)
        new_stock_date = new_stock_date.strftime("%Y%m%d")
        all_data = pd.merge(data, stock, on=['证券代码'], how="left")
        all_data = all_data[all_data.IpoDate > new_stock_date]

        # get Vol and Pct of New Stock
        code_list = list(set(all_data['证券代码'].values))
        code_str = ','.join(code_list)
        pct = w.wsq(code_str, "rt_pct_chg,rt_vol")
        pct = pd.DataFrame(pct.Data, columns=pct.Codes, index=['Pct', 'Vol']).T
        pct['证券代码'] = pct.index

        # filter multi_factor
        new_data = pd.merge(all_data, pct, on=['证券代码'], how="left")
        new_data = new_data[new_data['Vol'] > 0]
        new_data = new_data[new_data['Pct'] < 0.09]

        # New Local Folder
        out_sub_path = os.path.join(self.data_path, today)
        if not os.path.exists(out_sub_path):
            os.mkdir(out_sub_path)

        # New FTP Folder
        ftp = MyFtp()
        ftp.connect()
        ftp_folder = os.path.join(self.ftp_path, today)
        ftp.upload_folder(ftp_folder)
        ftp.close()

        # manager data
        manager_data = MfcData().get_manager_fund()

        for i_manager in range(len(manager_data.columns)):

            manager_name = manager_data.columns[i_manager]
            manager_fund = manager_data[manager_name]
            manager_fund = manager_fund.dropna()

            fund_data = new_data[new_data['基金名称'].map(lambda x: x in manager_fund.values)]

            if len(fund_data) > 0:

                warnings.filterwarnings("ignore")

                fund_data_out = fund_data[['证券代码', '指令数量', '交易市场内部编号',
                                           '基金编号（序号）', '基金名称', '组合编号']]
                fund_data_out['委托方向'] = 2
                fund_data_out['指令价格'] = 0
                fund_data_out['交易市场内部编号'] = fund_data_out['交易市场内部编号'].map(lambda x: 1 if x == 'SH' else 2)
                fund_data_out['价格模式'] = ""
                fund_data_out['当前指令市值/净值（%）'] = ""
                fund_data_out['目标市值/净值（%）'] = ""
                fund_data_out['基金名称'] = ""
                fund_data_out['证券代码'] = fund_data_out['证券代码'].map(lambda x: x[0:6])
                fund_data_out = fund_data_out[['证券代码', '委托方向', '指令数量', '指令价格',
                                               '价格模式', '交易市场内部编号', '当前指令市值/净值（%）', '目标市值/净值（%）',
                                               '基金编号（序号）', '基金名称', '组合编号']]

                file = manager_name + '.xls'
                out_file = os.path.join(out_sub_path, file)
                print(out_file)
                fund_data_out.to_excel(out_file, index=None)

                ftp = MyFtp()
                ftp.connect()
                ftp_file = os.path.join(self.ftp_path, today, file)
                ftp.upload_file(ftp_file, out_file)
                ftp.close()


if __name__ == '__main__':

    self = CalIPOSell()
    today = datetime.today().strftime("%Y%m%d")
    self.ipo_sell(today)
