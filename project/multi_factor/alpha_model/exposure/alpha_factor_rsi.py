import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaRSI(AlphaFactor):

    """
    因子说明： - 28天 RSI （参数太小换手率太高）

    A——N日内收盘涨幅的平均数
    B——N日内收盘跌幅之平均数(取正值)
    N日RSI =A /（A+B）×100
    实际理解为：在某一阶段价格上涨所产生的波动占整个波动的百分比
    感觉有些类似于低波 或者反转
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_rsi'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        term = 28
        effective_term = int(term * 0.8)

        # data
        pct = Stock().read_factor_h5("Pct_chg")

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(pct.columns))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            data_period = pct.ix[:, data_beg_date:current_date]
            data_period = data_period.T.dropna(how='all')

            if len(data_period) > effective_term:

                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                data_positive = data_period[data_period > 0.0].mean()
                data_negative = - data_period[data_period <= 0.0].mean()
                data_sum = data_positive + data_negative
                code_list = data_sum[data_sum != 0.0].index
                data_date = data_positive[code_list] / data_sum[code_list]
                effective_number = data_period.count()
                data_date[effective_number <= effective_term] = np.nan
                data_date = - pd.DataFrame(data_date.values, columns=[current_date], index=data_date.index)
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                data_date = pd.DataFrame([], columns=[current_date], index=pct.index)

            res = pd.concat([res, data_date], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaRSI()
    self.cal_factor_exposure(beg_date, end_date)
