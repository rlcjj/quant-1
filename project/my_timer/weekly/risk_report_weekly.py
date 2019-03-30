from quant.utility.email_sender import EmailSender


def risk_report_weekly():

    """ 风险周报的发送 """

    sender_mail_name = 'fucheng.dou@mfcteda.com'  # 发送邮箱

    receivers_mail_name = ['yaoxin.liu@mfcteda.com', 'fucheng.dou@mfcteda.com']  # 接收邮箱 list
    acc_mail_name = ['jie.dai@mfcteda.com', 'jing.yuan@mfcteda.com', 'ping.zhong@mfcteda.com']  # 抄送邮箱 list

    subject_header = "金融工程风险周报(2019年3月18日-3月22日)"  # 邮件标题
    body_text = '瑶歆：<br>你好! 上周金融工程无风险， 供知晓， 谢谢!<br>' \
                '祝好<br><br>窦福成<br>泰达宏利基金管理有限公司<br>金融工程部'

    email = EmailSender()
    email.attach_html_text(body_text)
    email.send_mail_mfcteda(sender_mail_name, receivers_mail_name, acc_mail_name, subject_header)


if __name__ == '__main__':

    risk_report_weekly()

