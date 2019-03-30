import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaAmountIR(AlphaFactor):

    """
    因子说明：-1* 过去40天成交额标准差 / 过去40天成交额均值
    成绩额越大越稳定的得分越高
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_amount_ir'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # params
        long_term = 40
        short_term = int(long_term * 0.5)
        min_term = int(long_term * 0.8)

        # read data
        trade_amount = Stock().read_factor_h5("TradeAmount").T
        trade_amount = trade_amount.dropna(how='all')

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(trade_amount.index) & set(date_series))
        date_series.sort()
        res = pd.DataFrame([])

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(long_term - 1))
            amount_before = trade_amount.loc[data_beg_date:current_date, :]
            amount_before = amount_before.fillna(0.0)

            if len(amount_before) >= min_term:

                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                zero_number = amount_before.applymap(lambda x: 1.0 if x == 0.0 else 0.0).sum()
                code_filter_list = (zero_number[zero_number < short_term]).index

                amount_pre = trade_amount.loc[data_beg_date:current_date, code_filter_list]
                amount_pre_cv = - amount_pre.std() / amount_pre.mean()
                amount_pre_cv = pd.DataFrame(amount_pre_cv)
                amount_pre_cv.columns = [current_date]

            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                amount_pre_cv = pd.DataFrame([], columns=[current_date], index=trade_amount.columns)

            res = pd.concat([res, amount_pre_cv], axis=1)

        res = res.T.dropna(how='all').T
        self.save_risk_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaAmountIR()
    self.cal_factor_exposure(beg_date, end_date)
