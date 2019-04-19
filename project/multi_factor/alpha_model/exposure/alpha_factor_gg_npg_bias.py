import pandas as pd
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaGGNPGBias(AlphaFactor):

    """
    因子说明: 一致预期净利润同比偏离
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_gg_npg_bias'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        long_term = 35
        short_term = 5

        # read data
        ltg = Stock().read_factor_h5("ExpectedNetProfitYoY").T
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(ltg.index))
        date_series.sort()
        result = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            long_beg_date = Date().get_trade_date_offset(current_date, -(long_term - 1))
            short_beg_date = Date().get_trade_date_offset(current_date, -(short_term - 1))

            long_mean = ltg.loc[long_beg_date:current_date, :].mean()
            short_mean = ltg.loc[short_beg_date:current_date, :].mean()
            bias = short_mean - long_mean
            std = ltg.loc[long_beg_date:short_beg_date, :].std()
            res_add = pd.DataFrame(bias / (1 + std))
            res_add.columns = [current_date]
            result = pd.concat([result, res_add], axis=1)

        # save data
        ltg = ltg.T.dropna(how='all').T
        self.save_alpha_factor_exposure(ltg, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaGGNPGBias()
    self.cal_factor_exposure(beg_date, end_date)
