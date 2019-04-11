import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.utility.write_excel import WriteExcel
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_update import AlphaFactorUpdate


class MfcAlphaExposure(Data):

    """ 计算泰达基金在Alpha因子的暴露 """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\alpha_expsore'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self, beg_date, end_date):

        """ 更新数据 """
        print(beg_date, end_date)
        AlphaFactorUpdate().update_alpha_factor(beg_date, end_date)

    def get_fund_file(self, fund_pool):

        """ 得到基金列表 """

        file = os.path.join(self.data_path, "fund.xlsx")
        data = pd.read_excel(file, index_col=[0], sheetname=fund_pool)

        return data

    def get_alpha_file(self):

        """ Alpha 参数表 """

        file = os.path.join(self.data_path, "alpha.xlsx")
        data = pd.read_excel(file)
        data = data.dropna(subset=['因子名'])
        data.index = data['因子名']

        return data

    def fund_alpha_exposure(self, fund_pool, report_date):

        """ 生成基金Alpha暴露 """

        fund_info = self.get_fund_file(fund_pool)
        fund_holder = Fund().get_fund_holding_stock_all()
        fund_holder = fund_holder[fund_holder.ReportDate == report_date]
        fund_holder = fund_holder.reset_index(drop=True)
        alpha_list = self.get_alpha_file()
        trade_date = Date().get_trade_date_offset(report_date, 0)

        result = pd.DataFrame([], index=fund_info.index)

        for i_alpha in range(0, len(alpha_list)):

            alpha_name_en = alpha_list.index[i_alpha]
            alpha_name_ch = alpha_list.loc[alpha_name_en, "名称"]
            alpha_data = AlphaFactor().get_alpha_factor_exposure(alpha_name_en)

            for i_fund in range(0, len(fund_info)):

                fund_code = fund_info.index[i_fund]
                fund_name = fund_info.loc[fund_code, "基金名称"]
                holder = fund_holder[fund_holder.FundCode == fund_code]
                holder = holder.reset_index(drop=True)
                holder.index = holder.StockCode
                weight = pd.DataFrame(holder.Weight)

                if (len(weight) > 0) and (trade_date in alpha_data.columns):
                    weight = weight.sort_values(by=['Weight'], ascending=False)
                    alpha = pd.DataFrame(alpha_data[trade_date])
                    alpha.columns = [alpha_name_ch]
                    concat_data = pd.concat([weight, alpha], axis=1)
                    concat_data = concat_data.dropna()
                    concat_data['WeightAlpha'] = concat_data['Weight'] * concat_data[alpha_name_ch]
                    weight_alpha = concat_data['WeightAlpha'].sum() / concat_data['Weight'].sum()
                    result.loc[fund_code, alpha_name_ch] = weight_alpha
                    print(fund_name, fund_code, alpha_name_ch, alpha_name_en)
                else:
                    print(fund_name, fund_code, alpha_name_ch, alpha_name_en, "is Null")

        result = result.dropna(how="all")
        res = pd.concat([fund_info[['基金名称', '类型', '成立日期']], result], axis=1)
        res = res.loc[result.index, :]

        # write pandas
        num_format_pd = pd.DataFrame([], columns=res.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.ix['format', ['SUE0', 'SPTTM', 'BP']] = '0.00'

        sheet_name = fund_pool
        file = os.path.join(self.data_path, "%s_%s.xlsx" % (fund_pool, report_date))
        excel = WriteExcel(file)
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(res, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        for i in range(len(res.columns)):
            excel.conditional_format(worksheet, 1, i + 5, 1 + len(res), i + 5, None)

        excel.close()

    def fund_alpha_exposure_all(self, beg_date, end_date):

        """ 所有时期 """

        date_series = Date().get_normal_date_series(beg_date, end_date, "S")
        print(date_series)

        for report_date in date_series:
            self.fund_alpha_exposure("中证500", report_date)
            self.fund_alpha_exposure("沪深300", report_date)

if __name__ == '__main__':

    """ 参数 """

    today = datetime.today().strftime("%Y%m%d")
    end_date = Date().get_trade_date_offset(today, -1)
    beg_date = Date().get_trade_date_offset(today, -10)
    report_date = "20181231"

    self = MfcAlphaExposure()
    # self.update_data(beg_date, end_date)
    self.fund_alpha_exposure_all("20180101", "20190401")

