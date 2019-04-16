import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaNoticeProfitMin(AlphaFactor):

    """
    因子说明：业绩预告中增速下限
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_notice_profit_min'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        notice_min = Stock().read_factor_h5("ProfitNoticeChangeMin")

        # 将披露日期转化成为季报日期
        notice_data = Stock().read_factor_h5("ProfitNoticeDate")
        date_series = Date().get_trade_date_series(beg_date, end_date, "D")
        report_data = pd.DataFrame()

        for i_date in range(len(date_series)):
            date = date_series[i_date]
            before_date = Date().get_trade_date_offset(date, -150)
            print(date)
            location = (notice_data <= int(date)) & (notice_data >= int(before_date))
            res_add = pd.DataFrame(notice_data[location].T.idxmax())
            res_add.columns = [date]
            report_data = pd.concat([report_data, res_add], axis=1)

        notice_min = Stock().change_quarter_to_daily_with_disclosure_date(notice_min, report_data, beg_date, end_date)

        res = notice_min.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20100101'
    end_date = datetime.today()

    self = AlphaNoticeProfitMin()
    self.cal_factor_exposure(beg_date, end_date)
