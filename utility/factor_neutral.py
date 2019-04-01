import pandas as pd
import statsmodels.api as sm


class FactorNeutral(object):

    """
    因子中性化
    """

    def __init__(self):
        pass

    def factor_exposure_neutral(self, factor_series, neutral_frame):

        """
        factor_series 原始因子series
        neutral_frame 需要中性化的风险因子(一般是Barra风格+行业因子)
        注意行业因子不能标准化，这里也没有对风格因子做标准化，注意市场因子，有可能会共线性
        """

        concat_data = pd.concat([factor_series, neutral_frame], axis=1)
        concat_data = concat_data.dropna()

        factor_val = concat_data.iloc[:, 0]
        neutral_val = concat_data.iloc[:, 1:]

        model = sm.OLS(factor_val.values, neutral_val.values)
        regress = model.fit()

        params = pd.DataFrame(regress.params, index=neutral_val.columns, columns=['param'])
        t_values = pd.DataFrame(regress.tvalues, index=neutral_val.columns, columns=['t_values'])
        factor_res = factor_val - regress.predict(neutral_val)

        return params, t_values, factor_res

    def factor_exposure_corr(self, factor_series, neutral_frame):

        """
        计算和其他因子的相关性
        """

        concat_data = pd.concat([factor_series, neutral_frame], axis=1)
        concat_data = concat_data.dropna()

        corr = pd.DataFrame([], columns=['Corr'], index=concat_data.columns[1:])

        for i in range(1, len(concat_data.columns)):
            col = concat_data.columns[i]
            corr.loc[col, 'Corr'] = concat_data.iloc[:, 0].corr(concat_data.loc[:, col])

        return corr

if __name__ == "__main__":

    # Data
    ##########################################################################################
    from quant.stock.barra import Barra
    from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor

    name = 'alpha_raw_ep'
    date = "20171229"
    data_pandas = AlphaFactor().get_alpha_factor_exposure(name)
    factor_series = data_pandas[date]
    neutral_frame = Barra().get_factor_exposure_date(date, type_list=['STYLE', 'INDUSTRY'])

    params, t_values, factor_res = FactorNeutral().factor_exposure_neutral(factor_series, neutral_frame)
    print(params)
    print(factor_res)
    print(t_values)
    ##########################################################################################
