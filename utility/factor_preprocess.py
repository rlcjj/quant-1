from quant.utility.factor_fillna import FactorFillNa
from quant.utility.factor_operate import FactorOperate
from quant.utility.factor_remove_value import FactorRemoveValue
from quant.utility.factor_standard import FactorStandard
import pandas as pd


class FactorPreProcess(FactorStandard, FactorRemoveValue,
                       FactorOperate, FactorFillNa):

    """
    对 Series 或者 DataFrame 类型的数据 进行预处理

    FactorStandard  逆正态化 标准化
    FactorRemoveValue 去除极值
    FactorFillNa 补充缺失值
    FactorOperate 因子常做的操作 同行列 覆盖合并

    """

    def __init__(self):

        FactorStandard.__init__(self)
        FactorRemoveValue.__init__(self)
        FactorOperate.__init__(self)
        FactorFillNa.__init__(self)


if __name__ == '__main__':

    # Data
    ###################################################################
    from quant.stock.stock_factor_data import StockFactorData
    name = 'EP_Roll'
    data_pandas = StockFactorData().read_factor_h5(name, StockFactorData().get_h5_path(type='mfc_alpha'))
    data_series = data_pandas["20171229"]
    data_second = pd.DataFrame([], columns=["20171228", "20171229"], index=["000001.SZ", "600000.SH"])
    data_second_series = data_second["20171229"]

    # Series
    ###################################################################

    [same_one, same_two] = FactorPreProcess().make_same_index_columns([data_series, data_second_series])
    # print(same_one, '\n', same_two)

    remove_std_series = FactorPreProcess().remove_extreme_value_std(data_series)
    remove_mad_series = FactorPreProcess().remove_extreme_value_mad(data_series)
    inv_normalization_series = FactorPreProcess().inv_normalization(data_series)
    standardization_series = FactorPreProcess().standardization(data_series)
    standardization_series_mv = FactorPreProcess().standardization_free_mv(data_series)

    result = pd.concat([data_series, remove_std_series,
                        remove_mad_series, inv_normalization_series,
                        standardization_series, standardization_series_mv], axis=1)
    result.columns = ["raw_data", 'remove_std', "remove_mad", 'normal', 'standard', "standard_mv"]
    # print(result[result['raw_data'] > 0.15])
    print(result)
    # DataFrame
    ###################################################################

    [same_one, same_two] = FactorPreProcess().make_same_index_columns([data_pandas, data_second])
    # print(same_one, '\n', same_two)

    remove_std_pandas = FactorPreProcess().remove_extreme_value_std(data_pandas)
    remove_mad_pandas = FactorPreProcess().remove_extreme_value_mad(data_pandas)
    inv_normalization_pandas = FactorPreProcess().inv_normalization(data_pandas)
    standardization_pandas = FactorPreProcess().standardization(data_pandas)
    standardization_pandas_mv = FactorPreProcess().standardization_free_mv(data_pandas)

    result = pd.concat([data_pandas["20171229"], remove_std_pandas["20171229"],
                        remove_mad_pandas["20171229"], inv_normalization_pandas["20171229"],
                        standardization_pandas["20171229"], standardization_pandas_mv["20171229"]], axis=1)

    result.columns = ["raw_data", 'remove_std', "remove_mad", 'normal', 'standard', "standard_mv"]
    # print(result[result['raw_data'] > 0.15])
    print(result)
    ###################################################################

