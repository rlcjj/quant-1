import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.barra import Barra
from quant.mfc.mfc_get_data import MfcGetData
from quant.utility.code_format import CodeFormat
from quant.utility.factor_operate import FactorOperate


class MfcExposure(Data):

    """
    计算,获取泰达基金的 Barra 因子暴露(满仓的暴露值)

    cal_mfc_holding_barra_exposure_date()
    cal_mfc_holding_barra_exposure_perieds()
    cal_mfc_holding_barra_exposure_allfund_perieds()

    get_barra_exposure()
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\exposure'
        self.exposure_data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    @staticmethod
    def cal_mfc_holding_barra_exposure_date(fund_name, date):

        """ 计算某只基金在某天的暴露 """

        date = Date().get_trade_date_offset(date, 0)
        type_list = ["STYLE", "COUNTRY", "INDUSTRY"]

        try:
            holding_data = MfcGetData().get_fund_security(date)
            holding_data = holding_data[["基金名称", "证券代码", "市值", '证券类别']]
            holding_data = holding_data[holding_data["基金名称"] == fund_name]
            holding_data = holding_data[holding_data['证券类别'] == "股票"]
            holding_data.columns = ["FundName", "StockCode", "Weight", 'Type']

            exposure = Barra().get_factor_exposure_date(date, type_list=type_list)
            holding_data['Weight'] = holding_data['Weight'] / holding_data['Weight'].sum()
            holding_data.StockCode = holding_data.StockCode.map(CodeFormat().stock_code_add_postfix)
            holding_data.index = holding_data.StockCode
            weight = holding_data

            data = pd.concat([weight, exposure], axis=1)
            data = data.sort_values(by=['Weight'], ascending=True)
            data = data.dropna(subset=["Weight"])
            res = pd.DataFrame([], columns=exposure.columns, index=[date])

            if data['Weight'].sum() > 0.0:
                for i_col in range(len(exposure.columns)):
                    risk_factor_name = exposure.columns[i_col]
                    exposure_sum = (data["Weight"] * data[risk_factor_name]).sum()
                    res.ix[date, risk_factor_name] = exposure_sum / data['Weight'].sum()
                print(" Calculate Mfcteda Fund %s Barra Exposure at %s" % (fund_name, date))
            else:
                print(" Calculate Mfcteda Fund %s At %s of Weight Stock is Zero" % (fund_name, date))
            return res

        except Exception as e:
            print(" Calculate Mfcteda Fund %s Barra Exposure at %s is Null " % (fund_name, date))
            name = Barra().get_factor_name(type_list=type_list)
            res = pd.DataFrame([], columns=list(name.NAME_EN.values), index=[date])
            return res

    def cal_mfc_holding_barra_exposure_period(self, fund_name, beg_date, end_date):

        """ 计算某只基金在一段时间内暴露 """

        date_series_daily = Date().get_trade_date_series(beg_date, end_date)
        new_data = pd.DataFrame()

        for i_date in range(len(date_series_daily)):
            date = date_series_daily[i_date]
            res = self.cal_mfc_holding_barra_exposure_date(fund_name, date)
            new_data = pd.concat([new_data, res], axis=0)

        out_file = os.path.join(self.exposure_data_path, "MfcRiskExposure_" + fund_name + '.csv')
        if os.path.exists(out_file):
            data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
            data.index = data.index.map(str)
            data = FactorOperate().pandas_add_row(data, new_data)
        else:
            data = new_data

        type_list = ["STYLE", "COUNTRY", "INDUSTRY"]
        name = Barra().get_factor_name(type_list=type_list)
        data = data[list(name.NAME_EN.values)]
        data.to_csv(out_file)

    def cal_mfc_holding_barra_exposure_allfund_perieds(self, beg_date, end_date):

        """ 计算所有基金在一段时间内暴露 """

        fund_info = MfcGetData().get_mfc_fund_info()
        fund_info = fund_info.dropna(subset=["Manager"])
        for i_fund in range(0, len(fund_info.Name)):
            fund_name = fund_info.Name[i_fund]
            self.cal_mfc_holding_barra_exposure_period(fund_name, beg_date, end_date)

    def get_mfc_holding_barra_exposure(self, fund_name, beg_date, end_date):

        """ 得到某只基金在一段时间内暴露 """

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        file = os.path.join(self.exposure_data_path, "MfcRiskExposure_" + fund_name + '.csv')
        data = pd.read_csv(file, encoding='gbk', index_col=[0])
        data.index = data.index.map(str)
        data = data.loc[beg_date:end_date, :]
        data = data.dropna()

        return data

    def get_mfc_holding_barra_exposure_date(self, fund_name, date, type_list=["STYLE"]):

        """ 计算某只基金在某天的暴露 """

        date = Date().change_to_str(date)
        file = os.path.join(self.exposure_data_path, "MfcRiskExposure_" + fund_name + '.csv')
        data = pd.read_csv(file, encoding='gbk', index_col=[0])
        data.index = data.index.map(str)
        barra_name = list(Barra().get_factor_name(type_list)['NAME_EN'].values)

        try:
            data = data.loc[date, barra_name]
            data = pd.DataFrame(data.values, index=data.index, columns=[fund_name]).T
        except Exception as e:
            print(e)
            data = pd.DataFrame([])
        return data

    @staticmethod
    def cal_mfc_holding_alpha_exposure_date(fund_name, factor_name_list, date):

        """ 计算泰达持仓对alpha因子的暴露（满仓）"""

        from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor
        date = Date().get_trade_date_offset(date, 0)

        try:
            holding_data = MfcGetData().get_fund_security(date)
            holding_data = holding_data[["基金名称", "证券代码", "市值", '证券类别']]
            holding_data = holding_data[holding_data["基金名称"] == fund_name]
            holding_data = holding_data[holding_data['证券类别'] == "股票"]
            holding_data.columns = ["FundName", "StockCode", "Weight", 'Type']
            holding_data['Weight'] = holding_data['Weight'] / holding_data['Weight'].sum()
            holding_data.StockCode = holding_data.StockCode.map(CodeFormat().stock_code_add_postfix)
            holding_data.index = holding_data.StockCode
            weight = holding_data

            exposure = pd.DataFrame()

            for factor_name in factor_name_list:
                alpha = AlphaFactor().get_alpha_factor_exposure(factor_name)
                exposure_add = pd.DataFrame(alpha[date])
                exposure_add.columns = [factor_name]
                exposure = pd.concat([exposure, exposure_add], axis=1)

            data = pd.concat([weight, exposure], axis=1)
            data = data.sort_values(by=['Weight'], ascending=True)
            data = data.dropna(subset=["Weight"])
            res = pd.DataFrame([], columns=factor_name_list, index=[date])

            if data['Weight'].sum() > 0.0:
                for i_col in range(len(exposure.columns)):
                    factor_name = exposure.columns[i_col]
                    data_factor = data[["Weight", factor_name]]
                    data_factor = data_factor.dropna()
                    exposure_sum = (data_factor["Weight"] * data_factor[factor_name]).sum()
                    res.loc[date, factor_name] = exposure_sum / data['Weight'].sum()
                print(" Calculate Mfcteda Fund %s Alpha Exposure at %s" % (fund_name, date))
            else:
                print(" Calculate Mfcteda Fund %s At %s of Weight Stock is Zero" % (fund_name, date))
            return res

        except Exception as e:
            print(" Calculate Mfcteda Fund %s Alpha Exposure at %s is Null " % (fund_name, date))
            res = pd.DataFrame([], columns=factor_name_list, index=[date])
            return res

    def cal_mfc_holding_alpha_exposure_period(self, fund_name, factor_name_list, beg_date, end_date):

        """ 计算某只基金在一段时间内暴露 """

        date_series_daily = Date().get_trade_date_series(beg_date, end_date)
        new_data = pd.DataFrame()

        for i_date in range(len(date_series_daily)):
            date = date_series_daily[i_date]
            res = self.cal_mfc_holding_alpha_exposure_date(fund_name, factor_name_list, date)
            new_data = pd.concat([new_data, res], axis=0)

        out_file = os.path.join(self.exposure_data_path, "MfcAlphaExposure_" + fund_name + '.csv')
        if os.path.exists(out_file):
            data = pd.read_csv(out_file, encoding='gbk', index_col=[0])
            data.index = data.index.map(str)
            data = FactorOperate().pandas_add_row(data, new_data)
        else:
            data = new_data

        data = data[factor_name_list]
        data.to_csv(out_file)

    def cal_mfc_holding_alpha_exposure_allfund_period(self, beg_date, end_date, factor_name_list):

        """ 计算所有基金在一段时间内暴露 """

        fund_info = MfcGetData().get_mfc_fund_info()
        fund_info = fund_info.dropna(subset=["Manager"])
        for i_fund in range(0, len(fund_info.Name)):
            fund_name = fund_info.Name[i_fund]
            self.cal_mfc_holding_alpha_exposure_period(fund_name, factor_name_list, beg_date, end_date)

    def get_mfc_holding_alpha_exposure(self, fund_name, beg_date, end_date):

        """ 得到某只基金在一段时间内暴露 """

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        file = os.path.join(self.exposure_data_path, "MfcAlphaExposure_" + fund_name + '.csv')
        data = pd.read_csv(file, encoding='gbk', index_col=[0])
        data.index = data.index.map(str)
        data = data.loc[beg_date:end_date, :]
        data = data.dropna(how="all")

        return data

    def get_mfc_holding_alpha_exposure_date(self, fund_name, date):

        """ 计算某只基金在某天的暴露 """

        date = Date().change_to_str(date)
        file = os.path.join(self.exposure_data_path, "MfcAlphaExposure_" + fund_name + '.csv')
        data = pd.read_csv(file, encoding='gbk', index_col=[0])
        data.index = data.index.map(str)

        try:
            data = data.loc[date, :]
            data = pd.DataFrame(data.values, index=data.index, columns=[fund_name]).T
        except Exception as e:
            print(e)
            data = pd.DataFrame([])
        return data

if __name__ == '__main__':

    """ 参数 """

    beg_date = "20160101"
    end_date = datetime.today().strftime("%Y%m%d")
    factor_name_list = ["alpha_raw_bp", "alpha_raw_roe", "alpha_raw_sue0"]
    fund_name = "泰达逆向策略"
    date = "20181228"
    self = MfcExposure()

    """ 计算 Risk Barra Exposure """

    # self.cal_mfc_holding_barra_exposure_allfund_perieds(beg_date, end_date)
    # self.cal_mfc_holding_barra_exposure_perieds("泰达逆向策略", beg_date, end_date)
    # print(self.get_mfc_holding_barra_exposure_date("泰达逆向策略", "20171229"))
    # print(self.get_mfc_holding_barra_exposure("泰达逆向策略", beg_date, end_date))

    """ 计算 Alpha Barra Exposure """
    self.cal_mfc_holding_alpha_exposure_allfund_period("20190301", end_date, factor_name_list)
    self.cal_mfc_holding_alpha_exposure_period("泰达逆向策略", factor_name_list, beg_date, end_date)
    print(self.get_mfc_holding_alpha_exposure_date("泰达逆向策略", "20171229"))
    print(self.get_mfc_holding_alpha_exposure("泰达逆向策略", beg_date, end_date))