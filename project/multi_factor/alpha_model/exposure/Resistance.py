import pandas as pd
import numpy as np
from quant.stock.stock import Stock
from quant.stock.date import Date


def Resistance(beg_date, end_date):

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

    # param
    #################################################################################
    LongTerm = 120
    MinimumSize = 96
    factor_name = "Resistance"
    ipo_num = 90

    # read data
    #################################################################################
    price = Stock().read_factor_h5("PriceCloseAdjust")
    trade_amount = Stock().read_factor_h5("TradeAmount")

    # data precessing
    #################################################################################
    [trade_amount, price] = Stock().make_same_index_columns([trade_amount, price])

    # calculate data daily
    #################################################################################
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(set(date_series) & set(price.columns))
    date_series.sort()

    for i in range(0, len(date_series)):

        current_date = date_series[i]
        data_beg_date = Date().get_trade_date_offset(current_date, -(LongTerm-1))
        price_before = price.ix[:, data_beg_date:current_date]
        price_before = price_before.T.dropna(how='all').T
        pct_current = price.ix[:, current_date]
        trade_amount_before = trade_amount.ix[:, data_beg_date:current_date]
        trade_amount_before = trade_amount_before.T.dropna(how='all').T

        if len(price_before) > MinimumSize:
            print('Calculating factor %s at date %s' % (factor_name, current_date))
            price_sub_abs = price_before.sub(pct_current, axis='index').abs()
            W1 = np.log(1/price_sub_abs.mul(1/pct_current, axis='index'))

            # 要扣除价格等于当前价格情况，此情况下空间权为0
            W1[np.isinf(W1)] = 0.0
            N = len(price_before.columns)
            L = len(price_before)

            Weight = np.array(range(1, 1+N)) / np.array(range(1, 1+N)).sum()
            W2 = pd.DataFrame(np.tile(Weight, (L, 1)), index=price_before.index, columns=price_before.columns)

            TotalPower = trade_amount_before.mul(W1).mul(W2)
            Sign = np.sign(price_before.sub(pct_current, axis='index'))
            ResistancePower = Sign.mul(TotalPower)

            ratio = ResistancePower.sum(axis=1) / TotalPower.sum(axis=1)
            ratio = pd.DataFrame(ratio.values, index=ratio.index, columns=[current_date])

        else:
            print('Calculating factor %s at date %s is null' % (factor_name, current_date))
            ratio = pd.DataFrame([], columns=[current_date], index=trade_amount_before.index)

        if i == 0:
            res = ratio
        else:
            res = pd.concat([res, ratio], axis=1)

    res = res.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '2017-01-01'
    end_date = datetime.today()
    data = Resistance(beg_date, end_date)
    print(data)

