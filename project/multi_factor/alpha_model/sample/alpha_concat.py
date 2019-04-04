import pandas as pd

from quant.data.data import Data
from quant.stock.date import Date
from quant.project.multi_factor.alpha_model.sample.alpha_split import AlphaSplit
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor
from quant.project.multi_factor.alpha_model.sample.alpha_summary import AlphaSummary


class ConcatAlpha(Data):

    """
    Alpha因子简单拆分后
    合成大类因子
    """

    def __init__(self):

        Data.__init__(self)

    def concat_ew_to_major_alpha(self, stock_pool_name, beg_date, end_date, period):

        """ 等权大类因子 剔除ICIR表现不好的因子及因子值变化太快的因子 """

        term = 500
        beg_date = "20040101"
        end_date = "20190101"
        period = "W"

        date_series = Date().get_trade_date_series(beg_date, end_date, "W")

        if stock_pool_name == "hs300":
            min_icir = 1.2
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
                if corr >= min_corr and icir > min_icir and date in alpha.columns:


                    result = result.add(alpha, fill_value=0.0)

    def concat_ew_alpha(self, stock_pool_name):

        """ 等权合成因子 剔除ICIR表现不好的因子及因子值变化太快的因子 """

        factor_list = AlphaFactor().get_all_alpha_factor_file()
        major_factor_list = list(set(factor_list.index))

        for i in range(len(major_factor_list)):

            major_factor = major_factor_list[i]
            factor_select = factor_list[factor_list.index == major_factor]
            factor_name_list = list(factor_select["因子名"].values)
            result = pd.DataFrame()
            AlphaSplit().save_alpha_res_exposure(result, major_factor, stock_pool_name)

    def concat_ew_major_alpha(self, stock_pool_name):

        """ 等权大类因子  """

        major_factor_list = AlphaFactor().get_major_alpha_name()
        result = pd.DataFrame()
        for i in range(len(major_factor_list)):

            major_factor = major_factor_list[i]
            alpha = AlphaSplit().get_alpha_res_exposure(major_factor, stock_pool_name)
            result = result.add(alpha, fill_value=0.0)

        result /= len(major_factor_list)
        AlphaSplit().save_alpha_res_exposure(result, "alpha", stock_pool_name)


if __name__ == "__main__":

    self = ConcatAlpha()
    stock_pool_name = "AllChinaStockFilter"
    # self.concat_ew_alpha(stock_pool_name)
    # self.concat_ew_alpha("hs300")
    # self.concat_ew_alpha("zz500")
    self.concat_ew_major_alpha(stock_pool_name)
    self.concat_ew_major_alpha("hs300")
    self.concat_ew_major_alpha("zz500")