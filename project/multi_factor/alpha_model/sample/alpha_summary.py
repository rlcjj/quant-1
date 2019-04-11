import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.utility.write_excel import WriteExcel
from quant.project.multi_factor.alpha_model.sample.alpha_split import AlphaSplit


class AlphaSummary(Data):

    """
    Alpha因子简单拆分后
    简单测试 Alpha因子效果
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_path = r'stock_data\alpha_model\factor_return\sample_split'
        self.data_path = os.path.join(self.primary_data_path, self.sub_path)
        self.return_path = os.path.join(self.data_path, "factor_return")
        self.summary_path = os.path.join(self.data_path, "factor_summary")

        self.group_number = 10
        self.year_trade_days = 242
        self.min_stock_number = 0
        self.labels = ["Group" + str(i) for i in list(range(1, self.group_number + 1))]
        self.cum_labels = ["Cum_" + str(x) for x in self.labels]

    def cal_factor_return(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 计算Alpha因子收益率 """

        price = Stock().read_factor_h5("Price_Unadjust")
        alpha_res = AlphaSplit().get_alpha_res_exposure(factor_name, stock_pool_name)

        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        date_series = list(set(date_series) & set(alpha_res.columns) & set(price.columns))
        date_series.sort()

        alpha_return = pd.DataFrame([], index=date_series)

        for i_date in range(len(date_series) - 1):

            data_date = date_series[i_date]
            buy_date = Date().get_trade_date_offset(data_date, 1)
            sell_date = Date().get_trade_date_offset(date_series[i_date + 1], 1)

            alpha_return.index.name = 'CalDate'
            alpha_return.loc[data_date, "BuyDate"] = buy_date
            alpha_return.loc[data_date, "SellDate"] = sell_date

            alpha_date = pd.DataFrame(alpha_res[data_date])
            alpha_date.columns = ['Alpha']
            alpha_date = alpha_date.dropna()

            pct_date = price[sell_date] / price[buy_date] - 1.0
            pct_date = pct_date.dropna()

            stock_pool = Stock().get_invest_stock_pool(date=data_date, stock_pool_name=stock_pool_name)
            stock_pool = list(set(stock_pool) & set(alpha_date.index) & set(pct_date.index))
            stock_pool.sort()
            alpha_date = alpha_date.loc[stock_pool, "Alpha"]

            res = pd.concat([alpha_date, pct_date], axis=1)
            res.columns = ['alpha', 'pct']
            res = res.dropna()

            if len(res) > self.min_stock_number:

                try:
                    print("Calculating %s Alpha Return At %s %s" % (factor_name, data_date, stock_pool_name))
                    res = res.sort_values(by=['alpha'], ascending=False)
                    res['weight'] = res['alpha'] / res['alpha'].abs().sum()
                    res['group'] = pd.qcut(res['alpha'], q=self.group_number, labels=self.labels)

                    period_return = (res['weight'] * res['pct']).sum()
                    information_correlation = res['alpha'].corr(res['pct'], method="pearson")
                    group_pct = res.groupby(by=['group'])['pct'].mean()
                    group_pct -= res['pct'].mean()

                    alpha_return.loc[data_date, "FactorReturn"] = period_return
                    alpha_return.loc[data_date, "IC"] = information_correlation
                    for i_label in range(len(self.labels)):
                        alpha_return.loc[data_date, self.labels[i_label]] = group_pct.values[i_label]
                except:
                    print("Calculating %s Alpha Return At %s %s is Error" % (factor_name, data_date, stock_pool_name))
            else:
                print("Calculating %s Alpha Return At %s %s is Null" % (factor_name, data_date, stock_pool_name))

        # save file
        alpha_return = alpha_return.dropna(subset=['FactorReturn'])
        alpha_return["CumFactorReturn"] = alpha_return['FactorReturn'].cumsum()
        alpha_return[self.cum_labels] = alpha_return[self.labels].cumsum()

        path = os.path.join(self.return_path, stock_pool_name)
        if not os.path.exists(path):
            os.makedirs(path)
        file = os.path.join(path, 'factor_return_%s.csv' % factor_name)
        alpha_return.to_csv(file)

    def get_factor_return(self, factor_name, stock_pool_name="AllChinaStockFilter"):

        """ 得到因子收益率 得到因子残差暴露 和其他因子的相关性等指标 """

        path = os.path.join(self.return_path, stock_pool_name)
        file = os.path.join(path, 'factor_return_%s.csv' % factor_name)
        alpha_return = pd.read_csv(file, index_col=[0], encoding='gbk')
        alpha_return.index = alpha_return.index.map(str)
        return alpha_return

    def get_factor_icir(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 得到一段时间的 ICIR的情况 """

        data = self.get_factor_return(factor_name, stock_pool_name)
        data = data.loc[beg_date:end_date, :]
        year_number = Date().get_period_number_for_year(period)
        icir = data["IC"].mean() / data["IC"].std() * np.sqrt(year_number)

        return icir

    def cal_factor_summary(self, beg_date, end_date, factor_name, period="W", stock_pool_name="AllChinaStockFilter"):

        """ 计算每年的因子表现（首先得计算因子收益率 残差因子暴露等信息） """

        year_number = Date().get_period_number_for_year(period)
        alpha_return = self.get_factor_return(factor_name, stock_pool_name)
        alpha_return = alpha_return.loc[beg_date:end_date, :]

        alpha_return['year'] = alpha_return.index.map(lambda x: datetime.strptime(x, "%Y%m%d").year)
        alpha_return['date'] = alpha_return.index

        # summary 部分:每年 因子收益率 ICIR等
        bg_date = alpha_return.groupby(by=['year'])['date'].min()
        ed_date = alpha_return.groupby(by=['year'])['date'].max()
        year_fr = alpha_return.groupby(by=['year'])['FactorReturn'].sum()
        year_fr_std = alpha_return.groupby(by=['year'])['FactorReturn'].std() * np.sqrt(year_number)
        year_count = alpha_return.groupby(by=['year'])['FactorReturn'].count()
        year_ic_mean = alpha_return.groupby(by=['year'])['IC'].mean()
        year_ic_std = alpha_return.groupby(by=['year'])['IC'].std()
        summary = pd.concat([year_fr, year_fr_std, year_count, year_ic_mean, year_ic_std, bg_date, ed_date], axis=1)
        summary.columns = ['年化收益', '年化波动率', '调仓次数', 'IC均值', 'IC波动', '开始时间', '结束时间']
        summary['年化收益'] = summary['年化收益'] / summary['调仓次数'] * year_number
        summary['ICIR'] = summary['IC均值'] / summary['IC波动'] * np.sqrt(year_number)

        back_test_days = Date().get_trade_date_diff(alpha_return.index[0], alpha_return.index[-1])
        year = back_test_days / self.year_trade_days
        summary.loc['All', '年化收益'] = alpha_return["FactorReturn"].sum() / year
        summary.loc['All', '年化波动率'] = alpha_return["FactorReturn"].std() * np.sqrt(year_number)
        summary.loc['All', '调仓次数'] = summary['调仓次数'].sum()
        summary.loc['All', 'ICIR'] = alpha_return["IC"].mean() / alpha_return["IC"].std() * np.sqrt(year_number)
        summary.loc['All', 'IC均值'] = alpha_return["IC"].mean()
        summary.loc['All', 'IC波动'] = alpha_return["IC"].std()
        summary.loc['All', '开始时间'] = alpha_return.index[0]
        summary.loc['All', '结束时间'] = alpha_return.index[-1]
        summary.index = summary.index.map(str)

        for i in range(len(summary)):

            label = summary.index[i]
            bdate = summary.loc[label, "开始时间"]
            edate = summary.loc[label, "结束时间"]
            corr_mean = AlphaSplit().get_alpha_res_corr(factor_name, bdate, edate, period, stock_pool_name)
            summary.loc[label, "自相关系数"] = corr_mean

        # group 部分:每年 分组收益等
        group = alpha_return.groupby(by=['year'])[self.labels].sum()
        group.loc['All', self.labels] = alpha_return[self.labels].sum() / year
        group.index = group.index.map(str)

        for i in range(len(group)):
            year = group.index[i]
            corr_pd = pd.DataFrame(group.loc[year, self.labels].values, index=self.labels, columns=['group_return'])
            corr_pd['group_number'] = (list(range(1, self.group_number + 1)))
            group.loc[year, 'Group_Corr'] = corr_pd.corr().iloc[0, 1]

        # 写入Excel
        path = os.path.join(self.summary_path, stock_pool_name)
        if not os.path.exists(path):
            os.makedirs(path)
        filename = os.path.join(path, 'summary_%s.xlsx' % factor_name)

        sheet_name = factor_name
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

        pos_pic = len(summary.index) + 3
        pos_end = len(summary.index) + 1
        excel.chart_columns_plot(worksheet, sheet_name, series_name=["分组超额收益"],
                                 chart_name="分组超额收益%s" % factor_name,
                                 insert_pos="B%s" % pos_pic, cat_beg="N1", cat_end="W1",
                                 val_beg_list=["N%s" % pos_end], val_end_list=["W%s" % pos_end])

        try:

            # 风险暴露部分:每年Alpha在risk上的暴露
            alpha_risk = AlphaSplit().get_alpha_risk_exposure(factor_name, stock_pool_name).T
            alpha_risk['year'] = alpha_risk.index.map(lambda x: datetime.strptime(str(x), "%Y%m%d").year)
            alpha_risk = alpha_risk.groupby(by=['year']).mean()
            alpha_risk.loc['All', :] = alpha_risk.mean()
            alpha_risk.index = alpha_risk.index.map(str)

            num_format_pd = pd.DataFrame([], columns=alpha_risk.columns, index=['format'])
            num_format_pd.loc['format', :] = '0.00%'
            beg_col = 5 + len(group.columns) + len(summary.columns)
            excel.write_pandas(alpha_risk, worksheet, begin_row_number=0, begin_col_number=beg_col,
                               num_format_pd=num_format_pd, color="blue", fillna=True)

            excel.chart_columns_plot(worksheet, sheet_name, series_name=["风格暴露"],
                                     chart_name="风格暴露%s" % factor_name,
                                     insert_pos="N%s" % pos_pic, cat_beg="AA1", cat_end="AJ1",
                                     val_beg_list=["AA%s" % pos_end], val_end_list=["AJ%s" % pos_end])
        except:
            print("没有残差因子在风险上的暴露程度")

        excel.close()

    def cal_all_factor_return(self, beg_date, end_date, factor_list=None,
                              period="W", stock_pool_name="AllChinaStockFilter", force=1):

        """ 计算所有因子收益率 """

        if factor_list is None:
            factor_list = AlphaSplit().get_all_alpha_factor_name(stock_pool_name)

        for i in range(0, len(factor_list)):

            factor_name = factor_list[i]
            path = os.path.join(self.return_path, stock_pool_name)
            filename = os.path.join(path, 'factor_return_%s.csv' % factor_name)
            if force or not os.path.exists(filename):
                print("Cal Alpha Factor Return", factor_name)
                self.cal_factor_return(beg_date, end_date, factor_name, period, stock_pool_name)
            else:
                print("Already Exist Alpha Factor Return", factor_name)

    def cal_all_factor_summary(self, beg_date, end_date, factor_list=None,
                               period="W", stock_pool_name="AllChinaStockFilter", force=1):

        """ 计算所有因子表现 """

        if factor_list is None:
            factor_list = AlphaSplit().get_all_alpha_factor_name(stock_pool_name)

        for i in range(0, len(factor_list)):

            factor_name = factor_list[i]
            path = os.path.join(self.summary_path, stock_pool_name)
            filename = os.path.join(path, 'summary_%s.xlsx' % factor_name)
            if force or not os.path.exists(filename):
                print("Summary Alpha Factor Return", factor_name)
                self.cal_factor_summary(beg_date, end_date, factor_name, period, stock_pool_name)
            else:
                print("Already Summary Alpha Factor Return", factor_name)

    def concat_summary(self, stock_pool_name):

        """ 所有因子回测结果汇总 """

        factor_list = AlphaSplit().get_all_alpha_factor_name(stock_pool_name)
        all_data = pd.DataFrame()

        for i in range(0, len(factor_list)):

            factor_name = factor_list[i]
            try:
                print("Summary Alpha Factor Return", factor_name)
                path = os.path.join(self.summary_path, stock_pool_name)
                filename = os.path.join(path, 'summary_%s.xlsx' % factor_name)
                data = pd.read_excel(filename, index_col=[1])
                columns = ['ICIR', 'IC均值', '年化波动率', '年化收益', '开始时间', '结束时间', '自相关系数']
                data_factor = pd.DataFrame(data.loc['All', columns])
                data_factor.columns = [factor_name]
                data_factor = data_factor.T
                all_data = pd.concat([all_data, data_factor], axis=0)
            except Exception as e:
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

    def get_concat_summary(self, stock_pool_name):

        """ 得到所有因子测试结果 """

        filename = os.path.join(self.summary_path, 'AlphaSummary_%s.xlsx' % stock_pool_name)
        data = pd.read_excel(filename, index_col=[1])
        data = data.T.dropna(how='all').T
        return data


if __name__ == '__main__':

    """ 参数 """

    self = AlphaSummary()
    beg_date, end_date, period = "20040101", datetime.today().strftime("%Y%m%d"), "W"
    factor_name = "alpha_raw_sue0"
    stock_pool_name = "AllChinaStockFilter"

    """ 计算一个因子 在某个股票池 """

    stock_pool_name = "AllChinaStockFilter"
    self.cal_factor_return(beg_date, end_date, factor_name, period, stock_pool_name)
    self.cal_factor_summary(beg_date, end_date, factor_name, period, stock_pool_name)
    self.concat_summary(stock_pool_name)

    stock_pool_name = "hs300"
    self.cal_factor_return(beg_date, end_date, factor_name, period, stock_pool_name)
    self.cal_factor_summary(beg_date, end_date, factor_name, period, stock_pool_name)
    self.concat_summary(stock_pool_name)

    stock_pool_name = "zz500"
    self.cal_factor_return(beg_date, end_date, factor_name, period, stock_pool_name)
    self.cal_factor_summary(beg_date, end_date, factor_name, period, stock_pool_name)
    self.concat_summary(stock_pool_name)

    """ 计算所有因子 在某个股票池 """

    # stock_pool_name = "AllChinaStockFilter"
    # self.cal_all_factor_return(beg_date, end_date, period, stock_pool_name, 0)
    # self.cal_all_factor_summary(beg_date, end_date, period, stock_pool_name, 0)
    # self.concat_summary(stock_pool_name)
    #
    # stock_pool_name = "hs300"
    # self.cal_all_factor_return(beg_date, end_date, period, stock_pool_name, 0)
    # self.cal_all_factor_summary(beg_date, end_date, period, stock_pool_name, 0)
    # self.concat_summary(stock_pool_name)
    #
    # stock_pool_name = "zz500"
    # self.cal_all_factor_return(beg_date, end_date, period, stock_pool_name, 0)
    # self.cal_all_factor_summary(beg_date, end_date, period, stock_pool_name, 0)
    # self.concat_summary(stock_pool_name)
