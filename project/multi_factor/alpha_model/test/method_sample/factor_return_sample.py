import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.barra import Barra
from quant.utility.write_excel import WriteExcel
from quant.utility.factor_neutral import FactorNeutral
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class FactorReturnSample(Data):

    """ 简单测试Alpha因子 """

    def __init__(self):

        Data.__init__(self)
        self.sub_path = r'stock_data\alpha_model\factor_return\sample'
        self.sample_test_path = os.path.join(self.primary_data_path, self.sub_path)
        self.return_path = os.path.join(self.sample_test_path, "factor_return")
        self.exposure_path = os.path.join(self.sample_test_path, "res_exposure")
        self.corr_path = os.path.join(self.sample_test_path, "corr")
        self.summary_path = os.path.join(self.sample_test_path, "summary")

        if not os.path.exists(self.corr_path):
            os.makedirs(self.corr_path)

        if not os.path.exists(self.exposure_path):
            os.makedirs(self.exposure_path)

        if not os.path.exists(self.return_path):
            os.makedirs(self.return_path)

        if not os.path.exists(self.summary_path):
            os.makedirs(self.summary_path)

        self.group_number = 10
        self.year_trade_days = 242
        self.min_stock_number = 100
        self.labels = ["Group" + str(i) for i in list(range(1, self.group_number + 1))]
        self.period = ""
        self.year_number = ""
        self.stock_pool_name = ""

        self.price = None
        self.alpha = None
        self.industry = None
        self.date_series = None
        self.alpha_res = None
        self.alpha_return = None
        self.corr = None
        self.alpha_factor_name = None

    def get_all_data(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 得到数据 """

        self.period = period
        self.alpha_factor_name = factor_name
        self.year_number = Date().get_period_number_for_year(period)
        self.price = Stock().read_factor_h5("Price_Unadjust")
        self.industry = Stock().read_factor_h5("industry_citic1")
        self.alpha = AlphaFactor().get_standard_alpha_factor(self.alpha_factor_name)
        self.stock_pool_name = stock_pool_name

        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        date_series = list(set(date_series) & set(self.alpha.columns) &
                           set(self.industry.columns) & set(self.price.columns))
        date_series.sort()
        self.date_series = date_series

        self.alpha_return = pd.DataFrame([], index=date_series)
        self.alpha_res = pd.DataFrame([], index=date_series, columns=self.price.index)
        self.corr = pd.DataFrame([])

    def cal_factor_return(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """计算每个换仓周期的因子收益率\计算因子残差暴露\因子与其他因子的相关性"""

        # get data
        self.get_all_data(beg_date, end_date, factor_name, period, stock_pool_name)

        for i_date in range(len(self.date_series) - 2):

            data_date = self.date_series[i_date]
            buy_date = Date().get_trade_date_offset(data_date, 1)
            sell_date = Date().get_trade_date_offset(self.date_series[i_date + 1], 1)

            output = (self.alpha_factor_name, data_date, self.stock_pool_name)
            print("Calculating %s Alpha Return At %s %s" % output)

            self.alpha_return.index.name = 'CalDate'
            self.alpha_return.ix[data_date, "BuyDate"] = buy_date
            self.alpha_return.ix[data_date, "SellDate"] = sell_date

            alpha_date = pd.DataFrame(self.alpha[data_date])
            alpha_date.columns = ['Alpha']
            buy_price = self.price[buy_date]
            sell_price = self.price[sell_date]
            pct_date = sell_price / buy_price - 1.0

            alpha_date = alpha_date.dropna()
            neutral_frame = Barra().get_factor_exposure_date(data_date, type_list=['STYLE', 'INDUSTRY'])
            stock_pool = Stock().get_invest_stock_pool(date=data_date, stock_pool_name=self.stock_pool_name)
            stock_pool = list(set(stock_pool) & set(neutral_frame.index) & set(alpha_date.index))
            stock_pool.sort()
            alpha_date = alpha_date.loc[stock_pool, "Alpha"]
            neutral_frame = neutral_frame.loc[stock_pool, :]

            if len(alpha_date) > self.min_stock_number:

                params, t_values, alpha_date_res = FactorNeutral().factor_exposure_neutral(alpha_date, neutral_frame)
                exposure_corr = FactorNeutral().factor_exposure_corr(alpha_date, neutral_frame)
                exposure_corr.columns = [data_date]
                self.corr = pd.concat([self.corr, exposure_corr], axis=1)
                self.alpha_res.loc[data_date, :] = alpha_date_res

                res = pd.concat([alpha_date_res, pct_date], axis=1)
                res.columns = ['alpha_val', 'period_pct']
                res = res.dropna()
                res = res.sort_values(by=['alpha_val'], ascending=False)
                res['weight'] = res['alpha_val'] / res['alpha_val'].abs().sum()
                res['group'] = pd.qcut(res['alpha_val'], q=self.group_number, labels=self.labels)

                period_return = (res['weight'] * res['period_pct']).sum()
                information_correlation = res['alpha_val'].corr(res['period_pct'], method="pearson")
                group_pct = res.groupby(by=['group'])['period_pct'].mean()
                group_pct -= res['period_pct'].mean()

                self.alpha_return.loc[data_date, "FactorReturn"] = period_return
                self.alpha_return.loc[data_date, "IC"] = information_correlation
                for i_label in range(len(self.labels)):
                    self.alpha_return.loc[data_date, self.labels[i_label]] = group_pct.values[i_label]

        # save file
        self.alpha_return = self.alpha_return.dropna(subset=['FactorReturn'])
        self.alpha_return["CumFactorReturn"] = self.alpha_return['FactorReturn'].cumsum()
        cum_labels = ["Cum_" + str(x) for x in self.labels]
        self.alpha_return[cum_labels] = self.alpha_return[self.labels].cumsum()

        file_postfix = (self.alpha_factor_name, self.stock_pool_name)
        file = os.path.join(self.return_path, 'factor_return_%s_%s.csv' % file_postfix)
        self.alpha_return.to_csv(file)

        file = os.path.join(self.exposure_path, 'res_exposure_%s_%s.csv' % file_postfix)
        self.alpha_res = self.alpha_res.astype(np.float)
        self.alpha_res.T.to_csv(file)

        file = os.path.join(self.corr_path, 'corr_%s_%s.csv' % file_postfix)
        self.corr = self.corr.astype(np.float)
        self.corr.T.to_csv(file)

    def get_factor_data(self, alpha_factor_name, stock_pool_name="AllChinaStockFilter"):

        """ 得到因子收益率 得到因子残差暴露 和其他因子的相关性等指标 """

        self.alpha_factor_name = alpha_factor_name
        self.stock_pool_name = stock_pool_name
        file_postfix = (self.alpha_factor_name, self.stock_pool_name)

        file = os.path.join(self.exposure_path, 'res_exposure_%s_%s.csv' % file_postfix)
        self.alpha_res = pd.read_csv(file, index_col=[0], encoding='gbk')
        self.alpha_res.columns = self.alpha_res.columns.map(str)

        file = os.path.join(self.return_path, 'factor_return_%s_%s.csv' % file_postfix)
        self.alpha_return = pd.read_csv(file, index_col=[0], encoding='gbk')
        self.alpha_return.index = self.alpha_return.index.map(str)

        file = os.path.join(self.corr_path, 'corr_%s_%s.csv' % file_postfix)
        self.corr = pd.read_csv(file, index_col=[0], encoding='gbk')
        self.corr.index = self.corr.index.map(str)

    def get_alpha_res_corr(self, beg_date, end_date):

        """ 计算残差暴露的相关性 """

        data = self.alpha_res.loc[:, beg_date:end_date]
        res = pd.DataFrame([], index=data.columns, columns=['Corr'])

        for i in range(len(data.columns)-1):
            date = data.columns[i]
            date_next = data.columns[i + 1]
            data_date = pd.concat([data[date], data[date_next]], axis=1)
            data_date = data_date.dropna()
            res.loc[date, "Corr"] = data_date.corr().iloc[0, 1]
        corr = res.mean().values[0]
        return corr

    def cal_factor_summary(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 计算每年的因子表现（首先得计算因子收益率 残差因子暴露等信息） """

        if self.year_number == "":
            self.get_all_data(beg_date, end_date, factor_name, period, stock_pool_name)

        self.get_factor_data(factor_name, stock_pool_name)
        back_test_days = Date().get_trade_date_diff(self.alpha_res.columns[0], self.alpha_res.columns[-1])
        year = back_test_days / self.year_trade_days
        self.alpha_return['year'] = self.alpha_return.index.map(lambda x: datetime.strptime(x, "%Y%m%d").year)
        self.corr['year'] = self.corr.index.map(lambda x: datetime.strptime(str(x), "%Y%m%d").year)
        self.alpha_return['date'] = self.alpha_return.index

        bg_date = self.alpha_return.groupby(by=['year'])['date'].min()
        ed_date = self.alpha_return.groupby(by=['year'])['date'].max()
        year_fr = self.alpha_return.groupby(by=['year'])['FactorReturn'].sum()
        year_fr_std = self.alpha_return.groupby(by=['year'])['FactorReturn'].std() * np.sqrt(self.year_number)
        year_count = self.alpha_return.groupby(by=['year'])['FactorReturn'].count()
        year_ic_mean = self.alpha_return.groupby(by=['year'])['IC'].mean()
        year_ic_std = self.alpha_return.groupby(by=['year'])['IC'].std()

        summary = pd.concat([year_fr, year_fr_std, year_count, year_ic_mean, year_ic_std, bg_date, ed_date], axis=1)
        summary.columns = ['年化收益', '年化波动率', '调仓次数', 'IC均值', 'IC波动', '开始时间', '结束时间']
        summary['年化收益'] = summary['年化收益'] / summary['调仓次数'] * self.year_number
        summary['ICIR'] = summary['IC均值'] / summary['IC波动'] * np.sqrt(self.year_number)
        summary.loc['All', '年化收益'] = self.alpha_return["FactorReturn"].sum() / year
        summary.loc['All', '年化波动率'] = self.alpha_return["FactorReturn"].std() * np.sqrt(self.year_number)
        mean = self.alpha_return["IC"].mean()
        std = self.alpha_return["IC"].std()
        summary.loc['All', '调仓次数'] = summary['调仓次数'].sum()
        summary.loc['All', 'ICIR'] = mean / std * np.sqrt(self.year_number)
        summary.loc['All', 'IC均值'] = mean
        summary.loc['All', 'IC波动'] = std
        summary.loc['All', '开始时间'] = self.alpha_return.index[0]
        summary.loc['All', '结束时间'] = self.alpha_return.index[-1]
        summary.index = summary.index.map(str)

        for i in range(len(summary)):
            label = summary.index[i]
            bdate = summary.loc[label, "开始时间"]
            edate = summary.loc[label, "结束时间"]
            summary.loc[label, "自相关系数"] = self.get_alpha_res_corr(bdate, edate)

        group = self.alpha_return.groupby(by=['year'])[self.labels].sum()
        group.loc['All', self.labels] = self.alpha_return[self.labels].sum() / year
        group.index = group.index.map(str)

        for i in range(len(group)):
            year = group.index[i]
            corr_pd = pd.DataFrame(group.loc[year, self.labels].values, index=self.labels, columns=['group_return'])
            corr_pd['group_number'] = (list(range(1, self.group_number + 1)))
            group.loc[year, 'Group_Corr'] = corr_pd.corr().iloc[0, 1]

        corr = self.corr.groupby(by=['year']).mean()
        corr.loc['All', :] = corr.mean()
        corr.index = corr.index.map(str)

        file_postfix = (self.alpha_factor_name, self.stock_pool_name)
        filename = os.path.join(self.summary_path, "summary_%s_%s.xlsx" % file_postfix)
        sheet_name = self.alpha_factor_name
        excel = WriteExcel(filename)
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=summary.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        num_format_pd.loc['format', ['调仓次数', 'ICIR']] = '0.00'
        excel.write_pandas(summary, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        num_format_pd = pd.DataFrame([], columns=group.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        num_format_pd.loc['format', ['Group_Corr']] = '0.00'
        beg_col = 3 + len(summary.columns)
        excel.write_pandas(group, worksheet, begin_row_number=0, begin_col_number=beg_col,
                           num_format_pd=num_format_pd, color="blue", fillna=True)

        num_format_pd = pd.DataFrame([], columns=corr.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        beg_col = 5 + len(group.columns) + len(summary.columns)
        excel.write_pandas(corr, worksheet, begin_row_number=0, begin_col_number=beg_col,
                           num_format_pd=num_format_pd, color="blue", fillna=True)

        pos_pic = len(summary) + 3
        pos_end = len(summary) + 1
        excel.chart_columns_plot(worksheet, sheet_name, series_name=["分组超额收益"],
                                 chart_name="分组超额收益%s" % self.alpha_factor_name,
                                 insert_pos="B%s" % pos_pic, cat_beg="N1", cat_end="W1",
                                 val_beg_list=["N%s" % pos_end], val_end_list=["W%s" % pos_end])

        excel.chart_columns_plot(worksheet, sheet_name, series_name=["风格暴露"],
                                 chart_name="风格暴露%s" % self.alpha_factor_name,
                                 insert_pos="N%s" % pos_pic, cat_beg="AA1", cat_end="AJ1",
                                 val_beg_list=["AA%s" % pos_end], val_end_list=["AJ%s" % pos_end])
        excel.close()

    def cal_all_factor_summary(self, beg_date, end_date, period="W",  stock_pool_name="AllChinaStockFilter", force=0):

        """ 计算所有因子表现 """

        file_list = os.listdir(AlphaFactor().exposure_hdf_path)
        factor_list = list(map(lambda x: x[0:-3], file_list))

        for i in range(0, len(factor_list)):

            factor_name = factor_list[i]
            self.alpha_factor_name = factor_name
            self.stock_pool_name = stock_pool_name
            file_postfix = (self.alpha_factor_name, self.stock_pool_name)
            filename = os.path.join(self.summary_path, "summary_%s_%s.xlsx" % file_postfix)
            if force or not os.path.exists(filename):
                print("Cal Alpha Factor Return", factor_name)
                self.cal_factor_return(beg_date, end_date, factor_name, period, stock_pool_name)
            else:
                print("Already Exist Alpha Factor Return", factor_name)
            self.cal_factor_summary(beg_date, end_date, factor_name, period, stock_pool_name)

    def concat_summary(self, stock_pool_name):

        """ 所有因子回测结果汇总 """

        all_data = pd.DataFrame([])
        file_list = os.listdir(AlphaFactor().exposure_hdf_path)
        factor_list = list(map(lambda x: x[0:-3], file_list))

        for i in range(0, len(factor_list)):
            factor_name = factor_list[i]
            print("Summary Alpha Factor Return", factor_name)
            self.alpha_factor_name = factor_name
            self.stock_pool_name = stock_pool_name
            try:
                file_postfix = (self.alpha_factor_name, self.stock_pool_name)
                filename = os.path.join(self.summary_path, "summary_%s_%s.xlsx" % file_postfix)
                data = pd.read_excel(filename, index_col=[1])
                columns = ['ICIR', 'IC均值', '年化波动率', '年化收益', '开始时间', '结束时间', '自相关系数']
                data_factor = pd.DataFrame(data.loc['All', columns])
                data_factor.columns = [factor_name]
                data_factor = data_factor.T
                all_data = pd.concat([all_data, data_factor], axis=0)
            except Exception as e:
                print(e)
                print("Can not Find Factor Result", factor_name)

        all_data['股票池'] = stock_pool_name
        all_data['开始时间'] = all_data['开始时间'].map(str)
        all_data['结束时间'] = all_data['结束时间'].map(str)

        filename = os.path.join(self.summary_path, 'AlphaSummary_%s.xlsx' % stock_pool_name)
        excel = WriteExcel(filename)
        worksheet = excel.add_worksheet("因子表现%s" % stock_pool_name)
        num_format_pd = pd.DataFrame([], columns=all_data.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', ['年化波动率', '年化收益']] = '0.00%'
        excel.write_pandas(all_data, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)
        excel.close()


if __name__ == '__main__':

    self = FactorReturnSample()
    beg_date, end_date, period = "20040101", datetime.today().strftime("%Y%m%d"), "W"

    factor_name = "daily_alpha_raw_ts_rank9"
    stock_pool_name = "AllChinaStockFilter"
    # self.cal_factor_return(beg_date, end_date, factor_name, period, stock_pool_name)
    # self.cal_factor_summary(beg_date, end_date, factor_name, period)

    stock_pool_name = "AllChinaStockFilter"
    self.cal_all_factor_summary(beg_date, end_date, period, stock_pool_name, 0)
    self.concat_summary(stock_pool_name)

    stock_pool_name = "hs300"
    self.cal_all_factor_summary(beg_date, end_date, period, stock_pool_name, 0)
    self.concat_summary(stock_pool_name)

    stock_pool_name = "zz500"
    self.cal_all_factor_summary(beg_date, end_date, period, stock_pool_name, 0)
    self.concat_summary(stock_pool_name)