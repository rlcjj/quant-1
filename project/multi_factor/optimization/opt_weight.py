import os
from datetime import datetime

import pandas as pd
from project.multi_factor.alpha_model.test.method_sample.factor_return_sample import FactorReturnSample
from quant.data.data import Data
from quant.fund.fund_factor import FundFactor
from quant.fund.fund_pool import FundPool
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad
from quant.stock.barra import Barra
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.utility.code_format import CodeFormat


class OptWeight(Data):

    def __init__(self):

        """
        优化函数母类
        主要是共同的取数据函数
        """

        Data.__init__(self)

        self.port_name = ""
        self.weight_name = ""
        self.benchmark_code = ""
        self.stock_pool_name = ""

        self.industry_deviate = ""
        self.style_deviate = ""
        self.stock_deviate = ""
        self.double_turnover = ""
        self.min_tor = 0.001  # 权重最小容忍值
        self.style_columns = []
        self.weight_sum = 0.95
        self.track_error = 0.05
        self.weight_type = 'fixed'

        self.free_mv = None
        self.trading_status = None
        self.alpha_data = None
        self.date_series = None
        self.wind_port_path = WindPortUpLoad().path

    def update_data(self):

        """ 更新数据 指数风格行业暴露 股票协方差矩阵等等 """

        end_date = datetime.today()
        beg_date = Date().get_trade_date_offset(end_date, -10)
        Index().cal_index_exposure(self.weight_name, beg_date, end_date)
        Barra().cal_stock_covariance_period(beg_date, end_date)

    def get_stock_sum_date(self, date):

        """ 总股票权重 """

        if self.weight_type == 'ptgp_fund':
            quarter_date = Date().get_last_fund_quarter_date(date)
            stock_ratio = FundFactor().get_fund_factor('Stock_Ratio').T
            fund_pool = FundPool().get_fund_pool_code(name="普通股票型基金", date=quarter_date)
            weight_stock = stock_ratio.loc[fund_pool, quarter_date].median() / 100.0
        else:
            weight_stock = self.weight_sum

        return weight_stock

    def get_alpha_factor(self, alpha_name, alpha_type):

        """ 得到alpha """

        if alpha_type == "my_alpha":
            self.alpha_data = Stock().read_factor_h5(alpha_name, Stock().get_h5_path("my_alpha"))
        elif alpha_type == 'my_res_sample_alpha':
            self.alpha_data = FactorReturnSample(alpha_name).get_alpha_res()

        if len(self.alpha_data.index[0]) <= 6:
            self.alpha_data.index = self.alpha_data.index.map(CodeFormat.stock_code_add_postfix)

    def get_benchmark_weight_date(self, date):

        """ 得到 股票基准权重 """

        benchmark_weight = Index().get_weight_date(index_code=self.weight_name, date=date)
        benchmark_weight.columns = ['BenchWeight']
        return benchmark_weight

    def get_invest_stock_pool_date(self, date):

        """ 得到 可投资股票池 """

        stock_pool = Stock().get_invest_stock_pool(self.stock_pool_name, date)
        return stock_pool

    def get_none_suspension_stock_date(self, date):

        """ 得到 非停牌股票池 """

        status = pd.DataFrame(self.trading_status[date])
        status = status[status[date] == 0.0]
        code_list = list(status.index)
        return code_list

    def get_can_trade_stock_date(self, date):

        """ 得到 当日可交易股票池（停牌股票和投资股票池日期不一致）"""

        last_date = Date().get_trade_date_offset(date, -1)
        invest_stock = self.get_invest_stock_pool_date(last_date)
        none_suspension_stock = self.get_none_suspension_stock_date(date)
        can_trade_stock = list(set(invest_stock) & set(none_suspension_stock))
        can_trade_stock.sort()
        print("Stock Can Trade Number is ", len(can_trade_stock))
        return can_trade_stock

    def get_stock_alpha_date(self, date):

        """ 得到 最近股票 alpha """

        date_list = list(self.alpha_data.columns)
        date_list.sort()
        date_list_pd = pd.DataFrame(date_list, columns=['date'])
        date_list_pd = date_list_pd[date_list_pd['date'] <= date]
        last_date = date_list_pd.loc[date_list_pd.index[-1], 'date']

        stock_alpha = pd.DataFrame(self.alpha_data[last_date])
        stock_alpha = stock_alpha.dropna()
        stock_alpha.columns = ['Alpha']
        return stock_alpha

    def get_benchmark_risk_exposure_date(self, date):

        """ 得到 基准 risk exposure_return """

        type_list = ['COUNTRY', 'STYLE', 'INDUSTRY']
        exposure = Index().get_index_exposure_date(self.weight_name, date, type_list)
        return exposure

    def get_stock_covariance_date(self, date):

        """ 得到 股票协方差矩阵 """

        Barra().cal_stock_covariance(date)
        stock_cov = Barra().get_stock_covariance(date)
        return stock_cov

    def get_stock_risk_exposure_date(self, date):

        """ 得到股票 risk exposure_return """

        type_list = ['COUNTRY', 'STYLE', 'INDUSTRY']
        data = Barra().get_factor_exposure_date(date, type_list)
        return data

    def get_stock_weight_limit_up(self, date):

        """ 得到股票投资绝对权重上限（与市值相关） """

        free_mv_date = pd.DataFrame(self.free_mv[date])
        free_mv_date.columns = ['FreeMV']
        free_mv_date = free_mv_date.dropna()
        free_mv_date = free_mv_date.sort_values(by=['FreeMV'], ascending=False)
        free_mv_date['UpRatio'] = 0.02

        number = len(free_mv_date)
        free_mv_date.loc[free_mv_date.index[0:int(number/20)], "UpRatio"] = 0.05
        free_mv_date.loc[free_mv_date.index[int(number/20):int(number/10)], "UpRatio"] = 0.04
        free_mv_date.loc[free_mv_date.index[int(number/10):int(number/5)], "UpRatio"] = 0.03

        return free_mv_date

    def get_last_stock_weight(self, date):

        """ 得到上期股票权重 """

        try:
            sub_path = os.path.join(self.wind_port_path, self.port_name)
            file_list = os.listdir(sub_path)
            date_list = list(map(lambda x: x[-12:-4], file_list))
            date_list.sort()

            date_pd = pd.DataFrame(date_list, columns=['date'], index=date_list)
            last_date = date_pd[date_pd['date'] < date].iloc[-1, 0]
            print("Get Last Weight At Date %s" % last_date)

            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, last_date))
            weight = pd.read_csv(file, index_col=[0], encoding='gbk')
            weight = pd.DataFrame(weight['Weight'])

            if "Cash" in weight.index:
                weight = weight.drop(["Cash"], axis=0)

            weight /= weight.sum()
        except Exception as e:
            stock = self.get_can_trade_stock_date(date)
            weight = pd.DataFrame([], columns=['Weight'], index=stock)
            weight = weight.fillna(0.0)

        return weight

    def generate_weight_file(self, weight, date, next_date):

        """ 基金权重文件 """

        weight = weight[weight['Weight'] > self.min_tor]
        weight = weight.sort_values(by=['Weight'], ascending=False)
        weight /= weight.sum()
        print("Number of multi_factor", len(weight), date)

        weight.index.name = "Code"
        weight['Name'] = weight.index.map(lambda x: Stock().get_stock_name_date(x, next_date))
        weight["CreditTrading"] = "No"
        weight["Date"] = next_date
        weight["Price"] = 0.0
        weight["Direction"] = "Long"
        weight_sum = self.get_stock_sum_date(date)
        weight['Weight'] *= weight_sum
        weight.loc['Cash', 'Weight'] = 1 - weight_sum

        sub_path = os.path.join(self.wind_port_path, self.port_name)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, next_date))
        weight.to_csv(file)

    def backtest(self):

        """ 计算 回测结果 """

        port = BackTest()
        port.set_info(self.port_name, self.benchmark_code)
        port.read_weight_at_all_change_date()
        port.cal_weight_at_all_daily()
        port.cal_port_return()
        port.cal_turnover()
        port.cal_summary()


if __name__ == '__main__':

    # 因子
    self = OptWeight()
