from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaGGLTG(AlphaFactor):

    """
    因子说明: 朝阳永续一致预期复合增长率
    """

    def __init__(self):

        AlphaFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'alpha_raw_gg_ltg'

    def cal_factor_exposure(self, beg_date, end_date):

        """ 计算因子暴露 """

        # read data
        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)
        ltg = Stock().read_factor_h5("LTG_gogoal").T
        ltg = ltg.loc[beg_date:end_date, :].T / 100.0

        # save data
        ltg = ltg.T.dropna(how='all').T
        self.save_alpha_factor_exposure(ltg, self.raw_factor_name)

if __name__ == "__main__":

    from datetime import datetime
    beg_date = '20040101'
    end_date = datetime.today()

    self = AlphaGGLTG()
    self.cal_factor_exposure(beg_date, end_date)
