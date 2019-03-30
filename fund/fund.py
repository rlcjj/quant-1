from quant.fund.fund_pool import FundPool
from quant.fund.fund_static import FundStatic
from quant.fund.fund_holder import FundHolder
from quant.fund.fund_factor import FundFactor
from quant.fund.fund_exposure import FundExposure


class Fund(FundStatic,
           FundPool,
           FundHolder,
           FundFactor,
           FundExposure):

    """
    继承多个Fund Class
    FundStatic()
    FundPool()
    FundHolder()
    FundFactor()
    FundStockStyleRatio()
    FundReturnDecomposition()
    """

    def __init__(self):

        FundHolder.__init__(self)
        FundFactor.__init__(self)
        FundPool.__init__(self)
        FundStatic.__init__(self)
        FundExposure.__init__(self)

    def update_fund_data(self, beg_date=None, end_date=None):

        """ 更新所有基金数据 """
        from quant.stock.date import Date
        # Date().load_trade_date_series()

        if end_date is None:
            end_date = Date().change_to_str(datetime.today())
        if beg_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -70)

        Fund().load_findb_sec_info()
        Fund().load_findb_fund_info()
        Fund().load_fund_factor_all(beg_date, end_date)
        Fund().update_fund_holding()

if __name__ == "__main__":

    from datetime import datetime
    fund = '000001.OF'
    beg_date = "20171231"
    end_date = datetime.today().strftime("%Y%m%d")

    Fund().cal_fund_holder_exposure_halfyear(fund, beg_date, end_date)
    Fund().cal_fund_holder_exposure_quarter(fund, beg_date, end_date)

    print(Fund().get_wind_fund_info())
    print(Fund().get_fund_pool_name())
    print(Fund().get_fund_holding_stock_date("20171231"))
    print(Fund().get_fund_factor("Repair_Nav"))
