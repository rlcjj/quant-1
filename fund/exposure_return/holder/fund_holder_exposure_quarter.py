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


class FundHolderExposureQuarter(Data):

    """
    利用季报持仓信息计算当时基金的BARRA因子暴露
    这里的暴露值为仓位暴露值 还要得到基金仓位

    cal_fund_holder_exposure_quarter()
    cal_fund_holder_exposure_quarter_all()
    get_fund_holder_exposure_quarter()

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_barra_exposure'
        self.data_path_exposure = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_fund_holder_exposure_quarter(self, fund, beg_date, end_date):

        """  计算单个基金的季度持仓暴露 (前十大重仓暴露) """

        type_list = ['STYLE', 'COUNTRY', 'INDUSTRY']
        date_series = Date().get_normal_date_series(beg_date, end_date, period='Q')
        fund_holding = FundHolder().get_fund_stock_weight_quarter(fund)

        if fund_holding is not None:
            date_series = list(set(date_series) & set(fund_holding.columns))
            date_series.sort()
        else:
            return None

        for i_date in range(0, len(date_series)):

            date = date_series[i_date]
            report_date = Date().get_normal_date_month_end_day(date)
            trade_date = Date().get_trade_date_month_end_day(date)

            barra_name = list(Barra().get_factor_name(type_list)['NAME_EN'].values)
            barra_exposure = Barra().get_factor_exposure_date(trade_date, type_list)

            print("########## Calculate Quarter Holder Exposure %s %s ##########" % (fund, report_date))

            if (barra_exposure is None) or (fund_holding is None):
                exposure_add = pd.DataFrame([], columns=barra_name, index=[report_date])
            else:
                fund_holding_date = pd.DataFrame(fund_holding[report_date])
                fund_holding_date = fund_holding_date.dropna()
                fund_holding_date = fund_holding_date.sort_values(by=[report_date], ascending=False)
                fund_holding_date.columns = ["Weight"]
                data = pd.concat([fund_holding_date, barra_exposure], axis=1)
                data = data.dropna()

                if (len(data) == 0) or (data is None):
                    exposure_add = pd.DataFrame([], columns=barra_name, index=[report_date])
                else:
                    exposure_add = pd.DataFrame([], columns=barra_name, index=[report_date])

                    for i_factor in range(len(barra_name)):
                        factor_name = barra_name[i_factor]
                        data_weight = data[['Weight', factor_name]]
                        data_weight['StockExposure'] = data['Weight'] * data[factor_name]
                        exposure_add.ix[report_date, factor_name] = data_weight['StockExposure'].sum() / 100.0

                    country_name = Barra().get_factor_name(["COUNTRY"])["NAME_EN"].values[0]
                    position = FundFactor().get_fund_factor("Stock_Ratio", date_list=[report_date], fund_pool=[fund])
                    position = position.values[0][0]
                    exposure_add.ix[report_date, country_name] = position / 100

            if i_date == 0:
                exposure_new = exposure_add
            else:
                exposure_new = pd.concat([exposure_new, exposure_add], axis=0)

        # 合并新数据
        ####################################################################
        out_path = os.path.join(self.data_path_exposure, 'fund_holding_exposure_quarter')
        out_file = os.path.join(out_path, 'Fund_Holder_Exposure_Quarter_' + fund + '.csv')

        if os.path.exists(out_file):
            exposure_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure_old.index = exposure_old.index.map(str)
            params = FactorOperate().pandas_add_row(exposure_old, exposure_new)
        else:
            params = exposure_new
        params.to_csv(out_file)

    def cal_fund_holder_exposure_quarter_all(self, beg_date="19991231",
                                             end_date=datetime.today().strftime("%Y%m%d"),
                                             fund_pool="股票+灵活配置60型基金"):

        """  计算所有基金的季度持仓暴露 (前十大重仓暴露) """

        quarter_date = Date().get_last_fund_quarter_date(end_date)
        fund_pool = FundPool().get_fund_pool_code(quarter_date, fund_pool)

        for i_fund in range(0, len(fund_pool)):
            fund_code = fund_pool[i_fund]
            self.cal_fund_holder_exposure_quarter(fund_code, beg_date, end_date)

    def get_fund_holder_exposure_quarter(self, fund, type_list=['STYLE', 'COUNTRY', 'INDUSTRY']):

        """  得到单个基金的季度持仓暴露 (前十大重仓暴露) """

        out_path = os.path.join(self.data_path_exposure, 'fund_holding_exposure_quarter')
        out_file = os.path.join(out_path, 'Fund_Holder_Exposure_Quarter_' + fund + '.csv')
        try:
            exposure = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure.index = exposure.index.map(str)

            factor_name = Barra().get_factor_name(type_list=type_list)
            factor_name = list(factor_name["NAME_EN"].values)
            exposure = exposure[factor_name]
        except Exception as e:
            exposure = None
        return exposure

    def get_fund_holder_exposure_quarter_date(self, fund, date, type_list=['STYLE', 'COUNTRY', 'INDUSTRY']):

        """  计算单个基金的季度持仓暴露 """

        date = Date().get_normal_date_month_end_day(date)
        try:
            exposure = self.get_fund_holder_exposure_quarter(fund, type_list)
            exposure_date = exposure.ix[date, :]
            exposure_date = pd.DataFrame(exposure_date.values, index=exposure_date.index, columns=[fund]).T
        except Exception as e:
            exposure_date = None
        return exposure_date

    def get_fund_holder_exposure_quarter_daily(self, fund, beg_date, end_date,
                                                type_list=['STYLE', 'COUNTRY', 'INDUSTRY']):

        """  计算单个基金的一段时间内季度持仓暴露 (前十大重仓暴露) """

        exposure = self.get_fund_holder_exposure_quarter(fund, type_list=type_list)
        if exposure is None:
            return None
        date_series = Date().get_trade_date_series(beg_date, end_date)
        exposure_daily = pd.DataFrame([], index=date_series, columns=exposure.columns)
        quarter_date = Date().get_last_fund_quarter_date(end_date)
        exposure = exposure.loc[:quarter_date, :]

        for i_date in range(len(exposure.index)):

            report_date = exposure.index[i_date]
            publish_date = Date().get_trade_date_offset(report_date, -30)
            exposure_daily.loc[publish_date, :] = exposure.loc[report_date, :]

        exposure_daily = exposure_daily.sort_index()
        exposure_daily = exposure_daily.fillna(method="pad")
        exposure_daily = exposure_daily.loc[beg_date:end_date, :]
        exposure_daily = exposure_daily.dropna()
        return exposure_daily


if __name__ == "__main__":

    FundHolderExposureQuarter().cal_fund_holder_exposure_quarter("000001.OF", "20171231", "20180808")
    FundHolderExposureQuarter().cal_fund_holder_exposure_quarter_all("20171231", "20180928", fund_pool="量化基金")

    print(FundHolderExposureQuarter().get_fund_holder_exposure_quarter("000001.OF"))
    print(FundHolderExposureQuarter().get_fund_holder_exposure_quarter_date("000001.OF", "20171231"))
    print(FundHolderExposureQuarter().get_fund_holder_exposure_quarter_daily("000001.OF", "20161031", "20180809"))