from datetime import datetime
import os
import pandas as pd

from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate
from quant.stock.index import Index
from quant.project.fund_project.fund_selected_department.fund_regression_exposure_index import FundRegressionExposureIndex


class FundRegressionRiskAlphaReturnIndex(object):

    """
    """

    def __init__(self):

        self.data_path = r"E:\3_Data\4_fund_data\9_fund_selected_department\return"
        # self.file_prefix = "Fund_Regression_Risk_Alpha_Index_"
        self.file_prefix = "Fund_Regression_Risk_Alpha_Index_Industry_"
        # self.index_code_list = ["H11006.CSI", "H11008.CSI",
        #                         "801853.SI", "000300.SH", "000905.SH", "000852.SH", "399006.SZ"]
        self.index_code_list = ["H11006.CSI", "H11008.CSI",
                                "CI005909.WI", "CI005910.WI", "CI005911.WI", "CI005912.WI", "CI005913.WI",
                                "CI005914.WI", "CI005915.WI", "CI005916.WI"]

    def cal_fund_regression_risk_alpha_return_index(self, fund, beg_date, end_date):

        # 参数
        ####################################################################
        exposure_index = FundRegressionExposureIndex().get_fund_regression_exposure_index(fund)

        if exposure_index is not None:

            # 取得数据 指数收益率数据 和 基金涨跌幅数据
            ####################################################################
            for i_index in range(len(self.index_code_list)):
                index_code = self.index_code_list[i_index]
                index_return = Index().get_index_factor(index_code, attr=["PCT"])
                if i_index == 0:
                    index_return = Index().get_index_factor(index_code, attr=["PCT"])
                    index_return_all = index_return
                else:
                    index_return_all = pd.concat([index_return_all, index_return], axis=1)

            index_return_all.columns = self.index_code_list

            if fund[len(fund) - 2:] == 'OF':
                fund_return = FundFactor().get_fund_factor("Repair_Nav_Pct", None, [fund]) / 100.0
                fund_return.columns = ["FundReturn"]
            else:
                fund_return = Index().get_index_factor(fund, attr=["PCT"])
                fund_return.columns = ["FundReturn"]

            exposure_index = exposure_index.dropna(how="all")
            index_exposure_return = index_return_all.mul(exposure_index)
            index_exposure_return = index_exposure_return.dropna(how="all")
            data = pd.concat([fund_return, index_exposure_return], axis=1)
            data = data.dropna(how="all")
            data = data.loc[index_exposure_return.index, :]
            data = data.dropna(subset=["FundReturn"])
            data["SumReturn"] = data[self.index_code_list].sum(axis=1, skipna=True)
            data["AlphaReturn"] = data["FundReturn"] - data["SumReturn"]
            data = data.loc[beg_date:end_date, :]
            data["CumFundReturn"] = (data["FundReturn"] + 1.0).cumprod() - 1.0
            data["CumAlphaReturn"] = (data["AlphaReturn"] + 1.0).cumprod() - 1.0
            data["CumSumReturn"] = (data["SumReturn"] + 1.0).cumprod() - 1.0

            # 合并新数据
            ####################################################################
            out_path = self.data_path
            out_file = os.path.join(out_path, self.file_prefix + fund + '.csv')

            if os.path.exists(out_file):
                params_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
                params_old.index = params_old.index.map(str)
                params = FactorOperate().pandas_add_row(params_old, data)
            else:
                params = data
            print(params)
            params.to_csv(out_file)

    def cal_fund_regression_risk_alpha_return_index_all(self, beg_date, end_date,
                                                        fund_pool_file="Stock_Fund_Info.xlsx"):

        file = fund_pool_file
        fund_pool = pd.read_excel(file, index_col=[0])
        fund_pool = list(fund_pool.Code)
        # fund_pool = ["001017.OF", "002263.OF", '229002.OF',
        #              '162213.OF', '001733.OF', '004484.OF', '162216.OF', '162211.OF']

        for i_fund in range(0, len(fund_pool)):
            fund_code = fund_pool[i_fund]
            self.cal_fund_regression_risk_alpha_return_index(fund_code, beg_date, end_date)

    def get_fund_regression_risk_alpha_return_index(self, fund):

        out_path = self.data_path
        out_file = os.path.join(out_path, self.file_prefix + fund + '.csv')
        try:
            exposure = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure.index = exposure.index.map(str)
        except Exception as e:
            exposure = None
        return exposure

    def get_fund_regression_risk_alpha_return_index_date(self, fund, date):

        try:
            exposure = self.get_fund_regression_risk_alpha_return_index(fund)
            exposure = pd.DataFrame(exposure.ix[date, :].values, index=exposure.columns, columns=[fund])
        except Exception as e:
            exposure = None
        return exposure


if __name__ == "__main__":

    #############################################################################################################
    fund = '885012.WI'
    fund = '000001.OF'
    beg_date = "20040101"
    end_date = datetime.today().strftime("%Y%m%d")
    file = r"E:\3_Data\4_fund_data\9_fund_selected_department\fund_pool\Stock_Fund_Info.xlsx"

    FundRegressionRiskAlphaReturnIndex().cal_fund_regression_risk_alpha_return_index_all(beg_date, end_date, file)
    #############################################################################################################

