import pandas as pd
from quant.stock.date import Date
import os
from datetime import datetime


def fund_select_ability():

    # 参数
    #######################################################################################
    path = 'E:\\Data\\fund_data\\fund_select_stock\\'
    beg_date = "20040101"
    end_date = datetime.today().strftime("%Y%m%d")

    # 读取数据
    #######################################################################################
    date_series = Date().get_normal_date_series(beg_date, end_date, "Q")
    result = {}

    for i in range(len(date_series)):

        report_date = date_series[i]
        file = "FundBarraDecomposeReturnQuarter" + report_date + '.csv'
        file = os.path.join(path, "FundBarraDecomposeReturnQuarter", file)
        fund_decompose_return = pd.read_csv(file, index_col=[0], encoding='gbk')
        result[report_date] = fund_decompose_return

    #######################################################################################
    result_panel = pd.Panel(result)

    file = "FundAlphaReturnQuarter.csv"
    file = os.path.join(path, "FundAlphaFactor", file)
    result_panel[:, :, "Alpha"].to_csv(file)

    file = "FundStyleReturnQuarter.csv"
    file = os.path.join(path, "FundAlphaFactor", file)
    result_panel[:, :, "Style"].to_csv(file)

    file = "FundIndustryReturnQuarter.csv"
    file = os.path.join(path, "FundAlphaFactor", file)
    result_panel[:, :, "Industry"].to_csv(file)

    file = "FundAllReturnQuarter.csv"
    file = os.path.join(path, "FundAlphaFactor", file)
    result_panel[:, :, "All"].to_csv(file)

if __name__ == "__main__":

    fund_select_ability()
