import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaAR2E(AlphaFactor):

    """
    因子说明：预收账款 / 净资产
    财报期 最近可以得到的最新财报
    若有一个为负值 结果为负值
    表征了股票的对下游的议价能力
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_ar2e'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        advance = Stock().read_factor_h5("AdvanceReceiptsDaily")
        equity = Stock().read_factor_h5("TotalShareHoldeRequityDaily")

        # data precessing
        [advance, equity] = Stock().make_same_index_columns([advance, equity])

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(advance.columns) & set(equity.columns))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))

            data_date = pd.concat([advance[current_date], equity[current_date]], axis=1)
            data_date.columns = ['advance', 'equity']
            data_date = data_date.dropna()
            data_date = data_date[data_date['equity'] != 0.0]
            data_date['ratio'] = data_date['advance'] / data_date['equity']

            # 只要有一个是负数 比例为负数
            mimus_index = (data_date['advance'] < 0.0) | (data_date['equity'] < 0.0)
            data_date.loc[mimus_index, 'ratio'] = - data_date.loc[mimus_index, 'ratio'].abs()
            res_add = pd.DataFrame(data_date['ratio'])
            res_add.columns = [current_date]

            res = pd.concat([res, res_add], axis=1)

        res = res.T.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name)

if __name__ == '__main__':

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaAR2E()
    self.cal_factor_exposure(beg_date, end_date)
