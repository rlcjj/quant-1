import os
import shutil
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.index import Index
from quant.mfc.mfc_data import MfcData

from quant.utility.zip_file import ZipFile
from quant.utility.email_sender import EmailSender
from quant.utility.code_format import CodeFormat


class HoldingDaily(Data):

    """
    1、下载持仓文件
    2、拆分持仓、计算新股市值监控、计算5日反向
    3、下载指数权重
    4、发送权重及持仓文件
    """

    def __init__(self, today=datetime.today().strftime("%Y%m%d")):

        """ 初始化 """
        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\mail_holding'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.today = Date().change_to_str(today)
        self.index_code_list = ["000300.SH", "000905.SH", "000016.SH", "881001.WI", '399101.SZ', '399102.SZ']

    def load_holding_data(self):

        """ 从网盘下载持仓文件 并修改名字 """

        lmd = MfcData()
        lmd.load_network_holding_date(date=self.today)
        lmd.load_network_stock_pool_date(date=self.today)
        lmd.change_holding_date(date=self.today)

    def load_other_data(self):

        """
        下载昨日收盘的指数权重
        下载股票池
        下载今日的股票上市日期
        下载昨天股票自由流通市值 用以计算全A
        """

        # 交易日更新
        print("Load Other Data")
        Date().load_trade_date_series("D")
        before_trade_date = Date().get_trade_date_offset(self.today, -1)

        # 下载指数权重
        Index().load_weight_from_ftp_date("000300.SH", before_trade_date)
        Index().load_weight_from_ftp_date("000905.SH", before_trade_date)
        Index().load_weight_from_ftp_date("000940.SH", before_trade_date)
        Index().load_weight_from_wind_date("000016.SH", before_trade_date)
        Index().load_weight_from_wind_date("000852.SH", before_trade_date)
        Index().load_weight_from_wind_date("399101.SZ", before_trade_date)
        Index().load_weight_from_wind_date("399102.SZ", before_trade_date)
        Index().load_weight_windqa_date(before_trade_date)

        Stock().load_all_stock_code_now()  # 下载股票池
        Stock().load_ipo_date()  # 下载上市日期
        # Stock().load_trade_status_today()  # 下载停牌股票

    def cal_reverse_5days(self):

        """
        每天开盘前计算 前5个交易日 各个基金的股票成交情况
        不能自反向 ：若每只基金自身 前五天有卖出（买入）情况某只股票的情况 那么基金当天不能买入（卖出）
        """
        day_period = 5

        end_date = Date().get_trade_date_offset(self.today, -1)
        beg_date = Date().get_trade_date_offset(end_date, - (day_period - 1))
        trade_series = Date().get_trade_date_series(beg_date, end_date)

        manager_info = MfcData().get_mfc_manage_info()

        for i_col in range(len(manager_info.columns)):

            person_name = manager_info.columns[i_col]
            manager_fund = manager_info[person_name]
            manager_fund = manager_fund.dropna()
            fund_list = list(manager_fund.values)

            for i_fund in range(len(fund_list)):

                fund_name = fund_list[i_fund]
                print(" Cal Fund Reverse 5 days ", fund_name, person_name)
                result = pd.DataFrame([])

                for i_date in range(len(trade_series)):

                    cur_date = trade_series[i_date]
                    data = MfcData().get_trade_statement(cur_date)
                    data = data.dropna(subset=['基金名称'])
                    data = data[['基金名称', '证券代码', '委托方向', '成交数量', '资产类别']]
                    data.columns = ['FundName', 'StockCode', 'Direction', 'TradeNumber', 'Type']
                    data = data[data.FundName == fund_name]
                    data = data[data.Type == '股票资产']
                    data.StockCode = data.StockCode.map(CodeFormat().stock_code_add_postfix)
                    data.Direction = data.Direction.map(lambda x: 2 if x == '卖出' else 1)

                    result_date = pd.DataFrame(data.Direction.values, index=data.StockCode.values, columns=[cur_date])
                    try:
                        result = pd.concat([result, result_date], axis=1)
                    except Exception as e:
                        pass

                result = result.fillna(0)
                result.index.name = 'CODE'
                result = result.astype(np.int)

                my_result = []

                for i_row in range(len(result)):

                    vals_list = list(result.ix[i_row, trade_series])
                    vals_set = list(set(result.ix[i_row, trade_series]))

                    if 2 in vals_set:
                        append_row = [result.index[i_row], 2]
                        append_row.extend(vals_list)
                        my_result.append(append_row)

                    if 1 in vals_set:
                        append_row = [result.index[i_row], 1]
                        append_row.extend(vals_list)
                        my_result.append(append_row)

                col = ['CODE', 'FLAG']
                col.extend(trade_series)
                my_result = pd.DataFrame(my_result, columns=col)

                out_sub_path = os.path.join(self.data_path, person_name, self.today, 'reverse_5days')
                if not os.path.exists(out_sub_path):
                    os.makedirs(out_sub_path)
                out_file = os.path.join(out_sub_path, fund_name + '.csv')
                my_result.to_csv(out_file, index=None)
                print(fund_name, len(result), len(my_result))

    def cal_ipo_mkt_monitor(self):

        """
        每天开盘前计算 前20个交易日 公募基金 两市分别的股票市值
        现在打新的下限 是在某个市场上 股票市值20个交易日的平均值 大于6000万
        计算前20个交易日基金股票市值的平均值 利用20*6000万-前19个交易日的股票市值=昨天能够打新的市值下限
        这样计算出的结果和昨天真实持仓的差就是 今天应该增加多少股票市值
        所需要的文件是所有基金的证券持仓 和 当日的收盘价
        """
        thread_value = 60000000
        day_period = 20
        person_list = ['liuxin', 'liuyang']

        end_date = Date().get_trade_date_offset(self.today, -1)
        beg_date = Date().get_trade_date_offset(end_date, - (day_period - 1))
        trade_series = Date().get_trade_date_series(beg_date, end_date)

        # 基金经理管理的基金
        fund = MfcData().get_mfc_manage_info()

        # 所需要的持仓文件
        holding_data = pd.DataFrame([])

        for i_date in range(len(trade_series)):

            date = trade_series[i_date]
            data = MfcData().get_group_security(date)
            data = data.dropna(subset=['基金名称'])

            data = data[['基金名称', '证券代码', '持仓', '证券类别', '最新价']]
            data.columns = ['FundName', 'StockCode', 'Holding', 'Type', 'Price']
            data['Date'] = date
            data = data[data.Type == '股票']
            data.StockCode = data.StockCode.map(CodeFormat().stock_code_add_postfix)
            data["Market"] = data.StockCode.map(CodeFormat().get_stcok_market)
            data['Holding'] = data['Holding'].astype(np.float)
            data['Price'] = data['Price'].astype(np.float)
            data['StockMarketValue'] = data['Holding'] * data['Price']
            holding_data = pd.concat([holding_data, data], axis=0)

        holding_data = holding_data.reset_index(drop=True)

        # 开始计算每只基金的股票平均市值
        for i_col in range(len(person_list)):

            person_name = person_list[i_col]
            fund_val = fund.loc[:, person_name]
            fund_val = fund_val.dropna()
            fund_list = list(fund_val.values)

            columns = ['沪市平均', '沪市最新', '沪市目标', '深市平均', '深市最新', '深市目标']
            result = pd.DataFrame([], index=fund_list, columns=columns)

            for i_fund in range(len(fund_list)):
                fund_name = fund_list[i_fund]
                print(" Cal Fund IPO Stock MarketValue 20 days ", fund_name)

                holding_data_fund = holding_data[holding_data.FundName == fund_name]
                fund_gb = holding_data_fund.groupby(by=['Date', 'Market'])['StockMarketValue'].sum()
                fund_gb = fund_gb.unstack()

                result.loc[fund_name, "沪市平均"] = fund_gb.loc[:, "SH"].mean()
                result.loc[fund_name, "沪市最新"] = fund_gb.loc[fund_gb.index[-1], "SH"]
                result.loc[fund_name, "沪市目标"] = thread_value * day_period - fund_gb.ix[0:-1, "SH"].sum()
                result.loc[fund_name, "深市平均"] = fund_gb.loc[:, "SZ"].mean()
                result.loc[fund_name, "深市最新"] = fund_gb.loc[fund_gb.index[-1], "SZ"]
                result.loc[fund_name, "深市目标"] = thread_value * day_period - fund_gb.ix[0:-1, "SZ"].sum()

            result = result[(result["沪市平均"] < thread_value) | (result["深市平均"] < thread_value)]
            result /= 10000

            out_sub_path = os.path.join(self.data_path, person_name, self.today, 'ipo_mkt_monitor')
            if not os.path.exists(out_sub_path):
                os.makedirs(out_sub_path)
            out_file = os.path.join(out_sub_path, '新股市值监控.csv')
            result.to_csv(out_file)

    def holding_data_for_manager(self, person_name='liuyang'):

        """
        holding_data 中包含 基金资产、单个基金证券、股票池
        index_weight 为指数权重
        """

        # 输入参数
        print(" Prepare Data For ", person_name)
        before_trade_data = Date().get_trade_date_offset(self.today, -1)

        # 基金列表
        fund = MfcData().get_mfc_manage_info()
        fund_val = fund[person_name]
        fund_val = fund_val.dropna()
        fund_list = list(fund_val.values)

        # 基金资产
        fund_asset = MfcData().get_fund_asset(before_trade_data)
        fund_asset = fund_asset[['序号', '统计日期', '基金编号', '基金名称',
                                 '股票资产', '净值', '基金份额',
                                 '单位净值', '单位净值涨跌幅(%)', '累计单位净值',
                                 '昨日单位净值', '当日股票收益率(%)',
                                 '当日股票净买入金额', '股票资产/净值(%)',
                                 '当前现金余额', '累计应收金额', '累计应付金额',
                                 '期货保证金账户余额', '期货保证金', '可用期货保证金',
                                 '保证金', 'T+0交易可用', 'T+1交易可用',
                                 'T+0交易可用/净值(%)', 'T+1交易可用/净值(%)']]

        fund_asset_fund = fund_asset[fund_asset['基金名称'].map(lambda x: x in fund_list)]
        out_sub_path = os.path.join(self.data_path, person_name, self.today, "holding_data")
        if not os.path.exists(out_sub_path):
            os.makedirs(out_sub_path)
        out_file = os.path.join(out_sub_path, '基金资产.xlsx')
        fund_asset_fund.to_excel(out_file, index=None)

        # 基金持仓证券
        fund_asset = MfcData().get_fund_security(before_trade_data)
        fund_asset = fund_asset[['持仓日期', '序号', '基金名称', '证券代码', '证券名称', '证券类别',
                                 '市值', '市值比净值(%)', '持仓', '净买量', '净买金额', '费用合计',
                                 '当日涨跌幅(%)', '持仓多空标志', '估值价格', '最新价']]

        for i_fund in range(len(fund_list)):

            fund_name = fund_list[i_fund]
            fund_asset_fund = fund_asset[fund_asset['基金名称'] == fund_name]
            out_file = os.path.join(out_sub_path, fund_name + '持仓.xlsx')
            fund_asset_fund.to_excel(out_file, index=None)

        # 股票库
        pool_path = MfcData().data_path
        pool_path = os.path.join(pool_path, r"mfc_holding_raw\201806_now")

        if person_name == 'liuyang':

            pool_list = ["改革动力股票库.xls", "改革动力禁止库.xls", "改革动力限制库.xls",
                         "公司超五库.xls", "公司股票库.xls", "公司关联库.xls", "公司禁止库.xls", "公司限制库.xls",
                         "逆向股票库.xls", "逆向禁止库.xls", "逆向限制库.xls", "同顺禁止库.xls",
                         "量化限制库.xls", '沪深300关联禁止库.xls', '沪深300投资库.xls', '沪深300限制库.xls',
                         '中证500关联禁止库.xls', '中证500投资库.xls', '中证500限制库.xls']

        elif person_name == 'liuxin':

            pool_list = ["改革动力股票库.xls", "改革动力禁止库.xls", "改革动力限制库.xls",
                         "公司超五库.xls", "公司股票库.xls", "公司关联库.xls", "公司禁止库.xls", "公司限制库.xls",
                         "逆向股票库.xls", "逆向禁止库.xls", "逆向限制库.xls", "同顺禁止库.xls",
                         "量化限制库.xls", '红利禁止库.xls']
        elif person_name == 'caolongjie':

            pool_list = ["公司超五库.xls", "公司股票库.xls", "公司关联库.xls", "公司禁止库.xls", "公司限制库.xls",
                         "专户禁止库.xls", "量化11号禁止库.xls", "人寿固收限制库.xls", "人寿固收禁止库(委托人发送).xls",
                         "量化限制库.xls"]

        for i_file in range(len(pool_list)):

            file = pool_list[i_file]
            src_file = os.path.join(pool_path, 'raw_file', self.today, file)
            out_file = os.path.join(out_sub_path, file)
            try:
                shutil.copyfile(src_file, out_file)
            except Exception as e:
                print(e)
                print(src_file)
                print(out_file)
                pd.DataFrame([]).to_excel(out_file)

        # 指数权重 Axioma
        out_sub_path = os.path.join(self.data_path, person_name, self.today, "index_weight")
        if not os.path.exists(out_sub_path):
            os.makedirs(out_sub_path)

        for index_code in self.index_code_list:
            data = Index().get_weight_date(index_code, before_trade_data)
            out_file = os.path.join(out_sub_path, index_code + '.csv')
            data.index = data.index.map(lambda x: x[0:6] + '-CN')
            data = data.sort_values(by=['WEIGHT'], ascending=False)
            data.to_csv(out_file, header=None)

    def mail_for_manager(self, person_name='liuyang', person_name_ch="刘洋",
                         mail_add='yang.liu@mfcteda.com', test=True):

        """ 发送邮件（测试发送只发送自己） """

        print(" Mailing For ", person_name)
        sender_mail_name = 'fucheng.dou@mfcteda.com'

        receivers_mail_name = [mail_add, 'fucheng.dou@mfcteda.com']
        if test:
            receivers_mail_name = ['fucheng.dou@mfcteda.com']
        out_sub_path = os.path.join(self.data_path, person_name, self.today)
        zip_filename = "holding_data_" + self.today + ".rar"
        ZipFile().zip_folder(out_sub_path, os.path.join(out_sub_path, zip_filename))

        acc_mail_name = []
        subject_header = "持仓相关文件_部门内部自动发送_%s" % person_name_ch
        email = EmailSender()
        email.attach_file(os.path.join(out_sub_path, zip_filename))
        email.send_mail_mfcteda(sender_mail_name, receivers_mail_name,
                                acc_mail_name, subject_header)
        os.remove(os.path.join(out_sub_path, zip_filename))


if __name__ == "__main__":

    self = HoldingDaily()
    today = datetime.today().strftime("%Y%m%d")

    self.load_holding_data()
    self.load_other_data()
    self.cal_reverse_5days()
    self.cal_ipo_mkt_monitor()

    self.holding_data_for_manager("liuyang")
    self.holding_data_for_manager("liuxin")
    self.holding_data_for_manager("caolongjie")

    self.mail_for_manager("liuyang", "刘洋", "yang.liu@mfcteda.com", False)
    self.mail_for_manager("liuxin", "刘欣", "xin.liu@mfcteda.com", False)
    self.mail_for_manager("caolongjie", "曹龙洁", "longjie.cao@mfcteda.com", False)

    os.system("pause")
