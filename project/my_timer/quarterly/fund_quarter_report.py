from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.mfc.mfc_data import MfcData

from quant.utility.zip_file import ZipFile
from quant.utility.write_word import WriteWord
from quant.utility.code_format import CodeFormat
from quant.utility.email_sender import EmailSender

import pandas as pd
import shutil
import os

from WindPy import w
w.start()


class FundQuarterReport(Data):

    """ 生成基金季报(还有年报、半年报) """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\fund_report\quarter_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.network_path = r'\\10.1.0.7\rd\※※金融工程部数据产品※※\# 基金季报月报\基金季报'

    def load_param_file(self):

        """ 从网盘下载参数文件 """

        src_file = os.path.join(self.network_path, '参数', '季报参数_回顾展望.xlsx')
        dst_file = os.path.join(self.data_path, "参数", '季报参数_回顾展望.xlsx')
        shutil.copyfile(src=src_file, dst=dst_file)

        src_file = os.path.join(self.network_path, '参数', '季报参数_投资策略.xlsx')
        dst_file = os.path.join(self.data_path, "参数", '季报参数_投资策略.xlsx')
        shutil.copyfile(src=src_file, dst=dst_file)

    def get_report_industry_change(self, fund_name, report_date, last_report_date):

        """ 报告期之间的权重变动 """

        # report_date = "20181231"
        # last_report_date = "20180930"
        # fund_name = "泰达逆向策略"

        report_date = Date().get_trade_date_offset(report_date, 0)
        last_report_date = Date().get_trade_date_offset(last_report_date, 0)
        print(fund_name, report_date, last_report_date)

        data_report = MfcData().get_fund_stock_weight(fund_name=fund_name, date=report_date)
        data_report.columns = ['NowHolder']
        data_report = data_report[~data_report.index.duplicated()]

        data_report_last = MfcData().get_fund_stock_weight(fund_name=fund_name, date=last_report_date)
        data_report_last.columns = ['LastHolder']
        data_report_last = data_report_last[~data_report_last.index.duplicated()]

        industry = Stock().read_factor_h5("industry_citic1")
        industry_date = pd.DataFrame(industry[report_date])
        industry_date.columns = ['Industry']

        data_report_last_industry = pd.concat([data_report_last, industry_date], axis=1)
        data_report_last_industry = data_report_last_industry.dropna()
        data_last_gb = pd.DataFrame(data_report_last_industry.groupby(by=['Industry']).sum()['LastHolder'])

        data_report_industry = pd.concat([data_report, industry_date], axis=1)
        data_report_industry = data_report_industry.dropna()
        data_gb = pd.DataFrame(data_report_industry.groupby(by=['Industry']).sum()['NowHolder'])

        data = pd.concat([data_last_gb, data_gb], axis=1)
        data.index = data.index.map(lambda x: Stock().get_industry_citic1_name_ch(x))
        data['Diff'] = data['NowHolder'] - data['LastHolder']
        data = data.sort_values(by=['Diff'], ascending=False)

        data_bigger = data.iloc[0:3, :]
        str1 = "本报告期内，本基金增加了" + "、".join(data_bigger.index) + "的配置"

        data = data.sort_values(by=['Diff'], ascending=True)
        data_smaller = data.iloc[0:3, :]

        str2 = "，减少了" + "、".join(data_smaller.index) + '的配置。'

        return str1 + str2

    def generate_report(self, fund_name, fund_operation, fund_strategy,
                        market_quotation, market_outlook, report_date,
                        report_name, report_type, last_report_date, fund_manager):

        """ 生成基金季报（年报或者半年报） """

        # file
        sub_path = os.path.join(self.data_path, report_name, fund_manager)
        file = os.path.join(sub_path, fund_name + '基金' + report_name + '投资策略.doc')

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
        if os.path.exists(file):
            os.remove(file)

        # write
        title = fund_name + u'基金投资策略'
        para1 = u'截止报告期末' + report_date + u'，报告期内的行业回顾及市场展望：'
        industry_analysis = self.get_report_industry_change(fund_name, report_date, last_report_date)

        word = WriteWord()
        word.add_paragraph(text=title, size=14, line_spacing=True, align=True, bold=True)
        word.add_paragraph(text=para1, size=12, line_spacing=True, bold=False, blank=True)

        word.add_paragraph(text='（1）行情回顾及运作分析', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=market_quotation, size=12, line_spacing=True, align=False, bold=False, blank=True)
        word.add_paragraph(text=fund_operation+industry_analysis, size=12, line_spacing=True, align=False, bold=False, blank=True)

        word.add_paragraph(text='（2）市场展望和投资策略', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=market_outlook, size=12, line_spacing=True, align=False, bold=False, blank=True)
        word.add_paragraph(text=fund_strategy, size=12, line_spacing=True, align=False, bold=False, blank=True)

        word.save(file)

    def generate_all_report(self):

        """ 生成所有基金季报 """

        dst_file = os.path.join(self.data_path, "参数", '季报参数_回顾展望.xlsx')
        strategy_info = pd.read_excel(dst_file, index_col=[0])

        dst_file = os.path.join(self.data_path, "参数", '季报参数_投资策略.xlsx')
        fund_info = pd.read_excel(dst_file, index_col=[0])

        for i in range(len(fund_info)):

            fund_name = fund_info.index[i]
            fund_operation = fund_info.loc[fund_name, "基金运作分析"]
            fund_strategy = fund_info.loc[fund_name, "基金投资策略"]
            fund_manager = fund_info.loc[fund_name, "基金经理"]
            print(fund_name)
            report_name = strategy_info.loc["报告名", fund_manager]
            report_type = strategy_info.loc["报告类型", fund_manager]
            report_date = Date().change_to_str(strategy_info.loc["报告期末", fund_manager])
            last_report_date = Date().change_to_str(strategy_info.loc["上个报告期末", fund_manager])
            market_quotation = strategy_info.loc["行情回顾及运作分析", fund_manager]
            market_outlook = strategy_info.loc["市场展望和投资策略", fund_manager]

            self.generate_report(fund_name, fund_operation, fund_strategy,
                                 market_quotation, market_outlook, report_date,
                                 report_name, report_type, last_report_date, fund_manager)

    def upload_file(self):

        """ 将生成的本地文件上传至网盘 """

        dst_file = os.path.join(self.data_path, "参数", '季报参数_回顾展望.xlsx')
        strategy_info = pd.read_excel(dst_file, index_col=[0])

        for manager_name in strategy_info.columns:

            report_name = strategy_info.loc["报告名", manager_name]
            net_sub_path = os.path.join(self.network_path, report_name, manager_name)
            local_sub_path = os.path.join(self.data_path, report_name, manager_name)

            if not os.path.exists(net_sub_path):
                os.makedirs(net_sub_path)

            file_list = os.listdir(local_sub_path)

            for file in file_list:
                local_file = os.path.join(local_sub_path, file)
                net_file = os.path.join(net_sub_path, file)
                print(local_file, net_file)
                shutil.copyfile(local_file, net_file)

    def mail_liuxin(self):

        """ 发送邮件 """

        sender_mail_name = 'fucheng.dou@mfcteda.com'
        receivers_mail_name = ['xin.liu@mfcteda.com', 'fucheng.dou@mfcteda.com']
        # receivers_mail_name = ['fucheng.dou@mfcteda.com']
        manager_name = "刘欣"

        acc_mail_name = []
        dst_file = os.path.join(self.data_path, "参数", '季报参数_回顾展望.xlsx')
        strategy_info = pd.read_excel(dst_file, index_col=[0])
        report_name = strategy_info.loc["报告名", manager_name]

        subject_header = "基金季报_自动发送_%s_%s" % (report_name, manager_name)

        email = EmailSender()
        zip_filename = report_name + ".rar"

        web_sub_path = os.path.join(self.network_path, report_name, manager_name)
        ZipFile().zip_folder(web_sub_path, os.path.join(self.network_path, zip_filename))
        email.attach_file(os.path.join(self.network_path, zip_filename))
        email.send_mail_mfcteda(sender_mail_name, receivers_mail_name, acc_mail_name, subject_header)
        os.remove(os.path.join(self.network_path, zip_filename))

    def mail_liuyang(self):

        """ 发送邮件 """

        sender_mail_name = 'fucheng.dou@mfcteda.com'
        receivers_mail_name = ['yang.liu@mfcteda.com', 'fucheng.dou@mfcteda.com']
        # receivers_mail_name = ['fucheng.dou@mfcteda.com']
        manager_name = "刘洋"

        acc_mail_name = []
        dst_file = os.path.join(self.data_path, "参数", '季报参数_回顾展望.xlsx')
        strategy_info = pd.read_excel(dst_file, index_col=[0])
        report_name = strategy_info.loc["报告名", manager_name]

        subject_header = "基金季报_自动发送_%s_%s" % (report_name, manager_name)

        email = EmailSender()
        zip_filename = report_name + ".rar"

        web_sub_path = os.path.join(self.network_path, report_name, manager_name)
        ZipFile().zip_folder(web_sub_path, os.path.join(self.network_path, zip_filename))
        email.attach_file(os.path.join(self.network_path, zip_filename))
        email.send_mail_mfcteda(sender_mail_name, receivers_mail_name, acc_mail_name, subject_header)
        os.remove(os.path.join(self.network_path, zip_filename))

if __name__ == '__main__':

    self = FundQuarterReport()
    # self.load_param_file()
    # self.generate_all_report()
    # self.upload_file()
    # self.mail_liuxin()
    self.mail_liuyang()

