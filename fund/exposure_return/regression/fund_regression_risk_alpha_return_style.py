import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.barra import Barra
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate
from quant.fund.exposure_return.regression.fund_regression_exposure_style import FundRegressionExposureStyle


class FundRegressionRiskAlphaReturnStyle(Data):

    """
    """

    def __init__(self):

        self.regression_exposure_name = 'Fund_Regression_Risk_Alpha_Style'
        self.index_code_list = ["885062.WI", "885008.WI", "801853.SI",
                                "000300.SH", "000905.SH", "000852.SH", "399006.SZ", "399005.SZ"]
        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_barra_exposure'
        self.data_path_exposure = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_fund_regression_risk_alpha_return_style(self, fund, beg_date, end_date):

        # 参数
        ####################################################################
        exposure_index = FundRegressionExposureStyle().get_fund_regression_exposure_style(fund)

        if exposure_index is not None:

            # 取得数据 指数收益率数据 和 基金涨跌幅数据
            ####################################################################
            barra_name = list(Barra().get_factor_name(['STYLE'])['NAME_EN'].values)
            barra_name.extend(list(Barra().get_factor_name(["COUNTRY"])['NAME_EN'].values))

            barra_return = Barra().get_factor_return(None, None, type_list=["INDUSTRY", "COUNTRY", "STYLE"])
            barra_return = barra_return[barra_name]
            barra_return /= 100.0

            if fund[len(fund) - 2:] == 'OF':
                fund_return = FundFactor().get_fund_factor("Repair_Nav_Pct", None, [fund]) / 100.0
                fund_return.columns = ["FundReturn"]
            else:
                fund_return = Index().get_index_factor(fund, attr=["PCT"])
                fund_return.columns = ["FundReturn"]

            exposure_index = exposure_index.dropna(how="all")
            index_exposure_return = barra_return.mul(exposure_index)
            index_exposure_return = index_exposure_return.dropna(how="all")
            data = pd.concat([fund_return, index_exposure_return], axis=1)
            data = data.dropna(how="all")
            data = data.loc[index_exposure_return.index, :]
            data = data.dropna(subset=["FundReturn"])
            data["SumReturn"] = data[barra_name].sum(axis=1, skipna=True)
            data["AlphaReturn"] = data["FundReturn"] - data["SumReturn"]
            data = data.loc[beg_date:end_date, :]
            data["CumFundReturn"] = (data["FundReturn"] + 1.0).cumprod() - 1.0
            data["CumAlphaReturn"] = (data["AlphaReturn"] + 1.0).cumprod() - 1.0
            data["CumSumReturn"] = (data["SumReturn"] + 1.0).cumprod() - 1.0

            # 合并新数据
            ####################################################################
            out_path = os.path.join(self.data_path_exposure, 'fund_regression_risk_alpha_return_style')
            out_file = os.path.join(out_path, 'Fund_Regression_Risk_Alpha_Style_' + fund + '.csv')

            if os.path.exists(out_file):
                params_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
                params_old.index = params_old.index.map(str)
                params = FactorOperate().pandas_add_row(params_old, data)
            else:
                params = data
            print(params)
            params.to_csv(out_file)

    def cal_fund_regression_risk_alpha_return_style_all(self, beg_date, end_date, fund_pool="基金持仓基准基金池"):

        quarter_date = Date().get_last_fund_quarter_date(end_date)
        fund_pool = FundPool().get_fund_pool_code(quarter_date, fund_pool)

        for i_fund in range(200, len(fund_pool)):
            fund_code = fund_pool[i_fund]
            self.cal_fund_regression_risk_alpha_return_style(fund_code, beg_date, end_date)

    def get_fund_regression_risk_alpha_return_style(self, fund):

        out_path = os.path.join(self.data_path_exposure, 'fund_regression_risk_alpha_return_style')
        out_file = os.path.join(out_path, 'Fund_Regression_Risk_Alpha_Style_' + fund + '.csv')
        try:
            exposure = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure.index = exposure.index.map(str)
        except Exception as e:
            exposure = None
        return exposure

    def get_fund_regression_risk_alpha_return_style_date(self, fund, date):

        try:
            exposure = self.get_fund_regression_risk_alpha_return_style(fund)
            exposure = pd.DataFrame(exposure.ix[date, :].values, index=exposure.columns, columns=[fund])
        except Exception as e:
            exposure = None
        return exposure


if __name__ == "__main__":


    fund = '885012.WI'
    # fund = '000001.OF'
    # fund = "881001.WI"
    fund = "000300.SH"
    beg_date = "20040101"
    end_date = datetime.today().strftime("%Y%m%d")
    FundRegressionRiskAlphaReturnStyle().cal_fund_regression_risk_alpha_return_style(fund, beg_date, end_date)
    FundRegressionRiskAlphaReturnStyle().cal_fund_regression_risk_alpha_return_style_all(beg_date, end_date, fund_pool="基金持仓基准基金池")
    # FundRegressionRiskAlphaReturnStyle().cal_fund_regression_risk_alpha_return_style_all(beg_date, end_date, fund_pool="量化基金")
    # FundRegressionRiskAlphaReturnStyle().cal_fund_regression_risk_alpha_return_style_all(beg_date, end_date, fund_pool="东方红基金")
    # FundRegressionRiskAlphaReturnStyle().cal_fund_regression_risk_alpha_return_style_all(beg_date, end_date, fund_pool="指数型基金")

