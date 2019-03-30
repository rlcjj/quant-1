import os
import pandas as pd

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate
from quant.fund.exposure_return.regression.fund_regression_exposure_index import FundRegressionExposureIndex


class FundRegressionRiskAlphaReturnIndex(Data):

    """
    计算基金在指数上的暴露
    1、可以观察某只基金在指数上的构成
    2、可以进一步用以分解基金收益，求解基金Alpha
    """

    def __init__(self, folder_name="SizeIndex", index_code_list=None):

        Data.__init__(self)
        self.folder_name = folder_name
        self.file_prefix = "IndexReturnDecomposition"
        self.sub_data_path = r'fund_data\fund_exposure\fund_regression_risk_alpha_return_index'
        self.index_return_path = os.path.join(self.primary_data_path, self.sub_data_path, self.folder_name)
        if not os.path.exists(self.index_return_path):
            os.makedirs(self.index_return_path)

        if index_code_list is None:
            self.index_code_list = ["885062.WI", "885008.WI", "801853.SI", "000300.SH",
                                    "000905.SH", "000852.SH", "399006.SZ", "399005.SZ"]
        else:
            self.index_code_list = index_code_list

    def cal_fund_regression_risk_alpha_return_index(self, fund):

        # 参数
        ####################################################################
        exposure_index = FundRegressionExposureIndex().get_fund_regression_exposure_index(fund)

        if exposure_index is not None:

            # 取得数据 指数收益率数据 和 基金涨跌幅数据
            print(fund)
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
            data["CumFundReturn"] = (data["FundReturn"] + 1.0).cumprod() - 1.0
            data["CumAlphaReturn"] = (data["AlphaReturn"] + 1.0).cumprod() - 1.0
            data["CumSumReturn"] = (data["SumReturn"] + 1.0).cumprod() - 1.0

            # 合并新数据
            file = '%s_%s_%s.csv' % (self.file_prefix, self.folder_name, fund)
            out_file = os.path.join(self.index_return_path, file)
            data.to_csv(out_file)

    def cal_fund_regression_risk_alpha_return_index_all(self,
                                                        beg_date,
                                                        end_date,
                                                        fund_pool="指数+主动股票+灵活配置60基金",
                                                        file_rewrite=False):

        quarter_date = Date().get_last_fund_quarter_date(end_date)
        fund_pool = FundPool().get_fund_pool_all(quarter_date, fund_pool)
        fund_pool = fund_pool[fund_pool['if_etf'] == "非ETF基金"]
        fund_pool = fund_pool[fund_pool['if_a'] == "A类基金"]
        fund_pool = fund_pool[fund_pool['if_connect'] == "非联接基金"]
        fund_pool = fund_pool[fund_pool['if_hk'] == "非港股基金"]
        fund_pool = fund_pool.reset_index(drop=True)
        fund_pool.index = fund_pool['wind_code']

        for i_fund in range(0, len(fund_pool)):
            fund_code = fund_pool.index[i_fund]
            fund_name = fund_pool.sec_name[i_fund]
            file = '%s_%s_%s.csv' % (self.file_prefix, self.folder_name, fund_code)
            out_file = os.path.join(self.index_return_path, file)
            if not os.path.exists(out_file) or file_rewrite:
                print(fund_name, fund_code)
                self.cal_fund_regression_risk_alpha_return_index(fund_code)

    def get_fund_regression_risk_alpha_return_index(self, fund):

        file = '%s_%s_%s.csv' % (self.file_prefix, self.folder_name, fund)
        out_file = os.path.join(self.index_return_path, file)
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

    from datetime import datetime
    fund = '885012.WI'
    fund = '000001.OF'
    beg_date = "20040101"
    end_date = datetime.today().strftime("%Y%m%d")

    self = FundRegressionRiskAlphaReturnIndex()
    # print(self.get_fund_regression_risk_alpha_return_index(fund))
    # self.cal_fund_regression_risk_alpha_return_index_all(beg_date, end_date)
    # self.cal_fund_regression_risk_alpha_return_index("160615.OF")
