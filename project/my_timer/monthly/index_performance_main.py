from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.macro import Macro
from quant.utility.email_sender import EmailSender
from quant.utility.win32com_excel import Win32ComExcel
from quant.project.my_timer.monthly.index_performance.index_report import load_index_close_daily, generate_summary

import os
from datetime import datetime


def index_performance_main(end_month_date, save_path):

    """ 各国指数涨幅 """

    pic_name = 'IndexPerformance'
    end_date = datetime.today().strftime("%Y%m%d")

    load_index_close_daily(Date().get_trade_date_offset(end_date, -30), end_date)
    Macro().load_all_macro_data_wind(Date().get_trade_date_offset(end_date, -90), end_date)

    generate_summary(end_month_date, save_path)

    file_name = os.path.join(save_path, "IndexPerformance" + "_" + end_month_date + '.xlsx')
    win32comexcel = Win32ComExcel()
    win32comexcel.read_workbook(file_name)
    win32comexcel.read_worksheet('主要指数表现')
    win32comexcel.catch_screen("B1:I35", save_path, pic_name)
    win32comexcel.close()

    sender_mail_name = 'fucheng.dou@mfcteda.com'
    receivers_mail_name = ['fucheng.dou@mfcteda.com']
    receivers_mail_name = ['fucheng.dou@mfcteda.com', 'jie.dai@mfcteda.com',
                           'xin.liu@mfcteda.com', 'chao.yang@mfcteda.com',
                           'longjie.cao@mfcteda.com', 'yang.liu@mfcteda.com', 'tingting.li@mfcteda.com']
    acc_mail_name = []
    subject_header = "各国指数涨跌幅月报%s_自动发送" % end_month_date

    email = EmailSender()
    email.attach_file(file_name)
    email.attach_picture_inside_body("各国指数涨跌幅", os.path.join(save_path, pic_name + '.png'))
    email.send_mail_mfcteda(sender_mail_name, receivers_mail_name, acc_mail_name, subject_header)

    os.system("pause")


if __name__ == '__main__':

    end_month_date = Date().get_normal_date_last_month_end_day(datetime.today())
    print(end_month_date)
    save_path = os.path.join(Data().primary_data_path, r'index_data\index_month_report')
    index_performance_main(end_month_date, save_path)
