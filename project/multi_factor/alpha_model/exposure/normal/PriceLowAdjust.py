from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.utility.factor_preprocess import FactorPreProcess


def PriceLowAdjust(beg_date, end_date):

    """
    因子说明 ：复权最低价格
    """

    # param
    #################################################################################
    factor_name = "PriceLowAdjust"
    beg_date = Date().change_to_str(beg_date)
    end_date = Date().change_to_str(end_date)

    # read data
    #################################################################################
    price_unadjust = Stock().read_factor_h5("PriceLowUnadjust")
    price_facor = Stock().read_factor_h5("AdjustFactor")
    price_unadjust = price_unadjust.ix[:, beg_date:end_date]
    price_facor = price_facor.ix[:, beg_date:end_date]

    # calculate data
    #################################################################################
    [price_unadjust, price_facor] = FactorPreProcess().make_same_index_columns([price_unadjust, price_facor])
    price_adjust = price_unadjust.mul(price_facor)
    res = price_adjust

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))
    return res


if __name__ == "__main__":

    from datetime import datetime
    beg_date = '2002-01-01'
    end_date = datetime.today()
    data = PriceLowAdjust(beg_date, end_date)
    print(data)

