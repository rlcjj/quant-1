import os
import pandas as pd

from quant.stock.date import Date
from quant.stock.barra import Barra
from quant.project.multi_factor.risk_model.model.risk_model import RiskModel


class BarraCNE5(RiskModel):

    """
    Barra CNE5模型 特有的一些函数
    和真实的 Barra 模型的进行比较
    """

    def __init__(self):

        RiskModel.__init__(self)
        self.risk_model_name = 'cne5'
        self.model_path = os.path.join(self.data_path, self.risk_model_name)

    def compare_exposure_date(self, date):

        """ 计算某日所有两个 Barra模型因子暴露的相关性 """

        barra_exposure = Barra().get_factor_exposure_date(date, type_list=['STYLE'])
        my_exposure = self.get_factor_exposure(date)

        corr = pd.DataFrame([], index=barra_exposure.columns, columns=[date])
        rank_corr = pd.DataFrame([], index=barra_exposure.columns, columns=[date])
        nan = pd.DataFrame([], index=barra_exposure.columns, columns=[date])

        for i_factor in range(len(barra_exposure.columns)):

            factor = barra_exposure.columns[i_factor]
            data = pd.concat([barra_exposure[factor], my_exposure[factor]], axis=1)
            data = data.dropna(how='all')

            nan_number = data.isnull().sum().iloc[1]
            corr_date = data.corr().iloc[1, 0]
            rank_corr_date = data.corr(method="spearman").iloc[1, 0]

            nan.loc[factor, date] = nan_number
            corr.loc[factor, date] = corr_date
            rank_corr.loc[factor, date] = rank_corr_date
            print(date, factor, nan_number, corr_date, rank_corr_date)

        return nan, corr, rank_corr

    def compare_exposure(self, beg_date, end_date):

        """ 计算所有交易日所有两个Barra模型因子暴露的相关性 """

        date_series = Date().get_trade_date_series(beg_date, end_date, "W")
        nan, corr, rank_corr = pd.DataFrame([]), pd.DataFrame([]), pd.DataFrame([])

        for date in date_series:

            nan_date, corr_date, rank_corr_date = self.compare_exposure_date(date)
            nan = pd.concat([nan, nan_date], axis=1)
            corr = pd.concat([corr, corr_date], axis=1)
            rank_corr = pd.concat([rank_corr, rank_corr_date], axis=1)

        rank_corr = rank_corr.T
        print(rank_corr)
        print(rank_corr.mean())


if __name__ == '__main__':

    self = BarraCNE5()
    self.compare_exposure("20090101", "20180901")
