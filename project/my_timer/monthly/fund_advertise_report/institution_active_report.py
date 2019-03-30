from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.mfc.mfc_data import MfcData

from quant.utility.write_excel import WriteExcel
from quant.utility.write_word import WriteWord
from quant.utility.win32com_word import Win32ComWord
from quant.utility.financial_series import FinancialSeries

from datetime import datetime
import pandas as pd
import numpy as np
import os
from WindPy import w
w.start()


class InstitutionActiveReport(Data):

    """ 基金宣传单页（机构-主动量化版）"""

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\fund_report\advertise_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.fund_code = ""
        self.date = ""
        self.fund_name = ""
        self.fund_strategy = ""
        self.asset_allocation_strategy = ""
        self.last_trade_date = ""
        self.quarter_date = ""
        self.halfyear_date = ""
        self.fund_all_stock = ""
        self.fund_top10_stock = ""
        self.fund_nav = ""
        self.comparsion_bench_list = []
        self.prefix = "机构"
        self.fund_manager = ""
        self.outlook = ""

    def get_input_data(self, fund_code, fund_name,
                       fund_strategy, asset_allocation_strategy,
                       comparsion_bench_list, date, fund_manager):

        """
        输入基金名称 基金代码 当日日期
        得到最近的交易日、季报日、半年报年报日
        得到基金净值数据、季报和半年报持仓数据
        """

        self.fund_code = fund_code
        self.fund_name = fund_name
        self.date = date
        self.fund_strategy = fund_strategy
        self.asset_allocation_strategy = asset_allocation_strategy
        self.last_trade_date = Date().get_trade_date_offset(date, 0)
        self.quarter_date = Date().get_last_fund_quarter_date(date)
        self.halfyear_date = Date().get_last_fund_halfyear_date(date)
        print("参数时间", self.last_trade_date, self.quarter_date, self.halfyear_date)
        self.fund_nav = MfcData().get_mfc_public_fund_nav(self.fund_code)
        self.fund_top10_stock = Fund().get_fund_top10_stock_date(self.fund_code, self.quarter_date)
        self.fund_top10_stock /= 100.0
        self.fund_all_stock = Fund().get_fund_all_stock_date(self.fund_code, self.halfyear_date)
        self.fund_all_stock /= 100.0
        self.comparsion_bench_list = comparsion_bench_list
        self.fund_manager = fund_manager

    def update_data(self):

        """ 更新基金净值 和 持仓数据 指数价格数据"""

        Fund().update_fund_holding()
        MfcData().load_mfc_public_fund_nav()

        Index().load_index_factor(index_code='H00985.CSI', beg_date="20040101", end_date=datetime.today())
        Index().load_index_factor(index_code="885001.WI", beg_date="20180101", end_date=datetime.today())

    def get_update_date(self):

        """ wind 得到基金的基本信息 类型 成立日期 最新规模等等 """

        data_info = pd.DataFrame([], columns=["更新日期"])

        data_info.loc['最近交易日', "更新日期"] = self.last_trade_date
        data_info.loc['最近季报日', "更新日期"] = self.quarter_date
        data_info.loc['最近年报或半年报日', "更新日期"] = self.halfyear_date
        data_info['日期'] = data_info.index
        data_info = data_info[['日期', '更新日期']]
        return data_info

    def get_fund_basic_info(self):

        """ wind 得到基金的基本信息 类型 成立日期 最新规模等等 """

        data = w.wss(self.fund_code, "fund_setupdate,fund_investtype,netasset_total",
                     "unit=1;tradeDate=%s" % self.last_trade_date)
        data_pd = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes).T
        data_pd.columns = ['成立日期', '基金类型', '基金规模（亿）']
        data_pd['成立日期'] = data_pd['成立日期'].map(lambda x: x.strftime("%Y%m%d"))
        data_pd['基金规模（亿）'] = data_pd['基金规模（亿）'].map(lambda x: np.round(x / 100000000, 2))
        data_pd = data_pd.T
        data_info = pd.DataFrame([self.fund_code, self.fund_name],
                                 columns=[self.fund_code], index=['基金代码', '基金名称'])
        data_concat = pd.concat([data_info, data_pd], axis=0)
        data_concat.columns = ['内容']
        data_concat['基本信息'] = data_concat.index
        data_concat = data_concat[['基本信息', '内容']]
        return data_concat

    def get_fund_strategy(self):

        """ 基金投资策略 """

        data = pd.DataFrame([self.asset_allocation_strategy, self.fund_strategy],
                            columns=['策略内容'], index=['配置策略', '投资策略'])

        last_month_end_date = Date().get_normal_date_last_month_end_day(datetime.today())
        print(last_month_end_date, "投资展望")

        # 营销月报的投资展望
        try:
            from quant.project.my_timer.monthly.month_report import FundMonthReport
            report = FundMonthReport()
            report.load_param_file()
        except Exception as e:
            print("网盘投资展望获取失败，利用本地投资展望")
        print("投资展望的日期", last_month_end_date)

        dst_file = os.path.join(report.data_path, "参数", '基金营销月报投资展望.xlsx')
        strategy_data = pd.read_excel(dst_file, index_col=[0])
        strategy_data.index = strategy_data.index.map(Date().change_to_str)
        strategy_data = strategy_data.fillna(method='pad')
        data.loc["市场展望", "策略内容"] = strategy_data.loc[last_month_end_date, self.fund_manager]
        self.outlook = strategy_data.loc[last_month_end_date, self.fund_manager]

        data['投资策略'] = data.index
        data = data[['投资策略', '策略内容']]
        return data

    def get_fund_asset_allocation(self):

        """ 资产配置（股票、债券、基金、现金占比）"""
        data = w.wss(self.fund_code,
                     "prt_stocktonav,prt_bondtonav,prt_fundtonav,"
                     "prt_cashtonav,prt_othertonav",
                     "rptDate=%s" % self.quarter_date)

        data_pd = pd.DataFrame(data.Data, index=data.Fields, columns=data.Codes)
        data_pd.columns = ['占净值比']
        data_pd.index = ['股票', '债券', '基金', '现金', '其他']
        data_pd = data_pd.fillna(0.0)
        data_pd /= 100.0
        data_pd['资产配置(%s)' % self.quarter_date] = data_pd.index
        data_pd = data_pd[['资产配置(%s)' % self.quarter_date, '占净值比']]
        return data_pd

    def get_fund_industry_allocation(self):

        """ 半年报行业配置（银行、房地产、医药等等）"""

        fund_all_stock = self.fund_all_stock
        industry = Stock().read_factor_h5("industry_citic1")
        date = Date().get_trade_date_offset(self.halfyear_date, 0)
        industry_date = pd.DataFrame(industry[date])
        industry_date.columns = ['IndustryCode']
        industry_date = industry_date.dropna()
        data_concat = pd.concat([fund_all_stock, industry_date], axis=1)
        data_concat = data_concat.dropna()
        data_concat['IndustryName'] = data_concat['IndustryCode'].map(Stock().get_industry_citic1_name_ch)
        data_industry_group = pd.DataFrame(data_concat.groupby(by=['IndustryName'])['Weight'].sum())
        data_industry_group = data_industry_group.sort_values(by=['Weight'], ascending=False)
        data_industry_group.columns = ['占基金净值比']
        stock_weight_sum = data_industry_group['占基金净值比'].sum()
        data_industry_group['占股票市值比'] = data_industry_group['占基金净值比'] / stock_weight_sum
        data_industry_group['行业名称'] = data_industry_group.index
        data_industry_group['行业配置(%s)' % self.halfyear_date] = range(1, len(data_industry_group) + 1)
        data_industry_group = data_industry_group[['行业配置(%s)' % self.halfyear_date, '行业名称', '占股票市值比', '占基金净值比']]
        data_industry_group = data_industry_group.iloc[0:10, :]
        return data_industry_group

    def get_fund_top10_stock(self):

        """ 前十大重仓股 """

        fund_top10_stock = self.fund_top10_stock
        fund_top10_stock.columns = ['占基金净值比']
        fund_top10_stock['股票名称'] = fund_top10_stock.index.map(Stock().get_stock_name_date)
        data = w.wss(self.fund_code, "prt_stocktonav", "rptDate=%s" % self.quarter_date)

        stock_sum = data.Data[0][0] / 100.0
        fund_top10_stock['占股票市值比'] = fund_top10_stock['占基金净值比'] / stock_sum
        fund_top10_stock['重仓股票(%s)' % self.quarter_date] = range(1, len(fund_top10_stock) + 1)
        fund_top10_stock = fund_top10_stock[['重仓股票(%s)' % self.quarter_date,
                                             '股票名称', '占股票市值比', '占基金净值比']]
        return fund_top10_stock

    def get_fund_performace_date(self):

        """ 业绩表现开始结束日期 """

        end_date = self.last_trade_date
        datetime_last_date = datetime.strptime(end_date, "%Y%m%d")
        day = datetime_last_date.day
        month = datetime_last_date.month
        year = datetime_last_date.year

        date_3m = Date().get_trade_date_offset(end_date, -60)
        date_6m = Date().get_trade_date_offset(end_date, -120)
        date_year_beg = Date().change_to_str(datetime(year, 1, 1))
        date_1y = Date().change_to_str(datetime(year-1, month, day))
        date_3y = Date().change_to_str(datetime(year-3, month, day))
        date_5y = Date().change_to_str(datetime(year-5, month, day))

        date_array = [["最近3个月", date_3m, end_date],
                      ["最近6个月", date_6m, end_date],
                      ["年初至今", date_year_beg, end_date],
                      ["最近1年", date_1y, end_date],
                      ["最近3年", date_3y, end_date],
                      ["最近5年", date_5y, end_date]]

        return date_array

    def get_fund_last_performance(self):

        """ 基金和对比基准最近业绩表现 """

        date_array = self.get_fund_performace_date()
        fund_nav = self.fund_nav
        result_fund = pd.DataFrame([], columns=['收益率'])

        # fund
        fund_series = FinancialSeries(pd.DataFrame(fund_nav['NAV_ADJ']))

        for i in range(len(date_array)):

            label = date_array[i][0]
            beg_date = date_array[i][1]
            end_date = date_array[i][2]
            pct = fund_series.get_interval_return(beg_date, end_date, short_handled=True)
            result_fund.loc[label, "收益率"] = pct

        # benchmark
        for i_bench in range(len(self.comparsion_bench_list)):
            bench_name = self.comparsion_bench_list[i_bench][0]
            bench_code = self.comparsion_bench_list[i_bench][1]
            index_close = Index().get_index_factor(bench_code, attr=['CLOSE'])
            index_series = FinancialSeries(pd.DataFrame(index_close['CLOSE']))

            for i in range(len(date_array)):
                label = date_array[i][0]
                beg_date = date_array[i][1]
                end_date = date_array[i][2]
                pct = index_series.get_interval_return(beg_date, end_date, short_handled=True)
                result_fund.loc[label, bench_name] = pct

        columns = list(result_fund.columns)
        result_fund['最近表现'] = result_fund.index
        columns.insert(0, '最近表现')
        result_fund = result_fund[columns]
        return result_fund

    def get_stock_characteristic_size(self):

        """ 半年报或者年报在 在市值因子（自由流通市值）上的暴露 """

        # get data
        fund_all_stock = self.fund_all_stock
        fund_all_stock.columns = ['FundWeight']
        stock_sum_all = fund_all_stock['FundWeight'].sum()
        mkt_free = Stock().read_factor_h5("Mkt_freeshares")

        date = Date().get_trade_date_offset(self.halfyear_date, 0)
        mkt_free_date = pd.DataFrame(mkt_free[date])
        mkt_free_date /= 100000000.0
        mkt_free_date.columns = ['Mkt']

        index_weight_300 = Index().get_weight_date(index_code="000300.SH", date=date)
        index_weight_300.columns = ['300Weight']
        index_weight_500 = Index().get_weight_date(index_code="000905.SH", date=date)
        index_weight_500.columns = ['500Weight']

        # 市值中位数
        # concat_data = pd.concat([fund_all_stock, mkt_free_date], axis=1)
        # concat_data = concat_data.dropna()
        # concat_data = concat_data.sort_values(by=['FundWeight'], ascending=False)
        # size_median = np.round(concat_data['Mkt'].median(), 2)

        # 300成分占比
        concat_data = pd.concat([fund_all_stock, index_weight_300], axis=1)
        concat_data = concat_data.dropna()
        stock_300_weight = concat_data['FundWeight'].sum()
        stock_300_weight /= stock_sum_all

        # 500成分占比
        concat_data = pd.concat([fund_all_stock, index_weight_500], axis=1)
        concat_data = concat_data.dropna()
        stock_500_weight = concat_data['FundWeight'].sum()
        stock_500_weight /= stock_sum_all

        # 其他成分占比
        other_weight = 1 - stock_300_weight - stock_500_weight

        stock_characteristic_size = pd.DataFrame([stock_300_weight, stock_500_weight, other_weight],
                                                 index=['沪深300成分股权重', '中证500成分股权重', '其他成分股权重'],
                                                 columns=['数值'])
        stock_characteristic_size['持股特征(%s)' % self.halfyear_date] = '市值分布'
        stock_characteristic_size['具体表现'] = stock_characteristic_size.index
        return stock_characteristic_size

    def get_stock_characteristic_constituent(self):

        """ 半年报或者年报在 在板块上的暴露 """

        # get data
        fund_all_stock = self.fund_all_stock
        fund_all_stock.columns = ['FundWeight']
        stock_sum_all = fund_all_stock['FundWeight'].sum()

        constituent_6 = fund_all_stock[fund_all_stock.index.map(lambda x: x[0:3] in ["000", "600", "001"])].sum().values[0]
        constituent_0 = fund_all_stock[fund_all_stock.index.map(lambda x: x[0:3] == '002')].sum().values[0]
        constituent_3 = fund_all_stock[fund_all_stock.index.map(lambda x: x[0:3] == '300')].sum().values[0]

        constituent_6 /= stock_sum_all
        constituent_0 /= stock_sum_all
        constituent_3 /= stock_sum_all
        stock_characteristic_constituent = pd.DataFrame([constituent_6, constituent_0, constituent_3],
                                                        index=['沪深主板成分股权重', '中小板成分股权重', '创业板成分股权重'],
                                                        columns=['数值'])
        stock_characteristic_constituent['持股特征(%s)' % self.halfyear_date] = '板块分布'
        stock_characteristic_constituent['具体表现'] = stock_characteristic_constituent.index
        return stock_characteristic_constituent

    def get_stock_characteristic_quality(self):

        """ 半年报或者年报在 在盈利上的暴露 """

        # get data
        fund_all_stock = self.fund_all_stock
        fund_all_stock.columns = ['FundWeight']
        stock_sum_all = fund_all_stock['FundWeight'].sum()
        fund_all_stock /= stock_sum_all
        date = Date().get_trade_date_offset(self.halfyear_date, 0)

        roe = Stock().read_factor_h5("alpha_raw_roe_ttm", path=Stock().get_h5_path("my_alpha"))
        income_yoy = Stock().read_factor_h5("alpha_raw_income_yoy", path=Stock().get_h5_path("my_alpha"))
        net_profit_yoy = Stock().read_factor_h5("alpha_raw_profit_yoy", path=Stock().get_h5_path("my_alpha"))
        FEGR_1 = Stock().read_factor_h5("FEGR_1") / 100.0
        FEGR_2 = Stock().read_factor_h5("FEGR_2") / 100.0

        data = pd.concat([fund_all_stock, roe[date], income_yoy[date],
                          net_profit_yoy[date], FEGR_1[date], FEGR_2[date]], axis=1)
        data.columns = ['FundWeight', 'ROE', 'InComeYOY', 'NetProfitYOY', 'PERate1Y', 'PERate2Y']
        data = data.dropna(subset=['FundWeight'])

        # roe mean
        data_sub = data[['FundWeight', 'ROE']]
        data_sub = data_sub.dropna()
        data_sub.loc[data_sub['ROE'] > 0.50, "ROE"] = 0.50
        data_sub.loc[data_sub['ROE'] < -0.50, "ROE"] = -0.50
        data_sub['FundWeight'] = data_sub['FundWeight'] / data_sub['FundWeight'].sum()
        data_sub = data_sub.sort_values(by=['FundWeight'], ascending=False)
        roe_weight_mean = (data_sub['ROE'] * data_sub['FundWeight']).sum()

        # income_yoy ttm mean
        data_sub = data[['FundWeight', 'InComeYOY']]
        data_sub = data_sub.dropna()
        data_sub.loc[data_sub['InComeYOY'] > 2.00, "InComeYOY"] = 2.00
        data_sub.loc[data_sub['InComeYOY'] < -2.00, "InComeYOY"] = -2.00
        data_sub['FundWeight'] = data_sub['FundWeight'] / data_sub['FundWeight'].sum()
        data_sub = data_sub.sort_values(by=['FundWeight'], ascending=False)
        income_yoy_weight_mean = (data_sub['InComeYOY'] * data_sub['FundWeight']).sum()

        # profit ttm mean
        data_sub = data[['FundWeight', 'NetProfitYOY']]
        data_sub = data_sub.dropna()
        data_sub.loc[data_sub['NetProfitYOY'] > 2.00, "NetProfitYOY"] = 2.00
        data_sub.loc[data_sub['NetProfitYOY'] < -2.00, "NetProfitYOY"] = -2.00
        data_sub['FundWeight'] = data_sub['FundWeight'] / data_sub['FundWeight'].sum()
        data_sub = data_sub.sort_values(by=['FundWeight'], ascending=False)
        profit_yoy_weight_mean = (data_sub['NetProfitYOY'] * data_sub['FundWeight']).sum()

        # PERate1Y mean
        data_sub = data[['FundWeight', 'PERate1Y']]
        data_sub = data_sub.dropna()
        data_sub['FundWeight'] = data_sub['FundWeight'] / data_sub['FundWeight'].sum()
        perate1y_yoy_weight_mean = (data_sub['PERate1Y'] * data_sub['FundWeight']).sum()

        # profit ttm mean
        data_sub = data[['FundWeight', 'PERate2Y']]
        data_sub = data_sub.dropna()
        data_sub['FundWeight'] = data_sub['FundWeight'] / data_sub['FundWeight'].sum()
        perate2y_yoy_weight_mean = (data_sub['PERate2Y'] * data_sub['FundWeight']).sum()

        val_list = [roe_weight_mean, income_yoy_weight_mean, profit_yoy_weight_mean,
                    perate1y_yoy_weight_mean, perate2y_yoy_weight_mean]

        index = ['ROE_TTM', '营收同比增长率', '利润同比增长率', '预期盈利增长率明年', '预期盈利增长率后年']
        stock_characteristic_quality = pd.DataFrame(val_list, index=index, columns=['数值'])
        stock_characteristic_quality['持股特征(%s)' % self.halfyear_date] = '盈利能力'
        stock_characteristic_quality['具体表现'] = stock_characteristic_quality.index
        return stock_characteristic_quality

    def get_stock_characteristic_valuation(self):

        """ 半年报或者年报在 在估值上的暴露 """

        # get data
        fund_all_stock = self.fund_all_stock
        fund_all_stock.columns = ['FundWeight']
        stock_sum_all = fund_all_stock['FundWeight'].sum()
        fund_all_stock /= stock_sum_all
        date = Date().get_trade_date_offset(self.halfyear_date, 0)

        pe = Stock().read_factor_h5("PE_ttm")
        dividend = Stock().read_factor_h5("dividendyield2")
        bp = Stock().read_factor_h5("alpha_raw_bp", path=Stock().get_h5_path("my_alpha"))

        data = pd.concat([fund_all_stock, pe[date], dividend[date], bp[date]], axis=1)
        data.columns = ['FundWeight', 'PE', 'DivRate', 'BP']
        data = data.dropna(subset=['FundWeight'])
        data['EP'] = 1.0 / data['PE']
        data['DivRate'] /= 100.0

        # pe mean
        data_ep = data[['FundWeight', 'EP']]
        data_ep = data_ep.dropna()
        data_ep['FundWeight'] = data_ep['FundWeight'] / data_ep['FundWeight'].sum()
        ep_weight_mean = (data_ep['EP'] * data_ep['FundWeight']).sum()
        pe_weight_mean = np.round(1.0 / ep_weight_mean, 2)

        # pb mean
        data_bp = data[['FundWeight', 'BP']]
        data_bp = data_bp.dropna()
        data_bp['FundWeight'] = data_bp['FundWeight'] / data_bp['FundWeight'].sum()
        bp_weight_mean = (data_bp['BP'] * data_bp['FundWeight']).sum()
        pb_weight_mean = np.round(1.0 / bp_weight_mean, 2)

        # DivRate mean
        data_div = data[['FundWeight', 'DivRate']]
        data_div = data_div.dropna()
        data_div['FundWeight'] = data_div['FundWeight'] / data_div['FundWeight'].sum()
        div_weight_mean = (data_div['DivRate'] * data_div['FundWeight']).sum()

        stock_characteristic_valuation = pd.DataFrame([pe_weight_mean, pb_weight_mean, div_weight_mean],
                                                      index=['市盈率', '市净率', '股息率'],
                                                      columns=['数值'])
        stock_characteristic_valuation['持股特征(%s)' % self.halfyear_date] = '估值情况'
        stock_characteristic_valuation['具体表现'] = stock_characteristic_valuation.index
        return stock_characteristic_valuation

    def get_stock_characteristic(self):

        """ 半年报或者年报在 在各个方面的暴露 """
        characteristic_size = self.get_stock_characteristic_size()
        characteristic_constituent = self.get_stock_characteristic_constituent()
        characteristic_valuation = self.get_stock_characteristic_valuation()
        characteristic_quality = self.get_stock_characteristic_quality()

        characteristic = pd.concat([characteristic_size,
                                    characteristic_constituent,
                                    characteristic_valuation,
                                    characteristic_quality], axis=0)
        characteristic = characteristic[['持股特征(%s)' % self.halfyear_date, '具体表现', '数值']]
        return characteristic

    def write_excel(self):

        """ 写入Excel """

        # cal need data
        fund_basic_info = self.get_fund_basic_info()
        update_date = self.get_update_date()
        asset_allocation = self.get_fund_asset_allocation()
        top10_stock = self.get_fund_top10_stock()
        industry_allocation = self.get_fund_industry_allocation()
        fund_strategy_info = self.get_fund_strategy()
        last_performance = self.get_fund_last_performance()
        characteristic = self.get_stock_characteristic()

        # write xlsx
        sub_path = os.path.join(self.data_path, self.last_trade_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        xlsx_file = os.path.join(sub_path, '%s_%s.xlsx' % (self.prefix, self.fund_name))

        if os.path.exists(xlsx_file):
            os.remove(xlsx_file)
        excel = WriteExcel(xlsx_file)
        worksheet = excel.add_worksheet(self.fund_name)

        # update date
        num_format_pd = pd.DataFrame([], columns=update_date.columns, index=['format'])
        num_format_pd.ix['format', :] = ''
        excel.write_pandas(update_date, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 15])

        # fund_basic_info
        num_format_pd = pd.DataFrame([], columns=fund_basic_info.columns, index=['format'])
        num_format_pd.ix['format', :] = ''
        excel.write_pandas(fund_basic_info, worksheet, begin_row_number=5, begin_col_number=1,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 15])

        # fund_strategy_info
        num_format_pd = pd.DataFrame([], columns=fund_strategy_info.columns, index=['format'])
        num_format_pd.ix['format', :] = ''
        excel.write_pandas(fund_strategy_info, worksheet, begin_row_number=12, begin_col_number=1,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 15])
        blank = '     '
        excel.insert_merge_range(worksheet, 13, 2, 13, 9, self.asset_allocation_strategy)
        excel.insert_merge_range(worksheet, 14, 2, 14, 9, self.fund_strategy)
        excel.insert_merge_range(worksheet, 15, 2, 15, 18, self.outlook)
        excel.rewtite_cell_format(worksheet, 13, 2, blank + self.asset_allocation_strategy,  "", "left")
        excel.rewtite_cell_format(worksheet, 14, 2, blank + self.fund_strategy,  "", "left")
        excel.rewtite_cell_format(worksheet, 15, 2, blank + self.outlook, "", "left")

        # asset_allocation
        num_format_pd = pd.DataFrame([], columns=asset_allocation.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(asset_allocation, worksheet, begin_row_number=17, begin_col_number=1,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 15])

        # characteristic_size
        num_format_pd = pd.DataFrame([], columns=characteristic.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        beg_row_num = 24
        excel.write_pandas(characteristic, worksheet, begin_row_number=beg_row_num, begin_col_number=1,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 15, 8])

        excel.insert_merge_range(worksheet, beg_row_num + 1, 1, beg_row_num + 3, 1, "市值分布")
        excel.insert_merge_range(worksheet, beg_row_num + 4, 1, beg_row_num + 6, 1, "板块分布")
        excel.insert_merge_range(worksheet, beg_row_num + 7, 1, beg_row_num + 9, 1, "估值情况")
        excel.insert_merge_range(worksheet, beg_row_num + 10, 1, beg_row_num + 14, 1, "盈利能力")
        excel.rewtite_cell_format(worksheet, beg_row_num + 7, 3, characteristic.iloc[6, 2],  "0.00")
        excel.rewtite_cell_format(worksheet, beg_row_num + 8, 3, characteristic.iloc[7, 2],  "0.00")

        # performance
        num_format_pd = pd.DataFrame([], columns=last_performance.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(last_performance, worksheet, begin_row_number=5, begin_col_number=6,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 10, 10, 10])

        # top10 multi_factor
        num_format_pd = pd.DataFrame([], columns=top10_stock.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.loc['format', '重仓股票(%s)' % self.quarter_date] = ''
        excel.write_pandas(top10_stock, worksheet, begin_row_number=17, begin_col_number=6,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 10, 10, 10])

        # industry_allocation
        num_format_pd = pd.DataFrame([], columns=industry_allocation.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.loc['format', '行业配置(%s)' % self.halfyear_date] = ''
        excel.write_pandas(industry_allocation, worksheet, begin_row_number=29, begin_col_number=6,
                           num_format_pd=num_format_pd, color="blue", fillna=True,
                           need_index=False, header_font_color="white",
                           cell_delta=0.5, cell_basic=4.0, cell_len_list=[15, 10, 10, 10])
        excel.close()

    def write_word(self):

        # cal need data
        fund_basic_info = self.get_fund_basic_info()
        update_date = self.get_update_date()
        fund_strategy_info = self.get_fund_strategy()
        asset_allocation = self.get_fund_asset_allocation()
        top10_stock = self.get_fund_top10_stock()
        industry_allocation = self.get_fund_industry_allocation()
        last_performance = self.get_fund_last_performance()
        characteristic = self.get_stock_characteristic()

        # doc file
        sub_path = os.path.join(self.data_path, self.last_trade_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
        doc_file = os.path.join(sub_path, '%s_%s.docx' % (self.prefix, self.fund_name))
        word = WriteWord()

        # title
        title = "%s月报（%s版）" % (self.fund_name, self.prefix)
        word.add_paragraph(text=title, size=14, align=True, line_spacing=False, bold=True)

        vals = (update_date.loc["最近交易日", "更新日期"],
                update_date.loc["最近季报日", "更新日期"],
                update_date.loc["最近年报或半年报日", "更新日期"])
        text = "备注：最近更新交易日为%s，最近季报日为%s，最近年报或者半年报日为%s。" % vals

        # 基本信息
        header_text = "基本信息"
        word.add_paragraph(text=header_text, size=10, line_spacing=True, bold=True)
        fund_basic_info = word.reshape_dataframe_columns(fund_basic_info)
        fund_basic_info = fund_basic_info.astype(np.str)
        fund_basic_info_format = pd.DataFrame([], index=fund_basic_info.index, columns=fund_basic_info.columns)
        fund_basic_info_format.iloc[:, 1] = False
        word.add_table(data=fund_basic_info, width_list=[3.0, 5.0], format_force=fund_basic_info_format)

        # 投资策略
        header_text = "投资策略"
        word.add_paragraph(text=header_text, size=10, line_spacing=True, bold=True)
        fund_strategy_info = word.reshape_dataframe_columns(fund_strategy_info)
        word.add_table(data=fund_strategy_info, width_list=[2.4, 12.5], align=False)

        # 持股特征
        header_text = "持股特征"
        word.add_paragraph(text=header_text, size=10, line_spacing=True, bold=True)
        characteristic = word.reshape_dataframe_columns(characteristic)
        characteristic_format = pd.DataFrame([], index=characteristic.index, columns=characteristic.columns)
        characteristic_format.iloc[7, :] = False
        characteristic_format.iloc[8, :] = False
        characteristic_format = characteristic_format.fillna(True)
        word.add_table(data=characteristic, width_list=[3.5, 5.0, 2.4], format_force=characteristic_format)

        # 本页结束
        word.add_page_break()

        # 最近表现
        header_text = "最近表现"
        word.add_paragraph(text=header_text, size=10, line_spacing=True, bold=True)
        last_performance = word.reshape_dataframe_columns(last_performance)
        word.add_table(data=last_performance, width_list=[3.0, 3.0, 3.0, 3.0])

        # 资产配置
        header_text = "资产配置"
        word.add_paragraph(text=header_text, size=10, line_spacing=True, bold=True)
        asset_allocation = word.reshape_dataframe_columns(asset_allocation)
        word.add_table(data=asset_allocation, width_list=[3.5, 2.4])

        # 行业配置
        header_text = "行业配置"
        word.add_paragraph(text=header_text, size=10, line_spacing=True, bold=True)
        industry_allocation.iloc[:, 0] = industry_allocation.iloc[:, 0].map(lambda x: str(int(x)))
        industry_allocation = word.reshape_dataframe_columns(industry_allocation)
        industry_allocation_format = pd.DataFrame([], index=industry_allocation.index,
                                                  columns=industry_allocation.columns)
        industry_allocation_format.iloc[:, 0] = False
        industry_allocation_format = industry_allocation_format.fillna(True)
        word.add_table(data=industry_allocation, width_list=[3.5, 3.0, 3.0, 3.0],
                       format_force=industry_allocation_format)

        # 重仓股票
        header_text = "重仓股票"
        word.add_paragraph(text=header_text, size=10, line_spacing=True, bold=True)
        top10_stock.iloc[:, 0] = top10_stock.iloc[:, 0].map(lambda x: str(int(x)))
        top10_stock = word.reshape_dataframe_columns(top10_stock)
        top10_stock_format = pd.DataFrame([], index=top10_stock.index, columns=top10_stock.columns)
        top10_stock_format.iloc[:, 0] = False
        top10_stock_format = top10_stock_format.fillna(True)
        word.add_table(data=top10_stock, width_list=[3.5, 3.0, 3.0, 3.0],  format_force=top10_stock_format)

        word.save(doc_file)

        win32word = Win32ComWord(doc_file)
        win32word.add_footer(text=text, size=8)
        win32word.save()
        win32word.close()

if __name__ == '__main__':

    fund_code = "229002.OF"
    fund_name = "泰达宏利逆向策略"
    date = "20190131"
    fund_strategy = "配置盈利稳定增长、估值不高的公司，分散个股投资风险"
    asset_allocation_strategy = "战略上维持较高股票仓位，战术上根据宏观基本面、市场趋势、估值做适度调整"
    comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                             ["中证全指全收益", 'H00985.CSI']]
    fund_manager = "刘欣"

    self = InstitutionActiveReport()
    self.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                        comparsion_bench_list, date, fund_manager)
    # self.update_data()
    self.write_word()
    # self.write_excel()



