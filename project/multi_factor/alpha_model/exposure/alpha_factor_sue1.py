import numpy as np
import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaSUE1(AlphaFactor):

    """
    因子说明：盈利超预期因子
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_sue1'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        qfm_num = 12
        net_profit = Stock().read_factor_h5("NetProfitDeducted").T
        report_data = Stock().read_factor_h5("ReportDateDaily")

        result = pd.DataFrame()

        for i in range(qfm_num + 1, len(net_profit)):

            ed_date = net_profit.index[i]
            last_year_date = net_profit.index[i - 4]
            last_date = net_profit.index[i - 1]
            bg_date = net_profit.index[i - qfm_num - 1]
            data_series = net_profit.loc[bg_date:ed_date, :]
            data_diff = data_series - data_series.shift(4)
            data_diff = data_diff.dropna(how='all')
            diff_before = data_diff.loc[bg_date:last_date, :]

            predict_std = diff_before.std()
            predict_profit = data_diff.loc[last_year_date, :]
            result_date = (data_diff.loc[ed_date, :] - predict_profit) / predict_std
            valid = data_diff.count() >= int((qfm_num - 4) / 2)
            result_date[~valid] = np.nan
            result_date = pd.DataFrame(result_date)
            result_date.columns = [ed_date]
            result = pd.concat([result, result_date], axis=1)

        result = result.T.dropna(how="all").T
        sue0 = Stock().change_quarter_to_daily_with_disclosure_date(result, report_data, beg_date, end_date)
        res = sue0.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime

    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaSUE1()
    self.cal_factor_exposure(beg_date, end_date)
