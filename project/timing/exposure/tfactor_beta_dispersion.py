import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.timing.exposure.timing_factor import TimingFactor


class BetaDispersion(TimingFactor):

    """
    按照当月平均 beta值 排序
    前10% 的平均beta - 后10%的平均beta
    股票池是所有股票作为股票池 也可以挑选其他的股票池
    """

    def __init__(self):

        TimingFactor.__init__(self)
        self.factor_name = "BetaDispersion"

    def cal_factor_exposure(self, beg_date, end_date):

        month_days = 20

        data = Stock().read_factor_h5("Beta", Stock().get_h5_path('my_alpha'))
        data_mean = data.T.rolling(month_days).median()

        trade_date_series = Date().get_trade_date_series(beg_date, end_date, "M")
        data_month = data_mean.loc[trade_date_series, :]

        beta_dis = pd.DataFrame([], index=trade_date_series)

        for i_date in range(len(data_month)):

            date = data_month.index[i_date]
            data_series = data_month.loc[date, :]
            data_series = data_series.dropna()
            data_series = data_series[data_series > 0]

            try:
                # data_series = FactorPreProcess().remove_extreme_value_mad(data_series)

                data_series = data_series.sort_values()
                location = int(np.floor(len(data_month) * 0.15))
                min_value = data_series[0:location].max()

                data_series = data_series.sort_values(ascending=False)
                location = int(np.floor(len(data_month) * 0.15))
                max_value = data_series[0:location].min()

                beta_dis.loc[date, "MaxMeanBeta"] = max_value
                beta_dis.loc[date, "MinMeanBeta"] = min_value
                beta_dis.loc[date, "DiffBeta"] = max_value - min_value
                print("Cal Timing Factor %s At %s " % (self.factor_name, date))

            except Exception as e:
                print(e)
                print("Cal Timing Factor %s At %s is Empty " % (self.factor_name, date))

        beta_dis['TimeDiffBeta'] = beta_dis["DiffBeta"] - beta_dis['DiffBeta'].shift(1)

        # 历史分位数
        for i_date in range(36, len(data_month)):

            data_end_date = data_month.index[i_date]
            data_beg_date = data_month.index[i_date - 36]
            beta_period = beta_dis.loc[data_beg_date:data_end_date, :]
            beta_period = beta_period.dropna(subset=['TimeDiffBeta'])
            beta_period['TimeDiffBetaRank'] = beta_period['TimeDiffBeta'].rank() / len(beta_period)

            try:
                rank_pct = beta_period.loc[data_end_date, 'TimeDiffBetaRank']
                beta_dis.loc[data_end_date, "TimeDiffBetaRank"] = rank_pct

                if np.isnan(rank_pct):
                    beta_dis.loc[data_end_date, "Timer"] = np.nan
                elif rank_pct < 0.33:
                    beta_dis.loc[data_end_date, "Timer"] = -1
                elif rank_pct >= 0.67:
                    beta_dis.loc[data_end_date, "Timer"] = 1
                else:
                    beta_dis.loc[data_end_date, "Timer"] = 0

            except Exception as e:
                print(e)
                beta_dis.loc[data_end_date, "Timer"] = np.nan

        file = os.path.join(self.data_path, 'exposure', '%s.csv' % self.factor_name)
        beta_dis = beta_dis.dropna(how="all")
        beta_dis.to_csv(file)


if __name__ == "__main__":

    beg_date = "20050301"
    end_date = datetime.today().strftime("%Y%m%d")
    self = BetaDispersion()
    self.cal_factor_exposure(beg_date, end_date)
