import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaDailyTsRank9(AlphaFactor):

    """
    高频因子
    ts_rank(rank(low),9)
    首先计算每日股票最低价在股票池内的排名，再计算时间上述排名在最近9天的排名
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'daily_alpha_raw_ts_rank9'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        term = 9

        price_low = Stock().read_factor_h5("Price_Low_Adjust").T
        price_low_rank = price_low.rank(axis=1)

        date_series = Date().get_trade_date_series(beg_date, end_date)
        result = pd.DataFrame([], index=date_series, columns=price_low.columns)

        for i_date in range(len(date_series)):

            data_end_date = date_series[i_date]
            data_beg_date = Date().get_trade_date_offset(data_end_date, - term + 1)
            data_period = price_low_rank.loc[data_beg_date: data_end_date, :]

            if len(data_period) >= term:
                print('Calculating factor %s at date %s' % (self.raw_factor_name, data_end_date))
                ts_rank = data_period.rank().loc[data_end_date, :]
                result.loc[data_end_date, :] = ts_rank
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, data_end_date))

        res = result.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name)


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20190101'
    end_date = datetime.today()

    self = AlphaDailyTsRank9()
    self.cal_factor_exposure(beg_date, end_date)
