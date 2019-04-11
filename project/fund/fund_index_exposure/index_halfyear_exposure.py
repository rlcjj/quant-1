from quant.stock.index import Index
from quant.stock.date import Date
from quant.fund.fund import Fund
from quant.stock.stock import Stock
import os
import pandas as pd


def Cal_AllIndex_HalfYear_Holding_Exposure(path, report_date):

    """
    计算重点指数最近一个半年报 的持仓风格暴露
    """
    # 参数举例
    #####################################################################
    # path = 'E:\\3_Data\\4_fund_data\\8_fund_index_exposure_weekly\\'
    # report_date = '20171231'
    # today = datetime.today().strftime("%Y%m%d")

    # 基金池
    #####################################################################
    index_pool_file = os.path.join(path, "fund_pool", '重点指数代码.csv')
    index_pool = pd.read_csv(index_pool_file, index_col=[0], encoding='gbk')
    date = Date().get_trade_date_offset(report_date, 0)
    beg_date = Date().get_trade_date_offset(report_date, -2)
    end_date = Date().get_trade_date_offset(report_date, 2)

    # 计算重点所有重点 基金最近一个半年报 的持仓风格暴露
    #####################################################################
    # 计算万德全A的基准 因为每早下载 这里就不重复下载
    # Index().load_weight_china_index_date(date)

    for i_index in range(len(index_pool)):

        index_code = index_pool.index[i_index]
        # 下载指数权重 因为每早下载 这里就不重复下载
        # if index_code not in ["000300.SH", '000905.SH', '881001.WI']:
        #     Index().load_weight_from_wind_date(index_code=index_code, date=date)
        Index().cal_index_exposure(index_code, beg_date, end_date)

        if i_index == 0:
            exposure = Index().get_index_exposure_date(index_code, date, type_list=["STYLE"])
            exposure["CTY"] = 1.0
        else:
            exposure_add = Index().get_index_exposure_date(index_code, date, type_list=["STYLE"])
            exposure_add["CTY"] = 1.0
            exposure = pd.concat([exposure, exposure_add], axis=0)

    #####################################################################
    exposure.index = index_pool.index_name
    exposure.loc["1/3*中小板综+1/3*创业板综+1/3*中证500", :] = exposure.loc[["中小板综", "创业板综", "中证500"], :].mean()
    cols = list(exposure.columns)
    cols.insert(0, 'Type')
    exposure['Type'] = '市场指数'
    exposure = exposure[cols]
    exposure_file = os.path.join(path, "halfyear_holding_exposure", 'IndexHalfYearExposure_' + report_date + '.csv')
    exposure.to_csv(exposure_file)
    #####################################################################


if __name__ == '__main__':

    path = 'E:\\Data\\fund_data\\fund_index_exposure_weekly\\'
    report_date = '20180630'
    Cal_AllIndex_HalfYear_Holding_Exposure(path, report_date)