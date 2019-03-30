import pandas as pd

from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.code_format import CodeFormat
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorGEM(RiskFactor):

    """
    因子说明 是否是创业板
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'risk_raw_gem'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        new_stock_days = 60

        data = Stock().get_ipo_date()
        data.columns = ['ipo', 'delist']
        data = data.astype(str)
        date_series = Date().get_trade_date_series(beg_date, end_date)

        res = pd.DataFrame()

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print('Calculating Barra Risk factor %s at date %s' % (self.raw_factor_name, date))
            new_stock_date = Date().get_trade_date_offset(date, -new_stock_days)
            data_date = data[(data['ipo'] < new_stock_date) & (data['delist'] > date)]
            data_date['GEM'] = data_date.index.map(CodeFormat().get_gem_stock)
            res_date = pd.DataFrame(data_date['GEM'])
            res_date.columns = [date]
            res = pd.concat([res, res_date], axis=1)

        self.save_risk_factor_exposure(res, self.raw_factor_name)


if __name__ == "__main__":

    from datetime import datetime
    beg_date = "20190101"
    end_date = datetime.today().strftime("%Y%m%d")

    self = RiskFactorGEM()
    self.cal_factor_exposure(beg_date, end_date)
