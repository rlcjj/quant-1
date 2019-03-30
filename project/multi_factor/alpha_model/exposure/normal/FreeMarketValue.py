from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.utility.factor_preprocess import FactorPreProcess


def FreeMarketValue(beg_date, end_date):

    """
    计算股票的自由流通市值 = 自由流通股本 * 未复权股价
    """

    # param
    #################################################################################
    factor_name = "FreeMarketValue"
    beg_date = Date().change_to_str(beg_date)
    end_date = Date().change_to_str(end_date)

    # read data
    #################################################################################
    price_unadjust = Stock().read_factor_h5("Price_Unadjust")
    free_share = Stock().read_factor_h5("Free_FloatShare")
    price_unadjust = price_unadjust.ix[:, beg_date:end_date]
    free_share = free_share.ix[:, beg_date:end_date]

    # calculate data
    #################################################################################
    [price_unadjust, free_share] = FactorPreProcess().make_same_index_columns([price_unadjust, free_share])
    free_market_value = price_unadjust.mul(free_share)
    res = free_market_value
    # free_market_value /= 100000000.0

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    #############################################################################


if __name__ == "__main__":

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    FreeMarketValue(beg_date, end_date)
