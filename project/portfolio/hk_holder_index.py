import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad


class HKHolderIndex(Data):

    """
    【北上资金持股指数】编制方案 参考中证红利指数的编制方式
    权重为北上资金持股市值，wind里有股数，自己可以乘以股价获得市值。
    由于这个持仓股票数特别多，取累计权重前90%或300只股票的两者较大者为持仓，剩余剔除，等比例放大到100%，月度调仓
    另请大致测算下月、季、半年调仓对组合影响大不大。数据我记得从2017年3月开始的
    """

    def __init__(self, port_name):

        """ 数据存储位置 """
        Data.__init__(self)
        self.port_name = port_name
        self.wind_port_path = WindPortUpLoad().path
        self.data_weight_path = Index().data_path_weight
        self.data_factor_path = Index().data_data_factor
        self.beg_date = "20170301"

    def update_data(self):

        """ 下载数据"""

        Stock().load_h5_primary_factor()

    def cal_weight_date(self, date):

        """ 得到某一天的权重"""

        share_hk = Stock().read_factor_h5("HK2CHoldShare") * 100  # 原始数据为百股单位
        price_unadjust = Stock().read_factor_h5("Price_Unadjust")

        mv_hk = share_hk.mul(price_unadjust)
        mv_hk = mv_hk.T.dropna(how="all").T

        try:
            mv_date = pd.DataFrame(mv_hk[date])
        except Exception as e:
            date = Date().get_trade_date_offset(date, -1)
            mv_date = pd.DataFrame(mv_hk[date])

        mv_date = mv_date.dropna()
        mv_date = mv_date.sort_values(by=[date], ascending=False)
        mv_date.columns = ['MarketValue']
        mv_date['Weight'] = mv_date['MarketValue'] / mv_date['MarketValue'].sum()
        mv_date['WeightSum'] = mv_date['Weight'].cumsum()
        mv_date_filter = mv_date[mv_date['WeightSum'] <= 0.90]
        mv_date_filter = mv_date.iloc[0:max(len(mv_date_filter), 300), :]

        mv_date_filter['Weight'] = mv_date_filter['MarketValue'] / mv_date_filter['MarketValue'].sum()
        mv_date_filter['WeightSum'] = mv_date_filter['Weight'].cumsum()

        return mv_date_filter

    def cal_all_wind_file(self, period="Q"):

        """ 计算 所有季报日 普通股票型基金 基金平均持仓 还要考虑股票仓位 并生成wind文件"""

        date_series = Date().get_trade_date_series(self.beg_date, datetime.today(), period)
        if period == "S":
            date_series = list(map(lambda x: Date().get_trade_date_offset(x, -60), date_series))

        for i_date in range(len(date_series)-1):

            date = date_series[i_date]
            print(date)
            stock_data_weight = self.cal_weight_date(date)
            print(len(stock_data_weight))
            publish_date = Date().get_trade_date_offset(date, 1)
            stock_data_weight['Name'] = stock_data_weight.index.map(lambda x: Stock().get_stock_name_date(x, date))
            stock_data_weight.index.name = "Code"
            stock_data_weight["CreditTrading"] = "No"
            stock_data_weight["Date"] = publish_date
            stock_data_weight["Price"] = 0.0
            stock_data_weight["Direction"] = "Long"

            sub_path = os.path.join(self.wind_port_path, self.port_name)
            if not os.path.exists(sub_path):
                os.makedirs(sub_path)

            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, publish_date))
            stock_data_weight.to_csv(file)

    def cal_some_index(self, period):

        """计算一些指标 例如每次调入调出数量 重仓股权重行业分布等等 """
        date_series = Date().get_trade_date_series(self.beg_date, datetime.today(), period)
        if period == "S":
            date_series = list(map(lambda x: Date().get_trade_date_offset(x, -60), date_series))

        result = pd.DataFrame([])
        for i_date in range(1, len(date_series)-1):

            date = date_series[i_date]
            publish_date = Date().get_trade_date_offset(date, 1)
            last_date = date_series[i_date - 1]
            print(date, last_date)
            last_publish_date = Date().get_trade_date_offset(last_date, 1)

            sub_path = os.path.join(self.wind_port_path, self.port_name)
            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, publish_date))
            weight = pd.read_csv(file, index_col=[0], encoding='gbk')

            file = os.path.join(Stock().data_path_static, 'wind行业.xlsx')
            wind_industry = pd.read_excel(file, index_col=[0])
            wind_industry = wind_industry.dropna()
            weight_all = pd.concat([wind_industry, weight], axis=1)
            industry_weight = pd.DataFrame(weight_all.groupby(by=['行业名称']).sum()['Weight']).T
            industry_weight.index = [publish_date]

            result_add = industry_weight

            result_add.loc[publish_date, "WeightSum"] = weight.loc[weight.index[0:10], 'Weight'].sum()

            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, last_publish_date))
            last_weight = pd.read_csv(file, index_col=[0], encoding='gbk')

            diff_stock = list(set(weight.index) - set(last_weight.index))
            result_add.loc[publish_date, "ChangeNumber"] = len(diff_stock)
            result = pd.concat([result, result_add], axis=0)

        result.to_csv(r"C:\Users\doufucheng\OneDrive\Desktop\sum.csv")

    def cal_some_index2(self, period):

        """计算一些指标 样本股总市值占A股总市值的比例 换后率等等 等等 """

        date_series = Date().get_trade_date_series(self.beg_date, datetime.today(), period)
        if period == "S":
            date_series = list(map(lambda x: Date().get_trade_date_offset(x, -60), date_series))

        result = pd.DataFrame([])

        for i_date in range(1, len(date_series)-2):

            date = date_series[i_date]
            publish_date = Date().get_trade_date_offset(date, 1)
            last_date = date_series[i_date - 1]
            print(date, last_date)
            last_publish_date = Date().get_trade_date_offset(last_date, 1)

            sub_path = os.path.join(self.wind_port_path, self.port_name)
            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, publish_date))
            weight = pd.read_csv(file, index_col=[0], encoding='gbk')

            mv = Stock().read_factor_h5("TotalMarketValue", path=Stock().get_h5_path("my_alpha"))
            mv_date = pd.DataFrame(mv[publish_date])
            mv_date.columns = ['TotalMV']
            total_mv = mv_date['TotalMV'].sum()

            concat_data = pd.concat([weight, mv_date], axis=1)
            concat_data = concat_data.dropna()
            index_mv = concat_data['TotalMV'].sum()
            ratio = index_mv / total_mv
            result.loc[publish_date, "Ratio"] = ratio

            mv = Stock().read_factor_h5("Mkt_freeshares")
            mv_date = pd.DataFrame(mv[publish_date])
            mv_date.columns = ['FreeMV']
            total_mv = mv_date['FreeMV'].sum()

            concat_data = pd.concat([weight, mv_date], axis=1)
            concat_data = concat_data.dropna()
            index_mv = concat_data['FreeMV'].sum()
            ratio = index_mv / total_mv
            result.loc[publish_date, "FreeRatio"] = ratio

            file = os.path.join(sub_path, '%s_%s.csv' % (self.port_name, last_publish_date))
            last_weight = pd.read_csv(file, index_col=[0], encoding='gbk')
            diff_stock = pd.DataFrame(weight['Weight'] - last_weight['Weight'])

            result.loc[publish_date, "TO"] = diff_stock['Weight'].abs().sum()

        result.to_csv(r"C:\Users\doufucheng\OneDrive\Desktop\sum2.csv")

    def backtest(self, annual_number=4):

        """ 计算 回测结果 """

        port = BackTest()
        port.set_info(self.port_name, '000300.SH')
        port.read_weight_at_all_change_date()
        port.cal_weight_at_all_daily()
        port.cal_port_return(beg_date=self.beg_date)
        port.cal_turnover(annual_number=annual_number)
        port.cal_summary(all_beg_date=self.beg_date)

    def cal_weight_data(self):

        """
        将每天权重结果 和 指数每日涨跌幅表现 写入Index数据当中
        """

        port = BackTest()
        port.set_info(self.port_name, '000300.SH')
        port.get_weight_at_all_daily()
        port.get_port_return()
        port_daily = port.port_hold_daily

        # 写入每日收益率
        data = pd.DataFrame(port.port_return['PortReturn'])
        data.columns = ['PCT']
        data["CLOSE"] = (data['PCT'] + 1.0).cumprod() * 1000
        sub_path = self.data_factor_path
        data.to_csv(os.path.join(sub_path, self.port_name + '.csv'))

        # 写入每日权重
        sub_path = os.path.join(self.data_weight_path, self.port_name)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        for i_date in range(len(port_daily.columns)):

            date = port_daily.columns[i_date]
            weight_date = pd.DataFrame(port_daily[date])
            weight_date = weight_date.dropna()
            weight_date.columns = ['WEIGHT']
            weight_date.index.name = 'CODE'
            file = os.path.join(sub_path, '%s.csv' % date)
            print(file)
            weight_date.to_csv(file)

if __name__ == "__main__":

    # self = HKHolderIndex("北上资金持股指数季度")
    # self.cal_all_wind_file(period="Q")
    # self.backtest(annual_number=4)
    # WindPortUpLoad().upload_weight_period("北上资金持股指数季度")

    self = HKHolderIndex("北上资金持股指数月度")
    self.cal_some_index2("M")
    # self.cal_some_index("M")
    # self.cal_all_wind_file(period="M")
    # self.backtest(annual_number=12)
    # self.cal_weight_data()
    # WindPortUpLoad().upload_weight_period("北上资金持股指数月度")

    # self = HKHolderIndex("北上资金持股指数半年")
    # self.cal_all_wind_file(period="S")
    # self.backtest(annual_number=2)
    # WindPortUpLoad().upload_weight_period("北上资金持股指数半年")