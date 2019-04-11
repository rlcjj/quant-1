import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.macro import Macro
from quant.stock.stock import Stock

from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_bp import AlphaBP
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_roe import AlphaROE
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_asset_yoy import AlphaAssetYoY


class FamaFrench(Data):

    """
    Fama-French模型
    https://xueqiu.com/8287840120/71025121
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\fama_french'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def load_data(self, beg_date, end_date):

        """ 下载更新模型需要的数据 """

        # Stock().load_h5_primary_factor()
        AlphaBP().cal_factor_exposure(beg_date, end_date)
        AlphaROE().cal_factor_exposure(beg_date, end_date)
        AlphaAssetYoY().cal_factor_exposure(beg_date, end_date)

    def cal_all_factor_pct(self):

        """ 计算所有的因子收益 """

        self.cal_index_excess_pct()
        self.cal_smb_factor_pct()
        self.cal_hmi_factor_pct()
        self.cal_rmw_factor_pct()
        self.cal_cma_factor_pct()

    @staticmethod
    def get_stock_excess_pct():

        """ 得到股票超额收益率 """

        stock_pct = Stock().read_factor_h5("Pct_chg").T
        free_pct = Macro().get_daily_risk_free_rate()
        free_pct = free_pct['RiskFreeRate']

        stock_excess_pct = stock_pct.sub(free_pct, axis='index')
        stock_excess_pct = stock_excess_pct.dropna(how='all')

        return stock_excess_pct

    def cal_index_excess_pct(self):

        """ 计算指数超额收益率 """

        name = "Market"
        index_pct = Index().get_index_factor("000985.CSI", attr=['CLOSE'])
        index_pct = index_pct.iloc[0:-1, :]
        index_pct = index_pct.pct_change()
        index_pct.columns = ['StockIndexReturn']
        index_pct = index_pct['StockIndexReturn'] * 100

        free_pct = Macro().get_daily_risk_free_rate()
        free_pct = free_pct['RiskFreeRate']
        index_excess_pct = index_pct.sub(free_pct, axis='index')
        index_excess_pct = index_excess_pct.dropna()
        index_excess_pct = pd.DataFrame(index_excess_pct)
        index_excess_pct.columns = [name]
        index_excess_pct['CumSumReturn'] = index_excess_pct[name].cumsum()

        index_excess_pct.to_csv(os.path.join(self.data_path, 'factor_return', 'FactorReturn_%s.csv' % name))

    def cal_smb_factor_pct(self):

        """ 计算大市值股票相对于小市值股票的超额收益（分成三组） """

        name = "SMB"
        share_all = Stock().read_factor_h5("TotalShare")
        price_close = Stock().read_factor_h5("PriceCloseUnadjust")
        stock_pct = Stock().read_factor_h5("Pct_chg")
        total_mv = price_close.mul(share_all) / 100000000

        date_series = list(set(stock_pct.columns) & set(total_mv.columns))
        date_series.sort()

        result = pd.DataFrame([], index=date_series, columns=[name])

        for i_date in range(1, len(date_series)):

            date = date_series[i_date]
            last_date = date_series[i_date - 1]
            data_date = pd.concat([total_mv[last_date], stock_pct[date]], axis=1)
            data_date = data_date.dropna()
            data_date.columns = ['LastMv', 'Return']

            data_date = data_date.sort_values(by=['LastMv'])
            location = int(len(data_date) / 3)
            small_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            data_date = data_date.sort_values(by=['LastMv'], ascending=False)
            location = int(len(data_date) / 3)
            big_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            result.loc[date, name] = small_stock_pct_mean - big_stock_pct_mean

        result = result.dropna()
        result['CumSumReturn'] = result[name].cumsum()
        result.to_csv(os.path.join(self.data_path, 'factor_return', 'FactorReturn_%s.csv' % name))

    def cal_hmi_factor_pct(self):

        """ 计算高估值股票相对于低估值股票的超额收益（分成三组） """

        name = "HMI"
        bp = AlphaFactor().get_alpha_factor_exposure("alpha_raw_bp")
        stock_pct = Stock().read_factor_h5("Pct_chg")

        date_series = list(set(stock_pct.columns) & set(bp.columns))
        date_series.sort()

        result = pd.DataFrame([], index=date_series, columns=[name])

        for i_date in range(1, len(date_series)):

            date = date_series[i_date]
            last_date = date_series[i_date - 1]
            data_date = pd.concat([bp[last_date], stock_pct[date]], axis=1)
            data_date = data_date.dropna()
            data_date.columns = ['LastBP', 'Return']

            data_date = data_date.sort_values(by=['LastBP'])
            location = int(len(data_date) / 3)
            low_bp_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            data_date = data_date.sort_values(by=['LastBP'], ascending=False)
            location = int(len(data_date) / 3)
            high_bp_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            result.loc[date, name] = high_bp_stock_pct_mean - low_bp_stock_pct_mean

        result = result.dropna()
        result['CumSumReturn'] = result[name].cumsum()
        result.to_csv(os.path.join(self.data_path, 'factor_return', 'FactorReturn_%s.csv' % name))

    def cal_rmw_factor_pct(self):

        """ 计算高ROE股票相对于低ROE股票的超额收益（分成三组） """

        name = "RMW"
        bp = AlphaFactor().get_alpha_factor_exposure("alpha_raw_roe")
        stock_pct = Stock().read_factor_h5("Pct_chg")

        date_series = list(set(stock_pct.columns) & set(bp.columns))
        date_series.sort()

        result = pd.DataFrame([], index=date_series, columns=[name])

        for i_date in range(1, len(date_series)):

            date = date_series[i_date]
            last_date = date_series[i_date - 1]
            data_date = pd.concat([bp[last_date], stock_pct[date]], axis=1)
            data_date = data_date.dropna()
            data_date.columns = ['LastROE', 'Return']

            data_date = data_date.sort_values(by=['LastROE'])
            location = int(len(data_date) / 3)
            low_roe_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            data_date = data_date.sort_values(by=['LastROE'], ascending=False)
            location = int(len(data_date) / 3)
            high_roe_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            result.loc[date, name] = high_roe_stock_pct_mean - low_roe_stock_pct_mean

        result = result.dropna()
        result['CumSumReturn'] = result[name].cumsum()
        result.to_csv(os.path.join(self.data_path, 'factor_return', 'FactorReturn_%s.csv' % name))

    def cal_cma_factor_pct(self):

        """ 计算高资产增长率股票相对于低资产增长率股票的超额收益（分成三组）投资水平风险代表投资风险水平 """

        name = "CMA"
        bp = AlphaFactor().get_alpha_factor_exposure("alpha_raw_asset_yoy")
        stock_pct = Stock().read_factor_h5("Pct_chg")

        date_series = list(set(stock_pct.columns) & set(bp.columns))
        date_series.sort()

        result = pd.DataFrame([], index=date_series, columns=[name])

        for i_date in range(1, len(date_series)):

            date = date_series[i_date]
            last_date = date_series[i_date - 1]
            data_date = pd.concat([bp[last_date], stock_pct[date]], axis=1)
            data_date = data_date.dropna()
            data_date.columns = ['LastAssetYOY', 'Return']

            data_date = data_date.sort_values(by=['LastAssetYOY'])
            location = int(len(data_date) / 3)
            low_assetyoy_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            data_date = data_date.sort_values(by=['LastAssetYOY'], ascending=False)
            location = int(len(data_date) / 3)
            high_assetyoy_stock_pct_mean = data_date.loc[data_date.index[0:location], 'Return'].mean()

            result.loc[date, name] = high_assetyoy_stock_pct_mean - low_assetyoy_stock_pct_mean

        result = result.dropna()
        result['CumSumReturn'] = result[name].cumsum()
        result.to_csv(os.path.join(self.data_path, 'factor_return', 'FactorReturn_%s.csv' % name))

    def get_factor_pct(self, name):

        """ 得到因子收益率 """

        file = os.path.join(self.data_path, 'factor_return', 'FactorReturn_%s.csv' % name)
        data = pd.read_csv(file, index_col=[0], encoding='gbk', usecols=[0, 1])
        data.index = data.index.map(str)
        return data

    def ff3_model(self, beg_date, end_date):

        """ 三因素模型 市场 市值 估值 """

        term = 60
        stock_excess_pct = self.get_stock_excess_pct()
        index_excess_pct = self.get_factor_pct("Market")
        smb_factor_pct = self.get_factor_pct("SMB")
        hmi_factor_pct = self.get_factor_pct("HMI")

        date_series_all = Date().get_trade_date_series(beg_date, end_date)
        alpha = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        market_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        size_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        bp_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        res_return = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)

        for i_stock in range(len(stock_excess_pct.columns)):

            stock_code = stock_excess_pct.columns[i_stock]
            print("Calculate FF3 Model %s From %s To %s" % (stock_code, beg_date, end_date))
            data = pd.concat([stock_excess_pct[stock_code], index_excess_pct, smb_factor_pct, hmi_factor_pct], axis=1)
            data = data.dropna()
            data = data.astype(np.float)

            date_series = list(set(data.index) & set(date_series_all))
            date_series.sort()

            for i_date in range(len(date_series)):

                ed_date = date_series[i_date]
                bg_date = Date().get_trade_date_offset(ed_date, -term)
                data_period = data.loc[bg_date:ed_date, :]

                y = data_period.iloc[:, 0].values
                x = data_period.iloc[:, 1:].values
                x_add = sm.add_constant(x)
                stock_vol = np.std(y) / 100 * np.sqrt(250)

                if len(data_period) >= term or stock_vol > 0.05:
                    try:
                        model = sm.OLS(y, x_add)
                        res = model.fit()
                        residual_return_series = y - np.dot(x_add, res.params)
                        alpha.loc[ed_date, stock_code] = res.params[0]
                        market_beta.loc[ed_date, stock_code] = res.params[1]
                        size_beta.loc[ed_date, stock_code] = res.params[2]
                        bp_beta.loc[ed_date, stock_code] = res.params[3]
                        res_return.loc[ed_date, stock_code] = residual_return_series[-1]
                    except Exception as e:
                        print("Regression not Successful %s %s" % (stock_code, ed_date))
                else:
                    print("Length is Small or Stock Vol is Small %s %s" % (stock_code, ed_date))

        alpha = alpha.T
        market_beta = market_beta.T
        size_beta = size_beta.T
        bp_beta = bp_beta.T
        res_return = res_return.T

        path = os.path.join(self.data_path, "model_ff3")
        Stock().write_factor_h5(alpha, factor_name="FF3_Alpha", path=path)
        Stock().write_factor_h5(market_beta, factor_name="FF3_Market", path=path)
        Stock().write_factor_h5(size_beta, factor_name="FF3_Size", path=path)
        Stock().write_factor_h5(bp_beta, factor_name="FF3_BP", path=path)
        Stock().write_factor_h5(res_return, factor_name="FF3_ResidualReturn", path=path)

        alpha.to_csv(os.path.join(path, "FF3_Alpha.csv"))
        market_beta.to_csv(os.path.join(path, "FF3_Market.csv"))
        size_beta.to_csv(os.path.join(path, "FF3_Size.csv"))
        bp_beta.to_csv(os.path.join(path, "FF3_BP.csv"))
        res_return.to_csv(os.path.join(path, "FF3_ResidualReturn.csv"))

    def ff5_model(self, beg_date, end_date):

        """ 五因素模型 市场 市值 估值 盈利 资产增长率 """

        term = 60
        beg_date = Date().change_to_str(beg_date)
        end_date = Date().change_to_str(end_date)
        stock_excess_pct = self.get_stock_excess_pct()
        index_excess_pct = self.get_factor_pct("Market")
        smb_factor_pct = self.get_factor_pct("SMB")
        hmi_factor_pct = self.get_factor_pct("HMI")
        rmw_factor_pct = self.get_factor_pct("RMW")
        cma_factor_pct = self.get_factor_pct("CMA")

        date_series_all = Date().get_trade_date_series(beg_date, end_date)
        alpha = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        market_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        size_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        bp_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        roe_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        assetyoy_beta = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)
        res_return = pd.DataFrame([], index=date_series_all, columns=stock_excess_pct.columns)

        for i_stock in range(len(stock_excess_pct.columns)):

            stock_code = stock_excess_pct.columns[i_stock]
            print("Calculate FF5 Model %s From %s To %s" % (stock_code, beg_date, end_date))
            data = pd.concat([stock_excess_pct[stock_code], index_excess_pct,
                              smb_factor_pct, hmi_factor_pct, rmw_factor_pct, cma_factor_pct], axis=1)
            data = data.dropna()
            data = data.astype(np.float)

            date_series = list(set(data.index) & set(date_series_all))
            date_series.sort()

            for i_date in range(len(date_series)):

                ed_date = date_series[i_date]
                bg_date = Date().get_trade_date_offset(ed_date, -term)
                data_period = data.loc[bg_date:ed_date, :]

                y = data_period.iloc[:, 0].values
                x = data_period.iloc[:, 1:].values
                x_add = sm.add_constant(x)
                stock_vol = np.std(y) / 100 * np.sqrt(250)

                if len(data_period) >= term or stock_vol > 0.05:
                    try:
                        model = sm.OLS(y, x_add)
                        res = model.fit()
                        residual_return_series = y - np.dot(x_add, res.params)
                        alpha.loc[ed_date, stock_code] = res.params[0]
                        market_beta.loc[ed_date, stock_code] = res.params[1]
                        size_beta.loc[ed_date, stock_code] = res.params[2]
                        bp_beta.loc[ed_date, stock_code] = res.params[3]
                        roe_beta.loc[ed_date, stock_code] = res.params[4]
                        assetyoy_beta.loc[ed_date, stock_code] = res.params[5]
                        res_return.loc[ed_date, stock_code] = residual_return_series[-1]
                    except Exception as e:
                        print("Regression not Successful %s %s" % (stock_code, ed_date))
                else:
                    print("Length is Small or Stock Vol is Small %s %s" % (stock_code, ed_date))

        alpha = alpha.T
        market_beta = market_beta.T
        size_beta = size_beta.T
        bp_beta = bp_beta.T
        roe_beta = roe_beta.T
        assetyoy_beta = assetyoy_beta.T
        res_return = res_return.T

        path = os.path.join(self.data_path, "model_ff5")
        Stock().write_factor_h5(alpha, factor_name="FF5_Alpha", path=path)
        Stock().write_factor_h5(market_beta, factor_name="FF5_Market", path=path)
        Stock().write_factor_h5(size_beta, factor_name="FF5_Size", path=path)
        Stock().write_factor_h5(bp_beta, factor_name="FF5_BP", path=path)
        Stock().write_factor_h5(roe_beta, factor_name="FF5_ROE", path=path)
        Stock().write_factor_h5(assetyoy_beta, factor_name="FF5_AssetYOY", path=path)
        Stock().write_factor_h5(res_return, factor_name="FF5_ResidualReturn", path=path)

        alpha.to_csv(os.path.join(path, "FF5_Alpha.csv"))
        market_beta.to_csv(os.path.join(path, "FF5_Market.csv"))
        size_beta.to_csv(os.path.join(path, "FF5_Size.csv"))
        bp_beta.to_csv(os.path.join(path, "FF5_BP.csv"))
        roe_beta.to_csv(os.path.join(path, "FF5_ROE.csv"))
        assetyoy_beta.to_csv(os.path.join(path, "FF5_AssetYOY.csv"))
        res_return.to_csv(os.path.join(path, "FF5_ResidualReturn.csv"))

    def get_data(self, model_name="model_ff3", factor_name="FF3_Alpha"):

        """ 得到数据 """
        path = os.path.join(self.data_path, model_name)
        data = Stock().read_factor_h5(factor_name=factor_name, path=path)
        return data

if __name__ == '__main__':

    from datetime import datetime
    beg_date = "20190101"
    today = datetime.today().strftime("%Y%m%d")
    model_name = "model_ff3"
    factor_name = "FF3_Alpha"

    self = FamaFrench()

    # self.load_data(beg_date, today)
    # self.cal_all_factor_pct()
    # self.ff3_model(beg_date, end_date)
    # self.ff5_model("20150101", "20180101")
    print(self.get_data(model_name, factor_name))
