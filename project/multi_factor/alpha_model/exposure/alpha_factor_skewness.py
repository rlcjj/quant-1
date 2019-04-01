import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaSkewness(AlphaFactor):

    """
    因子说明： -1 * 偏度
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_skewness'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        term = 150
        effective_term = 120

        # read data
        pct = Stock().read_factor_h5("Pct_chg")

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(pct.columns) & set(date_series))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            pct_before = pct.ix[:, data_beg_date:current_date]
            pct_stock = pct_before.T.dropna(how='all')

            if len(pct_stock) > effective_term:
                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                skew_date = - pct_stock.skew()
                effective_number = pct_stock.count()
                skew_date[effective_number <= effective_term] = np.nan
                skew_date = pd.DataFrame(skew_date.values, columns=[current_date], index=skew_date.index)
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                skew_date = pd.DataFrame([], columns=[current_date], index=pct.index)

            res = pd.concat([res, skew_date], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaSkewness()
    self.cal_factor_exposure(beg_date, end_date)
