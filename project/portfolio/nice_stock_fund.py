import os
import numpy as np
import pandas as pd
import cvxpy as cvx
from datetime import datetime

from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.barra import Barra
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad
from quant.fund.fund_exposure import FundExposure
from quant.fund.fund_return_decomposition import FundReturnDecomposition


class NiceStockFund(Data):

    """
    优选股票型基金

    1、股票型基金（指数+增强+普通股票+偏股混合+灵活配置60以上）或者主动股票型（普通股票+偏股混合-量化基金）
    2、剔除新基金、最近基金经理有变动的基金
    3、回归的方法，计算基金Alpha（或者假设半年报、年报持仓不变，计算基金Alpha）
    4、得到基金的风格、仓位、行业暴露（利用持仓）
    5、最大化Alpha的同时，控制风格偏露
    6、控制换手率25%，构建每期组合
    7、本地回测组合表现
    8、上传wind组合回测

    未来可能再改进的方向
    1、剔除基金最近经理变动的基金
    2、考虑基金公司，是单只基金表现好，还是多个基金表现好
    3、2016年偏小盘，可能是回归指数没有比中证1000更小的指数
    4、考虑机构占比，机构可能知道更多的信息
    5、考虑真实费率，在费率和换手率之间到达平衡（申购赎回费率=0.5%+0.5%）
    （还可以考虑C类份额，大于500万只收1000元每笔，回测了高换手的50%组合，感觉不是特别理想，整体还是先控制换手）
    6、某些行业基金有短期的Alpha

    """

    def __init__(self,
                 fund_pool_name="指数+主动股票+灵活配置60基金",
                 benchmark_name="基金持仓基准基金池",
                 alpha_len=750,
                 alpha_column="RegressAlphaIR",
                 port_name="股票型基金优选750AlphaIR",
                 style_deviate=0.10,
                 position_deviate=0.02,
                 fund_up_ratio=0.15,
                 turnover=0.30
                 ):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\nice_stock_fund'
        self.port_name = port_name
        self.fund_pool_name = fund_pool_name
        self.benchmark_name = benchmark_name

        self.alpha_len = alpha_len
        self.setup_date_len = self.alpha_len + 50
        self.style_deviate = style_deviate
        self.position_deviate = position_deviate
        self.fund_up_ratio = fund_up_ratio
        self.turnover = turnover  # double
        self.alpha_column = alpha_column

        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path, self.port_name)
        self.port_path = os.path.join(WindPortUpLoad().path, self.port_name)
        if not os.path.exists(self.port_path):
            os.makedirs(self.port_path)
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    @staticmethod
    def update_data():

        """ 更新所需要的数据 """

        end_date = datetime.today().strftime("%Y%m%d")
        fund_pool_name = "指数+主动股票+灵活配置60基金"

        beg_date = Date().get_trade_date_offset(end_date, -20)
        print("下载指数数据 %s To %s ......" % (beg_date, end_date))
        Index().load_index_factor_all(beg_date, end_date)

        beg_date = Date().get_trade_date_offset(end_date, -120)
        print("计算所有股票型基在宽基指数上的暴露 %s To %s ......" % (beg_date, end_date))
        fund_exposure = FundExposure()
        fund_exposure.get_data()
        fund_exposure.cal_fund_regression_exposure_index_all(beg_date, end_date,
                                                             fund_pool=fund_pool_name, file_rewrite=True)

        beg_date = Date().get_trade_date_offset(end_date, -120)
        print("计算所有股票型基回归掉宽基指数后的Alpha %s To %s ......" % (beg_date, end_date))
        fund_return = FundReturnDecomposition()
        fund_return.cal_fund_regression_risk_alpha_return_index_all(beg_date, end_date,
                                                                    fund_pool=fund_pool_name, file_rewrite=True)

        beg_date = Date().get_trade_date_offset(end_date, -120)
        print("计算所有股票型基金的持仓暴露 %s To %s ......" % (beg_date, end_date))
        FundExposure().cal_fund_holder_exposure_halfyear_all(beg_date, end_date, fund_pool_name)

    def get_fund_pool(self, end_date):

        """ 成立时间满足一定时间的基金 """

        print("Project Nice Stock Fund Getting Fund Pool at %s ......" % end_date)
        fund_pool = Fund().get_fund_pool_all(name=self.fund_pool_name, date="20181231")
        fund_info = Fund().get_wind_fund_info()
        fund_pool.index = fund_pool['wind_code']
        fund_data = pd.concat([fund_pool, fund_info], axis=1)

        setup_date = Date().get_trade_date_offset(end_date, -self.setup_date_len)

        fund_data = fund_data[fund_data['SetupDate'] <= setup_date]
        fund_data = fund_data[['sec_name', 'SetupDate', 'InvestType', 'Corp']]
        fund_data.columns = ['SecName', 'SetupDate', 'InvestType', 'Corp']
        fund_data = fund_data.dropna()

        return fund_data

    def get_fund_manager_info(self, beg_date, end_date):

        """  当前基金经理和最近基金经理有无变动（运行时间较长，暂时没用） """

        print("Project Nice Stock Fund Getting FundManager at %s ......" % end_date)
        fund_pool = self.get_fund_pool(end_date)
        manager_columns = ['FundManager', 'FundManagerChange']
        fund_factor = pd.DataFrame([],  index=fund_pool.index, columns=manager_columns)

        for i_fund in range(len(fund_pool.index)):

            fund_code = fund_pool.index[i_fund]
            print("FundManager", fund_code, end_date)
            manager = Fund().get_fund_manager(end_date, fund_code)
            manager_change = Fund().get_fund_manager_change_info(beg_date, end_date, fund_code)
            fund_factor.loc[fund_code, "FundManager"] = manager
            fund_factor.loc[fund_code, 'FundManagerChange'] = manager_change

        return fund_factor

    def get_holder_halfyear_alpha(self, end_date):

        """ 半年持仓超额收益、基金总收益（暂时没用，用的是回归Alpha） """

        print("Project Nice Stock Fund Getting HalfYear Alpha at %s ......" % end_date)
        beg_date = Date().get_trade_date_offset(end_date, -self.alpha_len)
        fund_pool = self.get_fund_pool(end_date)
        fund_factor = pd.DataFrame([], index=fund_pool.index, columns=['FundReturn', 'HalfYearAlpha'])
        fund_return = FundReturnDecomposition()

        for i_fund in range(len(fund_pool.index)):

            fund_code = fund_pool.index[i_fund]
            # fund_return.cal_fund_holder_risk_alpha_return_halfyear(fund_code, end_date)
            try:
                alpha = fund_return.get_fund_holder_risk_alpha_return_halfyear(fund_code, end_date)
                alpha_period = alpha.loc[beg_date:end_date, :]
                if len(alpha_period) >= self.alpha_len:
                    fund_factor.loc[fund_code, "FundReturn"] = alpha_period['FundReturn'].sum()
                    fund_factor.loc[fund_code, "HalfYearAlpha"] = alpha_period['AlphaReturn'].sum()
                    print("Alpha HalfYear", fund_code, end_date)
                else:
                    print("Alpha HalfYear Data Length is Too Short", fund_code, end_date)

            except Exception as e:
                print(e)
                print("Alpha HalfYear Data is None", fund_code, end_date)

        return fund_factor

    def get_regression_index_alpha(self, end_date):

        """ 计算回归超额收益 """
        print("Project Nice Stock Fund Getting Regression Alpha at %s ......" % end_date)
        beg_date = Date().get_trade_date_offset(end_date, -self.alpha_len-1)
        fund_pool = self.get_fund_pool(end_date)
        fund_factor = pd.DataFrame([], index=fund_pool.index, columns=['RegressAlpha', 'RegressAlphaIR'])
        fund_return = FundReturnDecomposition()

        for i_fund in range(len(fund_pool.index)):

            fund_code = fund_pool.index[i_fund]

            try:
                alpha = fund_return.get_fund_regression_risk_alpha_return_index(fund_code)
                alpha_period = alpha.loc[beg_date:end_date, :]
                alpha_period['AlphaReturn'] *= 100.0
                if len(alpha_period) >= int(0.8*self.alpha_len):
                    alpha_return = alpha_period['AlphaReturn'].mean() * 250
                    alpha_std = alpha_period['AlphaReturn'].std() * np.sqrt(250)
                    fund_factor.loc[fund_code, "RegressAlpha"] = alpha_return
                    fund_factor.loc[fund_code, "RegressAlphaIR"] = alpha_return / alpha_std
                    print("Alpha Regression", fund_code, end_date)
                else:
                    print("Alpha Regression Data Length is Too Short", fund_code, end_date)

            except Exception as e:
                print(e)
                print("Alpha Regression Data is None", fund_code, end_date)

        return fund_factor

    def get_fund_risk_exposure(self, end_date):

        """ 基金持仓暴露(年报或者半年报) """

        type_list = ["STYLE", "COUNTRY"]
        fund_pool = self.get_fund_pool(end_date)
        last_halfyear_date = Date().get_last_fund_halfyear_date(end_date)
        print("Project Nice Stock Fund Getting Fund Style Exposure at %s ......" % last_halfyear_date)

        col = Barra().get_factor_name(type_list=type_list)['NAME_EN'].values
        fund_factor = pd.DataFrame([], index=fund_pool.index, columns=col)
        fund_exposure = FundExposure()

        for i_fund in range(len(fund_pool.index)):

            fund_code = fund_pool.index[i_fund]

            try:
                exposure = fund_exposure.get_fund_holder_exposure_halfyear_date(fund_code, last_halfyear_date, type_list)
                fund_factor.loc[fund_code, exposure.columns] = exposure.loc[fund_code, exposure.columns]
                print("Exposure Style", fund_code, last_halfyear_date)
            except Exception as e:
                print(e)
                print("Exposure Style is None", fund_code, last_halfyear_date)

        return fund_factor

    def cal_fund_factor_date(self, end_date):

        """ 得到单期各项因子值 """

        print("Project Nice Stock Fund Getting All Factor at %s ......" % end_date)
        # fund_manager = self.get_fund_manager_info(beg_date, end_date)
        fund_pool = self.get_fund_pool(end_date)
        # fund_holder_alpha = self.get_holder_halfyear_alpha(end_date)
        fund_index_alpha = self.get_regression_index_alpha(end_date)
        fund_exposure = self.get_fund_risk_exposure(end_date)
        fund_factor = pd.concat([fund_pool, fund_index_alpha, fund_exposure], axis=1)

        fund_factor = fund_factor.dropna(subset=[self.alpha_column])
        fund_factor = fund_factor.sort_values(by=[self.alpha_column], ascending=False)
        file = os.path.join(self.data_path, 'fund_factor', 'FundFactor_%s.csv' % end_date)
        path = os.path.join(self.data_path, 'fund_factor')
        if not os.path.exists(path):
            os.makedirs(path)
        fund_factor.to_csv(file)

    def opt_date(self, end_date, end_last_date, turnover_control=False):

        """
        单期优化
        1、风格不能偏离整体中位数太多
        2、仓位不能偏离整体中位数太多
        3、单个基金上限
        4、换手率约束
        5、每个基金管理公司最多有两只（未约束）
        6、基金个数约束（未约束）
        """

        print("Project Nice Stock Fund Optimization Fund Weight at %s ......" % end_date)

        # Fund Pool
        path = os.path.join(self.data_path, 'fund_factor')
        file = os.path.join(path, 'FundFactor_%s.csv' % end_date)
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        fund_benchmark_list = Fund().get_fund_pool_code("20181231", self.fund_pool_name)
        fund_benchmark_list = list(set(fund_benchmark_list) & set(data.index))
        fund_benchmark_list.sort()
        data = data.loc[fund_benchmark_list, :]

        # Name of Columns
        barra_style_list = Barra().get_factor_name(type_list=['STYLE'])['NAME_EN'].values
        position_list = Barra().get_factor_name(type_list=['COUNTRY'])['NAME_EN'].values
        risk_factor_list = Barra().get_factor_name(type_list=['COUNTRY', "STYLE"])['NAME_EN'].values
        alpha_col = [self.alpha_column]
        use_col = list(alpha_col)
        use_col.extend(risk_factor_list)

        # Fund Pool Filter
        data = data.dropna(subset=use_col)
        alpha_values = data[alpha_col].values
        data['UpRatio'] = self.fund_up_ratio
        weight_up_values = data['UpRatio'].values

        # BenchMark
        fund_benchmark_list = Fund().get_fund_pool_code("20181231", self.benchmark_name)
        fund_benchmark_list = list(set(fund_benchmark_list) & set(data.index))
        fund_benchmark_list.sort()

        # Val
        stock_style_values = data[barra_style_list].values
        stock_position_values = data[position_list].values
        bench_style_values = data.loc[fund_benchmark_list, barra_style_list].median().values
        bench_position_values = data.loc[fund_benchmark_list, position_list].median().values
        bench_style_up_values = bench_style_values.T + self.style_deviate
        bench_style_low_values = bench_style_values.T - self.style_deviate
        bench_position_up_values = bench_position_values.T + self.position_deviate
        bench_position_low_values = bench_position_values.T - self.position_deviate

        if len(data) == 0:
            print("Project Nice Stock Fund Length of Fund is %s at %s ...... is Zero" % (len(data), end_date))
        else:
            print("Project Nice Stock Fund Length of Fund is %s at %s ......" % (len(data), end_date))
            w = cvx.Variable(len(data))

            if turnover_control:

                try:
                    file = os.path.join(self.data_path, 'fund_opt', 'FundOpt_%s.csv' % end_last_date)
                    weight_last = pd.read_csv(file, index_col=[0], encoding='gbk')
                    weight_last = weight_last.dropna(subset=[self.alpha_column])
                    if len(weight_last) == 0:
                        weight_last = pd.Series(index=data.index)
                        weight_last = weight_last.fillna(0.0)
                        turnover = 2.00
                    else:
                        weight_last = weight_last.loc[data.index, "Weight"]
                        weight_last = weight_last.fillna(0.0)
                        turnover = self.turnover

                except Exception as e:
                    print(e)
                    weight_last = pd.Series(index=data.index)
                    weight_last = weight_last.fillna(0.0)
                    turnover = 2.00

                print(len(weight_last))
                weight_last_values = weight_last.values

                prob = cvx.Problem(cvx.Maximize(alpha_values.T * w),
                                   [cvx.sum(w) == 1,
                                    w >= 0,
                                    w <= weight_up_values,
                                    cvx.sum(cvx.abs(w - weight_last_values)) <= turnover,
                                    stock_style_values.T * w <= bench_style_up_values,
                                    stock_style_values.T * w >= bench_style_low_values,
                                    stock_position_values.T * w <= bench_position_up_values,
                                    stock_position_values.T * w >= bench_position_low_values,
                                    ])
                prob.solve()
            else:
                prob = cvx.Problem(cvx.Maximize(alpha_values.T * w),
                                   [cvx.sum(w) == 1,
                                    w >= 0,
                                    w <= weight_up_values,
                                    stock_style_values.T * w <= bench_style_up_values,
                                    stock_style_values.T * w >= bench_style_low_values,
                                    stock_position_values.T * w <= bench_position_up_values,
                                    stock_position_values.T * w >= bench_position_low_values,
                                    ])
                prob.solve()

            print("status:", prob.status)
            print("optimal value", prob.value)
            weight = pd.DataFrame(w.value, columns=['Weight'], index=data.index)
            weight['Weight'] = weight['Weight'].map(lambda x: 0.0 if x < 0.02 else x)
            weight['Weight'] /= weight['Weight'].sum()

            result_risk_exposure = weight.T.dot(data[risk_factor_list])
            result_risk_exposure = result_risk_exposure.T
            result_risk_exposure.columns = ['ResultExposure']

            up_risk_exposure = pd.DataFrame(data[risk_factor_list].median())
            up_risk_exposure.columns = ["UpExposure"]
            up_risk_exposure.loc[barra_style_list, "UpExposure"] += self.style_deviate
            up_risk_exposure.loc[position_list, "UpExposure"] += self.position_deviate

            low_risk_exposure = pd.DataFrame(data[risk_factor_list].median())
            low_risk_exposure.columns = ["LowExposure"]
            low_risk_exposure.loc[barra_style_list, "LowExposure"] -= self.style_deviate
            low_risk_exposure.loc[position_list, "LowExposure"] -= self.position_deviate

            bench_risk_exposure = pd.DataFrame(data[risk_factor_list].median())
            bench_risk_exposure.columns = ["BenchExposure"]

            exposure_result = pd.concat([bench_risk_exposure, up_risk_exposure,
                                         low_risk_exposure, result_risk_exposure], axis=1)

            data = pd.concat([data, weight], axis=1)
            data = data[data['Weight'] > 0.0]
            result = pd.concat([data, exposure_result.T], axis=0)
            col = ["SecName", "InvestType", "Corp", "SetupDate", "Weight",
                   "RegressAlpha", "RegressAlphaIR"]
            col.extend(risk_factor_list)
            result = result[col]
            path = os.path.join(self.data_path, 'fund_opt')
            file = os.path.join(self.data_path, 'fund_opt', 'FundOpt_%s.csv' % end_date)
            if not os.path.exists(path):
                os.makedirs(path)
            result.to_csv(file)

    def generate_wind_file(self, end_date):

        """ 生成wind组合文件"""

        path = os.path.join(self.data_path, 'fund_opt')
        file = os.path.join(path, 'FundOpt_%s.csv' % end_date)

        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data = data[['SecName', 'Weight', 'SetupDate', 'Corp', 'RegressAlphaIR', 'RegressAlpha']]
        data = data.dropna()
        end_date = Date().get_trade_date_offset(end_date, 0)

        data.index.name = 'Code'
        data["Price"] = 0.0
        data["Direction"] = "Long"
        data["CreditTrading"] = "No"
        data['Date'] = end_date
        out_file = os.path.join(self.port_path, self.port_name + "_" + end_date + '.csv')
        data.to_csv(out_file)

    def cal_fund_factor_alldate(self,
                                beg_date="20060101",
                                end_date=datetime.today().strftime("%Y%m%d")):

        """ 得到每期各项因子值 """

        date_series = Date().get_normal_date_series(beg_date, end_date, "Q")

        for i_date in range(0, len(date_series)):
            date = date_series[i_date]
            self.cal_fund_factor_date(date)

    def opt_alldate(self,
                    beg_date="20060101",
                    end_date=datetime.today().strftime("%Y%m%d"),
                    turnover_control=False):

        """ 得到每期组合优化值 并生成wind文件 """

        date_series = Date().get_normal_date_series(beg_date, end_date, "Q")

        for i_date in range(1, len(date_series)):
            end_date = date_series[i_date]
            end_last_date = date_series[i_date - 1]
            self.opt_date(end_date, end_last_date, turnover_control)
            self.generate_wind_file(end_date)

    def upload_all_wind_port(self):

        """ 上传wind组合 """
        WindPortUpLoad().upload_weight_period(self.port_name)

    def backtest(self, bench_code="885000.WI"):

        """ 本地基金组合回测 """

        backtest = BackTest()
        backtest.set_info(self.port_name, bench_code)
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return()
        backtest.cal_turnover(annual_number=4)
        backtest.cal_summary()


if __name__ == "__main__":

    """
    所有基金组合
    1、主动股票型基金优选750AlphaIR
    2、主动股票型基金优选500AlphaIR
    3、股票型基金优选500AlphaIR
    4、股票型基金优选750AlphaIR
    5、中证500基金优选500AlphaIR
    """

    # 更新基金Alpha
    # self = NiceStockFund()
    # self.update_data()

    # 1、主动股票型基金优选750AlphaIR
    fund_pool_name = "基金持仓基准基金池"
    benchmark_name = "基金持仓基准基金池"
    alpha_len = 750
    alpha_column = "RegressAlphaIR"
    port_name = "主动股票型基金优选750AlphaIR"
    beg_date = "20181201"
    end_date = "20190404"
    end_last_date = Date().get_trade_date_offset(end_date, -1)
    bench_code = "885000.WI"
    style_deviate = 0.20
    position_deviate = 0.02
    fund_up_ratio = 0.15
    turnover = 0.25

    self = NiceStockFund(fund_pool_name, benchmark_name, alpha_len, alpha_column, port_name,
                         style_deviate, position_deviate, fund_up_ratio, turnover)
    # self.cal_fund_factor_alldate(beg_date, end_date)
    # self.opt_alldate(beg_date, end_date, turnover_control=True)
    # self.upload_all_wind_port()
    # self.backtest(bench_code)

    # self.cal_fund_factor_date(end_date)
    # self.opt_date(end_date, end_last_date, turnover_control=True)
    # self.generate_wind_file(end_date)
    WindPortUpLoad().upload_weight_date(port_name, end_date)

    # 2、主动股票型基金优选500AlphaIR
    fund_pool_name = "基金持仓基准基金池"
    benchmark_name = "基金持仓基准基金池"
    alpha_len = 500
    alpha_column = "RegressAlphaIR"
    port_name = "主动股票型基金优选500AlphaIR"
    beg_date = "20181201"
    end_date = "20190404"
    bench_code = "885000.WI"
    style_deviate = 0.20
    position_deviate = 0.02
    fund_up_ratio = 0.15
    turnover = 0.25

    self = NiceStockFund(fund_pool_name, benchmark_name, alpha_len, alpha_column, port_name,
                         style_deviate, position_deviate, fund_up_ratio, turnover)
    # self.cal_fund_factor_alldate(beg_date, end_date)
    # self.opt_alldate(beg_date, end_date, turnover_control=True)
    # self.upload_all_wind_port()
    # self.backtest(bench_code)

    # self.cal_fund_factor_date(end_date)
    # self.opt_date(end_date, end_last_date, turnover_control=True)
    # self.generate_wind_file(end_date)
    WindPortUpLoad().upload_weight_date(port_name, end_date)

    # 3、股票型基金优选500AlphaIR
    fund_pool_name = "指数+主动股票+灵活配置60基金"
    benchmark_name = "基金持仓基准基金池"
    alpha_len = 500
    alpha_column = "RegressAlphaIR"
    port_name = "股票型基金优选500AlphaIR"
    beg_date = "20181201"
    end_date = "20190404"
    bench_code = "885000.WI"
    style_deviate = 0.20
    position_deviate = 0.02
    fund_up_ratio = 0.15
    turnover = 0.25

    self = NiceStockFund(fund_pool_name, benchmark_name, alpha_len, alpha_column, port_name,
                         style_deviate, position_deviate, fund_up_ratio, turnover)
    # self.cal_fund_factor_alldate(beg_date, end_date)
    # self.opt_alldate(beg_date, end_date, turnover_control=True)
    # self.upload_all_wind_port()
    # self.backtest(bench_code)

    # self.cal_fund_factor_date(end_date)
    # self.opt_date(end_date, end_last_date, turnover_control=True)
    # self.generate_wind_file(end_date)
    WindPortUpLoad().upload_weight_date(port_name, end_date)

    # 4、股票型基金优选750AlphaIR
    fund_pool_name = "指数+主动股票+灵活配置60基金"
    benchmark_name = "基金持仓基准基金池"
    alpha_len = 750
    alpha_column = "RegressAlphaIR"
    port_name = "股票型基金优选750AlphaIR"
    beg_date = "20181201"
    end_date = "20190404"
    bench_code = "885000.WI"
    style_deviate = 0.20
    position_deviate = 0.02
    fund_up_ratio = 0.15
    turnover = 0.25

    self = NiceStockFund(fund_pool_name, benchmark_name, alpha_len, alpha_column, port_name,
                         style_deviate, position_deviate, fund_up_ratio, turnover)
    # self.cal_fund_factor_alldate(beg_date, end_date)
    # self.opt_alldate(beg_date, end_date, turnover_control=True)
    # self.upload_all_wind_port()
    # self.backtest(bench_code)

    # self.cal_fund_factor_date(end_date)
    # self.opt_date(end_date, end_last_date, turnover_control=True)
    # self.generate_wind_file(end_date)
    WindPortUpLoad().upload_weight_date(port_name, end_date)
