import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaIlliquidity(AlphaFactor):

    """
    因子说明：非流动性=涨跌幅的绝对值 / 交易额
    20天均值
    有的交易额很小 去掉异常值
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_illiquidity'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        long_term = 20
        effective_term = int(long_term / 2)
        extreme_value = 80

        # read data
        pct = Stock().read_factor_h5("Pct_chg").T
        trade_amount = Stock().read_factor_h5("TradeAmount").T / 100000000

        # data precessing
        [pct, trade_amount] = Stock().make_same_index_columns([pct, trade_amount])
        trade_amount = trade_amount.fillna(0.0)

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(pct.index))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(long_term - 1))
            trade_amount_before = trade_amount.loc[data_beg_date:current_date, :]

            if len(trade_amount_before) > effective_term:
                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                zero_number = trade_amount_before.applymap(lambda x: 1.0 if x == 0.0 else 0.0).sum()
                code_filter_list = (zero_number[zero_number < effective_term]).index
                amount_before = trade_amount.loc[data_beg_date:current_date, code_filter_list]
                pct_before = pct.loc[data_beg_date:current_date, code_filter_list]
                iq = pct_before.abs().div(amount_before)
                iq[iq > extreme_value] = np.nan
                bias = iq.mean()
                bias = pd.DataFrame(bias)
                bias.columns = [current_date]
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                bias = pd.DataFrame([], columns=[current_date], index=trade_amount_before.columns)

            res = pd.concat([res, bias], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaIlliquidity()
    self.cal_factor_exposure(beg_date, end_date)
