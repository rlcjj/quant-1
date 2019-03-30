from quant.stock.stock import Stock
from quant.stock.date import Date
import pandas as pd


def IPONormalDays(beg_date, end_date):

    """
    因子说明 ：上市多少自然日
    """

    # param
    #################################################################################
    factor_name = 'IPONormalDays'
    beg_date = Date().change_to_datetime(beg_date)
    end_date = Date().change_to_datetime(end_date)

    # read data
    #################################################################################
    ipo = Stock().get_ipo_date()
    date_series = Date().get_trade_date_series(beg_date, end_date)
    date_series = list(map(Date().change_to_datetime, date_series))

    # data precessing
    #################################################################################
    result = pd.DataFrame([], index=ipo.index, columns=date_series)

    for i_code in range(len(result)):

        code = result.index[i_code]
        print('Calculating factor %s at code %s' % (factor_name, code))
        ipo_date = Date().change_to_datetime(ipo.ix[code, "IPO_DATE"])
        first_date = max(beg_date, ipo_date)
        delist_date = Date().change_to_datetime(ipo.ix[code, "DELIST_DATE"])
        last_date = min(delist_date, end_date)
        result.ix[code, first_date:last_date] = (result.ix[code, first_date:last_date].index - ipo_date).days

    result.columns = list(map(Date().change_to_str, list(result.columns)))

    # save data
    #############################################################################
    Stock().write_factor_h5(result, factor_name, Stock().get_h5_path("my_alpha"))
    return result
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime
    beg_date = '2002-01-01'
    end_date = datetime.today()
    data = IPONormalDays(beg_date, end_date)
    print(data)