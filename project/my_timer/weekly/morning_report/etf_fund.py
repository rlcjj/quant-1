from quant.data.data import Data
from quant.stock.date import Date
from quant.fund.fund_pool import FundPool
from quant.fund.fund_factor import FundFactor

from quant.utility.write_excel import WriteExcel
from datetime import datetime
import pandas as pd
import os


class ETFFund(Data):

    """ 晨会内容 ETF净申购数据 """

    def __init__(self):

        """ 数据存储位置 """
        Data.__init__(self)
        self.sub_data_path = r'stock_data\morning_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self):

        """ 更新所需要的数据 """
        Date().load_trade_date_series("D")
        end_date = datetime.today()
        beg_date = Date().get_trade_date_offset(end_date, -60)
        FundFactor().load_fund_factor_all(beg_date, end_date)

    def get_etf_fund_data(self, beg_date, end_date):

        """ 得到etf数据"""

        print("ETF Data %s %s" % (beg_date, end_date))
        exchange_share = FundFactor().get_fund_factor("Exchange_Share")
        exchange_share = exchange_share.fillna(method='pad', limit=3)

        unit_nav = FundFactor().get_fund_factor("Unit_Nav")
        unit_nav = unit_nav.fillna(method='pad', limit=1)

        exchange_share_date = pd.DataFrame(exchange_share.T[end_date])
        exchange_share_date.columns = ['Share']
        exchange_share_date_last = pd.DataFrame(exchange_share.T[beg_date])
        exchange_share_date_last.columns = ['ShareLast']

        unit_nav_date = pd.DataFrame(unit_nav.T[end_date])
        unit_nav_date.columns = ['UnitNav']

        fund_pool = FundPool().get_fund_pool_all(name="ETF基金", date="20181231")
        fund_pool = fund_pool[['sec_name', 'wind_code', 'setupdate', 'bench_code', 'bench_name']]
        fund_pool.index = fund_pool.wind_code
        concat_data = pd.concat([fund_pool, unit_nav_date, exchange_share_date, exchange_share_date_last], axis=1)
        concat_data = concat_data.dropna()
        concat_data['MvEnd'] = concat_data['Share'] * concat_data['UnitNav']
        concat_data['Inflow'] = (concat_data['Share'] - concat_data['ShareLast']) * concat_data['UnitNav']
        concat_data['MvEnd'] /= 100000000.0
        concat_data['Inflow'] /= 100000000.0

        return concat_data

    def get_etf_data_period_sum(self, beg_date, end_date):

        """ ETF整体 """
        # end_date = "20190111"

        concat_data = self.get_etf_fund_data(beg_date, end_date)
        concat_data = concat_data[['MvEnd', 'Inflow']]
        concat_data_sum = pd.DataFrame(concat_data.sum()).T
        concat_data_sum.index = [end_date]
        concat_data_sum['InflowRatio'] = concat_data_sum['Inflow'] / concat_data_sum['MvEnd']
        concat_data_sum.columns = ['总市值', '净流入金额', '净流入占比']
        return concat_data_sum

    def get_etf_data_period_type(self, beg_date, end_date):

        """ 按照基准种类加总 """

        concat_data = self.get_etf_fund_data(beg_date, end_date)
        gb_data = pd.DataFrame(concat_data.groupby(by=['bench_name']).sum()[['MvEnd', 'Inflow']])
        gb_data = gb_data.dropna()
        gb_data = gb_data.sort_values(by=['MvEnd'], ascending=False)
        gb_data['InflowRatio'] = gb_data['Inflow'] / gb_data['MvEnd']
        gb_data.columns = ['总市值', '净流入金额', '净流入占比']
        return gb_data

    def generate_excel(self, end_date):

        """ ETF净申购 输出到Excel """

        beg_date = Date().get_trade_date_offset(end_date, -120)
        beg_1m_date = Date().get_trade_date_offset(end_date, -20)

        # 一段时间内增减持额时间序列
        date_series = Date().get_trade_date_series(beg_date, end_date, "W")
        result = pd.DataFrame([])

        from quant.stock.index import Index
        index_data = Index().get_index_factor(index_code="000300.SH")

        ed_date = end_date
        for i in range(len(date_series)-1):
            bg_date = Date().get_trade_date_offset(ed_date, -5)
            print("ETF Fund %s %s" % (bg_date, ed_date))
            result_add = self.get_etf_data_period_sum(bg_date, ed_date)
            result_add.loc[ed_date, '沪深300'] = index_data.loc[ed_date, "CLOSE"]
            result = pd.concat([result, result_add], axis=0)
            ed_date = bg_date

        result = result.sort_index()

        # 不同类型ETF基金流入流出
        fund_type = self.get_etf_data_period_type(beg_1m_date, end_date)

        # 数据存贮位置
        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # 信息写入文件
        filename = os.path.join(sub_path, 'ETF流入.xlsx')
        excel = WriteExcel(filename)
        sheet_name = "ETF流入"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', "净流入占比"] = '0.00%'
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["净申购金额", '沪深300'],
                                 chart_name="每周ETF净申购金额（亿元）",
                                 insert_pos="F8", cat_beg="B2", cat_end="B25",
                                 val_beg_list=["D2", "F2"], val_end_list=["D25", "F25"])

        num_format_pd = pd.DataFrame([], columns=fund_type.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', "净流入占比"] = '0.00%'
        excel.write_pandas(fund_type, worksheet, begin_row_number=0, begin_col_number=15,
                           num_format_pd=num_format_pd, color="orange", fillna=True)
        excel.chart_columns_plot(worksheet, sheet_name=sheet_name,
                                 series_name=["净申购占比", '净申购金额'],
                                 chart_name="规模前10类ETF基金最近1月净流入",
                                 insert_pos="F24", cat_beg="P2", cat_end="P11",
                                 val_beg_list=["S2", "R2"], val_end_list=["S11", "R11"])


        excel.close()

    def generate_excel_history(self, end_date):

        """  历史ETF净申购 和沪深300"""

        # 一段时间内增减持额时间序列
        date_series = Date().get_trade_date_series("20080101", end_date, "M")
        result_all = pd.DataFrame([])

        from quant.stock.index import Index
        index_data = Index().get_index_factor(index_code="000300.SH")

        ed_date = end_date
        for i in range(len(date_series)-1):
            bg_date = Date().get_trade_date_offset(ed_date, -20)
            print("ETF Fund %s %s" % (bg_date, ed_date))
            result_add = self.get_etf_data_period_sum(bg_date, ed_date)
            result_add.loc[ed_date, '沪深300'] = index_data.loc[ed_date, "CLOSE"]
            result_all = pd.concat([result_all, result_add], axis=0)
            ed_date = bg_date

        result_all = result_all.sort_index()

        sub_path = os.path.join(self.data_path, end_date)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        filename = os.path.join(sub_path, 'ETF流入历史.xlsx')
        excel = WriteExcel(filename)
        sheet_name = "ETF流入"
        worksheet = excel.add_worksheet(sheet_name)

        num_format_pd = pd.DataFrame([], columns=result_all.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'
        num_format_pd.loc['format', "净流入占比"] = '0.00%'
        excel.write_pandas(result_all, worksheet, begin_row_number=0, begin_col_number=20,
                           num_format_pd=num_format_pd, color="orange", fillna=True)
        excel.close()

if __name__ == "__main__":

    self = ETFFund()
    beg_date = "20190115"
    end_date = "20190321"
    self.generate_excel(end_date)
    self.generate_excel_history(end_date)
