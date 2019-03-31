import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.write_excel import WriteExcel
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaFactorUpdate(Data):

    """ 更新计算全部Alpha因子 """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\alpha_model\factor\param'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    @staticmethod
    def update_alpha_factor(beg_date=None, end_date=None):

        """ 开始更新最近Alpha数据 """

        if end_date is None:
            end_date = datetime.today().strftime("%Y%m%d")
        if beg_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -60)

        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_income_yoy import AlphaIncomeYoY
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_profit_yoy import AlphaProfitYoY
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_roe import AlphaROE
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ths import AlphaTHS
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_to_bias import AlphaTOBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ths_bias import AlphaTHSBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_rsi import AlphaRSI

        AlphaIncomeYoY().cal_factor_exposure(beg_date, end_date)
        AlphaProfitYoY().cal_factor_exposure(beg_date, end_date)
        AlphaROE().cal_factor_exposure(beg_date, end_date)
        AlphaTHS().cal_factor_exposure(beg_date, end_date)
        AlphaRSI().cal_factor_exposure(beg_date, end_date)
        AlphaTHSBias().cal_factor_exposure(beg_date, end_date)
        AlphaTOBias().cal_factor_exposure(beg_date, end_date)

    def check_alpha_factor_update_date(self):

        """ 检查所有Alpha因子最后更新时间 """

        factor_name_list = AlphaFactor().get_all_alpha_factor_name()
        result = pd.DataFrame([], columns=['开始日期', '结束日期'], index=factor_name_list)

        for i in range(0, len(factor_name_list)):

            factor_name = factor_name_list[i]
            try:
                print("######### 检查更新日期 %s 数据 ############" % factor_name)
                factor = AlphaFactor().get_alpha_factor_exposure(factor_name)
                result.loc[factor_name, '开始日期'] = factor.columns[0]
                result.loc[factor_name, '结束日期'] = factor.columns[-1]
                result.loc[factor_name, "最后一天有效数据个数"] = factor.iloc[:, -1].count()
                result.loc[factor_name, "最后一天股票个数"] = len(factor.iloc[:, -1])
                result.loc[factor_name, "最后一天有效数据比率"] = factor.iloc[:, -1].count() / len(factor.iloc[:, -1])
            except Exception as e:
                result.loc[factor_name, '开始日期'] = ""
                result.loc[factor_name, '结束日期'] = ""
                result.loc[factor_name, "最后一天有效数据个数"] = ""
                result.loc[factor_name, "最后一天股票个数"] = ""
                result.loc[factor_name, "最后一天有效数据比率"] = ""
                print("########### %s 检查更新数据 为空 ！！！###########" % factor_name)

        out_file = os.path.join(self.data_path, "AlphaFactorUpdateDate.xlsx")
        we = WriteExcel(out_file)
        ws = we.add_worksheet("更新数据")

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0'
        num_format_pd.loc['format', ['最后一天有效数据比率']] = '0.00%'
        we.write_pandas(result, ws, begin_row_number=0, begin_col_number=1,
                        num_format_pd=num_format_pd, color="blue", fillna=True)

        we.close()


if __name__ == '__main__':

    self = AlphaFactorUpdate()
    # self.update_alpha_factor()
    self.check_alpha_factor_update_date()
