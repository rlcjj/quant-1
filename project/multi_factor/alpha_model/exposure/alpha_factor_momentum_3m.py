import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaMomentum3m(AlphaFactor):

    """
    因子说明：-1 * 最近3月收益率
    权重为线性加权
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_momentum_3m'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        term = 60
        effective_term = 30

        # read data
        pct = Stock().read_factor_h5("Pct_chg").T

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(pct.index))
        date_series.sort()

        res = pd.DataFrame([])

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            data_period = pct.loc[data_beg_date:current_date, :]
            data_period = data_period.dropna(how='all')
            data_period /= 100.0

            if len(data_period) == term:

                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                momentum = ((data_period + 1.0).cumprod() - 1.0).loc[current_date, :]
                vaild = data_period.count() > effective_term
                momentum[vaild] = np.nan
                momentum = - pd.DataFrame(momentum)
                momentum.columns = [current_date]
                res = pd.concat([res, momentum], axis=1)

            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaMomentum3m()
    self.cal_factor_exposure(beg_date, end_date)
