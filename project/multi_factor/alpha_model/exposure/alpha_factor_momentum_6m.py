import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaMomentum6m(AlphaFactor):

    """
    因子说明：-1 * 最近1月加权收益率
    权重为线性加权
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_momentum_6m'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        term = 120

        # read data
        pct = Stock().read_factor_h5("Pct_chg").T

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(pct.index))
        date_series.sort()

        res = pd.DataFrame([], columns=date_series, index=pct.columns)

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            data_period = pct.loc[data_beg_date:current_date, :]
            data_period = data_period.dropna(how='all')

            if len(data_period) == term:

                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))

                weight = np.array(list(range(1, term + 1)))
                weight = weight / weight.sum()
                weight_mat = np.transpose(np.tile(weight, (len(data_period.columns), 1)))
                weight_pd = pd.DataFrame(weight_mat, index=data_period.index, columns=data_period.columns)
                weight_pct = weight_pd.mul(data_period)
                data_date = - weight_pct.sum(skipna=False)
                res[current_date] = data_date
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaMomentum6m()
    self.cal_factor_exposure(beg_date, end_date)
