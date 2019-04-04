import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaEPTTM(AlphaFactor):

    """
    因子说明: 净利润TTM/总市值 根据最新财报更新数据
    披露日期 为 最近财报
    表明因子估值能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_ep_ttm'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        pe_ttm = Stock().read_factor_h5("PE_ttm")

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(pe_ttm.columns) & set(date_series))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
            data_cur = pe_ttm[current_date]
            data_cur = data_cur[data_cur != 0.0]
            ep_ttm = 1.0 / data_cur
            ep_ttm = pd.DataFrame(ep_ttm.values, columns=[current_date], index=ep_ttm.index)
            res = pd.concat([res, ep_ttm], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaEPTTM()
    self.cal_factor_exposure(beg_date, end_date)
