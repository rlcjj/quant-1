from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaAverageHolder(AlphaFactor):

    """
    因子说明：- 户均持股比例 = 就是持股户数的倒数
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_average_holder'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        holder = - Stock().read_factor_h5("HolderAvgPct")
        report_data = Stock().read_factor_h5("ReportDateDaily")
        holder = Stock().change_quarter_to_daily_with_disclosure_date(holder, report_data, beg_date, end_date)

        res = holder.T.dropna(how='all').T
        self.save_alpha_factor_exposure(res, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaAverageHolder()
    self.cal_factor_exposure(beg_date, end_date)
