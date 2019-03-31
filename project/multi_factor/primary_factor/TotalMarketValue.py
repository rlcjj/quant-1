from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.utility.factor_preprocess import FactorPreProcess


def TotalMarketValue(beg_date, end_date):

    """
    计算股票的总市值 = 总股本 * 未复权股价
    """

    # param
    #################################################################################
    factor_name = "TotalMarketValue"
    beg_date = Date().change_to_str(beg_date)
    end_date = Date().change_to_str(end_date)

    # read data
    #################################################################################
    price_unadjust = Stock().read_factor_h5("Price_Unadjust")
    free_share = Stock().read_factor_h5("TotalShare")
    price_unadjust = price_unadjust.ix[:, beg_date:end_date]
    free_share = free_share.ix[:, beg_date:end_date]

    # calculate data
    #################################################################################
    [price_unadjust, free_share] = FactorPreProcess().make_same_index_columns([price_unadjust, free_share])
    free_market_value = price_unadjust.mul(free_share)
    res = free_market_value

    # save data
    ################################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res
    ################################################################################


if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()
    TotalMarketValue(beg_date, end_date)
