import pandas as pd

from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.factor_preprocess import FactorPreProcess
from quant.project.multi_factor.risk_model.exposure.risk_factor import RiskFactor


class RiskFactorFundETFHolder(RiskFactor):

    """
    股票ETF基金重仓股持有市值 / 股票总市值
    日度数据 因为ETF基金有每日份额数据 可计算出ETF基金每日规模 根据季报重仓股可以计算出所有基金的
    """

    def __init__(self):

        RiskFactor.__init__(self)
        self.exposure_path = self.data_path
        self.raw_factor_name = 'risk_raw_fund_etf_holder'
        self.factor_name = 'risk_normal_fund_etf_holder'

    @staticmethod
    def update_data(beg_date, end_date):

        """ 更新需要的数据 """

        Stock().load_all_stock_code_now()
        Fund().load_fund_holding_stock()
        Fund().load_fund_factor_all(beg_date, end_date)
        Stock().load_h5_primary_factor()

    @staticmethod
    def get_etf_fund_code_list():

        """ 得到etf基金列表 """

        index_fund = Fund().get_fund_pool_all("20181231", '指数型基金')
        index_fund = index_fund[index_fund['if_etf'] == 'ETF基金']
        index_fund = index_fund[index_fund['if_connect'] == '非联接基金']
        index_fund = index_fund[index_fund['if_hk'] == '非港股基金']
        index_fund = index_fund.reset_index(drop=True)

        etf_fund_code_list = list(index_fund['wind_code'].values)
        return etf_fund_code_list

    def cal_factor_exposure(self, beg_date, end_date):

        """
        ETF 基金持有的股票总市值（年报、半年报数据 有具体持仓） 平时每日有基金份额 计算每日股票总市值
        股票当日总市值 = 股票年报总市值 * 股票价格变动倍数 * 基金规模变动倍数
        基金规模变动倍数 = 基金份额变动倍数 * 基金AdjustFactor变动倍数（基金份额拆分带来的）
        对于没有日度基金份额的ETF基金，按照当日基金份额和上个基金半年报基金份额不变的来处理，其他按照日度基金份额处理
        """

        # read data
        exchange_share = Fund().get_fund_factor("Exchange_Share")
        exchange_share = exchange_share.fillna(method='pad', limit=3)

        etf_fund_code_list = self.get_etf_fund_code_list()
        etf_fund_code_list = list(set(etf_fund_code_list) & set(exchange_share.columns))
        etf_fund_code_list.sort()
        exchange_share = exchange_share.loc[:, etf_fund_code_list]

        holding_data = Fund().get_fund_holding_stock_all()
        price_adjust = Stock().read_factor_h5("Price_Adjust")

        unit_nav = Fund().get_fund_factor("Unit_Nav")
        unit_nav = unit_nav.fillna(method='pad', limit=1)

        repair_nav = Fund().get_fund_factor("Repair_Nav")
        repair_nav = repair_nav.fillna(method='pad', limit=1)

        fund_adjust_factor = repair_nav.div(unit_nav)
        fund_adjust_factor = fund_adjust_factor.T.dropna(how='all').T.dropna(how='all')

        holding_data['IfIndexFund'] = holding_data['FundCode'].map(lambda x: x in etf_fund_code_list)
        index_fund_holding = holding_data[holding_data['IfIndexFund']]
        index_fund_holding = index_fund_holding.reset_index(drop=True)

        date_series = Date().get_trade_date_series(beg_date, end_date, "D")
        date_series = list(set(date_series) & set(price_adjust.columns))
        date_series.sort()
        share_holding = pd.DataFrame([], columns=date_series)

        # calculate daily
        for i_date in range(len(date_series)):

            date = date_series[i_date]
            half_year_date = Date().get_last_fund_halfyear_date(date)
            half_year_trade_date = Date().get_trade_date_month_end_day(half_year_date)
            index_fund_holding_date = index_fund_holding[index_fund_holding.ReportDate == half_year_date]
            index_fund_holding_adjust = pd.DataFrame([])

            fund_code_date = list(set(etf_fund_code_list) & set(index_fund_holding_date.FundCode))
            fund_code_date.sort()

            for i_fund in range(len(fund_code_date)):

                fund = fund_code_date[i_fund]
                print(date, half_year_trade_date, half_year_date, fund)
                index_fund_holding_fund = index_fund_holding_date[index_fund_holding_date.FundCode == fund]
                index_fund_holding_fund.index = index_fund_holding_fund['StockCode']

                price_pct = pd.DataFrame(price_adjust[date] / price_adjust[half_year_trade_date])
                price_pct.columns = ['PriceAdjust']

                concat_data = pd.concat([index_fund_holding_fund, price_pct], axis=1)
                concat_data = concat_data.dropna()

                factor_date = fund_adjust_factor.index[fund_adjust_factor.index <= date][-1]
                adjust_date = fund_adjust_factor.loc[factor_date, fund]
                adjust_pct = fund_adjust_factor.loc[half_year_trade_date, fund] / adjust_date

                share_date = exchange_share.index[exchange_share.index <= date][-1]
                share_pct = exchange_share.loc[share_date, fund] / exchange_share.loc[half_year_trade_date, fund]

                concat_data['AdjustFactor'] = adjust_pct * share_pct
                concat_data['AdjustFactor'] = concat_data['AdjustFactor'].fillna(1.0)
                concat_data['AdjustMV'] = concat_data['MarketValue'] * concat_data['AdjustFactor']
                concat_data['AdjustMV'] *= concat_data['PriceAdjust']

                concat_data = concat_data.reset_index()
                index_fund_holding_adjust = pd.concat([index_fund_holding_adjust, concat_data], axis=0)
                index_fund_holding_adjust = index_fund_holding_adjust.reset_index(drop=True)

            sum_share = pd.DataFrame(index_fund_holding_adjust.groupby(by=['StockCode'])['AdjustMV'].sum())
            sum_share.columns = [date]
            share_holding = pd.concat([share_holding, sum_share], axis=1)

        # save data
        share_holding = share_holding.T.dropna(how='all').T / 100000000
        share_holding - share_holding.round(4)
        self.save_risk_factor_exposure(share_holding, self.raw_factor_name)
        share_holding = FactorPreProcess().remove_extreme_value_mad(share_holding)
        share_holding = FactorPreProcess().standardization(share_holding)
        self.save_risk_factor_exposure(share_holding, self.factor_name)


if __name__ == '__main__':

    from datetime import datetime
    beg_date = "20110101"
    end_date = datetime.today().strftime("%Y%m%d")
    beg_date = "20060101"
    end_date = "20110101"

    self = RiskFactorFundETFHolder()
    # self.cal_factor_exposure(beg_date, end_date)

    data = self.get_risk_factor_exposure(self.raw_factor_name)
    data = data.round(4)
    self.save_risk_factor_exposure(data, self.raw_factor_name)

