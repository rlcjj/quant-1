import smtplib
import os
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header


class EmailSender(object):

    """
    发送邮件
    可以126邮箱 公司邮箱 或者 qq邮箱
    """

    def __init__(self):

        self.message = MIMEMultipart('related')
        self.message_alternative = MIMEMultipart('alternative')
        self.message.attach(self.message_alternative)
        self.imgHtml = ""

    def attach_text(self, body_text):

        """
        正文添加文本
        MIMEText(body_text, 'plain', 'utf-8') 和在正文中添加图片有冲突
        所以改成利用HTML的形式添加
        """
        thebody = MIMEText(body_text, 'plain', 'utf-8')
        self.message.attach(thebody)

    def attach_html_text(self, body_text):

        """
        正文添加文本
        MIMEText(body_text, 'plain', 'utf-8') 和在正文中添加图片有冲突
        所以改成利用HTML的形式添加
        """
        self.imgHtml += '<p style="font-size:15px;font-family:Comic Sans MS">%s</p><br>' % body_text

    def attach_html(self, body_text):

        """
        正文添加文本
        """

        body_text = '<p style="font-size:15px;font-family:Comic Sans MS">%s</p><br>' % body_text
        text_html = MIMEText(body_text, 'html', 'utf-8')
        self.message.attach(text_html)

    def check_contain_chinese(self, check_str):

        """ 检查字符串是否含有中文 """

        import re
        result = re.compile(u'[\u4e00-\u9fa5]+')
        if result.search(check_str):
            return True
        else:
            return False

    def attach_file(self, file_name):

        """ 添加附件，附件名称是英文名 中文名会出现AT000001的情况 """

        att = MIMEText(open(file_name, 'rb').read(), 'base64', 'utf-8')
        # att["Content-Type"] = 'application/octet-stream'
        path, file = os.path.split(file_name)
        print(" Attaching File ", path, file)

        if self.check_contain_chinese(file):
            att.add_header("Content-Disposition", "attachment", filename=("gbk", "", file))
        else:
            att['Content-Disposition'] = 'attachment; filename="%s"' % file
        self.message.attach(att)

    def attach_picture_inside_body(self, title,  pic_file):

        """ 正文添加图片（显示在正文 非附件） """
        self.imgHtml += '<p style="background-color:lightgrey;font-size:20px;font-weight:bold;' \
                   'font-family:Comic Sans MS">%s</p><br><img src="cid:%s"><br>' % (title, pic_file)
        fp = open(pic_file, 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<%s>' % (pic_file))
        self.message.attach(msgImage)

    def send_mail_mfcteda(self, sender_mail_name, receivers_mail_name,
                          acc_mail_name, subject_header):

        """ 泰达服务器 发送邮件 """

        """ 注意 抄送的邮箱不能太多 """
        mail_server_host = "10.1.0.163"  # 邮件服务器地址
        mail_server_user = "doufucheng"  # 服务器登录名
        mail_server_pass = "Mfcteda2019!!"  # 服务器登陆密码

        self.message['Subject'] = Header(subject_header, 'utf-8')  # 写好 邮件标题
        self.message['From'] = Header(sender_mail_name, 'utf-8')  # 写好 发送者
        self.message['To'] = Header(';'.join(receivers_mail_name), 'utf-8')  # 写好 接收者
        self.message['Cc'] = Header(';'.join(acc_mail_name), 'utf-8')  # 写好 接收者
        msgText = MIMEText(self.imgHtml, 'html')
        self.message_alternative.attach(msgText)

        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_server_host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(mail_server_user, mail_server_pass)

            smtpObj.sendmail(sender_mail_name, receivers_mail_name, self.message.as_string())
            print("邮件发送成功")
            smtpObj.quit()

        except Exception as e:
            print(e)
            print("Error: 无法发送邮件")

    def send_mail_qq(self, sender_mail_name, receivers_mail_name,
                     acc_mail_name, subject_header):

        """
        QQ服务器 发送邮件
        qq邮箱的密码是邮箱授权码 一个16位字符串 bxfiljzifsaggdea
        """

        smtpsever = 'smtp.qq.com'
        password = 'bxfiljzifsaggdea'

        self.message['Subject'] = Header(subject_header, 'utf-8')
        self.message['From'] = Header(sender_mail_name, 'utf-8')  # 写好 发送者
        self.message['To'] = Header(';'.join(receivers_mail_name), 'utf-8')  # 写好 接收者
        self.message['Cc'] = Header(';'.join(acc_mail_name), 'utf-8')  # 写好 接收者

        try:
            server = smtplib.SMTP_SSL(smtpsever)
            # server.connect() # ssl无需这条
            server.login(sender_mail_name, password)  # 登陆
            server.sendmail(sender_mail_name, receivers_mail_name, self.message.as_string())  # 发送
            print('邮件发送成功')
            server.quit()
        except Exception as e:
            print(e)
            print('邮件发送失败')


if __name__ == '__main__':

    """ 泰达测试邮件 """

    path = 'E:\\Data\\fund_data\\fund_index_exposure_weekly\\'
    last_date = '20181030'
    path = os.path.join(path, "output_exposure")
    xlsx_name = 'IndexFundExposure' + last_date + '.xlsx'
    exposure_file = os.path.join(path, xlsx_name)

    fig_name = 'last_trade_date.png'
    fig_file = os.path.join(path, fig_name)

    sender_mail_name = 'fucheng.dou@mfcteda.com'
    receivers_mail_name = ['fucheng.dou@mfcteda.com']
    acc_mail_name = []
    subject_header = "指数基金风格暴露周报_测试自动发送"

    email = EmailSender()
    email.attach_text('暴露如下')
    email.attach_file(exposure_file)
    email.attach_picture_inside_body("IndexFundExposure", fig_file)
    email.send_mail_mfcteda(sender_mail_name, receivers_mail_name,
                            acc_mail_name, subject_header)

    """ QQ测试邮件 """

    # sender_mail_name = '1119332482@qq.com'
    # receivers_mail_name = ['1119332482@qq.com']
    # acc_mail_name = ['fucheng.dou@mfcteda.com']
    # subject_header = "测试邮件标题"
    #
    # email = EmailSender()
    # email.attach_text("测试邮件正文")
    # email.attach_file(exposure_file)
    #
    # # 内嵌图片在QQ邮箱有些问题
    # # email.attach_picture_inside_body("IndexFundExposure", fig_file)
    # email.send_mail_qq(sender_mail_name, receivers_mail_name,
    #                    acc_mail_name, subject_header)

    """ 中文"""

    self = EmailSender()
    print(self.check_contain_chinese("好gg"))
    print(self.check_contain_chinese("djdjhfd.csv"))