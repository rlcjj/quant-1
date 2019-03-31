import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaMomentumBias(AlphaFactor):

    """
    因子说明：-240天扣除近60天涨跌幅/近60天涨跌幅
    暂时按照240天扣除近60天涨跌幅计算
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_momentum_bias'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        long_term = 240
        short_term = 60

        # read data
        close = Stock().read_factor_h5("Price_Adjust")

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(close.columns))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            long_date = Date().get_trade_date_offset(current_date, -(long_term - 1))
            short_date = Date().get_trade_date_offset(current_date, -(short_term - 1))

            if (long_date in close.columns) and (short_date in close.columns):
                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                pct_long = close[short_date] / close[long_date] - 1.0
                pct_long = - pd.DataFrame(pct_long.values, columns=[current_date], index=pct_long.index)
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                pct_long = pd.DataFrame([], columns=[current_date], index=close.index)

            res = pd.concat([res, pct_long], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaMomentumBias()
    self.cal_factor_exposure(beg_date, end_date)
