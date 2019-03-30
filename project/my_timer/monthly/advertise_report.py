import os
import pandas as pd
from datetime import datetime

from quant.stock.date import Date
from quant.stock.index import Index
from quant.mfc.mfc_data import MfcData
from quant.utility.zip_file import ZipFile
from quant.utility.email_sender import EmailSender


from quant.project.multi_factor.alpha_model.exposure.alpha_factor_bp import AlphaBP
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_roe import AlphaROE
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_income_yoy import AlphaIncomeYoY
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_profit_yoy import AlphaProfitYoY

from quant.project.my_timer.monthly.fund_advertise_report.inside_active_report import InsideActiveReport
from quant.project.my_timer.monthly.fund_advertise_report.inside_passive_report import InsidePassiveReport
from quant.project.my_timer.monthly.fund_advertise_report.institution_active_report import InstitutionActiveReport
from quant.project.my_timer.monthly.fund_advertise_report.institution_passive_report import InstitutionPassiveReport


def update_data(date):

    """更新数据"""

    # 更新日期
    beg_date = Date().get_trade_date_offset(date, -60)
    end_date = date

    # 更新因子数据（原始和alpha）
    # Stock().load_h5_primary_factor()

    AlphaBP().cal_factor_exposure(beg_date, end_date)
    AlphaROE().cal_factor_exposure(beg_date, end_date)
    AlphaProfitYoY().cal_factor_exposure(beg_date, end_date)
    AlphaIncomeYoY().cal_factor_exposure(beg_date, end_date)

    # 更新基金净值 和 持仓数据 指数价格数据
    # Fund().load_fund_holding_all("19991231", datetime.today())
    MfcData().load_mfc_public_fund_nav()
    update_end_date = datetime.today().strftime("%Y%m%d")
    update_beg_date = Date().get_trade_date_offset(update_end_date, -20)

    Index().load_index_factor(index_code='H00985.CSI', beg_date=update_beg_date, end_date=update_end_date)
    Index().load_index_factor(index_code="885001.WI", beg_date=update_beg_date, end_date=update_end_date)
    Index().load_index_factor(index_code="000300.SH", beg_date=update_beg_date, end_date=update_end_date)
    Index().load_index_factor(index_code="000905.SH", beg_date=update_beg_date, end_date=update_end_date)


def generate_excel_institution(date):

    """ 生成 Excel 机构版 """

    # 参数表
    param_file = os.path.join(MfcData().data_path, r"fund_report\advertise_report\参数", '宣传单页参数表.xlsx')
    param = pd.read_excel(param_file, index_col=[0])
    param = param.T
    comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                             ["中证全指全收益", 'H00985.CSI']]

    # 机构-主动量化
    param_active = param[param['基金类型'] == '主动量化']
    for i in range(0, len(param_active)):

        fund_code = param_active.index[i]
        fund_name = param_active.loc[fund_code, "基金名称"]
        print(fund_name, "excel", '机构')
        fund_strategy = param_active.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
        fund_manager = param_active.loc[fund_code, "基金经理"]

        self = InstitutionActiveReport()
        self.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                            comparsion_bench_list, date, fund_manager)
        self.write_excel()
        del self

    # 机构-指数
    param_passive = param[param['基金类型'] == '指数']
    for i in range(0, len(param_passive)):
        fund_code = param_passive.index[i]
        fund_name = param_passive.loc[fund_code, "基金名称"]
        print(fund_name, "excel", '机构')
        bench_code = param_passive.loc[fund_code, "指数代码"]
        fund_strategy = param_passive.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
        fund_manager = param_passive.loc[fund_code, "基金经理"]

        self = InstitutionPassiveReport()
        self.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                            bench_code, date, fund_manager)
        self.write_excel()
        del self


def generate_excel_inside(date):

    """ 生成Excel 内部版 """

    param_file = os.path.join(MfcData().data_path, r"fund_report\advertise_report\参数", '宣传单页参数表.xlsx')
    param = pd.read_excel(param_file, index_col=[0])
    param = param.T
    comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                             ["中证全指全收益", 'H00985.CSI']]

    # 内部-主动量化
    param_active = param[param['基金类型'] == '主动量化']

    if date < "20190109":
        param_active = param_active.drop("162212.OF")

    for i in range(0, len(param_active)):

        fund_code = param_active.index[i]
        fund_name = param_active.loc[fund_code, "基金名称"]
        print(fund_name, "excel", 'inside')
        inside_fund_name = param_active.loc[fund_code, "内部名称"]
        fund_strategy = param_active.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
        fund_manager = param_active.loc[fund_code, "基金经理"]
        self = InsideActiveReport()
        self.get_input_data(fund_code, fund_name, inside_fund_name,
                            fund_strategy, asset_allocation_strategy,
                            comparsion_bench_list, date, fund_manager)
        self.write_excel()

    # 内部-指数
    param_passive = param[param['基金类型'] == '指数']
    for i in range(0, len(param_passive)):
        fund_code = param_passive.index[i]
        fund_name = param_passive.loc[fund_code, "基金名称"]
        print(fund_name, "excel", '内部版')
        inside_fund_name = param_passive.loc[fund_code, "内部名称"]
        bench_code = param_passive.loc[fund_code, "指数代码"]
        fund_strategy = param_passive.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
        fund_manager = param_passive.loc[fund_code, "基金经理"]
        self = InsidePassiveReport()
        self.get_input_data(fund_code, fund_name, inside_fund_name,
                            fund_strategy, asset_allocation_strategy,
                            bench_code, date, fund_manager)
        self.write_excel()


def generate_word_inside(date):

    """ 生成word 内部版 """

    param_file = os.path.join(MfcData().data_path, r"fund_report\advertise_report\参数", '宣传单页参数表.xlsx')
    param = pd.read_excel(param_file, index_col=[0])
    param = param.T
    comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                             ["中证全指全收益", 'H00985.CSI']]

    # 内部-主动量化
    param_active = param[param['基金类型'] == '主动量化']

    if date < "20190109":
        param_active = param_active.drop("162212.OF")

    for i in range(0, len(param_active)):
        fund_code = param_active.index[i]
        fund_name = param_active.loc[fund_code, "基金名称"]
        print(fund_name, "excel", 'inside')
        inside_fund_name = param_active.loc[fund_code, "内部名称"]
        fund_strategy = param_active.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
        fund_manager = param_active.loc[fund_code, "基金经理"]
        self = InsideActiveReport()
        self.get_input_data(fund_code, fund_name, inside_fund_name,
                            fund_strategy, asset_allocation_strategy,
                            comparsion_bench_list, date, fund_manager)
        self.write_word()

    # 内部-指数
    param_passive = param[param['基金类型'] == '指数']
    for i in range(0, len(param_passive)):
        fund_code = param_passive.index[i]
        fund_name = param_passive.loc[fund_code, "基金名称"]
        print(fund_name, "word", '内部版')
        inside_fund_name = param_passive.loc[fund_code, "内部名称"]
        bench_code = param_passive.loc[fund_code, "指数代码"]
        fund_strategy = param_passive.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
        fund_manager = param_passive.loc[fund_code, "基金经理"]
        self = InsidePassiveReport()
        self.get_input_data(fund_code, fund_name, inside_fund_name,
                            fund_strategy, asset_allocation_strategy,
                            bench_code, date, fund_manager)
        self.write_word()


def generate_word_institution(date):

    """ 生成Word 机构版"""

    # 参数表
    param_file = os.path.join(MfcData().data_path, r"fund_report\advertise_report\参数", '宣传单页参数表.xlsx')
    param = pd.read_excel(param_file, index_col=[0])
    param = param.T
    comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                             ["中证全指全收益", 'H00985.CSI']]

    # 机构-主动量化
    param_active = param[param['基金类型'] == '主动量化']
    for i in range(0, len(param_active)):

        fund_code = param_active.index[i]
        fund_name = param_active.loc[fund_code, "基金名称"]
        print(fund_name, "word", "机构版")
        fund_strategy = param_active.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
        fund_manager = param_active.loc[fund_code, "基金经理"]

        self = InstitutionActiveReport()
        self.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                            comparsion_bench_list, date, fund_manager)
        self.write_word()
        del self

    # 机构-指数
    param_passive = param[param['基金类型'] == '指数']
    for i in range(0, len(param_passive)):
        fund_code = param_passive.index[i]
        fund_name = param_passive.loc[fund_code, "基金名称"]
        print(fund_name, "word")
        bench_code = param_passive.loc[fund_code, "指数代码"]
        fund_strategy = param_passive.loc[fund_code, "投资策略"]
        asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
        fund_manager = param_passive.loc[fund_code, "基金经理"]

        self = InstitutionPassiveReport()
        self.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                            bench_code, date, fund_manager)
        self.write_word()
        del self


def copyfile(date):

    """ 机构版文件上传网盘 """

    import shutil
    last_trade_day = Date().get_trade_date_offset(date, 0)
    web_path = r'Z:\# 量化产品宣传单页月报'
    web_sub_path = os.path.join(web_path, last_trade_day)
    if not os.path.exists(web_sub_path):
        os.makedirs(web_sub_path)
    my_path = InsidePassiveReport().data_path
    my_sub_path = os.path.join(my_path, last_trade_day)

    param_file = os.path.join(MfcData().data_path, r"fund_report\advertise_report\参数", '宣传单页参数表.xlsx')
    param = pd.read_excel(param_file, index_col=[0])
    param = param.T

    for i in range(0, len(param)):

        fund_code = param.index[i]
        fund_name = param.loc[fund_code, "基金名称"]
        print(fund_name)
        file = "机构_%s.docx" % fund_name
        web_file = os.path.join(web_sub_path, file)
        my_file = os.path.join(my_sub_path, file)
        shutil.copyfile(my_file, web_file)
        file = "机构_%s.xlsx" % fund_name
        web_file = os.path.join(web_sub_path, file)
        my_file = os.path.join(my_sub_path, file)
        shutil.copyfile(my_file, web_file)


def mail(date):

    """发送邮件"""

    last_trade_day = Date().get_trade_date_offset(date, 0)
    web_path = r'E:\Data\mfcteda_data\advertise_report'
    web_sub_path = os.path.join(web_path, last_trade_day)

    print(" Mailing Report Fund Monthly")
    sender_mail_name = 'fucheng.dou@mfcteda.com'

    receivers_mail_name = ['yang.liu@mfcteda.com', 'fucheng.dou@mfcteda.com']
    # receivers_mail_name = ['fucheng.dou@mfcteda.com']

    zip_filename = "fund_report_" + last_trade_day + ".rar"
    ZipFile().zip_folder(web_sub_path, os.path.join(web_path, zip_filename))

    acc_mail_name = []
    subject_header = "基金宣传单页_月报_机构版%s" % last_trade_day
    email = EmailSender()
    email.attach_html_text("机构版文件位于网盘 rd:\# 量化产品宣传单页月报，内部版如有需要单独发送 ")
    email.attach_file(os.path.join(web_path, zip_filename))
    email.send_mail_mfcteda(sender_mail_name, receivers_mail_name,
                            acc_mail_name, subject_header)
    os.remove(os.path.join(web_path, zip_filename))


if __name__ == '__main__':

    date = "20190308"
    update_data(date)
    # generate_excel_institution(date)
    # generate_word_institution(date)
    # generate_excel_inside(date)
    generate_word_inside(date)
    # copyfile(date)
    # mail(date)
