import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.utility.time_series_weight import TimeSeriesWeight
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorBarraMomentum(RiskFactor):

    """
    因子说明：长期动量减去短期动量
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'cne5_raw_momentum'
        self.factor_name = 'cne5_normal_momentum'

    @staticmethod
    def update_data():

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # params
        l, t, half_life, min_period = 21, 504, 126, 400

        # read data
        pct = Stock().read_factor_h5("Pct_chg").T
        pct = np.log(pct / 100.0 + 1.0) * 100

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        res_data = pd.DataFrame([])

        for i_date in range(len(date_series)):

            current_date = date_series[i_date]
            data_end = Date().get_trade_date_offset(current_date, -l + 1)
            data_beg = Date().get_trade_date_offset(current_date, -l - t + 2)
            pct_period = pct.loc[data_beg:data_end, :]
            pct_period = pct_period.dropna(how='all')
            count = pct_period.count()

            if len(pct_period) > min_period:
                print('Calculating Barra Risk factor %s at date %s' % (self.factor_name, current_date))
                weight = TimeSeriesWeight().exponential_weight(len(pct_period), half_life)
                weight_mat = np.tile(np.row_stack(weight), (1, len(pct_period.columns)))
                weight_pd = pd.DataFrame(weight_mat, index=pct_period.index, columns=pct_period.columns)
                pct_weight = pct_period.mul(weight_pd)
                mon = pd.DataFrame(pct_weight.sum(skipna=False))
                mon[count < min_period] = np.nan
                mon.columns = [current_date]
                res_data = pd.concat([res_data, mon], axis=1)
            else:
                print('Calculating Barra Risk factor %s at date %s is null' % (self.factor_name, current_date))

        res_data = res_data.T.dropna(how='all').T
        self.save_risk_factor_exposure(res_data, self.raw_factor_name)
        res_data = FactorPreProcess().remove_extreme_value_mad(res_data)
        res_data = FactorPreProcess().standardization(res_data)
        self.save_risk_factor_exposure(res_data, self.factor_name)

if __name__ == '__main__':

    from datetime import datetime
    beg_date = "20040101"
    end_date = datetime.today().strftime("%Y%m%d")

    self = RiskFactorBarraMomentum()
    # self.update_data()
    self.cal_factor_exposure(beg_date, end_date)
