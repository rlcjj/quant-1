from quant.mfc.mfc_load_data import MfcLoadData
from quant.mfc.mfc_get_data import MfcGetData
from quant.mfc.mfc_exposure import MfcExposure


class MfcData(MfcLoadData, MfcExposure, MfcGetData):

    def __init__(self):

        MfcLoadData.__init__(self)
        MfcGetData.__init__(self)
        MfcExposure.__init__(self)


if __name__ == '__main__':

    # params
    ##################################################################################################
    from datetime import datetime
    from quant.stock.date import Date
    date = Date().get_trade_date_offset(datetime.today(), -1)

    # Load Data
    ##################################################################################################
    MfcData().load_network_holding_date(date)
    MfcData().load_network_stock_pool_date(date)
    MfcData().change_holding_date(date)
    MfcData().load_mfc_fund_div()

    # Get Data
    ##################################################################################################
    fund_name = '泰达逆向策略'
    date = '20171229'
    fund_id = 38
    fund_code = '229002.OF'

    print(MfcData().get_fund_asset_period(fund_id, "20171229", "20180120"))
    print(MfcData().get_mfc_private_fund_nav(fund_name))
    print(MfcData().get_mfc_public_fund_nav(fund_code))

    # Mfc Exposure
    ##################################################################################################
    beg_date = "20181031"
    end_date = datetime.today().strftime("%Y%m%d")
    MfcExposure().cal_mfc_holding_barra_exposure_allfund_perieds(beg_date, end_date)
    ##################################################################################################
