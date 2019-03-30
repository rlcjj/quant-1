from quant.data.data import Data
from quant.fund.fund_holder import FundHolderData

import os
import pandas as pd


class FundHolderFactor(Data):

    """
    根据基金的持仓计算基金因子 例如基金换手率 前十大重仓股持股比率等等

    """

    def __init__(self):

        # 和FundFactor的路径一样 读取也利用FundFactor

        Data.__init__(self)
        self.sub_data_path = r'fund_data\fund_factor_data'
        self.data_path_holder_factor = os.path.join(self.primary_data_path, self.sub_data_path)

    def cal_fund_turnover(self):

        """ 利用年报和半年报信息来计算基金换手率 """

        data = FundHolderData().get_fund_holding_stock_all()

        fund_list = list(set(data['FundCode'].values))
        fund_list.sort()

        for i_fund in range(len(fund_list)):

            fund = fund_list[i_fund]
            print(" Calculating Fund %s TurnOver " % fund)
            try:
                data = FundHolderData().get_fund_holding_stock_all()
                data = data.T
                data = data.fillna(0.0)
                data_diff_abs = data.diff().abs()
                turnover_fund = pd.DataFrame(data_diff_abs.sum(axis=1))
                turnover_fund.columns = [fund]
            except Exception as e:
                turnover = pd.DataFrame([], columns=[fund])

            if i_fund == 0:
                turnover = turnover_fund
            else:
                turnover = pd.concat([turnover, turnover_fund], axis=1)

        turnover = turnover.T
        file = os.path.join(self.data_path_holder_factor, "fund_turnover", "FundTurnOver.csv")
        turnover = turnover.to_csv(file)
        return turnover

    def cal_fund_top10_weight(self):

        """ 利用季报信息来计算基金前十大重仓股权重之和 """

        file = os.path.join(self.data_path_holder_factor, "fund_holding_data", "Fund_Stock_Holding.csv")
        data = pd.read_csv(file, usecols=[0, 1, 2, 6], encoding='gbk')

        fund_list = list(set(data['FundCode'].values))
        fund_list.sort()

        for i_fund in range(len(fund_list)):

            fund = fund_list[i_fund]
            print(" Calculating Fund %s Top10Stock SumWeight " % fund)
            try:
                data = self.get_fund_holding_quarter(fund)
                weight_sum_fund = pd.DataFrame(data.sum())
                weight_sum_fund.columns = [fund]
            except Exception as e:
                weight_sum_fund = pd.DataFrame([], columns=[fund])
            if i_fund == 0:
                weight_sum = weight_sum_fund
            else:
                weight_sum = pd.concat([weight_sum, weight_sum_fund], axis=1)

        weight_sum = weight_sum.T
        file = os.path.join(self.data_path_holder, "fund_top10_weight", "FundTop10Weight.csv")
        weight_sum = weight_sum.to_csv(file)
        return weight_sum


if __name__ == '__main__':

    self = FundHolderFactor()

