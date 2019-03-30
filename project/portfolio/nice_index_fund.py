import os
import numpy as np
import pandas as pd
from datetime import datetime

from WindPy import w
w.start()

from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.barra import Barra
from quant.source.backtest import BackTest
from quant.source.wind_portfolio import WindPortUpLoad
from quant.utility.write_excel import WriteExcel


class NiceIndexFund(Data):

    """
    优选指数及指数增强基金（分为沪深300、中证500）

    1、雪球组合
    2、每月中更新一次打分，每半年调整持仓
    3、基金池为和300、500跟踪误差不大的基金，一些普通股票型基金也可以选入
    4、从最近1年跟踪误差、超额收益、信息比率、上个半年报的持仓超额暴露等4个方面打分
    5、最好的5个基金等权持有，每个基金公司只能有一个基金入选

    5、还未上传到wind
    6、之前还有一种想法，就是约束整个组合风格因子和中证500指数接近的情况下，最大化组合IR

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'fund_data\nice_index_fund'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.data_min_length = 200  # 最短有效数据长度
        self.data_length = 250

    def update_data(self):

        """ 更新需要的数据 """

        # 更新开始和结束时间
        end_date = Date().change_to_str(datetime.today())

        # 基金基本情况和股票基本情况
        Fund().load_findb_fund_info()
        Fund().load_findb_sec_info()
        Fund().load_wind_fund_info()

        # 基金净值数据 和指数价格额数据
        beg_date = Date().get_trade_date_offset(end_date, -30)
        Fund().load_fund_factor_all(beg_date, end_date)
        Index().load_index_factor_all(beg_date, end_date)

        # 计算基金和指数暴露
        Barra().load_barra_data()
        beg_date = Date().get_trade_date_offset(end_date, -30)
        Index().cal_index_exposure("000300.SH", beg_date=beg_date, end_date=end_date)
        Index().cal_index_exposure("000905.SH", beg_date=beg_date, end_date=end_date)

    def filter_fund_pool(self, index_code, index_name, end_date, track_error_up):

        """ 得到沪深300 、中证500基金池 """

        # 参数
        # end_date = "20181231"
        # index_name = '沪深300'
        # index_code = '000300.SH'
        # track_error_up = 0.03
        beg_date = Date().get_trade_date_offset(end_date, -250)

        # 读取数据
        fund_nav = Fund().get_fund_factor("Repair_Nav")
        index_close = Index().get_index_factor(index_code, attr=['CLOSE'])
        index_close.columns = [index_code]
        result = pd.DataFrame([], index=fund_nav.columns, columns=['跟踪误差', '数据长度'])

        # 计算最近1年跟踪误差数据
        fund_nav = fund_nav.loc[index_close.index, :]
        fund_pct = fund_nav.pct_change()
        index_pct = index_close.pct_change()
        index_pct = index_pct[index_code]
        fund_excess_pct = fund_pct.sub(index_pct, axis='index')
        fund_excess_pct_period = fund_excess_pct.loc[beg_date:end_date, :]
        result.loc[:, "数据长度"] = fund_excess_pct_period.count()
        result.loc[:, "跟踪误差"] = fund_excess_pct_period.std() * np.sqrt(250)

        # 筛选
        result = result.dropna()
        result = result[result['数据长度'] > self.data_min_length]
        result = result[result['跟踪误差'] < track_error_up]

        # concat fund basic info
        data_pd = Fund().get_wind_fund_info()
        data_pd = data_pd[['BenchMark', 'Name', 'FullName', 'SetupDate', 'InvestType']]
        data_pd.columns = ['基金基准', '基金简称', '基金全称', '上市日期', '基金类型']
        data = pd.concat([data_pd, result], axis=1)
        data = data.dropna()
        data = data[data["基金基准"].map(lambda x: index_name in x)]
        data = data[data["上市日期"] < beg_date]
        data = data[data["基金全称"].map(lambda x: "交易型开放式指数" not in x)]
        data = data[data["基金全称"].map(lambda x: "联接" not in x)]
        data['A类基金'] = data['基金简称'].map(Fund().if_a_fund)
        data = data[data['A类基金'] == 'A类基金']

        # 输出结果
        out_path = os.path.join(self.data_path, "filter_fund_pool")
        file_name = os.path.join(out_path, '基金最终筛选池_' + index_name + '.xlsx')

        sheet_name = "基金筛选池"
        num_format_pd = pd.DataFrame([], columns=data.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        num_format_pd.ix['format', '跟踪误差'] = '0.00%'
        num_format_pd.ix['format', '数据长度'] = '0'

        excel = WriteExcel(file_name)
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(data, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)

    def calculate_fund_factor(self, index_code, index_name, end_date):

        """ 计算基金最近一段时间内 跟踪误差、超额收益、信息比率 """

        # 参数
        # index_code = '000905.SH'
        # index_name = '中证500'
        # end_date = '20151231'
        beg_date = Date().get_trade_date_offset(end_date, -self.data_length)

        # 读取数据 基金池 基金净值数据 指数收盘价数据
        file = os.path.join(self.data_path, 'filter_fund_pool', '基金最终筛选池_' + index_name + '.xlsx')
        fund_code = pd.read_excel(file, index_col=[1], encoding='gbk')
        fund_code['上市日期'] = fund_code['上市日期'].map(str)

        fund_nav = Fund().get_fund_factor("Repair_Nav")
        index_close = Index().get_index_factor(index_code, attr=['CLOSE'])
        index_close.columns = [index_code]

        # 筛选新基金 并下载基金规模
        fund_code = fund_code.loc[:, ['上市日期', '基金全称', '基金简称']]
        fund_code = fund_code[fund_code['上市日期'] < beg_date]

        fund_code_str = ','.join(fund_code.index)
        fund_asset = w.wss(fund_code_str, "netasset_total", "unit=1;tradeDate=" + str(end_date))
        fund_asset = pd.DataFrame(fund_asset.Data, index=['基金规模'], columns=fund_asset.Codes).T
        fund_asset['基金规模'] /= 100000000.0
        fund_asset['基金规模'] = fund_asset['基金规模'].round(2)
        fund_asset = fund_asset[fund_asset['基金规模'] > 0.45]
        fund_info = pd.concat([fund_code, fund_asset], axis=1)
        fund_info = fund_info.dropna()

        # 计算最近1年 各项指标
        result = pd.DataFrame([], index=fund_code.index, columns=['跟踪误差'])
        fund_nav = fund_nav.ix[index_close.index, fund_code.index]
        fund_pct = fund_nav.pct_change()
        index_pct = index_close.pct_change()
        index_pct = index_pct[index_code]
        fund_excess_pct = fund_pct.sub(index_pct, axis='index')
        fund_excess_pct_period = fund_excess_pct.loc[beg_date:end_date, :]
        fund_nav_period = fund_nav.loc[beg_date:end_date, :]
        index_close_period = index_close.loc[beg_date:end_date, :]
        result.ix[:, "数据长度"] = fund_excess_pct_period.count()
        result.ix[:, "跟踪误差"] = fund_excess_pct_period.std() * np.sqrt(250)

        fund_return_log = (fund_nav_period.pct_change() + 1.0).applymap(np.log).cumsum().ix[-1, :]
        fund_return = fund_return_log.map(np.exp) - 1
        last_date_close = index_close_period.iloc[len(fund_nav_period) - 1, :]
        first_date_close = index_close_period.iloc[0, :]
        result.ix[:, "基金涨跌"] = fund_return
        result.ix[:, "指数涨跌"] = (last_date_close / first_date_close - 1.0).values[0]
        result.ix[:, "超额收益"] = result.ix[:, "基金涨跌"] - result.ix[:, "指数涨跌"]
        result.ix[:, "信息比率"] = result.ix[:, "超额收益"] / result.ix[:, "跟踪误差"]

        result = result[result['数据长度'] > self.data_min_length]
        result = pd.concat([fund_info, result], axis=1)
        result = result.sort_values(by=['信息比率'], ascending=False)
        result = result.dropna()
        result = result.fillna("")

        # 写到EXCEL表
        out_path = os.path.join(self.data_path, "cal_fund_factor", index_name)
        file_name = os.path.join(out_path, '基金指标_' + index_name + '_' + end_date + '.xlsx')

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'
        num_format_pd.ix['format', '数据长度'] = '0'
        num_format_pd.ix['format', '信息比率'] = '0.00'
        num_format_pd.ix['format', '基金规模'] = '0.00'
        num_format_pd.ix['format', '信息比率'] = '0.00'

        sheet_name = "基金指标"
        excel = WriteExcel(file_name)
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=0,
                           num_format_pd=num_format_pd, color="red", fillna=True)

    def fund_index_exposure(self, index_code, index_name, end_date, halfyear_date, recal_exposure=False):

        """ 计算和得到 上个半年报或者年报指数和基金的Barra暴露 """

        # index_name = '沪深300'
        # index_code = "000300.SH"

        file = os.path.join(self.data_path, 'filter_fund_pool', '基金最终筛选池_' + index_name + '.xlsx')
        fund_code = pd.read_excel(file, index_col=[1], encoding='gbk')

        halfyear_trade_date = Date().get_normal_date_month_end_day(halfyear_date)
        index_exposure = Index().get_index_exposure_date(index_code, halfyear_trade_date)
        exposure_fund = pd.DataFrame()

        for i_fund in range(0, len(fund_code.index)):

            fund = fund_code.index[i_fund]
            beg_date = Date().get_trade_date_offset(end_date, -260)
            if recal_exposure:
                Fund().cal_fund_holder_exposure_halfyear(fund_code=fund, beg_date=beg_date, end_date=end_date)
            exposure_add = Fund().get_fund_holder_exposure_halfyear(fund, type_list=['STYLE'])
            try:
                exposure_add = pd.DataFrame(exposure_add.loc[halfyear_date, :])
                exposure_add.columns = [fund]
            except Exception as e:
                print(e)
                exposure_add = pd.DataFrame([], columns=[fund])

            exposure_fund = pd.concat([exposure_fund, exposure_add], axis=1)

        exposure_fund = exposure_fund.T
        exposure = pd.concat([exposure_fund, index_exposure], axis=0)
        exposure = exposure.dropna()

        file = "BARRA风格暴露_" + index_name + "_" + halfyear_date + ".xlsx"
        file_name = os.path.join(self.data_path, "exposure", index_name, file)
        sheet_name = "BARRA风格暴露"

        num_format_pd = pd.DataFrame([], columns=exposure.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'

        excel = WriteExcel(file_name)
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(exposure, worksheet, begin_row_number=0, begin_col_number=0,
                           num_format_pd=num_format_pd, color="red", fillna=True)

    def score_quarter(self, x, val_25, val_75):

        """ 前1/4满分 后1/4零分 中间线性变化 0-5"""

        if x > val_75:
            r = 5
        elif x < val_25:
            r = 0
        else:
            r = 5 * (x - val_25) / (val_75 - val_25)
        return r

    def score_quarter_reverse(self, x, val_25, val_75):

        """ 前1/4满分 后1/4零分 中间线性变化 0-5"""

        if x > val_75:
            r = 0
        elif x < val_25:
            r = 5
        else:
            r = 5 - (5 * (x - val_25) / (val_75 - val_25))
        return r

    def score_ex(self, x):

        """ 暴露打分 0-1"""

        if x < 0.1:
            return 1
        elif x < 0.2:
            return 0.75
        elif x < 0.4:
            return 0.5
        elif x < 0.6:
            return 0.25
        else:
            return 0

    def fund_score_date(self, index_code, index_name, end_date, halfyear_normal_date, adjust=False):

        """ 从上述4个方面打分 """

        # 读取 基金指标
        print("Score %s %s %s" % (index_name, end_date, halfyear_normal_date))
        sub_path = os.path.join(self.data_path, 'cal_fund_factor', index_name)
        filename = os.path.join(sub_path, '基金指标_' + index_name + '_' + end_date + '.xlsx')
        fund_factor = pd.read_excel(filename, index_col=[0], encoding='gbk')

        # 读取 风格暴露
        sub_path = os.path.join(self.data_path, 'exposure', index_name)
        filename = os.path.join(sub_path, 'BARRA风格暴露_' + index_name + '_' + halfyear_normal_date + '.xlsx')
        exposure = pd.read_excel(filename, index_col=[0], encoding='gbk')
        exposure = exposure.dropna()

        exposure_diff = exposure - exposure.ix[index_code, :]
        exposure = exposure_diff.abs()
        exp_col = ['贝塔', '市净率', '市盈率', '成长', '杠杆', '流动性', '动量', '残差波动率', '市值', '非线性市值']
        exposure.columns = exp_col
        exposure_diff.columns = exp_col
        exposure_diff = exposure_diff.round(3)
        exposure_diff = exposure_diff.drop(index_code)

        fund_code_list = list(set(fund_factor.index) & set(exposure_diff.index))
        fund_code_list.sort()
        fund_factor = fund_factor.loc[fund_code_list, :]
        exposure_diff = exposure_diff.loc[fund_code_list, :]

        # 计算跟踪误差得分
        result = pd.DataFrame([], index=fund_factor.index)
        result.loc[:, '基金全称'] = fund_factor.loc[:, '基金全称']

        if index_name == '中证500':
            val_25 = max(0.03, fund_factor.loc[:, '跟踪误差'].quantile(0.20))
            val_75 = min(0.08, fund_factor.loc[:, '跟踪误差'].quantile(0.80))
        else:
            val_25 = max(0.02, fund_factor.loc[:, '跟踪误差'].quantile(0.20))
            val_75 = min(0.05, fund_factor.loc[:, '跟踪误差'].quantile(0.80))

        result.loc[:, '跟踪误差'] = fund_factor.loc[:, '跟踪误差']
        if adjust and "162216.OF" in result.index:
            result.loc["162216.OF", '跟踪误差'] -= 0.0025

        result.loc[:, '跟踪误差得分'] = fund_factor.loc[:, '跟踪误差'].map(lambda x:
                                                                 self.score_quarter_reverse(x, val_25, val_75)).round(2)

        # 计算超额收益得分
        if index_name == '中证500':
            val_25 = max(0.00, fund_factor.loc[:, '超额收益'].quantile(0.20))
            val_75 = min(0.15, fund_factor.loc[:, '超额收益'].quantile(0.80))

        else:
            val_25 = max(0.00, fund_factor.loc[:, '超额收益'].quantile(0.20))
            val_75 = min(0.10, fund_factor.loc[:, '超额收益'].quantile(0.80))

        result.loc[:, '超额收益'] = fund_factor.loc[:, '超额收益']
        if adjust and "162216.OF" in result.index:
            result.loc["162216.OF", '跟踪误差'] += 0.0025
        result.loc[:, '超额收益得分'] = fund_factor.loc[:, '超额收益'].map(lambda x:
                                                                 self.score_quarter(x, val_25, val_75)).round(2)

        # 计算信息比率得分
        val_25 = fund_factor.loc[:, '信息比率'].quantile(0.20)
        val_75 = fund_factor.loc[:, '信息比率'].quantile(0.80)

        result.ix[:, '信息比率'] = fund_factor.loc[:, '信息比率'].round(2)
        result.loc[:, '信息比率得分'] = fund_factor.loc[:, '信息比率'].map(lambda x:
                                                                 self.score_quarter(x, val_25, val_75)).round(2)

        # 计算风格偏露得分（十个风格 每个打1分，10个总共打10分，再乘以0.5）
        result = result.dropna(subset=["基金全称"])
        result.loc[:, '风格暴露得分'] = 0.0
        result = pd.concat([result, exposure_diff], axis=1)

        for i_col in range(len(exposure_diff.columns)):
            col = exposure_diff.columns[i_col]
            result.loc[:, '风格暴露得分'] += result.loc[:, col].map(self.score_ex)

        result.loc[:, '风格暴露得分'] = result.loc[:, '风格暴露得分'] * 0.5
        if adjust and "162216.OF" in result.index:
            result.loc["162216.OF", '风格暴露得分'] = min(5, result.loc["162216.OF", '风格暴露得分'] + 0.5)
        val_25 = result.loc[:, '风格暴露得分'].quantile(0.20)
        val_75 = result.loc[:, '风格暴露得分'].quantile(0.80)

        result.loc[:, '风格暴露得分'] = result.loc[:, '风格暴露得分'].map(lambda x:
                                                              self.score_quarter(x, val_25, val_75)).round(2)

        # 计算总得分（后期调整沪深300、中证500权重不一样，可以给中证500在超额收益上多一点权重）
        result['总得分'] = 0.0

        if index_name == "中证500":
            result['总得分'] += result['跟踪误差得分'] * 0.10
            result['总得分'] += result['超额收益得分'] * 0.40
            result['总得分'] += result['信息比率得分'] * 0.20
            result['总得分'] += result['风格暴露得分'] * 0.30
        else:
            result['总得分'] += result['跟踪误差得分'] * 0.10
            result['总得分'] += result['超额收益得分'] * 0.40
            result['总得分'] += result['信息比率得分'] * 0.20
            result['总得分'] += result['风格暴露得分'] * 0.30

        result = result.sort_values(by=['总得分'], ascending=False)

        col = ["基金全称", '总得分', '跟踪误差', '跟踪误差得分',
               '超额收益', '超额收益得分', '信息比率', '信息比率得分', '风格暴露得分']
        col.extend(exposure_diff[0:10])
        result = result[col]
        result = result.dropna()

        # 写到EXCEL表
        sub_path = os.path.join(self.data_path, 'score_fund', index_name)
        filename = os.path.join(sub_path, '基金得分_' + index_name + '_' + end_date + '.xlsx')

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00'
        num_format_pd.ix['format', ['跟踪误差', '超额收益']] = '0.00%'

        sheet_name = "基金得分"
        excel = WriteExcel(filename)
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=0,
                           num_format_pd=num_format_pd, color="red", fillna=True)

    def generate_wind_file(self, index_name, port_name, end_date):

        """ 生成wind文件 """

        port_path = os.path.join(WindPortUpLoad().path, port_name)
        if not os.path.exists(port_path):
            os.makedirs(port_path)

        sub_path = os.path.join(self.data_path, 'score_fund', index_name)
        filename = os.path.join(sub_path, '基金得分_' + index_name + '_' + end_date + '.xlsx')
        data = pd.read_excel(filename, index_col=[0], encoding='gbk')
        data = data[['基金全称', '总得分']]

        data = data.dropna()
        data = data.iloc[0:min(5, len(data)), :]
        end_date = Date().get_trade_date_offset(end_date, 0)

        data.index.name = 'Code'
        data["Price"] = 0.0
        data["Direction"] = "Long"
        data["CreditTrading"] = "No"
        data['Date'] = end_date
        data['Weight'] = 1.0 / len(data)
        out_file = os.path.join(port_path, port_name + "_" + end_date + '.csv')
        data.to_csv(out_file)

    def cal_all_date(self):

        """ 计算多期的数据 """

        data = Date().get_normal_date_series("20130622", datetime.today(), period="S")
        for i_date in range(0, len(data)):

            end_date = data[i_date]
            halfyear_date = Date().get_last_fund_halfyear_date(end_date)
            print("Cal Factor %s %s" % (end_date, halfyear_date))
            # self.calculate_fund_factor("000300.SH", "沪深300", end_date)
            # self.calculate_fund_factor("000905.SH", "中证500", end_date)
            # self.fund_index_exposure("000300.SH", "沪深300", end_date, halfyear_date, False)
            # self.fund_index_exposure("000905.SH", "中证500", end_date, halfyear_date, False)
            # self.fund_score_date("000300.SH", "沪深300", end_date, halfyear_date)
            # self.fund_score_date("000905.SH", "中证500", end_date, halfyear_date)
            self.generate_wind_file("沪深300", "优选沪深300基金", end_date)
            self.generate_wind_file("中证500", "优选中证500基金", end_date)

    def upload_all_wind_port(self):

        """ 上传wind组合 """
        WindPortUpLoad().upload_weight_period("优选沪深300基金")
        WindPortUpLoad().upload_weight_period("优选中证500基金")

    def backtest(self):

        """ 本地基金组合回测 """

        backtest = BackTest()
        backtest.set_info("优选沪深300基金", "000300.SH")
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return()
        backtest.cal_turnover(annual_number=4)
        backtest.cal_summary()

        backtest = BackTest()
        backtest.set_info("优选中证500基金", "000905.SH")
        backtest.read_weight_at_all_change_date()
        backtest.cal_weight_at_all_daily()
        backtest.cal_port_return()
        backtest.cal_turnover(annual_number=4)
        backtest.cal_summary()


if __name__ == '__main__':

    self = NiceIndexFund()
    end_date = "20190315"
    halfyear_date = "20180630"
    index_name = "沪深300"
    index_code = "000300.SH"
    recal_exposure = False   # 是否重新计算基金暴露
    adjust = True  # 调整中证500数据

    # self.filter_fund_pool("000300.SH", "沪深300", end_date, 0.045)
    # self.filter_fund_pool("000905.SH", "中证500", end_date, 0.07)
    # self.update_data()
    self.calculate_fund_factor("000300.SH", "沪深300", end_date)
    self.calculate_fund_factor("000905.SH", "中证500", end_date)
    self.fund_index_exposure("000300.SH", "沪深300", end_date, halfyear_date, recal_exposure)
    self.fund_index_exposure("000905.SH", "中证500", end_date, halfyear_date, recal_exposure)
    self.fund_score_date("000300.SH", "沪深300", end_date, halfyear_date, adjust)
    self.fund_score_date("000905.SH", "中证500", end_date, halfyear_date, adjust)

    # self.cal_all_date()
    # self.upload_all_wind_port()
    # self.backtest()
