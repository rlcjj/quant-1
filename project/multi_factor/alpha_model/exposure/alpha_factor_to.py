import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaTO(AlphaFactor):

    """
    因子说明：换手率 最近1个季度平均
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_to'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        term = 60
        effective_term = int(0.8 * term)

        # read data
        turn_over = Stock().read_factor_h5("TurnOver_Daily").T / 100

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(turn_over.index) & set(date_series))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            bg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            to = turn_over.loc[bg_date:current_date, :]

            if len(to) >= effective_term:
                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                turn_over_mean = to.mean()
                turn_over_mean = pd.DataFrame(turn_over_mean)
                turn_over_mean.columns = [current_date]

            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                turn_over_mean = pd.DataFrame([], columns=[current_date], index=turn_over.columns)

            res = pd.concat([res, turn_over_mean], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaTO()
    self.cal_factor_exposure(beg_date, end_date)
