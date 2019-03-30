import os
import numpy as np
import pandas as pd
import cvxpy as cvx
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor
from quant.utility.factor_operate import FactorOperate


class FundRegressionExposureIndex(Data):

    """
    利用有约束的线性回归的方法 计算收益率序列的在指数、风格、基金上的暴露
    将回归转化成为二次规划
    可以约束指数和为1，也可以不做约束

    cal_fund_regression_exposure()
    cal_fund_regression_exposure_all()
    get_fund_regression_exposure()

    """

    def __init__(self, folder_name="SizeIndex", index_code_list=None):

        """ 可以修改回归的指数列表 和文件夹的名称 """

        Data.__init__(self)
        self.folder_name = folder_name
        self.sub_data_path = r'fund_data\fund_exposure\fund_regression_exposure_index'
        self.file_prefix = "IndexExposure"
        self.index_exposure_path = os.path.join(self.primary_data_path, self.sub_data_path, self.folder_name)
        if not os.path.exists(self.index_exposure_path):
            os.makedirs(self.index_exposure_path)

        if index_code_list is None:
            self.index_code_list = ["885062.WI", "885008.WI", "801853.SI", "000300.SH",
                                    "000905.SH", "000852.SH", "399006.SZ", "399005.SZ"]
        else:
            self.index_code_list = index_code_list

        # 默认参数
        self.regression_period = 20
        self.regression_period_min = 15
        self.turnover = 0.03
        self.asset_pct = ""

    def get_data(self):

        """ 收益率数据 """

        index_pct = Index().get_index_cross_factor("PCT") * 100
        fund_pct = FundFactor().get_fund_factor("Repair_Nav_Pct")
        self.asset_pct = pd.concat([fund_pct, index_pct], axis=1)

    def update_data(self, beg_date=None, end_date=None):

        """ 更新计算基金暴露 所需要的数据  """

        if end_date is None:
            end_date = datetime.today().strftime("%Y%m%d")
        if beg_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -60)

        FundFactor().load_fund_factor("Repair_Nav_Pct", beg_date, end_date)
        for index_code in self.index_code_list:
            Index().load_index_factor(index_code, beg_date, end_date)

    def cal_fund_regression_exposure_index(self,
                                           reg_code,
                                           beg_date,
                                           end_date,
                                           period="D"):

        """
        回归单只基金区间内指数暴露
        用指数去你基金收益率 最小化跟踪误差的前提
        指数权重之和为1 指数不能做空 指数和上期权重换手不能太大
        """

        date_series = Date().get_trade_date_series(beg_date, end_date, period)
        data_beg_date = Date().get_trade_date_offset(beg_date, -self.regression_period)
        end_date = Date().change_to_str(end_date)

        code_list = [reg_code]
        code_list.extend(self.index_code_list)

        data = self.asset_pct.loc[data_beg_date:end_date, code_list]
        data = data.dropna(subset=[reg_code])

        if len(data) < self.regression_period:
            return None

        print("Regression %s With %s" % (reg_code, self.index_code_list))
        print("Length of Return Data Is %s " % len(data))

        date_series = list(set(date_series) & set(data.index))
        date_series.sort()

        # 上次计算的风格
        last_date = Date().get_trade_date_offset(date_series[0], -1)
        params_old = self.get_fund_regression_exposure_index_date(reg_code, last_date)
        params_old = params_old.T
        print("old", params_old)

        for i_date in range(0, len(date_series)):

            # 回归所需要的数据 过去60个交易日

            period_end_date = date_series[i_date]
            period_beg_date = Date().get_trade_date_offset(period_end_date, -self.regression_period)
            data_end_date = Date().get_trade_date_offset(period_end_date, -0)

            period_date_series = Date().get_trade_date_series(period_beg_date, data_end_date)
            data_periods = data.ix[period_date_series, :]
            data_periods = data_periods.dropna(subset=[reg_code])
            data_periods = data_periods.T.dropna(how='all').T
            data_periods = data_periods.T.fillna(data_periods.mean(axis=1)).T
            data_periods = data_periods.dropna()

            print("########## Calculate Regression Exposure %s %s %s %s ##########"
                  % (reg_code, period_beg_date, period_end_date, len(data_periods)))

            if len(data_periods) > self.regression_period_min and (len(data_periods.columns) > 1):

                y = data_periods.ix[:, 0].values
                x = data_periods.ix[:, 1:].values
                n = x.shape[1]

                if params_old.empty or params_old.sum().sum() < 0.5:
                    params_old = pd.DataFrame(n * [1 / n], columns=[period_end_date], index=data_periods.columns[1:]).T

                turnover = self.turnover
                params_old = params_old.loc[:, data_periods.columns[1:]]
                params_old = params_old.fillna(0.0)
                weight_old = params_old.values[0]

                w = cvx.Variable(n)
                sigma = y - x * w
                prob = cvx.Problem(cvx.Minimize(cvx.sum_squares(sigma)),
                                   [cvx.sum(w) == 1,
                                    w >= 0,
                                    cvx.sum(cvx.abs(w - weight_old)) <= turnover
                                    ])
                prob.solve()
                print('Solver Status : ', prob.status)

                # 计算回归 R2
                n = len(y)
                k = x.shape[1]
                tss = np.sum((y - np.mean(y)) ** 2) / n
                y_res = y - np.dot(x, w.value)
                rss = np.sum(y_res ** 2) / (n - k - 1)
                r2 = 1 - rss / tss

                params_add = pd.DataFrame(w.value, columns=[period_end_date], index=data_periods.columns[1:]).T
                params_add.loc[period_end_date, "R2"] = r2
                print('new', params_add)
                params_old = params_add

            else:
                last_date = Date().get_trade_date_offset(period_end_date, -1)
                params_old = self.get_fund_regression_exposure_index_date(reg_code, last_date)
                params_old = params_old.T
                print("old", params_old)
                params_add = params_old

            if i_date == 0:
                params_new = params_add
            else:
                params_new = pd.concat([params_new, params_add], axis=0)

        # 合并新数据
        file = '%s_%s_%s.csv' % (self.file_prefix, self.folder_name, reg_code)
        out_file = os.path.join(self.index_exposure_path, file)

        if os.path.exists(out_file):
            params_old = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            params_old.index = params_old.index.map(str)
            params = FactorOperate().pandas_add_row(params_old, params_new)
        else:
            params = params_new

        params.to_csv(out_file)

    def cal_fund_regression_exposure_index_all(self,
                                         beg_date,
                                         end_date,
                                         period="D",
                                         fund_pool="指数+主动股票+灵活配置60基金",
                                         file_rewrite=False):

        """ 回归基金池内所有基金指数暴露 """

        quarter_date = Date().get_last_fund_quarter_date(end_date)
        fund_pool = FundPool().get_fund_pool_all(quarter_date, fund_pool)
        fund_pool = fund_pool[fund_pool['if_etf'] == "非ETF基金"]
        fund_pool = fund_pool[fund_pool['if_a'] == "A类基金"]
        fund_pool = fund_pool[fund_pool['if_connect'] == "非联接基金"]
        fund_pool = fund_pool[fund_pool['if_hk'] == "非港股基金"]
        fund_pool = fund_pool.reset_index(drop=True)
        fund_pool.index = fund_pool['wind_code']
        print(len(fund_pool))

        for i_fund in range(0, len(fund_pool)):
            fund_code = fund_pool.index[i_fund]
            fund_name = fund_pool.sec_name[i_fund]
            file = '%s_%s_%s.csv' % (self.file_prefix, self.folder_name, fund_code)
            out_file = os.path.join(self.index_exposure_path, file)
            if not os.path.exists(out_file) or file_rewrite:
                print(fund_name, fund_code)
                self.cal_fund_regression_exposure_index(fund_code, beg_date, end_date, period)

    def get_fund_regression_exposure_index(self,
                                     reg_code):

        """ 得到基金的指数暴露 """

        file = '%s_%s_%s.csv' % (self.file_prefix, self.folder_name, reg_code)
        out_file = os.path.join(self.index_exposure_path, file)
        try:
            exposure = pd.read_csv(out_file, index_col=[0], encoding='gbk')
            exposure = exposure[self.index_code_list]
            exposure.index = exposure.index.map(str)
        except Exception as e:
            exposure = pd.DataFrame([])
        return exposure

    def get_fund_regression_exposure_index_date(self, fund, date):

        """ 得到基金某日在指数上的暴露 """

        try:
            exposure = self.get_fund_regression_exposure_index(fund)
            exposure = pd.DataFrame(exposure.ix[date, :].values, index=exposure.columns, columns=[fund])
        except Exception as e:
            print(e)
            exposure = pd.DataFrame([])
        return exposure

    def cal_regression_exposure_fundindex(self):

        """ 股票型基金指数集中回归方法 """

        reg_code = "885000.WI"

        ##########################################################################
        index_code_list = ["885062.WI", "885008.WI", "801853.SI", "000300.SH",
                           "000905.SH", "000852.SH", "399006.SZ", "399005.SZ"]
        self.folder_name = "SizeIndex"
        self.index_code_list = index_code_list
        self.get_data()
        self.cal_fund_regression_exposure_index(reg_code, beg_date, end_date)

        ##########################################################################
        index_code_list = ["885062.WI", "000300.SH", "000905.SH",
                           "000852.SH", "399006.SZ", "公募股票基金季报平均"]

        self.folder_name = "Holder_SizeIndex"
        self.index_code_list = index_code_list
        self.cal_fund_regression_exposure_index(reg_code, beg_date, end_date)

        ##########################################################################
        index_code_list = ["885062.WI", "000300.SH", "000905.SH",
                           "000852.SH", "399006.SZ", "公募股票基金季报平均", "HK2C90"]

        self.folder_name = "HK_Holder_SizeIndex"
        self.index_code_list = index_code_list
        self.cal_fund_regression_exposure_index(reg_code, beg_date, end_date)

        ##########################################################################
        index_code_list = ["H11006.CSI", "H11008.CSI",
                           "CI005909.WI", "CI005910.WI", "CI005911.WI",
                           "CI005912.WI", "CI005913.WI",
                           "CI005914.WI", "CI005915.WI", "CI005916.WI",
                           "公募股票基金季报满仓", "HK2C90"]

        self.folder_name = "HK_Holder_IndustryIndex"
        self.index_code_list = index_code_list
        self.cal_fund_regression_exposure_index(reg_code, beg_date, end_date)
        ##########################################################################


if __name__ == "__main__":

    beg_date = "20180901"
    end_date = datetime.today().strftime("%Y%m%d")
    period = "D"
    self = FundRegressionExposureIndex()
    self.get_data()
    self.cal_fund_regression_exposure_index_all(beg_date, end_date, period=period, file_rewrite=True)
    # print(self.get_fund_regression_exposure_index("000001.OF"))
