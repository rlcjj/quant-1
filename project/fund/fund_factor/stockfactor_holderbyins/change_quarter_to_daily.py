import os
import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.utility.hdf_mfc import HdfMfc


def ChangeQuarterToDaliy(data_path, name):

    """
    将基金季报数据转化为日度数据
    """

    # paramter
    ##################################################################################################
    # data_path = r"E:\SoftWare\anaconda\anaconda\Lib\site-packages\quant\project\fund\fund_factor\stockfactor_holderbyins\data"
    # name = "HolderRatioByQfii"

    # read xlsx data
    ##################################################################################################
    xlsx_file = os.path.join(data_path, name + '.xlsx')
    h5_file = os.path.join(data_path, name + '.h5')
    csv_file = os.path.join(data_path, name + '.csv')

    xlsx_data = pd.read_excel(xlsx_file, index_col=[0], encoding='gbk')
    xlsx_data = xlsx_data.drop('证券简称', axis=1)
    xlsx_data = xlsx_data.T
    quarter_date_series = Date().get_trade_date_series("20040101", "20181231", "Q")

    quarter_date_series_publish_date = list(map(lambda x: Date().get_stcok_same_publish_date(x), quarter_date_series))
    xlsx_data.index = quarter_date_series_publish_date
    xlsx_data = xlsx_data.dropna(how='all')
    xlsx_data = xlsx_data.fillna('miss')

    # change to daily
    ##################################################################################################
    date_series = Date().get_trade_date_series(xlsx_data.index[0], xlsx_data.index[-1])
    h5_data = xlsx_data.loc[date_series, :]
    h5_data = h5_data.fillna(method='pad')
    # h5_data.applymap(lambda x: np.nan if x is None else x)
    h5_data = h5_data.replace('miss', np.nan)
    # date_series = Date().get_trade_date_series(xlsx_data.index[0], xlsx_data.index[-1])
    h5_data = h5_data.loc[date_series, :]
    h5_data = h5_data.T

    # save h5 data
    ##################################################################################################
    HdfMfc().write_hdf_factor(h5_file, name, h5_data)
    h5_data.to_csv(csv_file)
    ##################################################################################################


def ChangeQuarterToDaliyIf(data_path, name):

    """
    将基金季报数据转化为日度数据
    """

    # paramter
    ##################################################################################################
    # data_path = r"E:\SoftWare\anaconda\anaconda\Lib\site-packages\quant\project\fund\fund_factor\stockfactor_holderbyins\data"
    # name = "HolderRatioByQfii"

    # read xlsx data
    ##################################################################################################
    xlsx_file = os.path.join(data_path, name + '.xlsx')
    name += 'If'
    h5_file = os.path.join(data_path, name + '.h5')
    csv_file = os.path.join(data_path, name + '.csv')

    xlsx_data = pd.read_excel(xlsx_file, index_col=[0], encoding='gbk')
    xlsx_data = xlsx_data.drop('证券简称', axis=1)
    xlsx_data = xlsx_data.T
    quarter_date_series = Date().get_trade_date_series("20040101", "20181231", "Q")
    quarter_date_series_publish_date = list(map(lambda x: Date().get_stcok_same_publish_date(x), quarter_date_series))
    xlsx_data.index = quarter_date_series_publish_date
    xlsx_data = xlsx_data.dropna(how='all')

    xlsx_data[xlsx_data.applymap(lambda x: ~np.isnan(x))] = 1.0
    xlsx_data[xlsx_data.applymap(lambda x: np.isnan(x))] = 0.0

    # change to daily
    ##################################################################################################
    date_series = Date().get_trade_date_series(xlsx_data.index[0], xlsx_data.index[-1])

    h5_data = xlsx_data.ix[date_series, :]
    h5_data = h5_data.fillna(method='pad')
    h5_data = h5_data.T

    # save h5 data
    ##################################################################################################
    HdfMfc().write_hdf_factor(h5_file, name, h5_data)
    h5_data.to_csv(csv_file)
    ##################################################################################################


if __name__ == '__main__':

    data_path = r"E:\SoftWare\anaconda\anaconda\Lib\site-packages\quant\project\fund_project\fund_factor\stockfactor_holderbyins\data"
    name = "HolderRatioByQfii"

    ChangeQuarterToDaliy(data_path, "HolderRatioByQfii")
    ChangeQuarterToDaliy(data_path, "HolderNumberBySiFund")
    ChangeQuarterToDaliy(data_path, "HolderRatioByTotalIns")
    ChangeQuarterToDaliy(data_path, "HolderRatioByFund")

    ChangeQuarterToDaliyIf(data_path, "HolderRatioByQfii")
    ChangeQuarterToDaliyIf(data_path, "HolderNumberBySiFund")
    ChangeQuarterToDaliyIf(data_path, "HolderRatioByTotalIns")
    ChangeQuarterToDaliyIf(data_path, "HolderRatioByFund")
