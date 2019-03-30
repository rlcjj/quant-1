from quant.utility.email_sender import EmailSender
import pandas as pd
import numpy as np
from WindPy import w
w.start()


def mail_index_pct():

    """
    发送今日指数临近收盘价数据，用来基金定投
    """

    data = w.wsq("000300.SH,000905.SH,CI005165.WI,CI005166.WI", "rt_pct_chg,rt_date,rt_pe_ttm,rt_pb_lf")
    data = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
    data['NAME'] = ["沪深300", "中证500", "中信证券二级行业指数", "中信保险二级行业指数"]

    string_total = ""

    for i in range(len(data)):

        string = str(data.ix[i, "RT_DATE"].astype(int)) + "日, " + data.ix[i, "NAME"]
        string += "现在涨幅为" + str(np.round(data.ix[i, "RT_PCT_CHG"] * 100, 2)) + '%, '
        string += "PB_LF为" + str(data.ix[i, "RT_PB_LF"].round(2)) + ', '
        string += "PE_TTM为" + str(data.ix[i, "RT_PE_TTM"].round(1)) + '.' + '<br>'
        print(string)
        string_total += string

    sender_mail_name = '1119332482@qq.com'
    receivers_mail_name = ['1119332482@qq.com', '547358759@qq.com']
    acc_mail_name = []
    subject_header = "今日指数涨跌幅"

    email = EmailSender()
    email.attach_html(string_total)
    email.send_mail_qq(sender_mail_name, receivers_mail_name,
                       acc_mail_name, subject_header)

if __name__ == "__main__":

    mail_index_pct()
