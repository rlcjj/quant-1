from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock_static import StockStatic
from quant.stock.stock_factor_data import StockFactorData
from quant.stock.stock_factor_operate import StockFactorOperate

from datetime import datetime
import pandas as pd
import numpy as np
import os


class StockForbidPool(Data):

    """
    股票禁投库

    1、财务类
    （已使用）
    1、1 净资产在全市场（剔除新股）后10%或者为负
    1、2 营业收入全市场（剔除新股）后10%或者为负
    1、3 应收账款/净资产大于200%或者非国企大于150%
    1、4 商誉占总资产比例超过行业平均一定的阈值

    （未使用）
    1、5 TTM毛利润为负数
    1、6 TTM净利润为负数
    1、7 业绩预告盈利为负数
    1、8 5年经营性现金流入除以营收小于60%
    1、9 5年经营性净现金流在中信三级行业内位于后30%且为负数

    2、监管类
    2、1 特别处理 ST *ST
    2、2 违规异常 对公司违规行为的处罚
    2、3 审计异常 年报审计非标准无保留意见

    3、流动性
    3、1 质押警告

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\stock_pool\forbid_stock_pool'
        self.data_path_forbid_pool = os.path.join(self.primary_data_path, self.sub_data_path)

    def get_all_stock_code_now(self):

        """ 所有历史上的股票池 """

        data = StockStatic().get_all_stock_code_now()
        return data

    def get_st_stock_date(self, date):

        """ 是否ST """

        code_list = StockStatic().get_all_stock_code_now()
        data = pd.DataFrame([], index=code_list, columns=['ST'])
        data['Name'] = data.index.map(lambda x: StockStatic().get_stock_name_date(x, date))
        data['if_ST'] = data['Name'].map(lambda x: "ST" in str(x))
        data = data[data['if_ST']]

        stock_list = list(data.index)

        name = "STStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=stock_list, columns=[name])
        data_pd.loc[stock_list, name] = data.loc[stock_list, 'Name']
        data_pd.to_csv(file)

        return stock_list

    def get_delist_stock_date(self, date):

        """ 得到已经不上市的企业 """

        ipo_date = StockStatic().get_ipo_date()
        date_time = datetime.strptime(date, "%Y%m%d")
        ipo_date['IpoDay'] = ipo_date['IPO_DATE'].map(lambda x: (datetime.strptime(x, "%Y%m%d") - date_time).days)
        ipo_date['DelistDay'] = ipo_date['DELIST_DATE'].map(lambda x: (datetime.strptime(x, "%Y%m%d") - date_time).days)

        not_list_stock = list(ipo_date[ipo_date['IpoDay'] >= 0].index)
        delist_stock = list(ipo_date[ipo_date['DelistDay'] <= 0].index)

        delist_all_stock = list(set(not_list_stock) | set(delist_stock))
        delist_all_stock.sort()

        name = "DelistStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=delist_all_stock, columns=[name])
        data_pd.loc[not_list_stock, name] = "未上市"
        data_pd.loc[delist_stock, name] = "已退市"
        data_pd.to_csv(file)

        return delist_all_stock

    def get_sub_new_date(self, date):

        """ 股票池 上市未满一个季度的次新股（90个自然日） """

        ipo_date = StockStatic().get_ipo_date()
        date_datetime = datetime.strptime(date, "%Y%m%d")
        ipo_date['DateDiff'] = ipo_date['IPO_DATE'].map(lambda x: (datetime.strptime(x, "%Y%m%d") - date_datetime).days)
        ipo_date = ipo_date.sort_values(by=['DateDiff'])
        ipo_date = ipo_date[ipo_date['DateDiff'] >= -90]
        ipo_date = ipo_date[ipo_date['DateDiff'] < 0]

        filter_stock_list = list(set(ipo_date.index))
        filter_stock_list.sort()

        name = "NewStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=filter_stock_list, columns=[name])
        data_pd[name] = "次新股"
        data_pd.to_csv(file)

        return filter_stock_list

    def get_negative_netprofit_ttm_stock_date(self, date):

        """ 股票池 净利润TTM为负数的股票 """

        path = StockFactorData().get_h5_path("mfc_primary")
        data = StockFactorData().read_factor_h5(factor_name="NetProfitDeducted", path=path)
        data_ttm = StockFactorOperate().change_single_quarter_to_ttm_quarter(data)

        quarter_date = Date().get_last_stock_quarter_date(date)

        data_date = pd.DataFrame(data_ttm[quarter_date])
        data_date = data_date.dropna()
        data_date = data_date[data_date[quarter_date] < 0.0]

        filter_stock_list = list(set(data_date.index))
        filter_stock_list.sort()

        name = "NegativeNeProfitStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=filter_stock_list, columns=[name])
        data_pd.loc[filter_stock_list, name] = data_date.loc[filter_stock_list, quarter_date]
        data_pd.to_csv(file)

        return filter_stock_list

    def get_freemv_ratio_stock_date(self, ratio, date):

        """ 股票池 取自由流通市值后x%的股票 """

        path = StockFactorData().get_h5_path("mfc_primary")
        data = StockFactorData().read_factor_h5(factor_name="Mkt_freeshares", path=path)

        data /= 100000000
        data_date = pd.DataFrame(data[date])
        data_date = data_date.dropna()
        data_date = data_date.sort_values(by=[date])

        beg_loc = 0
        end_loc = int(len(data_date) * ratio)
        data_date = data_date.iloc[beg_loc:end_loc, :]

        filter_stock_list = list(set(data_date.index))
        filter_stock_list.sort()

        name = "SmallFreeMVRatioStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=filter_stock_list, columns=[name])
        data_pd[name] = "自由流通市值后%s" % ratio
        data_pd.to_csv(file)

        return filter_stock_list

    def get_trade_amount_ratio_stock_date(self, ratio, date):

        """
        股票池 过去60个交易日交易额后x%的股票
        （交易额为0的情况，很可能是未上市或者股票停牌）需要特还成为NAN
        """

        path = StockFactorData().get_h5_path("mfc_primary")
        data = StockFactorData().read_factor_h5(factor_name="TradeAmount", path=path).T
        data /= 100000000
        beg_date = Date().get_trade_date_offset(date, -60)
        end_date = date
        data = data.replace(0.0, np.nan)
        data = data.loc[beg_date:end_date, :]
        data_mean = data.mean()

        data_date = pd.DataFrame(data_mean)
        data_date = data_date.dropna()
        data_date.columns = ['TradeAmount']
        data_date = data_date.loc[data_date['TradeAmount'] > 0.0, :]
        data_date = data_date.sort_values(by=["TradeAmount"])

        beg_loc = 0
        end_loc = int(len(data_date) * ratio)
        data_date = data_date.iloc[beg_loc:end_loc, :]

        filter_stock_list = list(set(data_date.index))
        filter_stock_list.sort()

        name = "SmallTradeAmountRatioStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=filter_stock_list, columns=[name])
        data_pd[name] = "最近交易额后%s" % ratio
        data_pd.to_csv(file)

        return filter_stock_list

    def get_trade_amount_threshold_stock_date(self, threshold, date):

        """
        股票池 过去60个交易日交易额大于一定金额的股票
        （交易额为0的情况，很可能是未上市或者股票停牌）需要替换成为NAN
        简单考虑 基金规模5个亿 持股比例1% 单次换手30% 交易额为150万 假设不能超过其总交易额的5%
        日均交易额的最小值约为3000万，即0.3亿
        """

        path = StockFactorData().get_h5_path("mfc_primary")
        data = StockFactorData().read_factor_h5(factor_name="TradeAmount", path=path).T
        data /= 100000000
        beg_date = Date().get_trade_date_offset(date, -60)
        end_date = date
        data = data.replace(0.0, np.nan)
        data = data.loc[beg_date:end_date, :]
        data_mean = data.mean()

        data_date = pd.DataFrame(data_mean)
        data_date = data_date.dropna()
        data_date.columns = ['TradeAmount']
        data_date = data_date.sort_values(by=["TradeAmount"])
        data_date = data_date.loc[data_date['TradeAmount'] < threshold, :]

        filter_stock_list = list(set(data_date.index))
        filter_stock_list.sort()

        name = "SmallTradeAmountThresholdStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=filter_stock_list, columns=[name])
        data_pd[name] = "最近交易额小于%s亿" % threshold
        data_pd.to_csv(file)

        return filter_stock_list

    def get_negative_net_asset_stock_date(self, date):

        """ 净资产为负 """

        path = StockFactorData().get_h5_path("mfc_primary")
        data = StockFactorData().read_factor_h5(factor_name="TotalShareHoldeRequityDaily", path=path)
        data_date = pd.DataFrame(data[date])
        data_date = data_date.dropna()
        data_date = data_date.sort_values(by=[date])

        data_date = data_date[data_date[date] < 0.0]

        filter_stock_list = list(set(data_date.index))
        filter_stock_list.sort()

        name = "NegativeNetAssetStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=filter_stock_list, columns=[name])
        data_pd.loc[filter_stock_list, name] = data_date.loc[filter_stock_list, date]
        data_pd.to_csv(file)

        return filter_stock_list

    def get_negative_income_ttm_stock_date(self, date):

        """ 股票池 营业收入TTM为负数的股票 """

        path = StockFactorData().get_h5_path("mfc_primary")
        data = StockFactorData().read_factor_h5(factor_name="OperatingIncomeTotal", path=path)
        data_ttm = StockFactorOperate().change_single_quarter_to_ttm_quarter(data)

        quarter_date = Date().get_last_stock_quarter_date(date)

        data_date = pd.DataFrame(data_ttm[quarter_date])
        data_date = data_date.dropna()
        data_date = data_date[data_date[quarter_date] < 0.0]

        filter_stock_list = list(set(data_date.index))
        filter_stock_list.sort()

        name = "NegativeIncomeTTMStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=filter_stock_list, columns=[name])
        data_pd.loc[filter_stock_list, name] = data_date.loc[filter_stock_list, quarter_date]
        data_pd.to_csv(file)

        return filter_stock_list

    def get_bad_accounts_receivable_stock_date(self, date):

        """ 应收账款/总资产比例 不能超过200% 非国企不能超过150 """

        company_nature = StockStatic().get_nature_info()
        path = StockFactorData().get_h5_path("mfc_primary")
        recep = StockFactorData().read_factor_h5(factor_name="AccountsReceivables", path=path)

        path = StockFactorData().get_h5_path("mfc_primary")
        netasset = StockFactorData().read_factor_h5(factor_name="TotalShareHoldeRequity", path=path)

        ratio = recep.div(netasset)

        quarter_date = Date().get_last_stock_quarter_date(date)
        data_date = pd.DataFrame(ratio[quarter_date])
        data_date = data_date.dropna()
        data_date = data_date[data_date[quarter_date] > 2.0]

        list_bigger_200 = list(data_date.index)

        data_date = pd.DataFrame(ratio[quarter_date])
        data_date = data_date.dropna()
        data_date = data_date[data_date[quarter_date] > 1.5]
        data_date = pd.concat([data_date, company_nature], axis=1)
        data_date = data_date.dropna()
        data_date['if_gq'] = data_date['NATURE'].map(lambda x: "国有" in x)
        data_date = data_date[~data_date['if_gq']]

        list_bigger_150 = list(data_date.index)

        list_code = list(set(list_bigger_150) | set(list_bigger_200))
        list_code.sort()

        name = "BadAccountsReceivableStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=list_code, columns=[name])
        data_pd.loc[list_bigger_200, name] = "国企应收账款/总资产比例大于超过200%"
        data_pd.loc[list_bigger_150, name] = "非国企应收账款/总资产比例大于超过150%"
        data_pd.to_csv(file)

        return list_code

    def get_bad_goodwill_ratio_stock_date(self, date):

        """ 商誉总资产占比 > 30% 并且 占比-行业占比平均 > 30% """

        goodwill = StockFactorData().read_factor_h5("goodwillDaily")
        totalasset = StockFactorData().read_factor_h5("TotalAssetDaily")
        industry = StockFactorData().read_factor_h5("industry_citic1")

        try:
            goodwill_date = pd.DataFrame(goodwill[date])
            totalasset_date = pd.DataFrame(totalasset[date])
            industry_date = pd.DataFrame(industry[date])
            data = pd.concat([goodwill_date, totalasset_date, industry_date], axis=1)
            data = data.dropna()
            data.columns = ['goodwill', 'totalasset', 'industry']
            data['ratio'] = data['goodwill'] / data['totalasset']

            data_industry = pd.DataFrame(data.groupby(by=['industry']).median()['ratio'])
            data_industry.columns = ['industry_median_ratio']
            data_industry['industry'] = data_industry.index
            data = data.sort_values(by=['ratio'], ascending=False)

            concat_data = pd.merge(data, data_industry, on="industry", right_index=True)
            concat_data['ratio_diff'] = concat_data['ratio'] - concat_data['industry_median_ratio']
            concat_data = concat_data[concat_data['ratio_diff'] > 0.30]
            concat_data = concat_data[concat_data['ratio'] > 0.30]

            list_code = list(concat_data.index)
            list_code.sort()
        except Exception as e:
            list_code = []

        name = "BadGoodwillRatioStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=list_code, columns=[name])
        data_pd.loc[list_code, name] = "商誉占比大于30%且超过行业30%"
        data_pd.to_csv(file)

    def get_bad_pledge_ratio_stock_date(self, date):

        """ 历史质押记录中未解压的部分，质押股本比例 / 前3大股东持股比例超90%
        且 质押股本比例 / 前1、2、3大股东持股比例 排前10%的上市公司 """

        pledge = StockStatic().get_stock_pledge()
        pledge = pledge[['wind_code', 'pledged_shares',
                         'pledge_start_date', 'pledge_end_date', 'pledge_termination_date']]
        pledge = pledge[pledge['pledge_start_date'] <= date]
        pledge['pledge_termination_date'] = pledge['pledge_termination_date'].replace("None", "20991231")
        pledge['pledge_end_date'] = pledge['pledge_end_date'].replace("None", "20991231")
        pledge = pledge[pledge['pledge_termination_date'] > date]
        pledge = pledge[pledge['pledge_end_date'] > date]

        path = StockFactorData().get_h5_path("mfc_primary")
        netasset = StockFactorData().read_factor_h5(factor_name="SharePledgeRatio", path=path)
        return []

    def get_bad_pledge_stock_date(self, date):

        """ 加上 最新股价 < 质押日股价 * 质押率(0.5) * 预警线(1.6)
        且 质押股本比例 > 质押股本预警比例(0.2) 的方式筛选出的上市公司 """

        pledge = StockStatic().get_stock_pledge()
        pledge = pledge[['wind_code', 'pledged_shares',
                         'pledge_start_date', 'pledge_end_date', 'pledge_termination_date']]
        pledge = pledge[pledge['pledge_start_date'] <= date]
        pledge['pledge_termination_date'] = pledge['pledge_termination_date'].replace("None", "20991231")
        pledge['pledge_end_date'] = pledge['pledge_end_date'].replace("None", "20991231")
        pledge = pledge[pledge['pledge_termination_date'] > date]
        pledge = pledge[pledge['pledge_end_date'] > date]

        return []

    def get_bad_audit_category(self, date):

        """ 最近年报审计意见非 标准无保留意见 """

        data = StockStatic().get_audit_category_date(date)
        data = data.dropna()
        year_date = Date().get_last_stock_year_report_date(date)
        data_bad = data[data[year_date] != "标准无保留意见"]

        if len(data_bad) == 0:
            list_code = []
        else:
            list_code = list(data_bad.index.values)
            list_code.sort()

        name = "BadAuditCategoryStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=list_code, columns=[name])
        data_pd.loc[list_code, name] = data_bad.loc[list_code, year_date]
        data_pd.to_csv(file)
        return list_code

    def get_illegality_stock_date(self, date):

        """ 最近半年被 中国证券监督管理委员会、上海证券交易所或深圳证券交易所 处罚过的上市公司"""

        illegality = StockStatic().get_stock_illegality()
        illegality = illegality[['wind_code', 'announce_date',
                                 'breach_subject', 'processor', 'sec_name']]
        date_180days = Date().get_normal_date_offset(date, -180)
        illegality = illegality[illegality['announce_date'] <= date]
        illegality = illegality[illegality['announce_date'] > date_180days]

        def processor_fun(x):

            bool_1 = "中国证券监督管理委员会" in x
            bool_2 = "深圳证券交易所" in x
            bool_3 = "上海证券交易所" in x
            bool = bool_1 or bool_2 or bool_3
            return bool

        illegality = illegality[illegality['processor'].map(processor_fun)]

        if len(illegality) == 0:
            list_code = []
        else:
            list_code = list(illegality['wind_code'].values)
            list_code.sort()

        name = "IllegalityStockPool"
        sub_path = os.path.join(self.data_path_forbid_pool, name)
        file = os.path.join(sub_path, "%s_%s.csv" % (name, date))

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        data_pd = pd.DataFrame([], index=list_code, columns=[name])
        data_pd.loc[list_code, name] = "最近半年被处罚"
        data_pd.to_csv(file)
        return list_code

    def get_forbid_pool(self, name, date):

        """ 得到最近一个 禁投库 """

        sub_path = os.path.join(self.data_path_forbid_pool, name)

        file_list = os.listdir(sub_path)
        date_list = list(map(lambda x: x[-12:-4], file_list))
        date_list.sort()
        date_list_pd = pd.DataFrame(date_list, index=date_list, columns=["date"])
        date_list_pd = date_list_pd[date_list_pd['date'] <= date]
        last_trade_days = date_list_pd.index[-1]

        file = os.path.join(sub_path, "%s_%s.csv" % (name, last_trade_days))
        data_pd = pd.read_csv(file, index_col=[0], encoding='gbk')
        data_pd = data_pd[~data_pd.index.duplicated()]
        print(file)

        return data_pd

    def cal_forbid_pool_all(self,
                            beg_date="20040101",
                            end_date=datetime.today().strftime("%Y%m%d"),
                            period="W"):

        """ 计算所有禁投库 """

        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            print("Cal Stock Forbid Pool %s" % date)
            # self.get_delist_stock_date(date)
            # self.get_bad_audit_category(date)
            # self.get_st_stock_date(date)
            self.get_bad_goodwill_ratio_stock_date(date)
            # self.get_bad_pledge_stock_date(date)
            # self.get_sub_new_date(date)
            # self.get_negative_netprofit_ttm_stock_date(date)
            # self.get_freemv_ratio_stock_date(0.2, date)
            # self.get_negative_income_ttm_stock_date(date)
            # self.get_bad_accounts_receivable_stock_date(date)
            # self.get_illegality_stock_date(date)
            # self.get_negative_net_asset_stock_date(date)
            # self.get_trade_amount_threshold_stock_date(0.3, date)
            # self.get_trade_amount_ratio_stock_date(0.2, date)


if __name__ == '__main__':

    # StockForbidPool
    ################################################################################
    self = StockForbidPool()
    # self.cal_st_data()

    date = "20181203"
    # print(self.get_bad_accounts_receivable_stock_date(date))
    # print(self.get_bad_pledge_stock_date(date))
    # print(self.get_freemv_ratio_stock_date(0.2, date))
    self.cal_forbid_pool_all(beg_date="20040101", period="W")

    ################################################################################
