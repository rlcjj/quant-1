from quant.fund.exposure_return.holder.fund_holder_exposure_quarter import FundHolderExposureQuarter
from quant.fund.exposure_return.holder.fund_holder_exposure_halfyear import FundHolderExposureHalfYear
from quant.fund.exposure_return.regression.fund_regression_exposure_index import FundRegressionExposureIndex
from quant.fund.exposure_return.regression.fund_regression_exposure_style import FundRegressionExposureStyle


class FundExposure(FundHolderExposureHalfYear,
                   FundRegressionExposureIndex):

    """
    FundHolderExposure()
    利用年度和半年度持仓信息计算当时基金的 Barra 因子暴露

    FundRegressionExposure()
    利用有约束的线性回归的方法推测当前基金的 Barra 风格暴露
    """

    def __init__(self):

        FundHolderExposureHalfYear.__init__(self)
        FundRegressionExposureIndex.__init__(self)

if __name__ == "__main__":

    from datetime import datetime
    fund = '000001.OF'
    beg_date = "20151231"
    end_date = datetime.today().strftime("%Y%m%d")
    self = FundExposure()

    self.get_fund_holder_exposure_halfyear_date(fund, beg_date)
    self.get_fund_regression_exposure_index_date(fund, end_date)
