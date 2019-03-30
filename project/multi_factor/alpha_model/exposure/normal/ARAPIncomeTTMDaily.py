import pandas as pd
from quant.stock.stock import Stock
from quant.stock.date import Date
from quant.stock.stock_factor_operate import StockFactorOperate


def ARAPIncomeTTMDaily(beg_date, end_date):

    """
    因子说明：(预收账款 + 应付账款) / 营业总收入 TTM
    最近一期财报 实时更新
    若有一个为负值 结果为负值
    """

    # param
    #################################################################################
    factor_name = 'ARAPIncomeTTMDaily'
    ipo_num = 90

    # read data
    #################################################################################
    income = Stock().read_factor_h5("OperatingIncome")
    advance = Stock().read_factor_h5("AdvanceReceipts")
    payable = Stock().read_factor_h5("AccountsPayable")

    # data precessing
    #################################################################################
    [advance, payable, income] = Stock().make_same_index_columns([advance, payable, income])

    add = advance.add(payable)
    ratio = add.div(income)
    report_data = Stock().read_factor_h5("ReportDateDaily")
    ratio = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(ratio, report_data, beg_date, end_date)

    res = ratio.T.dropna(how='all').T

    # save data
    #############################################################################
    Stock().write_factor_h5(res, factor_name, Stock().get_h5_path("my_alpha"))

    return res
    #############################################################################


if __name__ == '__main__':

    from datetime import datetime

    beg_date = '2004-01-01'
    end_date = datetime.today()
    data = ARAPIncomeTTMDaily(beg_date, end_date)
    print(data)

