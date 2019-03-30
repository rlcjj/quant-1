import os
from datetime import datetime

import pandas as pd
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.stock import Stock


def GenerateStockFactor(name, factor_name, freq="M"):

    # 参数
    ###########################################################################################
    path = r'E:\3_Data\4_fund_data\2_fund_factor'
    save_path = r'E:\3_Data\4_fund_data\2_fund_factor\fund_stock_alpha_factor'

    # 读取全部基金Alpha因子值
    ###########################################################################################
    file = os.path.join(path, "exposure", name + '.csv')
    values = pd.read_csv(file, index_col=[0], encoding='gbk')
    values.columns = values.columns.map(str)
    values.columns = values.columns.map(lambda x: Date().get_trade_date_offset(x, 0))
    date_series = Date().get_trade_date_series("20040101", datetime.today(), "M")

    stock_ratio = Fund().get_fund_factor('Stock_Ratio', None, None)

    if freq == "Q":
        date_series = list(filter(lambda x: x[4:6] in ['04', '07', '10', '01'], date_series))
    values_date_series = list(values.columns)

    use_date_series = list(set(values_date_series) & set(date_series))
    use_date_series.sort()

    # 每期计算股票Alpha因子值 len(use_date_series)
    ###########################################################################################
    for i in range(0, len(use_date_series)):

        # 日期
        ###########################################################################################
        date = use_date_series[i]
        data = pd.DataFrame(values[date])
        data = data.dropna()
        data = data.sort_values(by=[date], ascending=False)
        data.columns = ["Alpha"]
        data['Rank'] = data['Alpha'].rank()
        data['RankRatio'] = data['Rank'] / len(data)

        quarter_date = Date().get_last_fund_quarter_date(date)
        print(date, quarter_date)

        stock_data = pd.DataFrame([])

        # 所有基金当期季报股票综合
        ###########################################################################################
        for i_fund in range(len(data)):

            fund = data.index[i_fund]
            fund_weight = data.loc[fund, "RankRatio"]
            fund_weight = fund_weight * stock_ratio.loc[quarter_date, fund]
            # fund_weight = 1
            try:
                fund_holding = Fund().get_fund_holding_quarter(fund=fund)
                fund_holding_date = pd.DataFrame(fund_holding[quarter_date])
                fund_holding_date = fund_holding_date.dropna()
                fund_holding_date.columns = [fund]
                # fund_holding_date[fund] = 1.0
                fund_holding_date *= fund_weight
            except Exception as e:
                fund_holding_date = pd.DataFrame([], columns=[fund])
            if i_fund == 0:
                stock_data = fund_holding_date
            else:
                stock_data = pd.concat([stock_data, fund_holding_date], axis=1)

        ###########################################################################################
        stock_data = stock_data.dropna(how='all')
        stock_data_weight = pd.DataFrame(stock_data.sum(axis=1))
        stock_data_weight.columns = [date]

        # 每期股票Alpha合并
        ###########################################################################################
        if i == 0:
            result = stock_data_weight
        else:
            result = pd.concat([result, stock_data_weight], axis=1)

    # 转换成日频率数据
    ####################################################################################################
    result = result.T
    date_series = Date().get_normal_date_series(result.index[0], result.index[-1])

    result_daily = result.ix[date_series, :]
    result_daily = result_daily.fillna(method='pad', limit=92)

    result_daily = result_daily.T

    free_mv = Stock().read_factor_h5("MarketFreeShares")
    free_mv /= 1000000000

    result_daily = result_daily.div(free_mv)

    # 股票Alpha数据存储
    ####################################################################################################
    file = factor_name + "_" + str(freq) + '_AllFund'
    file = "RSAIR240_Ratio_M_AF"
    filename = os.path.join(save_path, file + '.csv')
    result_daily.to_csv(filename)
    result_daily = pd.read_csv(filename, index_col=[0], encoding='gbk')
    result_daily.columns = result_daily.columns.map(str)
    Stock().write_factor_h5(result_daily, file, "my_alpha")
    ####################################################################################################


if __name__ == "__main__":


    name = "FundRegressionStyle_AlphaReturnIR_240"
    factor_name = name
    GenerateStockFactor(name, factor_name, "M")

    def change_name(path, dsname, change_dsname):

        from quant.utility.hdf_mfc import HdfMfc
        from quant.utility.factor_preprocess import FactorPreProcess
        import os

        filename = os.path.join(path, dsname + '.h5')
        change_filename = os.path.join(path, change_dsname + '.h5')
        HdfMfc(filename, dsname).rename(dsname, change_filename, change_dsname)
        data = HdfMfc(change_filename, change_dsname).read_hdf_factor(change_dsname)
        month_date_series = Date().get_trade_date_series("20060101", "20180609", "M")
        month_data = data[month_date_series]
        corr = month_data.corr()
        corr.to_csv(os.path.join(path, change_dsname + '_MonthCorr.csv'))
        data_inv = FactorPreProcess().inv_normalization(data)
        # data_inv = data_inv.fillna(0.0)
        # data = FactorPreProcess().remove_extreme_value_mad(data)
        data = FactorPreProcess().standardization(data_inv)
        data.to_csv(os.path.join(path, change_dsname + '.csv'))
        # data = data.fillna(0.0)
        HdfMfc(filename, dsname).write_hdf_factor(change_filename, change_dsname, data)

    path = r'E:\3_Data\5_stock_data\3_alpha_model\alpha_data'
    dsname = "RSAIR240_Ratio_M_AF"
    change_dsname = "ERSAIR240_Ratio_M_AFI"
    change_name(path, dsname, change_dsname)
    # change_name(path, "FundRegressionIndex_FundReturnMean_240_AllFund", "RI_FM_240_AF")
    # change_name(path, "FundHolderQuarter_AlphaReturnMean_480_AllFund", "HQ_AM_480_AF")