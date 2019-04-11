import os
from datetime import datetime

from quant.stock.index import Index
from quant.project.timing.exposure.timing_factor import TimingFactor


class AverageDiff(TimingFactor):

    """
    均线差（观测指标）
    当短期均线位于上期均线之上的时候持有
    反之，不持有
    """

    def __init__(self):

        TimingFactor.__init__(self)
        self.factor_name = "AverageDiff"

    @staticmethod
    def score_average_diff(x):

        """ 将均线点位差转换成为仓位，在100%和-100%之间 """

        if x >= 0:
            position = 1
        else:
            position = -1

        return position

    def cal_factor_exposure(self, beg_date, end_date, index_code):

        """ 计算指标数值 """

        short_term = 5
        long_term = 90

        data = Index().get_index_factor(index_code, attr=['CLOSE'])
        print("Calculate Timing Factor %s At From %s To %s" % (self.factor_name, beg_date, end_date))
        data['AverageShort'] = data['CLOSE'].rolling(window=short_term).mean()
        data['AverageLong'] = data['CLOSE'].rolling(window=long_term).mean()
        data['Diff'] = data['AverageShort'] - data['AverageLong']
        data = data.dropna()
        data['DiffRatio'] = data['Diff'] / data['CLOSE']
        data['RawTimer'] = data['DiffRatio']
        data['Timer'] = data['RawTimer'].map(self.score_average_diff)

        file = os.path.join(self.data_path, 'exposure', '%s_%s.csv' % (self.factor_name, index_code))
        data = data.dropna(how="all")
        data.to_csv(file)


if __name__ == "__main__":

    beg_date = "20050301"
    end_date = datetime.today().strftime("%Y%m%d")
    index_code = "000300.SH"
    self = AverageDiff()
    self.cal_factor_exposure(beg_date, end_date, index_code)
