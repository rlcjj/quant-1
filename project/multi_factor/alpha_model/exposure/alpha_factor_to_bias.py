import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaTOBias(AlphaFactor):

    """
    因子说明：60天平均换手率 - 20天平均换手率
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_to_bias'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        long_term = 60
        short_term = 20
        effective_term = int(0.8 * long_term)

        # read data
        turn_over = Stock().read_factor_h5("TurnOver_Daily").T

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(turn_over.index) & set(date_series))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            beg_date_long = Date().get_trade_date_offset(current_date, -(long_term - 1))
            beg_date_short = Date().get_trade_date_offset(current_date, -(short_term - 1))

            to_long = turn_over.loc[beg_date_long:current_date, :]
            to_long = to_long.T.dropna(how='all').T
            to_short = turn_over.loc[beg_date_short:current_date, :]
            to_short = to_short.T.dropna(how='all').T

            if len(to_long) >= effective_term:
                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                turn_over_diff = to_long.mean() - to_short.mean()
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                turn_over_diff = pd.DataFrame([], columns=[current_date], index=turn_over.columns)

            res = pd.concat([res, turn_over_diff], axis=1)

        res = res.T.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaTOBias()
    self.cal_factor_exposure(beg_date, end_date)
