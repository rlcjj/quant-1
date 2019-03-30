from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.source.backtest import BackTest
from quant.project.fund.lasso_ols.fund_ols_stock_weight import FundOLSStockWeight
from quant.source.wind_portfolio import WindPortUpLoad

import pandas as pd
import os


class WindFile(object):

    def __init__(self):

        self.wind_port_path = WindPortUpLoad().path

    def ols_weight_fund_pool(self, pool_name, pool_date, port_name, beg_date, end_date, period='M', stock_weight=None):

        """
        将一个基金池内的所有OLS回归等权作为结果拆分成为可以上传的wind组合文件
        包含仓位信息
        """

        # 基金lasso预测结果等权相加

        fund_pool = Fund().get_fund_pool_code(pool_date, pool_name)
        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        for i_date in range(len(date_series)):

            weight_date = pd.DataFrame([])

            for i_fund in range(len(fund_pool)):

                date = date_series[i_date]
                fund_code = fund_pool[i_fund]
                print(date, fund_code)
                data = FundOLSStockWeight().get_ols_stock_weight_date(fund_code, date)
                data = data.dropna()
                weight_date = pd.concat([weight_date, data], axis=1)

            if len(weight_date) > 0:

                result = pd.DataFrame(weight_date.sum(axis=1) / len(weight_date.columns))
                result.columns = ['Weight']
                result = result[result['Weight'] > 0.0]
                result = result.sort_values(by=["Weight"], ascending=False)
                if stock_weight is not None:
                    result['Weight'] = (result['Weight'] / result['Weight'].sum()) * stock_weight

                stock_sum = result['Weight'].sum()
                result.loc['Cash', 'Weight'] = 1 - stock_sum

                result['Code'] = result.index
                result['Date'] = date
                result['Price'] = "0.0"
                result['Direction'] = "Long"
                result['CreditTrading'] = 'No'

                sub_path = os.path.join(self.wind_port_path, port_name)
                if not os.path.exists(sub_path):
                    os.makedirs(sub_path)

                file = os.path.join(self.wind_port_path, port_name, port_name + '_' + date + '.csv')
                result.to_csv(file)

    def ols_weight_fund(self, fund_code, port_name, beg_date, end_date, period='M', stock_weight=None):

        """
        将一个基金的所有OLS回归结果拆分成为可以上传的wind组合文件
        """

        # fund_code = "000619.OF"
        # port_name = "东方红产业升级"
        # beg_date, end_date, period = "20070101", "20181231", 'M'

        date_series = Date().get_trade_date_series(beg_date, end_date, period)

        # 将文件转化为单个持仓文件 供WIND上传

        for i_date in range(len(date_series)):

            date = date_series[i_date]
            data = FundOLSStockWeight().get_ols_stock_weight_date(fund_code, date)
            data = data.dropna()

            if len(data) > 0:

                data.columns = ['Weight']
                data = data[data['Weight'] > 0.0]
                data = data.sort_values(by=["Weight"], ascending=False)

                if stock_weight is not None:
                    data['Weight'] = (data['Weight'] / data['Weight'].sum()) * stock_weight

                stock_sum = data['Weight'].sum()
                data.loc['Cash', 'Weight'] = 1 - stock_sum

                data['Code'] = data.index
                data['Date'] = date
                data['Price'] = "0.0"
                data['Direction'] = "Long"
                data['CreditTrading'] = 'No'

                sub_path = os.path.join(self.wind_port_path, port_name)
                if not os.path.exists(sub_path):
                    os.makedirs(sub_path)
                file = os.path.join(self.wind_port_path, port_name, port_name + '_' + date + '.csv')
                data.to_csv(file)

    def generate_pool_upload(self, pool_name, pool_date, port_name, beg_date, end_date, benchmark_code,
                             period='M', stock_ratio=None):

        self.ols_weight_fund_pool(pool_name, pool_date, port_name, beg_date, end_date, period, stock_ratio)

        backtest = BackTest()
        backtest.set_info(port_name, benchmark_code)
        backtest.backtest()

        # WindPortUpLoad().upload_weight_period(port_name)

    def generate_fund_upload(self, fund_code, port_name, beg_date, end_date, benchmark_code,
                             period='M', stock_ratio=None):

        self.ols_weight_fund(fund_code, port_name, beg_date, end_date, period, stock_ratio)

        backtest = BackTest()
        backtest.set_info(port_name, benchmark_code)
        backtest.backtest()

        # WindPortUpLoad().upload_weight_period(port_name)


if __name__ == '__main__':

    """ 多个基金 """

    pool_date = '20180630'
    beg_date, end_date, period = "20070101", "20181231", 'M'
    pool_name = "东方红基金"
    port_name = "东方红精选"
    benchmark_code = "885000.WI"

    WindFile().generate_pool_upload(pool_name, pool_date, port_name, beg_date, end_date,
                                    benchmark_code, period)

    port_name = "东方红精选95"
    WindFile().generate_pool_upload(pool_name, pool_date, port_name, beg_date, end_date,
                                    benchmark_code, period, stock_ratio=0.95)

    """ 单个基金 """

    fund_code = "000619.OF"
    port_name = "东方红产业升级"
    beg_date, end_date, period = "20070101", "20181231", 'M'

    WindFile().generate_fund_upload(fund_code, port_name, beg_date, end_date,
                                    benchmark_code, period)
    port_name = "东方红产业升级95"
    WindFile().generate_fund_upload(fund_code, port_name, beg_date, end_date,
                                    benchmark_code, period, stock_ratio=0.95)