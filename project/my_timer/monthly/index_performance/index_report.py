import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.stock.index import Index
from quant.stock.date import Date
from quant.utility.write_excel import WriteExcel


def summary_market(excel, params, summary, date_array, sheet_name):

    # 添加新的sheet
    ##############################################################################
    worksheet = excel.add_worksheet(sheet_name)
    params = pd.DataFrame(params, columns=["Name", 'Code'])

    # 新的数据
    ##############################################################################
    summary_index = summary.loc[params.Name, :]

    index_code = params.iloc[0, 1]
    index_name = params.iloc[0, 0]

    index_data = Index().get_index_factor(index_code, attr=["CLOSE"])

    # 写入最近表现
    ##############################################################################
    col_number = 1
    num_format_pd = pd.DataFrame([], columns=summary_index.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    print(summary_index)
    excel.write_pandas(summary_index, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="red", fillna=True)
    col_number += len(summary_index.columns) + 2

    # 分日期区间写入主要指数（首个）累计收益率 和 时间序列图
    ##############################################################################
    for i_date in range(0, len(date_array)):

        # 整理数据
        ##############################################################################
        label = date_array.loc[i_date, "label"]
        bg_date = date_array.loc[i_date, "beg_date"]
        ed_date = date_array.loc[i_date, "end_date"]
        index_period = index_data.loc[bg_date:ed_date, :]
        index_period['Pct'] = index_period['CLOSE'].pct_change()
        index_period = index_period.dropna()
        index_period["CumPct"] = (index_period['Pct'] + 1.0).cumprod() - 1.0
        index_period_cum_pct = pd.DataFrame(index_period['CumPct'])
        index_period_cum_pct.columns = [label + index_name]
        print(index_period_cum_pct)

        # 写入累计收益率
        ##############################################################################
        num_format_pd = pd.DataFrame([], columns=index_period_cum_pct.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(index_period_cum_pct, worksheet, begin_row_number=0, begin_col_number=col_number,
                           num_format_pd=num_format_pd, color="blue", fillna=True)

        # 时间序列图
        ##############################################################################
        position = excel.change_row_col_to_cell(len(summary_index) + 3 + i_date * 15, 1)
        excel.line_chart_time_series_plot(worksheet, 0, col_number, index_period_cum_pct,
                                          [index_name], label + index_name + "累计收益率", position, sheet_name)
        col_number += len(index_period_cum_pct.columns) + 1
        ##############################################################################


def summary_allindex(excel, params, date_array):

    # 整理参数
    ################################################################################################
    params = pd.DataFrame(params, columns=["Name", 'Code'])
    summary = pd.DataFrame(params.Code.values, index=params.Name, columns=["wind代码"])

    # 开始计算 日期区间写入指数累计收益率、波动率
    ################################################################################################
    for i in range(len(params)):

        index_name = params.loc[i, "Name"]
        index_code = params.loc[i, "Code"]
        index_data = Index().get_index_factor(index_code, attr=["CLOSE"])
        index_data['Pct'] = index_data['CLOSE'].pct_change()

        for i_date in range(0, len(date_array)):
            label = date_array.loc[i_date, "label"]
            bg_date = date_array.loc[i_date, "beg_date"]
            ed_date = date_array.loc[i_date, "end_date"]
            try:
                bg_close = index_data.loc[bg_date, "CLOSE"]
                ed_close = index_data.loc[ed_date, "CLOSE"]
                pct = ed_close / bg_close - 1.0
                summary.loc[index_name, label + "_收益"] = pct
                std = index_data.loc[bg_date:ed_date, "Pct"].std() * np.sqrt(250)
                summary.loc[index_name, label + "_波动"] = std
            except Exception as e:
                pct = np.nan
                std = np.nan
                summary.loc[index_name, label + "_收益"] = pct
                summary.loc[index_name, label + "_波动"] = std

            print(" Cal Return Index %s From %s To %s is %s" % (index_name, bg_date, ed_date, pct))

    # 写入表格
    ################################################################################################
    sheet_name = "主要指数表现"
    worksheet = excel.add_worksheet(sheet_name)

    col_number = 1
    num_format_pd = pd.DataFrame([], columns=summary.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(summary, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="red", fillna=True)
    excel.conditional_format(worksheet, 1, 3, 1 + len(summary), 3, None)
    excel.conditional_format(worksheet, 1, 5, 1 + len(summary), 5, None)
    excel.conditional_format(worksheet, 1, 7, 1 + len(summary), 7, None)
    return summary
    ################################################################################################


def generate_summary(end_date, save_path):

    """
    汇率 债券 商品 各类指数计算每月收益率
    """

    # 参数举例
    ################################################################################################
    # end_date = "20181031"
    # save_path = r'C:\Users\doufucheng\OneDrive\Desktop'

    end_trade_date = Date().get_trade_date_month_end_day(end_date)
    beg_trade_date = Date().get_trade_date_last_month_end_day(end_trade_date)
    month = datetime.strptime(end_date, "%Y%m%d").month
    year_trade_date = Date().get_trade_date_offset(beg_trade_date, -250)

    date_array = [[str(month) + "月", beg_trade_date, end_trade_date],
                  ["2019年以来", "20181228", end_trade_date],
                  ["最近1年", year_trade_date, end_trade_date]]
    date_array = pd.DataFrame(date_array, columns=["label", "beg_date", "end_date"])

    # 指数列表
    ################################################################################################
    params = [["上证50", "000016.SH"],
              ["沪深300", "000300.SH"],
              ["中证500", "000905.SH"],
              ["万德全A", "881001.WI"],
              ["创业板指", "399006.SZ"],
              ["恒生指数", "HSI.HI"],
              ["美国道琼斯工业指数", "DJI.GI"],
              ["美国纳斯达克指数", "IXIC.GI"],
              ["美国标普500指数", "SPX.GI"],
              ["英国伦敦富时100指数", "FTSE.GI"],
              ["法国巴黎CAC40指数", "FCHI.GI"],
              ["德国法兰克福DAX指数", "GDAXI.GI"],
              ["日本东京日经225指数", "N225.GI"],
              ["富时新加坡STI", "STI.GI"],
              ["孟买Sensex30指数", "SENSEX.GI"],
              ["汇率_美元兑人民币_中间价", "USDCNY.EX"],
              ["货币市场基金指数", "885009.WI"],
              ["长期纯债型基金指数", "885008.WI"],
              ["中证全债", "H11001.CSI"],
              ["中证国债", "H11006.CSI"],
              ["中证信用债", "H11073.CSI"],
              ["中证转债", "000832.SH"],
              ["wind商品指数", "CCFI.WI"],
              ["wind贵金属", "NMFI.WI"],
              ["wind有色金属", "NFFI.WI"],
              ["wind煤焦钢矿", "JJRI.WI"],
              ["wind非金属建材", "NMBM.WI"],
              ["wind能源", "ENFI.WI"],
              ["wind化工", "CIFI.WI"],
              ["wind谷物", "CRFI.WI"],
              ["wind油脂油料", "OOFI.WI"],
              ["wind软商品", "SOFI.WI"],
              ["标普高盛商品总指数", "SPGSCITR.SPI"],
              ["标普高盛商品石油指数", "SPGSPTTR.SPI"],
              ]

    # EXCEL 表
    ################################################################################################
    file_name = os.path.join(save_path, "IndexPerformance" + "_" + end_date + '.xlsx')
    excel = WriteExcel(file_name)

    # 整体表现
    ################################################################################################
    summary = summary_allindex(excel, params, date_array)

    # 国内股票市场
    ################################################################################################
    params = [["沪深300", "000300.SH"],
              ["中证500", "000905.SH"],
              ["万德全A", "881001.WI"],
              ["创业板指", "399006.SZ"],
              ["恒生指数", "HSI.HI"]
              ]

    sheet_name = "国内股票"
    summary_market(excel, params, summary, date_array, sheet_name)

    # 国内债券市场
    ################################################################################################
    params = [["中证全债", "H11001.CSI"],
              ["长期纯债型基金指数", "885008.WI"],
              ["中证国债", "H11006.CSI"],
              ["中证信用债", "H11073.CSI"],
              ["中证转债", "000832.SH"]]

    sheet_name = "国内债券"
    summary_market(excel, params, summary, date_array, sheet_name)

    # 国内货币市场
    ################################################################################################
    params = [["货币市场基金指数", "885009.WI"]]

    sheet_name = "国内货币"
    summary_market(excel, params, summary, date_array, sheet_name)

    # 国内商品市场
    ################################################################################################
    params = [["wind商品指数", "CCFI.WI"],
              ["wind贵金属", "NMFI.WI"],
              ["wind有色金属", "NFFI.WI"],
              ["wind煤焦钢矿", "JJRI.WI"],
              ["wind非金属建材", "NMBM.WI"],
              ["wind能源", "ENFI.WI"],
              ["wind化工", "CIFI.WI"],
              ["wind谷物", "CRFI.WI"],
              ["wind油脂油料", "OOFI.WI"],
              ["wind软商品", "SOFI.WI"]]

    sheet_name = "国内商品"
    summary_market(excel, params, summary, date_array, sheet_name)

    # 国际股票市场
    ################################################################################################
    params = [["美国道琼斯工业指数", "DJI.GI"],
              ["美国纳斯达克指数", "IXIC.GI"],
              ["美国标普500指数", "SPX.GI"],
              ["英国伦敦富时100指数", "FTSE.GI"],
              ["法国巴黎CAC40指数", "FCHI.GI"],
              ["德国法兰克福DAX指数", "GDAXI.GI"],
              ["日本东京日经225指数", "N225.GI"],
              ["富时新加坡STI", "STI.GI"],
              ["孟买Sensex30指数", "SENSEX.GI"]]

    sheet_name = "国际股票"
    summary_market(excel, params, summary, date_array, sheet_name)

    # 国际商品市场
    ################################################################################################
    params = [["标普高盛商品总指数", "SPGSCITR.SPI"],
              ["标普高盛商品石油指数", "SPGSPTTR.SPI"]]

    sheet_name = "国际商品"
    summary_market(excel, params, summary, date_array, sheet_name)

    # 外汇市场
    ################################################################################################
    params = [["汇率_美元兑人民币_中间价", "USDCNY.EX"]]

    sheet_name = "外汇市场"
    summary_market(excel, params, summary, date_array, sheet_name)

    excel.close()


def load_index_close_daily(beg_date, end_date):

    """
    下载汇率 债券 商品 各类指数日度收盘价序列
    """

    params = [
        ["汇率_美元兑人民币_中间价", "USDCNY.EX"],
        ["中证全债", "H11001.CSI"],
        ["中证国债", "H11006.CSI"],
        ["中证信用债", "H11073.CSI"],
        ["中证转债", "000832.SH"],
        ["wind商品指数", "CCFI.WI"],
        ["wind贵金属", "NMFI.WI"],
        ["wind有色金属", "NFFI.WI"],
        ["wind煤焦钢矿", "JJRI.WI"],
        ["wind非金属建材", "NMBM.WI"],
        ["wind能源", "ENFI.WI"],
        ["wind化工", "CIFI.WI"],
        ["wind谷物", "CRFI.WI"],
        ["wind油脂油料", "OOFI.WI"],
        ["wind软商品", "SOFI.WI"],
        ["wind贵金属", "NMFI.WI"],
        ["wind贵金属", "NMFI.WI"],
        ["wind贵金属", "NMFI.WI"],
        ["上证50", "000016.SH"],
        ["恒生指数", "HSI.HI"],
        ["美国道琼斯工业指数", "DJI.GI"],
        ["美国纳斯达克指数", "IXIC.GI"],
        ["美国标普500指数", "SPX.GI"],
        ["英国伦敦富时100指数", "FTSE.GI"],
        ["法国巴黎CAC40指数", "FCHI.GI"],
        ["德国法兰克福DAX指数", "GDAXI.GI"],
        ["日本东京日经225指数", "N225.GI"],
        ["富时新加坡STI", "STI.GI"],
        ["孟买Sensex30指数", "SENSEX.GI"],
        ["标普高盛商品总指数", "SPGSCITR.SPI"],
        ["标普高盛商品石油指数", "SPGSPTTR.SPI"],
        ["长期纯债型基金指数", "885008.WI"],
        ["货币市场基金指数", "885009.WI"],
        ["中债国债总净价指数-总值", "CBA00602.CS"],
        ["中债国债总财富指数-总值", "CBA00601.CS"]
    ]

    # 开始下载
    ################################################################################################
    for i in range(len(params)):

        index_name = params[i][0]
        index_code = params[i][1]
        print(" Loading Index %s Close From %s To %s " % (index_name, beg_date, end_date))
        Index().load_index_factor(index_code, beg_date, end_date)

if __name__ == "__main__":

    end_month_date = "20190131"
    save_path = r'E:\Data\index_data\index_month_report'
    generate_summary(end_month_date, save_path)
