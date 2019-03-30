from quant.project.fund.fund_index_exposure.index_halfyear_exposure import Cal_AllIndex_HalfYear_Holding_Exposure
from quant.project.fund.fund_index_exposure.index_lastdate_exposure import Cal_AllIndex_LastDate_Holding_Exposure
from quant.project.fund.fund_index_exposure.mfcfund_lastdate_exposure import Cal_MfcFund_LastDate_Holding_Exposure
from quant.project.fund.fund_index_exposure.fund_halfyear_exposure import Cal_AllFund_HalfYear_Holding_Exposure
from quant.project.fund.fund_index_exposure.concat_save_file import concat_file
from quant.project.fund.fund_index_exposure.mail_exposure import mail_exposure

import os
from datetime import datetime
from quant.stock.barra import Barra
from quant.stock.date import Date


if __name__ == "__main__":

    # 参数
    path = 'E:\\Data\\fund_data\\fund_index_exposure_weekly\\'
    # Date().load_trade_date_series_all()

    today = datetime.today().strftime("%Y%m%d")
    last_date = Date().get_trade_date_offset(today, -1)
    report_date_halfyear = Date().get_last_fund_halfyear_date(today)
    print(report_date_halfyear)

    # 下载需要的Barra数据
    Barra().load_barra_data()

    # 以Barra最后更新的数据为主
    barra_path = r'\\10.3.12.202\fe\risk_model\BarraExposure'
    file_list = os.listdir(barra_path)
    date_list = list(map(lambda x: x[0:8], file_list))
    date_list.sort()
    last_date = date_list[-1]
    print(" 最近半年报是 %s 最近一个交易日为 %s " % (report_date_halfyear, last_date))

    # 计算上个半年报指数的暴露
    Cal_AllIndex_HalfYear_Holding_Exposure(path, report_date_halfyear)

    # 计算上个半年报重点基金的暴露
    Cal_AllFund_HalfYear_Holding_Exposure(path, report_date_halfyear, today)

    # 计算最近交易日指数的暴露
    Cal_AllIndex_LastDate_Holding_Exposure(path, last_date)

    # 计算最近交易日本部门基金的暴露
    Cal_MfcFund_LastDate_Holding_Exposure(path, last_date, today)

    # 合并所有文件
    concat_file(path, report_date_halfyear, last_date)
    mail_exposure(path, last_date, report_date_halfyear)
