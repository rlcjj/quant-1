import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.fama_french import FamaFrench
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaFF3VolBias(AlphaFactor):

    """
    因子说明: - 法玛三因子模型的残差波动率的变动
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_ff3_vol_bias'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        long_term = 60
        short_term = 20
        effective_term = int(long_term * 0.8)

        # read data
        ff3_residual = FamaFrench().get_data("model_ff3", "FF3_ResidualReturn") / 100.0

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(ff3_residual.columns) & set(date_series))
        date_series.sort()
        res = pd.DataFrame()

        # FamaFrench().cal_all_factor_pct()
        # FamaFrench().ff3_model(beg_date, end_date)

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            long_beg_date = Date().get_trade_date_offset(current_date, -(long_term - 1))
            short_beg_date = Date().get_trade_date_offset(current_date, -(short_term - 1))
            data_long = ff3_residual.loc[:, long_beg_date:current_date]
            data_short = ff3_residual.loc[:, short_beg_date:current_date]
            data_long = data_long.T.dropna(how='all')
            data_short = data_short.T.dropna(how='all')

            if len(data_long) > effective_term:
                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                data_date = - data_short.std() / data_long.std()
                effective_number = data_long.count()
                data_date[effective_number <= effective_term] = np.nan
                data_date = pd.DataFrame(data_date)
                data_date.columns = [current_date]
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                data_date = pd.DataFrame([], columns=[current_date], index=ff3_residual.index)

            res = pd.concat([res, data_date], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaFF3VolBias()
    self.cal_factor_exposure(beg_date, end_date)
