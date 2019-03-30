import pandas as pd
import numpy as np
import os

from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def StockST(beg_date, end_date):

    """
    股票名称
    """

    # param
    #################################################################################
    factor_name = "StockST"
    ipo_num = 90

    # read data
    #################################################################################
    # Stock().load_st_info()
    st = Stock().get_st_info()
    ipo_date = Stock().get_ipo_date()
    data = pd.DataFrame([])

    # 循环计算每只股票

    for i_code in range(0, len(st)):

        code = st.index[i_code]
        bg_date = ipo_date.loc[code, "IPO_DATE"]
        ed_date = ipo_date.loc[code, "DELIST_DATE"]
        today = datetime.today().strftime("%Y%m%d")
        ed_date = min(ed_date, today)
        date_series = Date().get_trade_date_series(bg_date, ed_date)
        st_code = pd.DataFrame([], index=date_series, columns=[code])
        st_code.loc[date_series, code] = 0.0
        st_info = st.loc[code, "RISKADMONITION_DATE"]
        print(" Cal ST %s" % code)

        if type(st_info) == np.str:

            st_info = st_info.replace("：", ":")
            st_info = st_info.split(",")
            st_info = [x.split(":") for x in st_info]
            st_info_pd = pd.DataFrame(st_info, columns=["Action", "Date"])
            st_info_pd = st_info_pd.sort_values(by="Date")
            st_info_pd = st_info_pd.reset_index(drop=True)

            st_date_list = []
            bg_ed_date = []
            find_beg_date = 1

            # 可能包含多次戴帽摘帽
            for i in range(len(st_info_pd)):

                action = st_info_pd.iloc[i, 0]
                date = st_info_pd.iloc[i, 1]

                if find_beg_date and action in ["ST", "*ST"]:
                    bg_ed_date.append(date)
                    find_beg_date = 0

                if ~find_beg_date and action in ["去ST", "去*ST"]:
                    bg_ed_date.append(date)
                    find_beg_date = 1
                    st_date_list.append(bg_ed_date)
                    bg_ed_date = []

                if i == len(st_info_pd) - 1 and action not in ["去ST", "去*ST"]:
                    bg_ed_date.append(ed_date)
                    find_beg_date = 1
                    st_date_list.append(bg_ed_date)
                    bg_ed_date = []

            for i in range(len(st_date_list)):
                st_bg_date = st_date_list[i][0]
                st_ed_date = st_date_list[i][1]
                st_code.loc[st_bg_date:st_ed_date, code] = 1.0
        else:
            pass

        data = pd.concat([data, st_code], axis=1)

    data = data.T
    path = Stock().get_h5_path("my_alpha")
    Stock().write_factor_h5(data=data, factor_name=factor_name, path=path)
    return data
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '20181218'
    end_date = datetime.today()
    data = StockName(beg_date, end_date)
    print(data)

