import pandas as pd
import numpy as np


class FactorRemoveValue(object):

    """
    对 Series 或者 DataFrame 类型的数据 进行操作

    去极值：三倍标准差 五倍中位数

    remove_extreme_value_std()
    remove_extreme_value_mad()

    """

    def __init__(self):
        pass

    @staticmethod
    def remove_extreme_value_std(data):

        """ 三倍标准差去极值 """

        if type(data) == pd.Series:
            data_series = data.copy()
            mean = data_series.mean()
            std = data_series.std()
            data_series = data_series.apply(lambda x: -3.0 * std + mean if x < -3.0 * std + mean else x)
            data_series = data_series.apply(lambda x: 3.0 * std + mean if x > 3.0 * std + mean else x)
            return data_series

        elif type(data) == pd.DataFrame:

            factor = data.copy()
            factor = factor.T
            factor_val = factor.values

            mean = factor.mean(axis=1)
            std = factor.std(axis=1)
            n = 3

            up_col_val = (mean + n * std).values
            up_remat_val = np.tile(np.vstack(up_col_val), (1, factor.shape[1]))
            up_mask = factor_val > up_remat_val
            up_factor_val = np.where(up_mask, up_remat_val, factor_val)

            down_col_val = (mean - n * std).values
            down_remat_val = np.tile(np.vstack(down_col_val), (1, factor.shape[1]))
            down_mask = up_factor_val < down_remat_val
            down_factor_val = np.where(down_mask, down_remat_val, up_factor_val)

            down_factor = pd.DataFrame(down_factor_val, index=factor.index, columns=factor.columns)
            down_factor = down_factor.T
            return down_factor

        else:
            print(" Type of Data can not be remove extreme value ")
            return None

    @staticmethod
    def remove_extreme_value_mad(data):

        """ 5倍中位数去极值 """

        if type(data) == pd.Series:
            data_series = data.copy()
            md = data_series.median()
            mad = np.abs(data_series - md).median()
            n = 1.483 * 3
            n = 5.0
            data_series = data_series.apply(lambda x: -n * mad + md if x < -n * mad + md else x)
            data_series = data_series.apply(lambda x: n * mad + md if x > n * mad + md else x)
            return data_series

        elif type(data) == pd.DataFrame:

            factor = data.copy()
            factor = factor.T
            factor_val = factor.values

            md = factor.median(axis=1)
            mad = factor.sub(md, axis='index').abs().median(axis=1)
            n = 1.483 * 3
            n = 5.0

            up_col_val = (md + n * mad).values
            up_remat_val = np.tile(np.vstack(up_col_val), (1, factor.shape[1]))
            up_mask = factor_val > up_remat_val
            up_factor_val = np.where(up_mask, up_remat_val, factor_val)

            down_col_val = (md - n * mad).values
            down_remat_val = np.tile(np.vstack(down_col_val), (1, factor.shape[1]))
            down_mask = up_factor_val < down_remat_val
            down_factor_val = np.where(down_mask, down_remat_val, up_factor_val)

            down_factor = pd.DataFrame(down_factor_val, index=factor.index, columns=factor.columns)
            down_factor = down_factor.T
            return down_factor

        else:
            print(" Type of Data can not be remove extreme value ")
            return None

if __name__ == "__main__":

    # Data
    ###################################################################
    from quant.stock.stock_factor_data import StockFactorData

    name = 'EP_Roll'
    data_pandas = StockFactorData().read_factor_h5(name, StockFactorData().get_h5_path(type='mfc_alpha'))
    data_series = data_pandas["20171229"]

    # Series
    ###################################################################

    remove_std_series = FactorRemoveValue().remove_extreme_value_std(data_series)
    remove_mad_series = FactorRemoveValue().remove_extreme_value_mad(data_series)

    result = pd.concat([data_series, remove_std_series, remove_mad_series], axis=1)
    result.columns = ["raw_data", 'remove_std', "remove_mad"]
    print(result[result['raw_data'] > 0.15])
    # print(result)

    # DataFrame
    ###################################################################
    remove_std_pandas = FactorRemoveValue().remove_extreme_value_std(data_pandas)
    remove_mad_pandas = FactorRemoveValue().remove_extreme_value_mad(data_pandas)

    result = pd.concat([data_pandas["20171229"], remove_std_pandas["20171229"], remove_mad_pandas["20171229"]], axis=1)

    result.columns = ["raw_data", 'remove_std', "remove_mad"]
    print(result[result['raw_data'] > 0.15])
    # print(result)
