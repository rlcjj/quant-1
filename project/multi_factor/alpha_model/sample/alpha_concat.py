import pandas as pd

from quant.data.data import Data
from quant.stock.date import Date
from quant.project.multi_factor.alpha_model.sample.alpha_split import AlphaSplit
from quant.project.multi_factor.alpha_model.sample.alpha_summary import AlphaSummary
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaConcat(Data):

    """
    Alpha因子简单拆分后
    合成大类因子
    1、首先等权合成大类因子(情绪、估值、质量、成长等等)
    2、再次ICIR合成Alpha
    """

    def __init__(self):

        Data.__init__(self)

    def ew_to_major_alpha(self, factor_name_list, stock_pool_name, beg_date, end_date, period):

        """ 等权合成大类因子 剔除ICIR表现不好的因子及因子值变化太快的因子 """

        term = 500
        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        if stock_pool_name == "hs300":
            min_icir = 1.25
            min_corr = 0.85
        else:
            min_icir = 1.5
            min_corr = 0.85

        result = pd.DataFrame()

        for i_date in range(len(date_series)):

            date = date_series[i_date]

            ed_date = Date().get_trade_date_offset(date, -1)
            bg_date = Date().get_trade_date_offset(date, -term-1)
            res_date = pd.DataFrame()

            for i_factor in range(len(factor_name_list)):

                name = factor_name_list[i_factor]
                icir = AlphaSummary().get_factor_icir(bg_date, ed_date, name, period, stock_pool_name)
                corr = AlphaSplit().get_alpha_res_corr(name, bg_date, ed_date, period, stock_pool_name)
                alpha = AlphaSplit().get_alpha_res_exposure(name, stock_pool_name)
                print(date, name, icir, corr)

                if corr >= min_corr and icir > min_icir and date in alpha.columns:

                    alpha_date = pd.DataFrame(alpha[date])
                    alpha_date.columns = [name]
                    res_date = pd.concat([res_date, alpha_date], axis=1)

            res_date["Mean"] = res_date.mean(axis=1)

        result = pd.concat([result, res_date], axis=1)
        return result

    def ew_to_all_major_alpha(self, stock_pool_name, beg_date, end_date, period):

        """ 等权合成因子 剔除ICIR表现不好的因子及因子值变化太快的因子 """

        factor_list = AlphaFactor().get_all_alpha_factor_file()
        major_factor_list = list(set(factor_list.index))

        for i in range(len(major_factor_list)):

            major_factor = major_factor_list[i]
            factor_select = factor_list[factor_list.index == major_factor]
            factor_name_list = list(factor_select["因子名"].values)
            result = self.ew_to_major_alpha(factor_name_list, stock_pool_name, beg_date, end_date, period)
            AlphaSplit().save_alpha_res_exposure(result, major_factor, stock_pool_name)

    def ew_to_alpha(self, stock_pool_name):

        """ 等权大类因子  """

        major_factor_list = AlphaFactor().get_major_alpha_name()
        result = pd.Panel()

        for i in range(len(major_factor_list)):

            major_factor = major_factor_list[i]
            alpha = AlphaSplit().get_alpha_res_exposure(major_factor, stock_pool_name)
            result = pd.concat([result, alpha])

        result.items = major_factor_list
        result_mean = result.mean(axis=0)
        AlphaSplit().save_alpha_res_exposure(result_mean, "alpha", stock_pool_name)


if __name__ == "__main__":

    self = AlphaConcat()
    stock_pool_name = "AllChinaStockFilter"
    beg_date, end_date, period = "20050101", "20190404", "W"

    self.ew_to_all_major_alpha(stock_pool_name, beg_date, end_date, period)
    self.ew_to_all_major_alpha("hs300", beg_date, end_date, period)
    self.ew_to_all_major_alpha("zz500", beg_date, end_date, period)

    self.ew_to_alpha(stock_pool_name)
    self.ew_to_alpha("hs300")
    self.ew_to_alpha("zz500")
