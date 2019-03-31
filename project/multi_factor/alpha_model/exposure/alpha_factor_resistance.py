import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaResistance(AlphaFactor):

    """
    因子说明：股票上行阻力 国泰君安
    阻力比例  resistance_ratio=resistance_num/power_num
    相当于绝对阻力除以总力量，是-1至1之间数字，1为全部是向上阻力，-1为全部是向下阻力
    绝对阻力  resistance_num=sum(sign(pi-p)*Vi*w1i*w2i)  ,相当于多头阻力减去空头阻力
    双向力量和  power_num=sum(Vi*w1i*w2i)   ，相当于多头阻力加上空头阻力
    其中
    w1i=ln(p/abs(pi-p))，空间距离，价格距离越远作用越小
    w2i=ln(1+i)/ln(1+N),时间距离，价格距离越近作用越大
    pi为i日前价格，Vi为i日交易额，N为时间区间长度

    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_resistance'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # param
        long_term = 120
        effective_term = 96

        # read data
        price = Stock().read_factor_h5("PriceCloseAdjust")
        trade_amount = Stock().read_factor_h5("TradeAmount")

        # data precessing
        [trade_amount, price] = Stock().make_same_index_columns([trade_amount, price])

        # calculate data daily
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(price.columns))
        date_series.sort()
        res = pd.DataFrame()

        for i in range(0, len(date_series)):

            current_date = date_series[i]
            data_beg_date = Date().get_trade_date_offset(current_date, -(long_term - 1))
            price_before = price.loc[:, data_beg_date:current_date]
            price_before = price_before.T.dropna(how='all').T
            pct_current = price.loc[:, current_date]
            trade_amount_before = trade_amount.loc[:, data_beg_date:current_date]
            trade_amount_before = trade_amount_before.T.dropna(how='all').T

            if len(price_before) > effective_term:

                print('Calculating factor %s at date %s' % (self.raw_factor_name, current_date))
                price_sub_abs = price_before.sub(pct_current, axis='index').abs()
                w1 = np.log(1 / price_sub_abs.mul(1 / pct_current, axis='index'))

                # 要扣除价格等于当前价格情况，此情况下空间权为0
                w1[np.isinf(w1)] = 0.0
                n = len(price_before.columns)
                l = len(price_before)

                weight = np.array(range(1, 1 + n)) / np.array(range(1, 1 + n)).sum()
                w2 = pd.DataFrame(np.tile(weight, (l, 1)), index=price_before.index, columns=price_before.columns)

                total_power = trade_amount_before.mul(w1).mul(w2)
                sign = np.sign(price_before.sub(pct_current, axis='index'))
                resistance_power = sign.mul(total_power)

                ratio = resistance_power.sum(axis=1) / total_power.sum(axis=1)
                ratio = pd.DataFrame(ratio.values, index=ratio.index, columns=[current_date])

            else:
                print('Calculating factor %s at date %s is null' % (self.raw_factor_name, current_date))
                ratio = pd.DataFrame([], columns=[current_date], index=trade_amount_before.index)

            res = pd.concat([res, ratio], axis=1)

        res = res.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaResistance()
    self.cal_factor_exposure(beg_date, end_date)
