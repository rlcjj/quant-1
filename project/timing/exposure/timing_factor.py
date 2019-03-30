import os
import pandas as pd
from quant.data.data import Data
from quant.stock.index import Index


class TimingFactor(Data):

    """ 所有择时指标的母类 """

    def __init__(self):

        """ 数据存储位置 """

        Data.__init__(self)
        self.sub_data_path = r"index_data\timing"
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def get_factor_exposure(self, factor_name):

        """ 得到择时指标的数值 """

        file = os.path.join(self.data_path, 'exposure', factor_name + '.csv')
        data = pd.read_csv(file, index_col=[0], encoding='gbk')
        data.index = data.index.map(str)
        return data

    def back_test_timing_factor(self, factor_name, index_code):

        """ 回测择时指标 """

        data = self.get_factor_exposure(factor_name)
        index_pct = Index().get_index_factor(index_code, attr=['CLOSE'])
        index_pct = index_pct.pct_change()
        index_pct.columns = ['IndexReturn']

        data = pd.concat([data, index_pct['IndexReturn']], axis=1)
        data = data.dropna(subset=['RawTimer', 'Timer', 'IndexReturn'])
        data['IndexNextReturn'] = data['IndexReturn'].shift(-1)

        data['LongTimer'] = data['Timer'].map(lambda x: x if x >= 0 else 0)
        data['ShortTimer'] = data['Timer'].map(lambda x: x if x <= 0 else 0)
        data['SPortNextReturn'] = data['IndexNextReturn'] * data['ShortTimer']
        data['LPortNextReturn'] = data['IndexNextReturn'] * data['LongTimer']
        data['LSPortNextReturn'] = data['IndexNextReturn'] * data['Timer']

        data['SPortCumReturn'] = data['SPortNextReturn'].cumsum()
        data['LPortCumReturn'] = data['LPortNextReturn'].cumsum()
        data['LSPortCumReturn'] = data['LSPortNextReturn'].cumsum()
        data['IndexCumReturn'] = data['IndexReturn'].cumsum()

        col_output = ["SPortCumReturn", "LPortCumReturn", "LSPortCumReturn", "IndexCumReturn"]
        data_plot = data[col_output]
        ax = data_plot.plot()
        fig = ax.get_figure()
        file = os.path.join(self.data_path, 'factor_picture', factor_name + 'fig.png')
        fig.savefig(file)

        result = pd.DataFrame([], columns=[factor_name])

        pos_corr = data['IndexNextReturn'].corr(data['Timer'])
        raw_corr = data['IndexNextReturn'].corr(data['RawTimer'])
        mean_zero = data.loc[data['Timer'] == 0, 'IndexNextReturn'].mean()

        mean_positive_profit = data.loc[(data['Timer'] > 0) & (data['IndexNextReturn'] > 0), 'IndexNextReturn'].mean()
        mean_positive_loss = data.loc[(data['Timer'] > 0) & (data['IndexNextReturn'] <= 0), 'IndexNextReturn'].mean()
        mean_negative_loss = - data.loc[(data['Timer'] < 0) & (data['IndexNextReturn'] >= 0), 'IndexNextReturn'].mean()
        mean_negative_profit = - data.loc[(data['Timer'] < 0) & (data['IndexNextReturn'] < 0), 'IndexNextReturn'].mean()

        number_positive = len(data.loc[data['Timer'] > 0, 'IndexNextReturn'])
        number_negative = len(data.loc[data['Timer'] < 0, 'IndexNextReturn'])
        number_zero = len(data.loc[data['Timer'] == 0, 'IndexNextReturn'])

        number_positive_profit = len(data.loc[(data['Timer'] > 0) & (data['IndexNextReturn'] > 0), 'IndexNextReturn'])
        number_negative_profit = len(data.loc[(data['Timer'] < 0) & (data['IndexNextReturn'] < 0), 'IndexNextReturn'])

        positive_wining_ratio = number_positive_profit / number_positive
        positive_profit_loss_ratio = - mean_positive_profit / mean_positive_loss
        negative_wining_ratio = number_negative_profit / number_negative
        negative_profit_loss_ratio = - mean_negative_profit / mean_negative_loss

        result.loc['开始时间', factor_name] = data.index[0]
        result.loc['结束时间', factor_name] = data.index[-1]
        result.loc['仓位相关系数', factor_name] = pos_corr
        result.loc['原始相关系数', factor_name] = raw_corr
        result.loc['多头收益', factor_name] = mean_positive_profit
        result.loc['多头损失', factor_name] = mean_positive_loss
        result.loc['空头收益', factor_name] = mean_negative_profit
        result.loc['空头损失', factor_name] = mean_negative_loss
        result.loc['空仓收益', factor_name] = mean_zero
        result.loc['多头信号数量', factor_name] = number_positive
        result.loc['空头信号数量', factor_name] = number_negative
        result.loc['空仓信号数量', factor_name] = number_zero
        result.loc['多头胜率', factor_name] = positive_wining_ratio
        result.loc['多头盈亏比', factor_name] = positive_profit_loss_ratio
        result.loc['空头胜率', factor_name] = negative_wining_ratio
        result.loc['空头盈亏比', factor_name] = negative_profit_loss_ratio

        file = os.path.join(self.data_path, 'factor_backtest', factor_name + '_Result.csv')
        result.to_csv(file)

        file = os.path.join(self.data_path, 'factor_backtest', factor_name + '_Return.csv')
        data.to_csv(file)

    def get_factor_exposure_date(self, factor_name, date):

        """ 得到某天某个指标的数据 """

        data = self.get_factor_exposure(factor_name)
        data = data[['RawTimer', 'Timer']]
        data = data.dropna()
        col_name = "%s_%s" % (factor_name, date)

        try:
            data_date = pd.DataFrame(data.loc[date, :])
            data_date.columns = [col_name]
        except Exception as e:
            print("Can not Find Timing Factor %s Values At Date %s" % (factor_name, date))
            data_date = pd.DataFrame([], columns=[col_name], index=['RawTimer', 'Timer'])

        return data_date


if __name__ == '__main__':

    self = TimingFactor()
    factor_name = "AverageDiff_000300.SH"
    index_code = "000300.SH"
    date = "20190322"
    self.back_test_timing_factor(factor_name, index_code)
    print(self.get_factor_exposure_date(factor_name, date))
