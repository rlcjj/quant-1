import os
from datetime import datetime
from quant.stock.date import Date
from quant.utility.zip_file import ZipFile
from quant.utility.email_sender import EmailSender
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor
from quant.project.multi_factor.risk_model.exposure.risk_factor_fund_etf_holder import RiskFactorFundETFHolder

class RiskFactorMail(object):

    def __init__(self):
        pass

    def cal_and_mail(self):

        """ 计算、压缩、发送邮件 """

        factor_name = "risk_raw_fund_etf_holder"
        today = datetime.today().strftime("%Y%m%d")
        beg_date = Date().get_trade_date_offset(today, -12)
        RiskFactorFundETFHolder().update_data(beg_date, today)
        RiskFactorFundETFHolder().cal_factor_exposure(beg_date, today)
        RiskFactor().generate_patch_file(factor_name, beg_date, today)

        path = RiskFactor().exposure_txt_path
        sub_path = os.path.join(path, factor_name)
        zip_file = os.path.join(path, "Risk_Factor.rar")
        ZipFile().zip_folder(sub_path, zip_file)

        email = EmailSender()
        email.attach_file(zip_file)
        sender_mail_name = "fucheng.dou@mfcteda.com"
        receivers_mail_name = ["fucheng.dou@mfcteda.com", "xin.liu@mfcteda.com"]
        email.send_mail_mfcteda(sender_mail_name, receivers_mail_name, [], "Risk_Factor")
        os.remove(zip_file)


if __name__ == '__main__':

    self = RiskFactorMail()
    self.cal_and_mail()

