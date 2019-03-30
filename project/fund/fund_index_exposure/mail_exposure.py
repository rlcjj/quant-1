from quant.utility.email_sender import EmailSender
from quant.utility.win32com_excel import Win32ComExcel
import os
from datetime import datetime
from quant.stock.date import Date


def mail_exposure(path, last_date, report_date_halfyear):

    # 最近交易日风格暴露
    ################################################################################
    path = os.path.join(path, "output_exposure")
    xlsx_name = 'IndexFundExposure' + last_date + '.xlsx'
    pic_name = 'last_trade_date'
    pic_name_halfyear = 'half_year_date'

    exposure_file = os.path.join(path, '最近交易日风格暴露' + last_date + '.xlsx')
    win32comexcel = Win32ComExcel()
    win32comexcel.read_workbook(exposure_file)
    win32comexcel.read_worksheet('最近交易日风格暴露')
    win32comexcel.catch_screen("B1:M22", path, pic_name)
    win32comexcel.close()

    exposure_file = os.path.join(path, '最近半年报风格暴露' + report_date_halfyear + '.xlsx')
    win32comexcel = Win32ComExcel()
    win32comexcel.read_workbook(exposure_file)
    win32comexcel.read_worksheet('最近半年报风格暴露')  # 最近半年报风格暴露
    win32comexcel.catch_screen("B1:N9", path, pic_name_halfyear) # N9
    win32comexcel.close()

    sender_mail_name = 'fucheng.dou@mfcteda.com'
    receivers_mail_name = ['fucheng.dou@mfcteda.com', 'longjie.cao@mfcteda.com']
    receivers_mail_name = ['fucheng.dou@mfcteda.com', 'jie.dai@mfcteda.com',
                           'xin.liu@mfcteda.com', 'chao.yang@mfcteda.com',
                           'longjie.cao@mfcteda.com', 'yang.liu@mfcteda.com', 'tingting.li@mfcteda.com']
    acc_mail_name = []
    subject_header = "指数基金风格暴露周报%s_自动发送" % last_date

    email = EmailSender()
    exposure_file = os.path.join(path, xlsx_name)
    email.attach_file(exposure_file)
    email.attach_picture_inside_body("最近交易日风格暴露" + last_date, os.path.join(path, pic_name + '.png'))
    email.attach_picture_inside_body("最近半年报风格暴露" + report_date_halfyear,
                                     os.path.join(path, pic_name_halfyear + '.png'))
    email.send_mail_mfcteda(sender_mail_name, receivers_mail_name,
                            acc_mail_name, subject_header)
    ################################################################################


if __name__ == '__main__':

    ################################################################################
    path = 'E:\\Data\\fund_data\\fund_index_exposure_weekly\\'
    # Date().load_trade_date_series_all()

    today = datetime.today().strftime("%Y%m%d")
    last_date = Date().get_trade_date_offset(today, -1)
    report_date_halfyear = Date().get_last_fund_halfyear_date(today)
    print(" 最近半年报是 %s 最近一个交易日为 %s " % (report_date_halfyear, last_date))

    mail_exposure(path, last_date, report_date_halfyear)