import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.barra import Barra
from quant.fund.fund_pool import FundPool
from quant.fund.fund_holder import FundHolder
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate


class FundHolderExposureHalfYear(Data):

    """
    利用半年报持仓信息计算当时基金的BARRA因子暴露
    这里的暴露值为全仓暴露值 还要得到基金仓位

    cal_fund_holder_exposure_halfyear()
    cal_fund_holder_exposure_halfyear_all()

    get_fund_holder_exposure_halfyear()
    get_fund_holder_exposure_halfyear_date()

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_exposure\fund_holding_exposure_halfyear'
        self.halfyear_exposure_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_fund_holder_exposure_halfyear(self, fund_code, beg_date, end_date):

        """ 计算单个基金的半年持仓暴露（注意计算的是非满仓暴露） """

        # fund_code, beg_date, end_date = "000001.OF", "20170101", "20190101"

        type_list = ['COUNTRY', 'STYLE', 'INDUSTRY']
        barra_name = list(Barra().get_factor_name(type_list)['NAME_EN'].values)
        out_file = os.path.join(self.halfyear_exposure_path, 'Fund_Holder_Exposure_HalfYear_%s.csv' % fund_code)

        if not os.path.exists(out_file):
            beg_date = "20040101"

        date_series = Date().get_normal_date_series(beg_date, end_date, period='S')
        fund_holding = FundHolder().get_fund_stock_weight_halfyear(fund_code)

        if fund_holding is not None:
            date_series = list(set(date_series) & set(fund_holding.columns))
            date_series.sort()
            print(date_series)
        else:
            return None

        if len(date_series) > 0:

            for i_date in range(0, len(date_series)):

                date = date_series[i_date]
                report_date = Date().get_normal_date_month_end_day(date)
                trade_date = Date().get_trade_date_month_end_day(date)
                print("Calculate HalfYear Holder Exposure %s %s" % (fund_code, report_date))

                barra_exposure = Barra().get_factor_exposure_date(trade_date, type_list)
                fund_holding_date = FundHolder().get_fund_stock_weight_halfyear(fund_code)

                if (barra_exposure is None) or (len(fund_holding_date) == 0):
                    exposure_add = pd.DataFrame([], columns=barra_name, index=[report_date])
                else:
                    fund_holding_date = pd.DataFrame(fund_holding[report_date])
                    fund_holding_date = fund_holding_date.dropna()
                    fund_holding_date = fund_holding_date.sort_values(by=[report_date], ascending=False)
                    fund_holding_date.columns = ["Weight"]
                    fund_holding_date /= 100.0
                    data = pd.concat([fund_holding_date, barra_exposure], axis=1)
                    data = data.dropna()

                    if (len(data) == 0) or (data is None):
                        exposure_add = pd.DataFrame([], columns=barra_name, index=[report_date])
                    else:
                        exposure_add = pd.DataFrame([], columns=barra_name, index=[report_date])

                        for i_factor in range(len(barra_name)):

                            factor_name = barra_name[i_factor]
                            data_weight = data[['Weight', factor_name]]
                            data_weight['StockExposure'] = data_weight['Weight'] * data_weight[factor_name]
                            exp = data_weight['StockExposure'].sum()
                            exposure_add.ix[report_date, factor_name] = exp

                        country_name = Barra().get_factor_name(["COUNTRY"])["NAME_EN"].values[0]
                        position = FundFactor().get_fund_factor("Stock_Ratio", date_list=[report_date],
                                                                fund_pool=[fund_code])
                        exposure_add.ix[report_date, country_name] = position.values[0][0] / 100

                if i_date == 0:
                    exposure_new = exposure_add
                else:
                    exposure_new = pd.concat([exposure_new, exposure_add], axis=0)
        else:
            exposure_new = pd.DataFrame([])

        # 合并新数据
        ####################################################################
        if os.path.exists(out_file):
            exposure_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure_old.index = exposure_old.index.map(str)
            params = FactorOperate().pandas_add_row(exposure_old, exposure_new)
        else:
            params = exposure_new

        if len(params) > 0:
            params = params[barra_name]
        params.to_csv(out_file)

    def cal_fund_holder_exposure_halfyear_all(self,
                                              beg_date="19991231",
                                              end_date=datetime.today(),
                                              fund_pool="股票+灵活配置60型基金"):

        """ 计算所有基金的半年持仓暴露（注意计算的是非满仓暴露） """

        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)

        quarter_date = Date().get_last_fund_quarter_date(end_date)
        fund_pool = FundPool().get_fund_pool_code(quarter_date, fund_pool)

        for i_fund in range(0, len(fund_pool)):
            fund_code = fund_pool[i_fund]
            self.cal_fund_holder_exposure_halfyear(fund_code, beg_date, end_date)

    def get_fund_holder_exposure_halfyear(self,
                                          fund_code,
                                          type_list=['STYLE', 'COUNTRY', 'INDUSTRY']):

        """ 得到单个基金的所有半年持仓暴露（注意计算的是非满仓暴露） """

        out_file = os.path.join(self.halfyear_exposure_path, 'Fund_Holder_Exposure_HalfYear_%s.csv' % fund_code)
        try:
            exposure = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure.index = exposure.index.map(str)

            factor_name = Barra().get_factor_name(type_list=type_list)
            factor_name = list(factor_name["NAME_EN"].values)
            exposure = exposure[factor_name]
        except Exception as e:
            exposure = pd.DataFrame([])

        return exposure

    def get_fund_holder_exposure_halfyear_date(self,
                                               fund_code,
                                               date,
                                               type_list=['STYLE', 'COUNTRY', 'INDUSTRY']):

        """ 得到单个基金的在某个时间点半年持仓暴露（注意计算的是非满仓暴露） """

        date = Date().get_normal_date_month_end_day(date)
        try:
            exposure = self.get_fund_holder_exposure_halfyear(fund_code, type_list)
            exposure_date = exposure.ix[date, :]
            exposure_date = pd.DataFrame(exposure_date.values, index=exposure_date.index, columns=[fund_code]).T
        except Exception as e:
            exposure_date = None
        return exposure_date

    def get_fund_holder_exposure_halfyear_daily(self,
                                                fund_code, beg_date, end_date,
                                                type_list=['STYLE', 'COUNTRY', 'INDUSTRY']):

        """ 得到单个基金的在一段时间点半年持仓暴露（注意计算的是非满仓暴露） """

        exposure = self.get_fund_holder_exposure_halfyear(fund_code, type_list=type_list)
        if exposure is None or len(exposure) == 0:
            return None
        date_series = Date().get_trade_date_series(beg_date, end_date)
        exposure_daily = pd.DataFrame([], index=date_series, columns=exposure.columns)
        quarter_date = Date().get_last_fund_quarter_date(end_date)
        exposure = exposure.loc[:quarter_date, :]

        for i_date in range(len(exposure.index)):

            report_date = exposure.index[i_date]
            publish_date = Date().get_trade_date_offset(report_date, 60)
            exposure_daily.loc[publish_date, :] = exposure.loc[report_date, :]

        exposure_daily = exposure_daily.sort_index()
        exposure_daily = exposure_daily.fillna(method="pad")
        exposure_daily = exposure_daily.loc[beg_date:end_date, :]
        exposure_daily = exposure_daily.dropna()
        return exposure_daily


if __name__ == "__main__":

    self = FundHolderExposureHalfYear()
    type_list = ['STYLE', 'COUNTRY', 'INDUSTRY']
    fund_code, beg_date, end_date = "000001.OF", "20170101", "20190101"

    # 计算
    # self.cal_fund_holder_exposure_halfyear("000001.OF", "20170930", "20180808")
    self.cal_fund_holder_exposure_halfyear_all(beg_date="20180130", end_date=datetime.today())

    # 获取
    print(self.get_fund_holder_exposure_halfyear("000001.OF"))
    print(self.get_fund_holder_exposure_halfyear_date("000001.OF", "20170630"))
    print(self.get_fund_holder_exposure_halfyear_daily("000001.OF", "20180228", "20180809")['ChinaEquity'])


