from quant.stock.stock_factor import StockFactor
from quant.stock.stock_static import StockStatic
from quant.stock.stock_pool import StockPool


class Stock(StockPool, StockStatic, StockFactor):

    def __init__(self):

        StockPool.__init__(self)
        StockStatic.__init__(self)
        StockFactor.__init__(self)


if __name__ == '__main__':

    from datetime import datetime
    date = datetime(2018, 7, 6)

    # StockPool
    ################################################################################

    # StockStatic
    ################################################################################
    Stock().load_trade_status_today()
    print(Stock().get_trade_status_date(date))

    Stock().load_free_market_value_date(date)
    print(Stock().get_free_market_value_date(date))

    Stock().load_ipo_date()
    print(Stock().get_ipo_date())
    ################################################################################

    # StockFactor
    print(Stock().read_factor_h5("Pct_chg"))
    ################################################################################

