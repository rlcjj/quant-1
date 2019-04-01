import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaInflow2FreeP(AlphaFactor):

    """
    因子说明：过去 10天 资金净流入额/自由流通市值
    流入为当日成交价上升的时候的成交额和成交量 流出为当日成交价下降时候的成交额和成交量
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_inflow2freep'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        term = 10
        effective_term = int(0.8 * term)

        # read data
        inflow = Stock().read_factor_h5("Mf_Inflow")
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")
        free_share = Stock().read_factor_h5("Free_FloatShare")

        # calculate data
        [price_unadjust, free_share] = Stock().make_same_index_columns([price_unadjust, free_share])
        free_mv = price_unadjust.mul(free_share)
        [inflow, free_mv] = Stock().make_same_index_columns([inflow, free_mv])
        inflow = inflow.T
        free_mv = free_mv.T

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(inflow.index))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(term - 1))
            inflow_pre = inflow.loc[data_beg_date:current_date, :]
            free_mv_pre = free_mv.loc[data_beg_date:current_date, :]

            if len(inflow_pre) >= effective_term:

                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                inflow_pre_sum = inflow_pre.sum()
                free_mv_pre_sum = free_mv_pre.sum()
                date_data = pd.concat([inflow_pre_sum, free_mv_pre_sum], axis=1)
                date_data.columns = ['inflow', 'free_mv']
                date_data = date_data[date_data['free_mv'] != 0.0]
                date_data['ratio'] = date_data['inflow'] / date_data['free_mv']
                date_data = pd.DataFrame(date_data['ratio']) * 100
                date_data.columns = [current_date]
            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                date_data = pd.DataFrame([], columns=[current_date], index=free_mv.columns)

            res = pd.concat([res, date_data], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaInflow2FreeP()
    self.cal_factor_exposure(beg_date, end_date)
