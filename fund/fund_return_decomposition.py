from quant.fund.exposure_return.holder.fund_holder_risk_alpha_return_halfyear import FundHolderRiskAlphaReturnHalfYear
from quant.fund.exposure_return.regression.fund_regression_risk_alpha_return_index import FundRegressionRiskAlphaReturnIndex


class FundReturnDecomposition(FundHolderRiskAlphaReturnHalfYear,
                              FundRegressionRiskAlphaReturnIndex):

    """
    FundHolderExposure()
    利用年度和半年度持仓信息计算当时基金的 Barra 收益拆分

    FundRegressionExposure()
    利用有约束的线性回归的方法推测当前基金的 收益拆分
    """

    def __init__(self):

        FundHolderRiskAlphaReturnHalfYear.__init__(self)
        FundRegressionRiskAlphaReturnIndex.__init__(self)

if __name__ == "__main__":

    from datetime import datetime
    fund = '000001.OF'
    beg_date = "20151231"
    end_date = datetime.today().strftime("%Y%m%d")
    self = FundReturnDecomposition()

    print(self.get_fund_regression_risk_alpha_return_index(fund))
    print(self.get_fund_holder_risk_alpha_return_halfyear(fund, beg_date))
