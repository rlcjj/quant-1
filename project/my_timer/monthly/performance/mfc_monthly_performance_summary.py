import calendar
from datetime import datetime

from fund.fund_rank import *
from quant.data.data import Data
from quant.mfc.mfc_data import MfcData
from quant.stock.index import Index
from quant.utility.financial_series import FinancialSeries
from quant.utility.write_excel import WriteExcel


class MfcMonthlyPerformanceSummary(Data):

    """ 泰达宏利金融工程部基金每个月的基金业绩表现总结 """

    def __init__(self):

        Data.__init__(self)
        self.data_path = os.path.join(self.primary_data_path, 'mfcteda_data\performance\LastPerformance')

    def get_date_pd(self, end_date_str):

        """ 得到今年1月-12月开始和结束日期"""

        year = datetime.strptime(end_date_str, '%Y%m%d').year
        beign_date_str = datetime(year=year, month=1, day=1).strftime("%Y%m%d")

        date_list = []
        date_list.append([beign_date_str, end_date_str])
        today_month = datetime.today().month

        for m in range(1, 13):

            firstDayWeekDay, monthRange = calendar.monthrange(year=year, month=m)
            begin_date_month = datetime(year=year, month=m, day=1)
            end_date_month = datetime(year=year, month=m, day=monthRange)
            if m == today_month:
                end_date_month = datetime(year=year, month=m, day=1)
            date_list.append([begin_date_month.strftime("%Y%m%d"), end_date_month.strftime("%Y%m%d")])

        index = ['YTD']
        index.extend([str(x) + '月' for x in range(1, 13)])
        date_pd = pd.DataFrame(date_list, index=index, columns=['beg_date', 'end_date']).T

        return date_pd

    def mfcteda_fund_return(self, end_date, fund_type, fund_code, fund_name):

        """ 计算1个基金今年所有月份收益 """

        date_pd = self.get_date_pd(end_date)
        fund_data = MfcData().get_mfc_nav(fund_code, fund_name, fund_type)

        return_pd = pd.DataFrame([], columns=date_pd.columns, index=[fund_name])

        for i in date_pd.columns:

            beg_date = date_pd.ix["beg_date", i]
            end_date = date_pd.ix["end_date", i]

            fs = FinancialSeries(pd.DataFrame(fund_data))
            try:
                return_pd.ix[fund_name, i] = fs.get_interval_return(beg_date, end_date)
            except Exception as e:
                pass
        return return_pd

    def get_mfcteda_all_return(self, end_date):

        """ 计算所有基金今年所有月份收益 """

        path = MfcData().data_path
        file = os.path.join(path, "static_data", "Fund_Info_For_Month.xlsx")
        params = pd.read_excel(file, encoding='gbk')

        for i in range(len(params)):

            fund_type = params.ix[i, 'Type']
            fund_name = params.ix[i, 'Name']
            fund_code = params.ix[i, 'Code']
            print(fund_name)
            if i == 0:
                return_pd = self.mfcteda_fund_return(end_date, fund_type, fund_code, fund_name)
            else:
                return_pd_add = self.mfcteda_fund_return(end_date, fund_type, fund_code, fund_name)
                return_pd = pd.concat([return_pd, return_pd_add], axis=0)

        return return_pd

    def mfcteda_benchmark_return(self, end_date, benchmark_code, benchmark_name):

        """ 计算1个指数今年所有月份收益 """

        date_pd = self.get_date_pd(end_date)

        benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
        return_pd = pd.DataFrame([], columns=date_pd.columns, index=[benchmark_name])

        for i in date_pd.columns:

            beg_date = date_pd.ix["beg_date", i]
            end_date = date_pd.ix["end_date", i]
            fs = FinancialSeries(pd.DataFrame(benchmark_data))
            try:
                return_pd.ix[benchmark_name, i] = fs.get_interval_return(beg_date, end_date)
            except Exception as e:
                pass

        return return_pd

    def get_benchmark_all_return(self, end_date):

        """ 计算所有指数今年所有月份收益 """

        params = [['000300.SH', '沪深300'],
                  ['000905.SH', '中证500'],
                  ['881001.WI', '万德全A'],
                  ['399006.SZ', '创业板指'],
                  ['885012.WI', '股票型基金总指数'],
                  ['885003.WI', '偏债混合基金指数'],
                  ['885007.WI', '混合债券二级基金指数']]
        params = pd.DataFrame(params, columns=['code', 'name'])

        for i in range(len(params)):

            index_code = params.ix[i, 'code']
            index_name = params.ix[i, 'name']
            print(index_name)
            if i == 0:
                return_pd = self.mfcteda_benchmark_return(end_date, index_code, index_name)
            else:
                return_pd_add = self.mfcteda_benchmark_return(end_date, index_code, index_name)
                return_pd = pd.concat([return_pd, return_pd_add], axis=0)

        return return_pd

    def mfcteda_fund_excess_return(self, end_date, fund_type, fund_code, fund_name, benchmark_code, benchmark_ratio):

        """ 计算1个基金今年所有月份超额收益 """

        date_pd = self.get_date_pd(end_date)

        if fund_type == "公募":
            fund_data = MfcData().get_mfc_public_fund_nav(fund_code)
            fund_data = fund_data['NAV_ADJ']
        else:
            fund_data = MfcData().get_mfc_private_fund_nav(fund_name)
            fund_data = fund_data['累计复权净值']

        benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
        return_pd = pd.DataFrame([], columns=date_pd.columns, index=[fund_name])

        for i in date_pd.columns:

            beg_date = date_pd.ix["beg_date", i]
            end_date = date_pd.ix["end_date", i]
            fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data) * benchmark_ratio)
            try:
                return_pd.ix[fund_name, i] = fs.get_interval_excess_return(beg_date, end_date)
            except Exception as e:
                pass

        return return_pd

    def get_mfcteda_all_excess_return(self, end_date):

        """ 计算所有基金今年所有月份超额收益 """

        path = MfcData().data_path
        file = os.path.join(path, "static_data", "Fund_Info_For_Month.xlsx")
        params = pd.read_excel(file, encoding='gbk')
        params = params.dropna(subset=['Index_Ratio'])
        params = params.reset_index(drop=True)

        for i in range(len(params)):

            fund_type = params.ix[i, 'Type']
            fund_name = params.ix[i, 'Name']
            fund_code = params.ix[i, 'Code']
            benchmark_code = params.ix[i, 'Index']
            benchmark_ratio = params.ix[i, 'Index_Ratio']
            print(fund_name)

            if i == 0:
                return_pd = self.mfcteda_fund_excess_return(end_date, fund_type, fund_code,
                                                       fund_name, benchmark_code, benchmark_ratio)
            else:
                return_pd_add = self.mfcteda_fund_excess_return(end_date, fund_type, fund_code,
                                                           fund_name, benchmark_code, benchmark_ratio)
                return_pd = pd.concat([return_pd, return_pd_add], axis=0)

        return return_pd

    def mfcteda_fund_rank(self, end_date, fund_code, fund_name, rank_pool, excess):

        """ 计算1个基金今年所有月份排名 """

        date_pd = self.get_date_pd(end_date)
        return_pd = pd.DataFrame([], columns=date_pd.columns, index=[fund_name])

        for i in date_pd.columns:

            beg_date = date_pd.ix["beg_date", i]
            end_date = date_pd.ix["end_date", i]
            new_fund_date = beg_date
            try:
                rank_str, rank_pct = rank_fund(fund_code, rank_pool, beg_date, end_date, new_fund_date, excess)
                return_pd.ix[fund_name, i] = rank_str
            except Exception as e:
                return_pd.ix[fund_name, i] = ""

        return return_pd

    def get_mfcteda_all_rank(self, end_date):

        """ 计算所有基金今年所有月份排名 """

        path = MfcData().data_path
        file = os.path.join(path, "static_data", "Fund_Info_For_Month.xlsx")
        params = pd.read_excel(file, encoding='gbk')
        params = params.dropna(subset=['Rank'])
        params = params.reset_index(drop=True)

        for i in range(len(params)):

            fund_name = params.ix[i, 'Name']
            fund_code = params.ix[i, 'Code']
            rank_pool = params.ix[i, 'Fund_Pool']
            excess = params.ix[i, 'Rank']
            print(fund_name)

            if i == 0:
                return_pd = self.mfcteda_fund_rank(end_date, fund_code, fund_name, rank_pool, excess)
            else:
                return_pd_add = self.mfcteda_fund_rank(end_date, fund_code, fund_name, rank_pool, excess)
                return_pd = pd.concat([return_pd, return_pd_add], axis=0)

        return return_pd

    def write_excel(self, end_date):

        """ 将所有基金收益率、超额收益、排名写入文件 """
        ###########################################################
        file_name = os.path.join(self.data_path, "基金最近表现_" + str(end_date) + ".xlsx")

        sheet_name = "指数和基金收益"
        excel = WriteExcel(file_name)
        worksheet = excel.add_worksheet(sheet_name)

        ###########################################################
        table = self.get_mfcteda_all_return(end_date)
        table2 = self.get_benchmark_all_return(end_date)
        table = pd.concat([table2, table], axis=0)

        num_format_pd = pd.DataFrame([], columns=table.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(table, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        ###########################################################
        sheet_name = "基金超额收益"
        worksheet = excel.add_worksheet(sheet_name)

        table = self.get_mfcteda_all_excess_return(end_date)
        num_format_pd = pd.DataFrame([], columns=table.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(table, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="green", fillna=True)

        ###########################################################
        sheet_name = "基金排名"
        worksheet = excel.add_worksheet(sheet_name)

        table = self.get_mfcteda_all_rank(end_date)
        print(table)
        num_format_pd = pd.DataFrame([], columns=table.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        excel.write_pandas(table, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="bule", fillna=True)

        excel.close()


if __name__ == '__main__':

    end_date = Date().get_normal_date_last_month_end_day(datetime.today())
    print(end_date)
    self = MfcMonthlyPerformanceSummary()
    self.write_excel(end_date)

