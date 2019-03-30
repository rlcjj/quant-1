from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.index import Index
from quant.utility.factor_fillna import FactorFillNa
from quant.utility.financial_series import FinancialSeries
from quant.utility.write_excel import WriteExcel

import os
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


class BackTest(Data):

    """
    股票(也包括基金、指数等资产)回测
    1、输入为每个时间点的持仓数据 wind_portfolio
    2、返回组合收益率、波动率、跟踪误差等信息 backtest_portfolio
    """

    def __init__(self):

        Data.__init__(self)
        self.port_path = os.path.join(self.primary_data_path, r'portfolio\wind_portfolio')
        self.save_path = os.path.join(self.primary_data_path, r'portfolio\backtest_portfolio')
        self.port_name = ""
        self.benchmark_code = ""

        self.port_hold = pd.DataFrame([])
        self.port_hold_daily = pd.DataFrame([])
        self.turnover = pd.DataFrame([])
        self.port_return = pd.DataFrame([], columns=["PortReturn"])

        self.stock_return = None
        self.index_return = None
        self.fund_return = None
        self.asset_return = None

    def set_info(self, port_name, benchmark_code):

        """
        输入 组合名称，基准指数代码, 读取给雷资产的日度收益率数据
        """

        self.port_name = port_name
        self.benchmark_code = benchmark_code
        sub_path = os.path.join(self.save_path, self.port_name)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 股票收益率数据
        # pct = Stock().read_factor_h5("Pct_chg")
        price = Stock().read_factor_h5("Price_Adjust")
        pct = price.T.pct_change(fill_method=None).T * 100
        # pct[pct > 50.0] = np.nan
        # pct[pct > 12.0] = 12.0
        # pct = FactorFillNa().replace_suspension_with_nan(pct)
        # pct = FactorFillNa().fillna_with_mad_market(pct)

        self.stock_return = pct
        self.index_return = Index().get_index_cross_factor("PCT").T * 100
        self.fund_return = Fund().get_fund_factor("Repair_Nav_Pct").T
        self.asset_return = pd.concat([self.stock_return, self.fund_return, self.index_return], axis=0)

    def read_weight_at_change_date(self, date):

        """
        读入组合在调仓日的权重
        """

        file = os.path.join(self.port_path, self.port_name, self.port_name + '_' + date + '.csv')
        data_pd = pd.read_csv(file, encoding='gbk')
        data_pd = data_pd[~data_pd.Code.duplicated()]
        # data_pd.Weight = data_pd.Weight.round(4)
        # data_pd = data_pd[data_pd.Weight >= 0.0001]
        data_pd.index = data_pd.Code
        data_pd = pd.DataFrame(data_pd.Weight)
        data_pd.columns = [date]

        print(" Reading Weight of Portfolio %s At Date %s " % (self.port_name, date))
        self.port_hold = pd.concat([self.port_hold, data_pd], axis=1)
        columns = list(self.port_hold.columns)
        columns.sort()
        self.port_hold = self.port_hold[columns]
        return data_pd

    def read_weight_at_all_change_date(self):

        """
        读入组合在所有调仓日的权重 并写入文件
        """

        sub_path = os.path.join(self.port_path, self.port_name)
        file_list = list(os.listdir(sub_path))
        date_list = list(map(lambda x: x[len(x)-12:len(x)-4], file_list))
        date_list.sort()

        for date in date_list:
            self.read_weight_at_change_date(date)

        sub_path = os.path.join(self.save_path, self.port_name)
        self.port_hold.to_csv(os.path.join(sub_path, self.port_name + '_PortHold.csv'))

    def get_weight_at_all_change_date(self):

        """
        读入文件 在所有调仓日的权重
        """

        sub_path = os.path.join(self.save_path, self.port_name)
        self.port_hold = pd.read_csv(os.path.join(sub_path, self.port_name + '_PortHold.csv'),
                                     index_col=[0], encoding='gbk')
        self.port_hold.columns = self.port_hold.columns.map(str)

    def cal_weight_at_all_daily(self):

        """
        计算在每个交易日的股票权重
        """

        self.get_weight_at_all_change_date()
        beg_date = self.port_hold.columns[0]
        end_date = datetime.today().strftime("%Y%m%d")
        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(date_series) & set(self.asset_return.columns))
        date_series.sort()
        date_change_date_list = list(self.port_hold.columns)

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            date_before = Date().get_trade_date_offset(date, -1)

            if date in date_change_date_list:
                self.port_hold_daily[date] = self.port_hold[date]
                print(" Calculating Weight of Portfolio %s At Date %s " % (self.port_name, date))
            else:
                print(" Calculating Weight of Portfolio %s At Date %s " % (self.port_name, date))
                weight_before = self.port_hold_daily[date_before]
                pct_date = self.asset_return[date]
                concat_data = pd.concat([weight_before, pct_date], axis=1)
                concat_data.columns = ["WeightBefore", "PctCur"]
                if "Cash" in concat_data.index:
                    concat_data.loc['Cash', "PctCur"] = 0.0
                concat_data = concat_data.dropna(subset=["WeightBefore"])
                average_pct = concat_data["PctCur"].median()
                concat_data["PctCur"] = concat_data["PctCur"].fillna(average_pct)
                concat_data["Weight"] = concat_data["WeightBefore"] * (1.0 + concat_data["PctCur"] / 100.0)
                concat_data["Weight"] = concat_data["Weight"] / concat_data["Weight"].sum()
                self.port_hold_daily[date] = concat_data["Weight"]

        sub_path = os.path.join(self.save_path, self.port_name)
        self.port_hold_daily.to_csv(os.path.join(sub_path, self.port_name + '_PortHoldDaily.csv'))

    def get_weight_at_all_daily(self):

        """
        读入文件 在所有交易日的权重
        """

        sub_path = os.path.join(self.save_path, self.port_name)
        self.port_hold_daily = pd.read_csv(os.path.join(sub_path, self.port_name + '_PortHoldDaily.csv'),
                                           index_col=[0], encoding='gbk')
        self.port_hold_daily.columns = self.port_hold_daily.columns.map(str)

    def cal_turnover(self, annual_number=12):

        """
        计算换手率
        """

        self.get_weight_at_all_change_date()
        self.get_weight_at_all_daily()
        port_hold = self.port_hold
        port_hold_daily = self.port_hold_daily
        turnover = pd.DataFrame([], columns=['TurnOver'])

        trade_change_date = list(set(port_hold.columns) & set(port_hold_daily.columns))
        trade_change_date.sort()

        """ 建仓的换手不计算入内 """

        for i_date in range(1, len(trade_change_date)):
            change_date = trade_change_date[i_date]
            change_before_date = Date().get_trade_date_offset(change_date, -1)
            data = port_hold_daily[[change_before_date, change_date]]
            data = data.dropna(how='all')
            data = data.fillna(0.0)
            data['Diff'] = data[change_date] - data[change_before_date]
            turnover.loc[change_date, 'TurnOver'] = data['Diff'].abs().sum()

        turnover['HalfTurnOver'] = turnover['TurnOver'] / 2
        turnover['Fee'] = turnover['HalfTurnOver'] * 0.0026
        self.turnover = turnover
        turnover.loc['Mean', :] = turnover.mean() * annual_number
        sub_path = os.path.join(self.save_path, self.port_name)
        turnover.to_csv(os.path.join(sub_path, self.port_name + '_TurnOver.csv'))

    def cal_port_return(self, beg_date=None, end_date=None):

        """
        计算组合日收益率序列 要用昨天的权重乘以今日的收益率 = 基金组合收益率
        """

        self.get_weight_at_all_change_date()
        self.get_weight_at_all_daily()
        date_series = list(self.port_hold_daily.columns)

        for i_date in range(1, len(date_series)):

            date = date_series[i_date]
            date_before = Date().get_trade_date_offset(date, -1)
            print(" Calculating Return Daily of Portfolio %s At Date %s " % (self.port_name, date))
            weight_before = self.port_hold_daily[date_before]
            return_date = self.asset_return[date]
            concat_data = pd.concat([weight_before, return_date], axis=1)
            concat_data.columns = ["WeightBefore", "PctCur"]
            concat_data = concat_data.dropna(subset=["WeightBefore"])
            average_pct = concat_data['PctCur'].median()
            concat_data["PctCur"] = concat_data["PctCur"].fillna(average_pct)
            pct = (concat_data["WeightBefore"] * concat_data["PctCur"]).sum() / 100.0
            self.port_return.loc[date, "PortReturn"] = pct

        pct = pd.DataFrame(self.asset_return.T[self.benchmark_code])
        pct /= 100.0
        pct.columns = ["IndexReturn"]
        self.port_return = pd.concat([self.port_return, pct], axis=1)
        self.port_return = self.port_return.dropna()
        if end_date is None:
            end_date = self.port_return.index[-1]
        if beg_date is None:
            beg_date = self.port_return.index[0]
        self.port_return = self.port_return.loc[beg_date:end_date, :]
        self.port_return['ExcessReturn'] = self.port_return['PortReturn'] - self.port_return['IndexReturn']
        self.port_return['CumExcessReturn'] = self.port_return['ExcessReturn'].cumsum()
        self.port_return["CumPortReturn"] = (self.port_return["PortReturn"] + 1.0).cumprod() - 1.0
        self.port_return["CumIndexReturn"] = (self.port_return["IndexReturn"] + 1.0).cumprod() - 1.0

        sub_path = os.path.join(self.save_path, self.port_name)
        self.port_return.to_csv(os.path.join(sub_path, self.port_name + '_PortReturn.csv'))

    def get_port_return(self):

        """
        得到组合日收益率序列
        """

        sub_path = os.path.join(self.save_path, self.port_name)
        self.port_return = pd.read_csv(os.path.join(sub_path, self.port_name + '_PortReturn.csv'),
                                       index_col=[0], encoding='gbk')
        self.port_return.columns = self.port_return.columns.map(str)
        self.port_return.index = self.port_return.index.map(str)

    def plot_port_return_period(self, beg_date=None, end_date=None):

        """
        区间收益率序列 画图
        """

        self.get_port_return()
        if beg_date is None:
            beg_date = self.port_return.index[0]
        if end_date is None:
            end_date = self.port_return.index[-1]

        port_return = self.port_return.loc[beg_date:end_date, :]
        port_return["CumPortReturn"] = (port_return["PortReturn"] + 1.0).cumprod() - 1.0
        port_return["CumIndexReturn"] = (port_return["IndexReturn"] + 1.0).cumprod() - 1.0
        port_return[["CumPortReturn", "CumIndexReturn"]].plot()
        beg_date = port_return.index[0]
        end_date = port_return.index[-1]
        sub_path = os.path.join(self.save_path, self.port_name)
        file = os.path.join(sub_path, self.port_name + '_Return_' + beg_date + '_' + end_date + '.png')
        plt.savefig(file)

    def cal_summary_period(self, beg_date=None, end_date=None):

        """
        计算组合在区间内 收益率、波动率等表现情况
        并画图并存储图片
        """

        self.get_port_return()
        if beg_date is None:
            beg_date = self.port_return.index[0]
        if end_date is None:
            end_date = self.port_return.index[-1]

        fs = FinancialSeries(pd.DataFrame(self.port_return["CumPortReturn"] + 1.0),
                             pd.DataFrame(self.port_return["CumIndexReturn"] + 1.0))

        port_return = self.port_return.loc[beg_date:end_date, :]
        result = pd.DataFrame([])
        beg_date = port_return.index[0]
        end_date = port_return.index[-1]
        label = str(beg_date)[0:4] + '年'
        result.loc[label, '开始时间'] = beg_date
        result.loc[label, '结束时间'] = end_date
        result.loc[label, "收益率"] = fs.get_interval_return(beg_date, end_date)
        result.loc[label, "年化收益率"] = fs.get_interval_return_annual(beg_date, end_date)
        result.loc[label, "年化波动率"] = fs.get_interval_std_annual(beg_date, end_date)
        result.loc[label, "年化跟踪误差"] = fs.get_interval_tracking_error(beg_date, end_date)
        result.loc[label, "最大回撤率"] = fs.get_interval_max_drawdown(beg_date, end_date)
        result.loc[label, "超额收益率"] = fs.get_interval_excess_return(beg_date, end_date)
        result.loc[label, "年化超额收益率"] = fs.get_interval_excess_return_annual(beg_date, end_date)
        result.loc[label, "超额收益率最大回撤"] = fs.get_interval_excess_return_max_drawdown(beg_date, end_date)
        result.loc[label, "基准收益率"] = fs.get_interval_return_benchmark(beg_date, end_date)
        result.loc[label, "基准年化收益率"] = fs.get_interval_return_annual_benchmark(beg_date, end_date)
        result.loc[label, "基准年化波动率"] = fs.get_interval_std_annual_benchmark(beg_date, end_date)
        result.loc[label, "基准最大回撤率"] = fs.get_interval_max_drawdown_benchmark(beg_date, end_date)
        self.plot_port_return_period(beg_date, end_date)
        return result.T

    def cal_summary(self, all_beg_date=None, all_end_date=None):

        """
        计算组合在每年的 收益率、波动率等表现情况
        """

        self.get_port_return()
        all_port_return = self.port_return
        all_port_return["Year"] = all_port_return.index.map(lambda x: x[0:4])
        if all_beg_date is None:
            all_beg_date = all_port_return.index[0]
        if all_end_date is None:
            all_end_date = all_port_return.index[-1]
        year_list = list(set(all_port_return["Year"]))
        year_list.sort()

        for i_year in range(len(year_list)):

            year = str(year_list[i_year])
            port_return = all_port_return.loc[all_port_return["Year"] == year, :]
            beg_date = port_return.index[0]
            end_date = port_return.index[-1]

            if i_year == 0:
                data = self.cal_summary_period(beg_date, end_date)
            else:
                data_add = self.cal_summary_period(beg_date, end_date)
                data = pd.concat([data, data_add], axis=1)

        data_add = self.cal_summary_period(all_beg_date, all_end_date)
        data_add.columns = ['All']
        data = pd.concat([data, data_add], axis=1)
        data = data.T
        sub_path = os.path.join(self.save_path, self.port_name)
        file = os.path.join(sub_path, self.port_name + '_Summary.xlsx')

        excel = WriteExcel(file)
        worksheet = excel.add_worksheet("Summary")
        num_format_pd = pd.DataFrame([], columns=data.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(data, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        excel.close()

    def backtest(self):

        """
        回测组合
        """

        self.read_weight_at_all_change_date()
        self.cal_weight_at_all_daily()
        self.cal_port_return()
        self.cal_turnover()
        self.cal_summary()


if __name__ == "__main__":

    """ 举例 """

    """ 方法1 """
    port_name = "公募股票基金季报满仓"
    benchmark_code = "885000.WI"
    self = BackTest()
    self.set_info(port_name, benchmark_code)
    # self.read_weight_at_all_change_date()
    # self.cal_weight_at_all_daily()
    # self.cal_port_return()
    # self.cal_turnover()
    # self.cal_summary()

    """ 方法2 """

    # port_name = "超预期30"
    # benchmark_code = "000300.SH"
    # self = BackTest()
    # self.set_info(port_name, benchmark_code)
    # self.backtest()
