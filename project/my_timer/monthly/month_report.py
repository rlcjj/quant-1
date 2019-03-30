import os
import shutil
from datetime import datetime

import numpy as np
import pandas as pd
from WindPy import w
from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.email_sender import EmailSender
from quant.utility.write_word import WriteWord

w.start()


class FundMonthReport(Data):

    """ 生成基金营销月报 """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\fund_report\month_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.network_path = r'\\10.1.0.7\rd\※※金融工程部数据产品※※\# 基金季报月报\基金营销月报'

    def load_param_file(self):

        """ 从网盘下载参数文件 """

        src_file = os.path.join(self.network_path, '参数', '基金营销月报投资展望.xlsx')
        dst_file = os.path.join(self.data_path, "参数", '基金营销月报投资展望.xlsx')
        shutil.copyfile(src=src_file, dst=dst_file)

    def get_date(self):

        """ 上个月开始日期和结束日期（普通日，注意有时需要跨年） """

        today = datetime.today().strftime('%Y%m%d')
        end_date = Date().get_normal_date_last_month_end_day(today)
        beg_date = Date().get_normal_date_last_month_first_day(today)
        print(beg_date, end_date)

        return beg_date, end_date

    def load_index_pe(self, code, end_date):

        """ 得到指数的pe """

        data = w.wss(code, "pe_ttm", "tradeDate=" + end_date)
        return np.round(data.Data[0][0], 2)

    def format_number_to_pctstr(self, x):

        """ 变成百分比的字符串格式 """

        x_str = '%.2f%%' % (x * 100.0)
        return x_str

    def load_index_pct(self, code, begin_date, end_date):

        """ 一段时间内指数的涨跌幅和波动率 """

        pct_data = w.wsd(code, "pct_chg", begin_date, end_date, "")
        pct_data_pd = pd.DataFrame(pct_data.Data, index=pct_data.Fields, columns=pct_data.Times).T
        std = (pct_data_pd['PCT_CHG'] / 100).std() * np.sqrt(250)
        pct = ((pct_data_pd['PCT_CHG'] / 100.0 + 1.0).cumprod() - 1.0)[len(pct_data_pd) - 1]

        return pct, std

    def load_fund_pct(self, code, begin_date, end_date):

        """ 一段时间内基金的涨跌幅和波动率 """

        pct_data = w.wsd(code, "NAV_adj_return1", begin_date, end_date, "")
        pct_data_pd = pd.DataFrame(pct_data.Data, index=['PCT_CHG'], columns=pct_data.Times).T
        std = (pct_data_pd['PCT_CHG'] / 100).std() * np.sqrt(250)
        pct = ((pct_data_pd['PCT_CHG'] / 100.0 + 1.0).cumprod() - 1.0)[len(pct_data_pd) - 1]

        return pct, std

    def load_three_industry(self, begin_date, end_date):

        """ 上月涨幅最大的三个行业和跌幅最大的三个行业 """

        data = w.wsd("CI005001.WI,CI005002.WI,CI005003.WI,CI005004.WI,CI005005.WI,CI005006.WI,CI005007.WI,CI005008.WI,"
                     "CI005009.WI,CI005010.WI,CI005011.WI,CI005012.WI,CI005013.WI,CI005014.WI,CI005015.WI,CI005016.WI,"
                     "CI005017.WI,CI005018.WI,CI005019.WI,CI005020.WI,CI005021.WI,CI005022.WI,CI005023.WI,CI005024.WI,"
                     "CI005025.WI,CI005026.WI,CI005027.WI,CI005028.WI,CI005029.WI",
                     "pct_chg", begin_date, end_date, "")
        pct_data_pd = pd.DataFrame(data.Data, index=data.Codes, columns=data.Times).T
        pct_data_pd.index = pct_data_pd.index.map(lambda x: x.strftime('%Y-%m-%d'))
        pct_data_pd_cum = ((pct_data_pd / 100.0 + 1.0).cumprod() - 1.0).ix[len(pct_data_pd) - 1, :]
        pct_data_pd_cum.name = 'pct'
        code_str = ','.join(list(pct_data_pd_cum.index))
        code_name = w.wss(code_str, "sec_name")
        code_name_pd = pd.DataFrame(code_name.Data, index=['name'], columns=data.Codes).T
        concat_data = pd.concat([pct_data_pd_cum, code_name_pd], axis=1)
        concat_data['name'] = concat_data['name'].map(lambda x: x[0:list(x).index('(')])
        concat_data = concat_data.sort_values(by=['pct'], ascending=False)
        concat_data_before = concat_data.iloc[0:3, :]
        concat_data_before['pct_str'] = concat_data_before['pct'].map(lambda x: ("%.2f%%") % (x * 100))
        concat_data_before['out'] = concat_data_before['name'] + '行业(' + concat_data_before['pct_str'] + ')'
        concat_data = concat_data.sort_values(by=['pct'], ascending=True)
        concat_data_after = concat_data.iloc[0:3, :]
        concat_data_after['pct_str'] = concat_data_after['pct'].map(lambda x: ("%.2f%%") % (x * 100))
        concat_data_after['out'] = concat_data_after['name'] + '行业(' + concat_data_after['pct_str'] + ')'
        return concat_data_before, concat_data_after

    def load_fund_rank(self, fund_code, begin_date, end_date):

        """ 一段时间内基金排名 """

        data = w.wss(fund_code, "peer_fund_return_rank_per", "startDate=" + begin_date +
                     ";endDate=" + end_date + ";fundType=3")

        return data.Data[0][0]

    def load_fund_rank_inside(self, fund_code, beg_date, end_date, rank_pool, excess):

        """ 一段时间内基金排名（内部函数） """

        from fund.fund_rank import rank_fund
        val, pct = rank_fund(fund_code, rank_pool, beg_date, end_date, beg_date, excess=excess)
        return val

    def insert_para(self, doc, strContent, font="仿宋_GB2312", size=12, space=12, align=0):

        """ 插入自然段 """

        # 插入段
        p = doc.Paragraphs.Add()
        p.Range.Font.Name = font
        p.Range.Font.Size = size
        p.Range.ParagraphFormat.Alignment = align
        p.Range.ParagraphFormat.LineSpacing = space
        p.Range.InsertBefore(strContent)

        return True

    def generate_passive_fund_word(self, fund_name, fund_code, benchmark_code,
                                   mb_date, strategy):

        """ 被动基金的基金月报 """

        # get data
        begin_date, end_date = self.get_date()
        half_year = Date().get_normal_date_offset(end_date, -183)

        pct, std = self.load_index_pct("000985.CSI", begin_date, end_date)
        pct_half, std_half = self.load_index_pct("000985.CSI", half_year, end_date)
        pe_ttm = self.load_index_pe("000985.CSI", end_date)

        pct_300, std_300 = self.load_index_pct("000300.SH", begin_date, end_date)
        pct_500, std_500 = self.load_index_pct("000905.SH", begin_date, end_date)
        pct_1000, std_1000 = self.load_index_pct("000852.SH", begin_date, end_date)
        pct_cyb, std_cyb = self.load_index_pct("399006.SZ", begin_date, end_date)

        fund_pct, fund_std = self.load_fund_pct(fund_code, begin_date, end_date)
        fund_pct_half, fund_std_half = self.load_fund_pct(fund_code, half_year, end_date)
        bm_pct, bm_std = self.load_index_pct(benchmark_code, begin_date, end_date)
        ind_before, ind_after = self.load_three_industry(begin_date, end_date)

        if fund_code == "162213.OF":
            rank = self.load_fund_rank_inside(fund_code, begin_date, end_date, "沪深300基金", True)
        if fund_code == "162216.OF":
            rank = self.load_fund_rank_inside(fund_code, begin_date, end_date, "中证500基金", True)

        mg_fund_pct, mg_fund_std = self.load_fund_pct(fund_code, mb_date, end_date)

        if fund_code == "162213.OF":
            mg_rank = self.load_fund_rank_inside(fund_code, mb_date, end_date, "沪深300基金", True)
        if fund_code == "162216.OF":
            mg_rank = self.load_fund_rank_inside(fund_code, mb_date, end_date, "中证500基金", True)

        mg_bm_pct, mg_bm_std = self.load_index_pct(benchmark_code, mb_date, end_date)

        # context
        title = fund_name + '月报'
        para1 = '截至' + str(end_date) + '日，上月中证全指涨跌幅为' + \
                self.format_number_to_pctstr(pct) + "，近半年指数的年化波动率为" + \
                self.format_number_to_pctstr(std_half) + '，指数期末动态市盈率为' + str(pe_ttm) + \
                "。风格上，上月沪深300涨跌幅为" + self.format_number_to_pctstr(pct_300) + \
                "，中证500涨跌幅为" + self.format_number_to_pctstr(pct_500) + \
                "，中证1000涨跌幅为" + self.format_number_to_pctstr(pct_1000) + \
                "，创业板指涨跌幅为" + self.format_number_to_pctstr(pct_cyb) + \
                "。行业上，上月涨幅最大的三个行业为" + ind_before.ix[0, "out"] + '，' + ind_before.ix[1, "out"] + \
                '和' + ind_before.ix[2, "out"] + "；上月跌幅最大的三个行业为" + ind_after.ix[0, "out"] +\
                '，' + ind_after.ix[1, "out"] + '和' + ind_after.ix[2, "out"] + '。'

        para2 = '截至' + str(end_date) + '日，上月' + fund_name + '基金涨跌幅为' + \
                self.format_number_to_pctstr(fund_pct) + "，最近半年本基金的年化波动率为" + \
                self.format_number_to_pctstr(fund_std_half) + '。' + fund_name + '基准涨跌幅为' + \
                self.format_number_to_pctstr(bm_pct) + '，基金超额收益率为' + \
                self.format_number_to_pctstr(fund_pct - bm_pct) + '，同类排名为' + rank + \
                '。管理以来(' + mb_date + ")基金涨跌幅为" + \
                self.format_number_to_pctstr(mg_fund_pct) + "，基金基准涨跌幅为" + \
                self.format_number_to_pctstr(mg_bm_pct) + '，基金超额收益率为' + \
                self.format_number_to_pctstr(mg_fund_pct - mg_bm_pct) + '，同类排名为' + mg_rank + '。'

        # file
        sub_path = os.path.join(self.data_path, str(end_date))
        file = os.path.join(sub_path, fund_name + '月报.doc')

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
        if os.path.exists(file):
            os.remove(file)

        # write
        word = WriteWord()
        word.add_paragraph(text=title, size=14, line_spacing=True, align=True, bold=True)
        word.add_paragraph(text='（1）近期市场回顾', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=para1, size=10, line_spacing=True, align=False, bold=False, blank=True)
        word.add_paragraph(text='（2）基金业绩表现', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=para2, size=10, line_spacing=True, align=False, bold=False, blank=True)
        word.add_paragraph(text='（3）投资展望', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=strategy, size=10, line_spacing=True, align=False, bold=False, blank=True)

        word.save(file)

    def generate_active_fund_word(self, fund_name, fund_code, benchmark_code,
                                  mb_date, strategy):

        """ 主动基金的基金月报 """

        # get data
        begin_date, end_date = self.get_date()
        half_year = Date().get_normal_date_offset(end_date, -183)
        one_year = Date().get_normal_date_offset(end_date, -365)
        three_year = Date().get_normal_date_offset(end_date, -365*3)
        five_year = Date().get_normal_date_offset(end_date, -365*5)

        pct, std = self.load_index_pct("000985.CSI", begin_date, end_date)
        pct_half, std_half = self.load_index_pct("000985.CSI", half_year, end_date)
        pe_ttm = self.load_index_pe("000985.CSI", end_date)

        pct_300, std_300 = self.load_index_pct("000300.SH", begin_date, end_date)
        pct_500, std_500 = self.load_index_pct("000905.SH", begin_date, end_date)
        pct_1000, std_1000 = self.load_index_pct("000852.SH", begin_date, end_date)
        pct_cyb, std_cyb = self.load_index_pct("399006.SZ", begin_date, end_date)

        fund_pct, fund_std = self.load_fund_pct(fund_code, begin_date, end_date)
        fund_pct_half, fund_std_half = self.load_fund_pct(fund_code, half_year, end_date)
        ind_before, ind_after = self.load_three_industry(begin_date, end_date)
        one_rank = self.load_fund_rank(fund_code, one_year, end_date)
        three_rank = self.load_fund_rank(fund_code, three_year, end_date)
        five_rank = self.load_fund_rank(fund_code, five_year, end_date)

        mg_fund_pct, mg_fund_std = self.load_fund_pct(fund_code, mb_date, end_date)
        mg_rank = self.load_fund_rank(fund_code, mb_date, end_date)
        mg_bm_pct, mg_bm_std = self.load_index_pct(benchmark_code, mb_date, end_date)

        # context
        title = fund_name + '月报'
        para1 = '截至' + str(end_date) + '日，上月中证全指涨跌幅为' + \
                self.format_number_to_pctstr(pct) + "，近半年指数的年化波动率为" + \
                self.format_number_to_pctstr(std_half) + '，指数期末动态市盈率为' + str(pe_ttm) + \
                "。风格上，上月沪深300涨跌幅为" + self.format_number_to_pctstr(pct_300) + \
                "，中证500涨跌幅为" + self.format_number_to_pctstr(pct_500) + \
                "，中证1000涨跌幅为" + self.format_number_to_pctstr(pct_1000) + \
                "，创业板指涨跌幅为" + self.format_number_to_pctstr(pct_cyb) + \
                "。行业上，上月涨幅最大的三个行业为" + ind_before.ix[0, "out"] + '，' + ind_before.ix[1, "out"] + \
                '和' + ind_before.ix[2, "out"] + "；上月跌幅最大的三个行业为" + ind_after.ix[0, "out"] +\
                '，' + ind_after.ix[1, "out"] + '和' + ind_after.ix[2, "out"] + '。'

        para2 = '截至' + str(end_date) + '日，上月' + fund_name + '基金涨跌幅为' + \
                self.format_number_to_pctstr(fund_pct) + "，最近半年基金的年化波动率为" + \
                self.format_number_to_pctstr(fund_std_half) + '。' + \
                '基金最近一年同类排名为' + one_rank + '，最近三年同类排名为' + three_rank + \
                '，最近五年同类排名为' + five_rank + '。现任基金经理管理以来(' + mb_date + \
                ")基金涨跌幅为" + self.format_number_to_pctstr(mg_fund_pct) + "，基金基准涨跌幅为" + \
                self.format_number_to_pctstr(mg_bm_pct) + '，基金超额收益率为' + \
                self.format_number_to_pctstr(mg_fund_pct - mg_bm_pct) + '，同类排名为' + mg_rank + '。'

        # file
        sub_path = os.path.join(self.data_path, str(end_date))
        file = os.path.join(sub_path, fund_name + '月报.doc')

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        if os.path.exists(file):
            os.remove(file)

        # write
        word = WriteWord()
        word.add_paragraph(text=title, size=14, line_spacing=True, align=True, bold=True)
        word.add_paragraph(text='（1）近期市场回顾', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=para1, size=10, line_spacing=True, align=False, bold=False, blank=True)
        word.add_paragraph(text='（2）基金业绩表现', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=para2, size=10, line_spacing=True, align=False, bold=False, blank=True)
        word.add_paragraph(text='（3）投资展望', size=12, line_spacing=True, align=False, bold=True)
        word.add_paragraph(text=strategy, size=10, line_spacing=True, align=False, bold=False, blank=True)

        word.save(file)

    def generate_all_word(self):

        """ 生成所有基金月报 """

        dst_file = os.path.join(self.data_path, "参数", '基金营销月报参数.xlsx')
        data = pd.read_excel(dst_file, index_col=[0])
        data['管理开始'] = data['管理开始'].map(Date().change_to_str)

        dst_file = os.path.join(self.data_path, "参数", '基金营销月报投资展望.xlsx')
        strategy_data = pd.read_excel(dst_file, index_col=[0])
        strategy_data.index = strategy_data.index.map(Date().change_to_str)
        strategy_data = strategy_data.fillna("")
        beg_date, end_date = self.get_date()

        for i in range(len(data)):

            fund_code = data.index[i]
            fund_name = data.loc[fund_code, "基金名称"]
            benchmark_code = data.loc[fund_code, "基准代码"]
            mb_date = data.loc[fund_code, "管理开始"]
            mg_name = data.loc[fund_code, "基金经理"]
            strategy = strategy_data.loc[end_date, mg_name]
            fund_type = data.loc[fund_code, "基金类型"]

            print(fund_name)
            if fund_type == "指数":
                self.generate_passive_fund_word(fund_name, fund_code, benchmark_code, mb_date, strategy)
            else:
                self.generate_active_fund_word(fund_name, fund_code, benchmark_code, mb_date, strategy)

    def upload_file(self):

        """ 将生成的本地文件上传至网盘 """

        begin_date, end_date = self.get_date()
        net_sub_path = os.path.join(self.network_path, end_date)
        local_sub_path = os.path.join(self.data_path, end_date)

        if not os.path.exists(net_sub_path):
            os.makedirs(net_sub_path)

        file_list = os.listdir(local_sub_path)

        for file in file_list:

            local_file = os.path.join(local_sub_path, file)
            net_file = os.path.join(net_sub_path, file)
            print(local_file, net_file)
            shutil.copyfile(local_file, net_file)

    def mail(self):

        """ 发送邮件 """

        sender_mail_name = 'fucheng.dou@mfcteda.com'
        receivers_mail_name = ['xin.liu@mfcteda.com', 'yang.liu@mfcteda.com',
                               'fucheng.dou@mfcteda.com', 'koala.li@mfcteda.com']

        acc_mail_name = ["jie.dai@mfcteda.com"]

        email = EmailSender()
        begin_date, end_date = self.get_date()
        local_sub_path = os.path.join(self.data_path, end_date)
        file_list = os.listdir(local_sub_path)
        subject_header = "基金营销月报_自动发送_%s" % str(end_date)

        for file in file_list:
            file_name = os.path.join(local_sub_path, file)
            print(file_name)
            email.attach_file(file_name)
        email.send_mail_mfcteda(sender_mail_name, receivers_mail_name, acc_mail_name, subject_header)

if __name__ == '__main__':

    self = FundMonthReport()
    # self.load_param_file()
    # self.generate_all_word()
    # self.upload_file()
    self.mail()
    os.system("pause")



