import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.mfc.mfc_data import MfcData
from quant.fund.fund_rank import FundRank
from quant.stock.date import Date
from quant.stock.index import Index
from quant.utility.write_excel import WriteExcel
from quant.utility.financial_series import FinancialSeries


class MfcManagerScore(Data):

    """
    基金经理得分计算
    长期考核权重


    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\mfc_manager_score'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self):

        """ 下载数据 需要更新 富时指数的数据 """

        today = datetime.today()
        beg_date = Date().get_trade_date_offset(today, -120)
        Index().load_index_factor("000907.CSI", beg_date, today)

    def score(self, x):

        """ 排名和得分装换 """
        if x is None:
            return None

        if type(x) == np.str:
            return None

        if x <= 0.10:
            score = 1.00
        elif x >= 0.90:
            score = 0.00
        else:
            score = (- 1.25) * x + 1.125

        return score

    def fund_score(self, fund_code, fund_name, end_date, rank_pool, mg_date, fund_type, my_index_code):

        """ 计算基金得分 """

        # index_code = "881001.WI"
        # fund_code = "162208.OF"
        # end_date = "20181231"
        # rank_pool = "普通股票型基金"
        # mg_date = "20141121"
        # fund_type = "行业基金"
        # my_index_code = "FTSE成长"

        end_date = Date().change_to_datetime(end_date)
        before_1y = datetime(year=end_date.year - 1, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        before_3y = datetime(year=end_date.year - 3, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        before_5y = datetime(year=end_date.year - 5, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        end_date = Date().change_to_str(end_date)

        result = pd.DataFrame([], columns=["名称", "1年收益", "1年排名", "1年排名百分比", "1年得分",
                                           "3年收益", "3年排名", "3年排名百分比", "3年得分",
                                           "5年收益", "5年排名", "5年排名百分比", "5年得分"
                                           ])

        result.loc[fund_code, "名称"] = fund_name
        beg_date = before_1y
        fund_nav = MfcData().get_mfc_public_fund_nav(fund_code)
        fs = FinancialSeries(pd.DataFrame(fund_nav['NAV_ADJ']))
        result.loc[fund_code, "1年收益"] = fs.get_interval_return(beg_date, end_date)
        str_rank, pct = FundRank().rank_fund(fund_code, rank_pool, beg_date, end_date, beg_date, excess=False)
        result.loc[fund_code, "1年排名百分比"] = pct
        result.loc[fund_code, "1年排名"] = str_rank
        result.loc[fund_code, "1年得分"] = self.score(pct)

        beg_date = before_3y
        fund_nav = MfcData().get_mfc_public_fund_nav(fund_code)
        fs = FinancialSeries(pd.DataFrame(fund_nav['NAV_ADJ']))
        result.loc[fund_code, "3年收益"] = fs.get_interval_return(beg_date, end_date)
        str_rank, pct = FundRank().rank_fund(fund_code, rank_pool, beg_date, end_date, beg_date, excess=False)
        result.loc[fund_code, "3年排名百分比"] = pct
        result.loc[fund_code, "3年排名"] = str_rank
        result.loc[fund_code, "3年得分"] = self.score(pct)

        beg_date = before_5y
        fund_nav = MfcData().get_mfc_public_fund_nav(fund_code)
        fs = FinancialSeries(pd.DataFrame(fund_nav['NAV_ADJ']))
        result.loc[fund_code, "5年收益"] = fs.get_interval_return(beg_date, end_date)
        str_rank, pct = FundRank().rank_fund(fund_code, rank_pool, beg_date, end_date, beg_date, excess=False)
        result.loc[fund_code, "5年排名百分比"] = pct
        result.loc[fund_code, "5年排名"] = str_rank
        result.loc[fund_code, "5年得分"] = self.score(pct)

        beg_date = mg_date
        fund_nav = MfcData().get_mfc_public_fund_nav(fund_code)
        fs = FinancialSeries(pd.DataFrame(fund_nav['NAV_ADJ']))
        result.loc[fund_code, "管理以来收益"] = fs.get_interval_return(beg_date, end_date)
        str_rank, pct = FundRank().rank_fund(fund_code, rank_pool, beg_date, end_date, beg_date, excess=False)
        result.loc[fund_code, "管理以来排名百分比"] = pct
        result.loc[fund_code, "管理以来排名"] = str_rank
        result.loc[fund_code, "管理以来得分"] = self.score(pct)
        print(result)
        return result

    def fund_excess_score(self, fund_code, fund_name, end_date, rank_pool, mg_date, fund_type, my_index_code):

        """ 行业基金超额收益得分 """
        end_date = Date().change_to_datetime(end_date)
        before_1y = datetime(year=end_date.year - 1, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        before_3y = datetime(year=end_date.year - 3, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        before_5y = datetime(year=end_date.year - 5, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        end_date = Date().change_to_str(end_date)

        result = pd.DataFrame([], columns=["名称", "1年超额收益", "1年超额排名", "1年超额排名百分比", "1年超额得分",
                                           "3年超额收益", "3年超额排名", "3年超额排名百分比", "3年超额得分",
                                           "5年超额收益", "5年超额排名", "5年超额排名百分比", "5年超额得分"
                                           ])

        result.loc[fund_code, "名称"] = fund_name

        if fund_type == "行业基金":

            beg_date = before_1y
            excess_return, pct, rank_str = FundRank().rank_excess_fund(fund_pool_name=rank_pool, ge_index_code="881001.WI",
                                                                       my_index_code=my_index_code, my_fund_code=fund_code,
                                                                       beg_date=beg_date, end_date=end_date)
            result.loc[fund_code, "1年超额收益"] = excess_return
            result.loc[fund_code, "1年超额排名"] = rank_str
            result.loc[fund_code, "1年超额排名百分比"] = pct
            result.loc[fund_code, "1年超额得分"] = self.score(pct)

            beg_date = before_3y
            excess_return, pct, rank_str = FundRank().rank_excess_fund(fund_pool_name=rank_pool, ge_index_code="881001.WI",
                                                                       my_index_code=my_index_code, my_fund_code=fund_code,
                                                                       beg_date=beg_date, end_date=end_date)
            result.loc[fund_code, "3年超额收益"] = excess_return
            result.loc[fund_code, "3年超额排名"] = rank_str
            result.loc[fund_code, "3年超额排名百分比"] = pct
            result.loc[fund_code, "3年超额得分"] = self.score(pct)

            beg_date = before_5y
            excess_return, pct, rank_str = FundRank().rank_excess_fund(fund_pool_name=rank_pool, ge_index_code="881001.WI",
                                                                       my_index_code=my_index_code, my_fund_code=fund_code,
                                                                       beg_date=beg_date, end_date=end_date)
            result.loc[fund_code, "5年超额收益"] = excess_return
            result.loc[fund_code, "5年超额排名百分比"] = pct
            result.loc[fund_code, "5年超额排名"] = rank_str
            result.loc[fund_code, "5年超额得分"] = self.score(pct)

            beg_date = mg_date
            excess_return, pct, rank_str = FundRank().rank_excess_fund(fund_pool_name=rank_pool,
                                                                       ge_index_code="881001.WI",
                                                                       my_index_code=my_index_code,
                                                                       my_fund_code=fund_code,
                                                                       beg_date=beg_date, end_date=end_date)
            result.loc[fund_code, "管理以来超额收益"] = excess_return
            result.loc[fund_code, "管理以来超额排名百分比"] = pct
            result.loc[fund_code, "管理以来超额排名"] = rank_str
            result.loc[fund_code, "管理以来超额得分"] = self.score(pct)


        return result

    def fund_score_all(self):

        """ 所有基金得分 """
        end_date = "20181231"
        file = os.path.join(self.data_path, "基金经理绩效考核.xlsx")
        data = pd.read_excel(file, sheetname="基金经理考核范围", index_col=[0])
        data['现任经理管理开始日'] = data['现任经理管理开始日'].map(str)
        data.index = data['代码']
        result = pd.DataFrame()
        end_date = Date().change_to_datetime(end_date)
        before_1y = datetime(year=end_date.year - 1, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        before_3y = datetime(year=end_date.year - 3, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        before_5y = datetime(year=end_date.year - 5, month=end_date.month, day=end_date.day).strftime("%Y%m%d")
        end_date = Date().change_to_str(end_date)

        # for i in range(0, len(data)):
        #
        #     fund_code = data.index[i]
        #     index_code = data.loc[fund_code, "基准代码"]
        #     rank_pool = data.loc[fund_code, "考核分类"]
        #     mg_date = data.loc[fund_code, "现任经理管理开始日"]
        #     fund_name = data.loc[fund_code, "名称"]
        #     fund_type = data.loc[fund_code, "基金类型"]
        #
        #     if mg_date <= before_1y:
        #
        #         res = self.fund_score(fund_code, fund_name, end_date, rank_pool, mg_date, fund_type, index_code)
        #         res.loc[fund_code, "当年研究贡献得分"] = 1.00
        #         res.loc[fund_code, "过去2年研究贡献得分"] = 1.00
        #
        #         if mg_date >= before_5y:
        #
        #             res.loc[fund_code, "5年收益"] = res.loc[fund_code, "管理以来收益"]
        #             res.loc[fund_code, "5年排名"] = res.loc[fund_code, "管理以来排名"]
        #             res.loc[fund_code, "5年排名百分比"] = res.loc[fund_code, "管理以来排名百分比"]
        #             res.loc[fund_code, "5年得分"] = res.loc[fund_code, "管理以来得分"]
        #
        #         if mg_date >= before_3y:
        #             res.loc[fund_code, "3年收益"] = res.loc[fund_code, "管理以来收益"]
        #             res.loc[fund_code, "3年排名"] = res.loc[fund_code, "管理以来排名"]
        #             res.loc[fund_code, "3年排名百分比"] = res.loc[fund_code, "管理以来排名百分比"]
        #             res.loc[fund_code, "3年得分"] = res.loc[fund_code, "管理以来得分"]
        #
        #         res.loc[fund_code, "长期得分"] = 0.0
        #         res.loc[fund_code, "长期得分"] += 0.20 * res.loc[fund_code, "过去2年研究贡献得分"]
        #         res.loc[fund_code, "长期得分"] += 0.40 * res.loc[fund_code, "3年得分"]
        #         res.loc[fund_code, "长期得分"] += 0.20 * res.loc[fund_code, "5年得分"]
        #         res.loc[fund_code, "长期得分"] += 0.20 * res.loc[fund_code, "管理以来得分"]
        #
        #         res.loc[fund_code, "当年得分"] = 0.0
        #         res.loc[fund_code, "当年得分"] += 0.20 * res.loc[fund_code, "当年研究贡献得分"]
        #         res.loc[fund_code, "当年得分"] += 0.40 * res.loc[fund_code, "1年得分"]
        #         res.loc[fund_code, "当年得分"] += 0.20 * res.loc[fund_code, "3年得分"]
        #         res.loc[fund_code, "当年得分"] += 0.10 * res.loc[fund_code, "5年得分"]
        #         res.loc[fund_code, "当年得分"] += 0.10 * res.loc[fund_code, "管理以来得分"]
        #
        #         result = pd.concat([result, res], axis=0)
        #
        # file = os.path.join(self.data_path, "基金经理效绩得分.xlsx")
        # excel = WriteExcel(file)
        # num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        # num_format_pd.loc['format', :] = '0.00%'
        #
        # sheet_name = ""
        # worksheet = excel.add_worksheet(sheet_name)
        # excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
        #                    num_format_pd=num_format_pd, color="red", fillna=True)
        # excel.close()

        # 超额收益
        result = pd.DataFrame()
        for i in range(0, len(data)):

            fund_code = data.index[i]
            index_code = data.loc[fund_code, "基准代码"]
            rank_pool = data.loc[fund_code, "考核分类"]
            mg_date = data.loc[fund_code, "现任经理管理开始日"]
            fund_name = data.loc[fund_code, "名称"]
            fund_type = data.loc[fund_code, "基金类型"]

            if (mg_date <= before_1y) and (fund_type == "行业基金"):
                res = self.fund_excess_score(fund_code, fund_name, end_date, rank_pool, mg_date, fund_type, index_code)
                if mg_date >= before_5y:
                    res.loc[fund_code, "5年超额收益"] = res.loc[fund_code, "管理以来超额收益"]
                    res.loc[fund_code, "5年超额排名"] = res.loc[fund_code, "管理以来超额排名"]
                    res.loc[fund_code, "5年超额排名百分比"] = res.loc[fund_code, "管理以来超额排名百分比"]
                    res.loc[fund_code, "5年超额得分"] = res.loc[fund_code, "管理以来超额得分"]
                if mg_date >= before_3y:
                    res.loc[fund_code, "3年超额收益"] = res.loc[fund_code, "管理以来超额收益"]
                    res.loc[fund_code, "3年超额排名"] = res.loc[fund_code, "管理以来超额排名"]
                    res.loc[fund_code, "3年超额排名百分比"] = res.loc[fund_code, "管理以来超额排名百分比"]
                    res.loc[fund_code, "3年超额得分"] = res.loc[fund_code, "管理以来超额得分"]
                result = pd.concat([result, res], axis=0)

        file = os.path.join(self.data_path, "基金经理效绩超额得分.xlsx")
        excel = WriteExcel(file)
        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'

        sheet_name = ""
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)
        excel.close()

if __name__ == '__main__':

    self = MfcManagerScore()
    self.fund_score_all()
