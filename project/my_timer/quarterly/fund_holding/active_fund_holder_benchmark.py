import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date


class ActiveFundHolderBenchMark(Data):

    """ 将主动股票基金的季报重仓持股以不同形式相加 得到作为基准或者风险因子等"""

    def __init__(self):

        Data.__init__(self)
        self.data_path = os.path.join(self.primary_data_path, r"fund_data\fund_holding_data\fund_holding_benchmark")

        # 全部股票权重下限和前10大重仓权重下限
        self.sum_weight_low = 60
        self.top10_weight_low = 30

    def get_data(self, report_date):

        """ 得到所有需要的数据（股票持仓、基金池、基金规模、基金净值等等）"""

        data = Fund().get_fund_holding_stock_date(report_date)
        hold_data = data[['FundCode', 'Weight', 'StockCode']]

        pool = Fund().get_fund_pool_code(report_date, "基金持仓基准基金池")
        fund_code = list(set(pool))
        fund_code.sort()

        return hold_data, fund_code

    def cal_equal_allstock_halfyear_date(self, report_date):

        """ 等权加总所有基金，半年报全部持仓股票 """

        # get_data
        report_date = Date().change_to_str(report_date)
        hold_data, fund_code = self.get_data(report_date)

        # 取全部持仓股票权重和大于60的基金
        data_fund_all = pd.DataFrame([])

        for i_fund in range(len(fund_code)):

            fund = fund_code[i_fund]
            data_fund = hold_data[hold_data['FundCode'] == fund]
            data_fund = data_fund.dropna(subset=['Weight'])
            data_fund = data_fund.sort_values(by=['Weight'], ascending=False)

            data_fund_add = data_fund.copy()
            all_weight = data_fund['Weight'].sum()
            if all_weight < self.sum_weight_low:
                data_fund_add = pd.DataFrame([], columns=data_fund.columns)
            data_fund_all = pd.concat([data_fund_all, data_fund_add], axis=0)


if __name__ == "__main__":

    self = ActiveFundHolderBenchMark()



