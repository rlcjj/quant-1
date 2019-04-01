from quant.stock.stock import Stock


class AlphaFactorTest(object):

    def __init__(self):

        pass

    def get_cross_pct_std(self):

        """
        计算在每个横截面股票的收益率的波动率
        """
        pct = Stock().read_factor_h5("Pct_chg").T
        pct /= 100.0
        pct_std = pct.std(axis=1)
        print(pct_std.mean())
        pct_std.plot()

