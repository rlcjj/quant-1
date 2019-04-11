import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaAmount60d(AlphaFactor):

    """
    因子说明：过去60个交易日 交易额平均
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_amount_60d'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # params
        term = 60
        short_term = int(term * 0.5)

        # read data
        trade_amount = Stock().read_factor_h5("TradeAmount").T / 100000000
        trade_amount = trade_amount.dropna(how='all')

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(trade_amount.index) & set(date_series))
        date_series.sort()
        res = pd.DataFrame([])

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            amount_before = trade_amount.loc[data_beg_date:current_date, :]
            amount_before = amount_before.fillna(0.0)

            if len(amount_before) == term:

                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                zero_number = amount_before.applymap(lambda x: 1.0 if x == 0.0 else 0.0).sum()
                code_filter_list = (zero_number[zero_number < short_term]).index

                amount_before = trade_amount.loc[data_beg_date:current_date, code_filter_list]
                amount_mean = pd.DataFrame(amount_before.mean())
                amount_mean.columns = [current_date]

            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                amount_mean = pd.DataFrame([], columns=[current_date], index=trade_amount.columns)

            res = pd.concat([res, amount_mean], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaAmount60d()
    self.cal_factor_exposure(beg_date, end_date)
