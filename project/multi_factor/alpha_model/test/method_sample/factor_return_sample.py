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
from quant.utility.factor_preprocess import FactorPreProcess


class FactorReturnSample(Data):

    """ 简单测试Alpha因子 """

    def __init__(self, factor_name=""):

        Data.__init__(self)
        self.sub_path = r'stock_data\alpha_model\factor_return\sample'
        self.path_factor_return_sample = os.path.join(self.primary_data_path, self.sub_path)

        self.group_number = 10
        self.year_trade_days = 242
        self.min_stock_number = 100
        self.labels = ["Group" + str(i) for i in list(range(1, self.group_number + 1))]
        self.period = "2W"
        self.year_number = 25

        self.price = None
        self.alpha = None
        self.industry = None
        self.date_series = None
        self.alpha_exposure = None
        self.alpha_return = None
        self.alpha_factor_name = ""
        self.corr_with_barra = pd.DataFrame([])
        self.alpha_factor_name = factor_name

    def get_data(self, beg_date, end_date, period="2W", year_number=25):

        """ 得到数据 """

        self.period = period
        self.year_number = year_number
        self.price = Stock().read_factor_h5("Price_Unadjust")
        self.industry = Stock().read_factor_h5("industry_citic1")

        alpha = Stock().read_factor_h5(self.alpha_factor_name, Stock().get_h5_path("my_alpha"))
        alpha = FactorPreProcess().remove_extreme_value_mad(alpha)
        alpha = FactorPreProcess().standardization(alpha)
        self.alpha = alpha

        date_series = Date().get_trade_date_series(beg_date, end_date, period=period)
        date_series = list(set(date_series) & set(self.alpha.columns) &
                           set(self.industry.columns) & set(self.price.columns))
        date_series.sort()
        self.date_series = date_series

        self.alpha_return = pd.DataFrame([], index=date_series)
        self.alpha_exposure = pd.DataFrame([], index=date_series, columns=self.price.index)
        self.corr_with_barra = pd.DataFrame([])

    def cal_factor_data(self):

        """计算每个换仓周期的因子收益率\计算因子残差暴露\因子与其他因子的相关性"""

        for i_date in range(len(self.date_series) - 2):

            data_date = self.date_series[i_date]
            buy_date = Date().get_trade_date_offset(data_date, 1)
            sell_date = Date().get_trade_date_offset(self.date_series[i_date + 1], 1)

            print(" Calculating Factor %s Alpha Return At %s" % (self.alpha_factor_name, data_date))

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
            stock_pool = Stock().get_invest_stock_pool(date=data_date, stock_pool_name="AllChinaStockFilter")
            stock_pool = list(set(stock_pool) & set(neutral_frame.index) & set(alpha_date.index))
            stock_pool.sort()
            alpha_date = alpha_date.loc[stock_pool, "Alpha"]
            neutral_frame = neutral_frame.loc[stock_pool, :]

            if len(alpha_date) > self.min_stock_number:

                params, t_values, alpha_date_res = FactorNeutral().factor_exposure_neutral(alpha_date, neutral_frame)
                exposure_corr = FactorNeutral().factor_exposure_corr(alpha_date, neutral_frame)
                exposure_corr.columns = [data_date]
                self.corr_with_barra = pd.concat([self.corr_with_barra, exposure_corr], axis=1)
                self.alpha_exposure.loc[data_date, :] = alpha_date_res
                res = pd.concat([alpha_date_res, pct_date], axis=1)
                res.columns = ['alpha_val', 'period_pct']
                res = res.dropna()
                res = res.sort_values(by=['alpha_val'], ascending=False)
                res['weight'] = res['alpha_val'] / res['alpha_val'].abs().sum()
                res['group'] = pd.qcut(res['alpha_val'], q=self.group_number, labels=self.labels)

                period_return = (res['weight'] * res['period_pct']).sum()
                self.alpha_return.ix[data_date, "FactorReturn"] = period_return

                information_correlation = res['alpha_val'].corr(res['period_pct'], method="pearson")
                self.alpha_return.ix[data_date, "IC"] = information_correlation

                group_pct = res.groupby(by=['group'])['period_pct'].mean()
                group_pct -= res['period_pct'].mean()
                for i_label in range(len(self.labels)):
                    self.alpha_return.ix[data_date, self.labels[i_label]] = group_pct.values[i_label]

        # factor return save file
        self.alpha_return = self.alpha_return.dropna(subset=['FactorReturn'])
        self.alpha_return["CumFactorReturn"] = self.alpha_return['FactorReturn'].cumsum()
        cum_labels = ["Cum_" + str(x) for x in self.labels]
        self.alpha_return[cum_labels] = self.alpha_return[self.labels].cumsum()
        return_path = os.path.join(self.path_factor_return_sample, "test")

        if not os.path.exists(return_path):
            os.makedirs(return_path)

        file = os.path.join(return_path, self.alpha_factor_name + '_factor_return.csv')
        self.alpha_return.to_csv(file)

        # factor exposure_return res save file
        exposure_path = os.path.join(self.path_factor_return_sample, "exposure")
        if not os.path.exists(exposure_path):
            os.makedirs(exposure_path)

        file = os.path.join(exposure_path, self.alpha_factor_name + '_factor_exposure.csv')
        self.alpha_exposure = self.alpha_exposure.astype(np.float)
        self.alpha_exposure.T.to_csv(file)

        # factor exposure_return with other factor
        corr_with_barra_path = os.path.join(self.path_factor_return_sample, "corr_with_barra")
        if not os.path.exists(corr_with_barra_path):
            os.makedirs(corr_with_barra_path)

        self.corr_with_barra = self.corr_with_barra.T
        file = os.path.join(corr_with_barra_path, self.alpha_factor_name + '_corr_with_barra.csv')
        self.corr_with_barra = self.corr_with_barra.astype(np.float)
        self.corr_with_barra.to_csv(file)

    def get_alpha_res(self):

        """ 得到因子残差暴露 """

        exposure_path = os.path.join(self.path_factor_return_sample, "exposure")
        file = os.path.join(exposure_path, self.alpha_factor_name + '_factor_exposure.csv')
        self.alpha_exposure = pd.read_csv(file, index_col=[0], encoding='gbk')
        self.alpha_exposure.columns = self.alpha_exposure.columns.map(str)
        return self.alpha_exposure

    def get_factor_data(self):

        """ 得到因子收益率 得到因子残差暴露 """

        exposure_path = os.path.join(self.path_factor_return_sample, "exposure")
        file = os.path.join(exposure_path, self.alpha_factor_name + '_factor_exposure.csv')
        self.alpha_exposure = pd.read_csv(file, index_col=[0], encoding='gbk')
        self.alpha_exposure.columns = self.alpha_exposure.columns.map(str)

        return_path = os.path.join(self.path_factor_return_sample, "test")
        file = os.path.join(return_path, self.alpha_factor_name + '_factor_return.csv')
        self.alpha_return = pd.read_csv(file, index_col=[0], encoding='gbk')
        self.alpha_return.index = self.alpha_return.index.map(str)

        corr_with_barra_path = os.path.join(self.path_factor_return_sample, "corr_with_barra")
        file = os.path.join(corr_with_barra_path, self.alpha_factor_name + '_corr_with_barra.csv')
        self.corr_with_barra = pd.read_csv(file, index_col=[0], encoding='gbk')
        self.corr_with_barra.index = self.corr_with_barra.index.map(str)

    def cal_factor_exposure_corr(self):

        """ 计算因子残差暴露前后两期相关性 """

        self.get_factor_data()
        exposure_corr = pd.DataFrame([], index=self.alpha_exposure.index, columns=['ExposureCorr'])

        for i_date in range(1, len(self.alpha_exposure.index)):

            last_exposure_date = self.alpha_exposure.index[i_date - 1]
            cur_exposure_date = self. alpha_exposure.index[i_date]
            exposure_adjoin = self.alpha_exposure.loc[last_exposure_date:cur_exposure_date, :]
            exposure_adjoin = exposure_adjoin.T.dropna()
            corr = exposure_adjoin.corr(method="spearman").iloc[0, 1]
            exposure_corr.loc[cur_exposure_date, 'ExposureCorr'] = corr

        exposure_corr = exposure_corr.dropna()
        exposure_corr.ix['Mean', 'ExposureCorr'] = exposure_corr['ExposureCorr'].mean()
        exposure_path = os.path.join(self.path_factor_return_sample, "factor_exposure_corr")

        if not os.path.exists(exposure_path):
            os.makedirs(exposure_path)
        filename = os.path.join(exposure_path, self.alpha_factor_name + "_factor_exposure_corr.csv")
        exposure_corr.to_csv(filename)

    def cal_factor_result(self):

        """ 计算每年的因子表现 """

        self.get_factor_data()
        back_test_beg_date = Date().get_trade_date_offset(self.date_series[0], 1)
        back_test_end_date = Date().get_trade_date_offset(self.date_series[len(self.date_series) - 1], 1)
        back_test_days = Date().get_trade_date_diff(back_test_beg_date, back_test_end_date)
        backtest_year = back_test_days / self.year_trade_days

        # 每年
        self.alpha_return['year'] = self.alpha_return.index.map(lambda x: datetime.strptime(x, "%Y%m%d").year)
        year_factor_return = self.alpha_return.groupby(by=['year'])['FactorReturn'].sum()
        year_factor_std = self.alpha_return.groupby(by=['year'])['FactorReturn'].std() * np.sqrt(self.year_number)
        year_count = self.alpha_return.groupby(by=['year'])['FactorReturn'].count()
        year_ic_mean = self.alpha_return.groupby(by=['year'])['IC'].mean()
        year_ic_std = self.alpha_return.groupby(by=['year'])['IC'].std()
        year_gp_mean = self.alpha_return.groupby(by=['year'])[self.labels].sum()

        yearly = pd.concat([year_factor_return, year_factor_std, year_count,
                            year_ic_mean, year_ic_std, year_gp_mean], axis=1)
        col = ['YearReturn', 'YearReturnStd', 'Count', 'IC_mean', 'IC_std']
        col.extend(self.labels)
        yearly.columns = col

        yearly['YearReturn'] = yearly['YearReturn'] / yearly['Count'] * year_count
        yearly['IC_IR'] = yearly['IC_mean'] / yearly['IC_std'] * np.sqrt(self.year_number)

        self.corr_with_barra['year'] = self.corr_with_barra.index.map(lambda x: datetime.strptime(str(x), "%Y%m%d").year)
        corr_yearly = self.corr_with_barra.groupby(by=['year']).mean()
        risk_col = list(corr_yearly.columns)

        yearly = pd.concat([yearly, corr_yearly], axis=1)

        # 整体
        yearly.loc['All', 'YearReturn'] = self.alpha_return["FactorReturn"].sum() / backtest_year
        yearly.loc['All', 'YearReturnStd'] = self.alpha_return["FactorReturn"].std() * np.sqrt(self.year_number)
        mean = self.alpha_return["IC"].mean()
        std = self.alpha_return["IC"].std()
        yearly.loc['All', 'Count'] = yearly['Count'].sum()
        yearly.loc['All', 'IC_IR'] = mean / std * np.sqrt(self.year_number)
        yearly.loc['All', 'IC_mean'] = mean
        yearly.loc['All', 'IC_std'] = std

        yearly.loc['All', self.labels] = self.alpha_return[self.labels].sum() / backtest_year
        yearly.loc['All', risk_col] = self.corr_with_barra[risk_col].mean()
        yearly.index = yearly.index.map(str)

        for i in range(len(yearly)):
            year = yearly.index[i]
            corr_pd = pd.DataFrame(yearly.ix[year, self.labels].values, index=self.labels, columns=['group_return'])
            corr_pd['group_number'] = (list(range(1, self.group_number + 1)))
            yearly.loc[year, 'Group_Corr'] = corr_pd.corr().ix[0, 1]

        num_format_pd = pd.DataFrame([], columns=yearly.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.ix['format', ['Count', 'IC_IR', 'Group_Corr']] = '0.00'

        # write pandas
        exposure_path = os.path.join(self.path_factor_return_sample, "factor_summary_year")

        if not os.path.exists(exposure_path):
            os.makedirs(exposure_path)
        filename = os.path.join(exposure_path, self.alpha_factor_name + "_factor_summary_year.xlsx")

        sheet_name = "factor_summary_year"
        excel = WriteExcel(filename)
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(yearly, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        excel.chart_columns_plot(worksheet, sheet_name, series_name="分组超额收益",
                                 insert_pos="B%s" % (len(yearly) + 3),
                                 cat_beg="H1", cat_end="Q1",
                                 val_beg_list=["H%s" % (len(yearly) + 1)],
                                 val_end_list=["Q%s" % (len(yearly) + 1)])

        excel.chart_columns_plot(worksheet, sheet_name, series_name="风格暴露",
                                 insert_pos="L%s" % (len(yearly) + 3),
                                 cat_beg="S1", cat_end="AB1",
                                 val_beg_list=["S%s" % (len(yearly) + 1)],
                                 val_end_list=["AB%s" % (len(yearly) + 1)])

        excel.chart_columns_plot(worksheet, sheet_name, series_name="行业暴露",
                                 insert_pos="W%s" % (len(yearly) + 3),
                                 cat_beg="AC1", cat_end="BH1",
                                 val_beg_list=["AC%s" % (len(yearly) + 1)],
                                 val_end_list=["BH%s" % (len(yearly) + 1)])

        excel.close()

    def cal_all_factor_result(self):

        """ 计算所有因子表现 """

        period = "2W"
        year_number = 26
        beg_date = "20040101"
        end_date = datetime.today().strftime("%Y%m%d")

        sub_path_file = r"stock_data\alpha_model\factor_exposure\param_file\MyAlpha.xlsx"
        file = os.path.join(Data().primary_data_path, sub_path_file)
        data = pd.read_excel(file, encoding='gbk')
        data = data[data['计算因子收益率'] == "是"]
        data = data.reset_index(drop=True)

        for i in range(0, len(data)):

            factor_name = data.loc[data.index[i], "因子名"]
            print("Cal Alpha Factor Return", factor_name)
            self.alpha_factor_name = factor_name
            self.get_data(beg_date, end_date, period, year_number)
            self.cal_factor_data()
            self.get_factor_data()
            self.cal_factor_exposure_corr()
            self.cal_factor_result()

    def cal_all_factor_summary(self):

        """ 所有因子回测结果汇总 """

        all_data = pd.DataFrame([])
        path = os.path.join(FactorReturnSample("").path_factor_return_sample, "factor_summary_year")
        file_list = os.listdir(path)
        factor_list = list(map(lambda x: x[0:-25], file_list))

        for i in range(0, len(factor_list)):
            factor_name = factor_list[i]
            print("Summary Alpha Factor Return", factor_name)
            self.alpha_factor_name = factor_name
            try:
                exposure_path = os.path.join(self.path_factor_return_sample, "factor_summary_year")
                filename = os.path.join(exposure_path, self.alpha_factor_name + "_factor_summary_year.xlsx")
                data = pd.read_excel(filename, index_col=[1])
                columns = ['IC_IR', 'IC_mean', 'IC_std', 'YearReturnStd', 'YearReturn']
                data_factor = pd.DataFrame(data.loc['All', columns])
                data_factor.columns = [factor_name]
                data_factor = data_factor.T
                all_data = pd.concat([all_data, data_factor], axis=0)
            except Exception as e:
                print(e)
                print("Can not Find Factor Result", factor_name)

        all_data.to_csv(os.path.join(path, 'Summary.csv'))


if __name__ == '__main__':

    self = FactorReturnSample()
    self.cal_all_factor_result()
    self.cal_all_factor_summary()
