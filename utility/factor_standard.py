import pandas as pd
from scipy.stats import norm

from quant.stock.date import Date
from quant.utility.factor_operate import FactorOperate


class FactorStandard(object):

    """
    对 Series 或者 DataFrame 类型的数据 进行操作

    逆正态化（正态化）：根据排名 转化为百分比 再转化为正态值
    标准化：减去均值 除以标准差 只是标准化 并没有正态化
    按照自由流通市值标准化

    inv_normalization()
    standardization()
    standardization_free_mv()

    """
    def __init__(self):
        pass

    @staticmethod
    def inv_normalization(data):

        """
        这里的（逆）正态化是 先给计算排名 给出分位数 再给出标准正太分布中的具体值
        """

        if type(data) == pd.Series:

            data_ser = data.copy()
            data_ser = data_ser.rank() / data_ser.count()
            data_ser[data_ser > 0.999] = 0.999
            data_ser[data_ser < 0.001] = 0.001
            data_ser = pd.Series(norm.ppf(list(data_ser.values), 0, 1), index=data.index, name=data.name)

            return data_ser

        elif type(data) == pd.DataFrame:

            factor = data.copy()
            factor_percentile = factor.rank() / factor.count()
            factor_percentile[factor_percentile > 0.999] = 0.999
            factor_percentile[factor_percentile < 0.001] = 0.001
            factor_value = pd.DataFrame(norm.ppf(list(factor_percentile.values), 0, 1),
                                        index=data.index, columns=data.columns)
            return factor_value
        else:
            print(" Type of Data can not be remove extreme value ")
            return None

    @staticmethod
    def standardization(data):

        """
        标准化 (data - mean) / std
        """

        if type(data) == pd.Series:

            data_ser = data.copy()
            mean = data_ser.mean()
            std = data_ser.std()
            normal_series = (data_ser - mean) / std
            return normal_series

        elif type(data) == pd.DataFrame:

            factor = data.copy()
            factor = factor.T

            mean = factor.mean(axis=1)
            std = factor.std(axis=1)
            factor = factor.sub(mean, axis='index')
            factor = factor.div(std, axis="index")
            factor = factor.T
            return factor

        else:
            print(" Type of Data can not be remove extreme value ")
            return None

    @staticmethod
    def standardization_free_mv(data, free_mv):

        """
        均值为市值加权均值 \ 标准差为普通标准差
        Barra风险模型做法 注意流通市值要用昨天的 而非今天的
        """

        if type(data) == pd.Series:

            data_ser = data.copy()

            concat_data = pd.concat([data_ser, free_mv], axis=1)
            concat_data.columns = ['Factor', 'Mv']
            concat_data = concat_data.dropna()
            concat_data['Mv'] = concat_data['Mv'] / concat_data['Mv'].sum()

            mean_weight_free_mv = (concat_data['Mv'] * concat_data['Factor']).sum()

            std = data_ser.std()
            normal_series = (data_ser - mean_weight_free_mv) / std
            return normal_series

        elif type(data) == pd.DataFrame:

            factor = data.copy()
            free_mv = free_mv.T.shift(1).T
            [factor, free_mv] = FactorOperate().make_same_index_columns([factor, free_mv])
            free_mv = free_mv / free_mv.sum()
            free_mv = free_mv.fillna(0.0)
            free_mv = free_mv.T
            factor = factor.T

            mean_weight_free_mv = factor.mul(free_mv).sum(axis=1)

            std = factor.std(axis=1)
            factor = factor.sub(mean_weight_free_mv, axis='index')
            factor = factor.div(std, axis="index")
            factor = factor.T
            return factor

        else:
            print(" Type of Data can not be remove extreme value ")
            return None

    @staticmethod
    def standardization_cross_free_mv(data, free_mv, date):

        """" 横截面所有数据市值加权 """

        factor = data.copy()
        free_mv_date = free_mv.loc[factor.index, date]
        free_mv_date.name = 'FreeMV'
        free_mv_date /= free_mv_date.sum()

        factor = factor.T
        factor = factor.fillna(0.0)
        free_mv_date = free_mv_date.fillna(0.0)

        mean_weight_free_mv = factor.dot(free_mv_date)

        std = factor.std(axis=1)
        factor = factor.sub(mean_weight_free_mv, axis='index')
        factor = factor.div(std, axis="index")
        factor = factor.T
        return factor


if __name__ == '__main__':

    # Data
    ###################################################################
    from quant.stock.stock_factor_data import StockFactorData

    data = StockFactorData().read_factor_h5('BP', StockFactorData().get_h5_path(type='my_alpha'))
    data_date = data["20171229"]
    free_mv = StockFactorData().read_factor_h5("Mkt_freeshares") / 100000000
    free_mv_date = free_mv["20171228"]

    # Series
    ###################################################################

    inv_normalization_series = FactorStandard().inv_normalization(data_date)
    standardization_series = FactorStandard().standardization(data_date)
    standardization_series_mv = FactorStandard().standardization_free_mv(data_date, free_mv_date)

    result = pd.concat([data_date, inv_normalization_series,
                        standardization_series, standardization_series_mv], axis=1)
    result.columns = ["raw_data", 'normal', 'standard', "standard_mv"]
    print(result[result['raw_data'] > 0.50])

    # DataFrame
    ###################################################################

    inv_normalization_pandas = FactorStandard().inv_normalization(data)
    standardization_pandas = FactorStandard().standardization(data)
    standardization_pandas_mv = FactorStandard().standardization_free_mv(data, free_mv)

    result = pd.concat([data["20171229"], inv_normalization_pandas["20171229"],
                        standardization_pandas["20171229"], standardization_pandas_mv["20171229"]], axis=1)

    result.columns = ["raw_data", 'normal', 'standard', "standard_mv"]
    print(result[result['raw_data'] > 0.50])

