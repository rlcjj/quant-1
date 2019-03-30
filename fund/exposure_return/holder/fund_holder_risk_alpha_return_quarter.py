import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.barra import Barra
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate
from quant.fund.exposure_return.holder.fund_holder_exposure_quarter import FundHolderExposureQuarter


class FundHolderRiskAlphaReturnQuarter(Data):

    """
    利用半年报持仓信息计算当时基金的BARRA 风格行业收益 和 alpha 收益

    cal_fund_holder_risk_alpha_return_halfyear()
    cal_fund_holder_risk_alpha_return_halfyear_all()
    get_fund_holder_risk_alpha_return_halfyear()

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_barra_exposure'
        self.data_path_exposure = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_fund_holder_risk_alpha_return_quarter(self, fund, end_date):

        """ 根据季报持仓风格暴露进行收益拆分 """

        beg_date = "20040101"
        type_list = ['STYLE', 'COUNTRY', 'INDUSTRY']
        fund_exposure = FundHolderExposureQuarter().get_fund_holder_exposure_quarter_daily(fund, beg_date, end_date)
        barra_riskfactor_return = Barra().get_factor_return(beg_date, end_date, type_list=type_list)
        date_series = Date().get_trade_date_series(beg_date, end_date)
        fund_pct = FundFactor().get_fund_factor("Repair_Nav_Pct", fund_pool=[fund], date_list=date_series)
        fund_pct.columns = ["FundReturn"]

        if fund_exposure is None:
            return None

        fund_riskfactor_return = barra_riskfactor_return.mul(fund_exposure)
        fund_return = pd.concat([fund_pct, fund_riskfactor_return], axis=1)
        fund_return = fund_return.dropna()

        barra_factor_name = list(Barra().get_factor_name(type_list=["STYLE"])["NAME_EN"].values)
        fund_return["StyleReturn"] = fund_return[barra_factor_name].sum(axis=1)
        barra_factor_name = list(Barra().get_factor_name(type_list=["INDUSTRY"])["NAME_EN"].values)
        fund_return["IndustryReturn"] = fund_return[barra_factor_name].sum(axis=1)
        barra_factor_name = list(Barra().get_factor_name(type_list=["COUNTRY"])["NAME_EN"].values)
        fund_return["CountryReturn"] = fund_return[barra_factor_name].sum(axis=1)
        barra_factor_name = ["StyleReturn", "IndustryReturn", "CountryReturn"]
        fund_return["SumReturn"] = fund_return[barra_factor_name].sum(axis=1)
        fund_return["AlphaReturn"] = fund_return["FundReturn"] - fund_return["SumReturn"]

        data_new = fund_return.dropna()

        # 合并新数据
        ####################################################################
        out_path = os.path.join(self.data_path_exposure, 'fund_holding_risk_alpha_return_quarter')
        out_file = os.path.join(out_path, 'Fund_Holder_Risk_Alpha_Return_Quarter_' + fund + "_" + end_date + '.csv')
        print(out_file)

        if os.path.exists(out_file):
            data_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            data_old.index = data_old.index.map(str)
            params = FactorOperate().pandas_add_row(data_old, data_new)
        else:
            params = data_new
        params.to_csv(out_file)
        return data_new

    def cal_fund_holder_risk_alpha_return_quarter_all(self, beg_date="20040101",
                                                      end_date=datetime.today().strftime("%Y%m%d"),
                                                      fund_pool="股票+灵活配置60型基金"):

        """ 根据季报持仓风格暴露进行收益拆分 所有基金 """

        date_series = Date().get_normal_date_series(beg_date, end_date, "Q")

        for i_date in range(0, len(date_series)):

            end_date = date_series[i_date]
            end_date = Date().get_trade_date_series(end_date, 15)
            quarter_date = Date().get_last_fund_quarter_date(end_date)
            fund_pool_list = FundPool().get_fund_pool_code(quarter_date, fund_pool)

            for i_fund in range(0, len(fund_pool_list)):
                fund_code = fund_pool_list[i_fund]
                self.cal_fund_holder_risk_alpha_return_quarter(fund_code, end_date)

    def get_fund_holder_risk_alpha_return_quarter(self, fund, report_date):

        """ 得到季报持仓风格暴露进行收益拆分 """

        out_path = os.path.join(self.data_path_exposure, 'fund_holding_risk_alpha_return_quarter')
        out_file = os.path.join(out_path, 'Fund_Holder_Risk_Alpha_Return_Quarter_' + fund + "_" + report_date + '.csv')
        return_halfyear = pd.read_csv(out_file, index_col=[0], encoding='gbk')
        return_halfyear.index = return_halfyear.index.map(str)
        return return_halfyear


if __name__ == "__main__":

    FundHolderRiskAlphaReturnQuarter().cal_fund_holder_risk_alpha_return_quarter_all("20030630", "20180909")
    FundHolderRiskAlphaReturnQuarter().cal_fund_holder_risk_alpha_return_quarter_all("20030630", "20180929",
                                                                                     fund_pool="量化基金")
