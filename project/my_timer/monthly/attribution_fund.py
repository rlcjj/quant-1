import os
import numpy as np
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.stock import Stock
from quant.stock.index import Index
from quant.stock.barra import Barra
from quant.mfc.mfc_data import MfcData
from quant.utility.code_format import CodeFormat
from quant.utility.write_excel import WriteExcel
from quant.utility.factor_operate import FactorOperate


class AttributionFund(Data):

    """
    泰达宏利 归因

    文件储存：例如：泰达逆向策略
             -- 资产收益 -- 股票、新股、期货等资产每日收益计算结果
             -- 每日拆分 -- 每日暴露、因子收益、风格收益、基金收益拆分
             -- 阶段归因 -- 不同时间段内归因的结果
    """

    def __init__(self):

        """ 初始化 """

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\attribution_new'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

        self.double_fee_ratio = 0.001 + 0.0008 * 2  # 印花税 + 交易佣金
        self.mg_fee_ratio = (1.2 / 100 + 0.2 / 100) / 250.0  # 管理费
        self.index_code_ratio = 0.95
        self.index_code = ""

        self.fund_code = ""
        self.fund_name = ""
        self.type = ""

        self.beg_date = ""
        self.end_date = ""
        self.beg_date_pre = ""
        self.period_name = ""

        self.close_unadjust = None
        self.adjust_factor = None
        self.data = None
        self.ipo_days = 40
        self.ipo_data = Stock().get_ipo_date()
        self.ipo_data.columns = ['IpoDate', 'DeListDate']
        self.ipo_data = pd.DataFrame(self.ipo_data['IpoDate'])

    def get_info(self, index_code_ratio, index_code, fund_code, fund_name,
                 type, beg_date, end_date, period_name, mg_fee_ratio):

        """ 需要的参数 """

        self.index_code_ratio = index_code_ratio
        self.index_code = index_code

        self.fund_code = fund_code
        self.fund_name = fund_name
        self.type = type

        date_sereis = Date().get_trade_date_series(beg_date, end_date)
        self.beg_date = date_sereis[0]
        self.end_date = date_sereis[-1]
        self.beg_date_pre = Date().get_trade_date_offset(beg_date, -1)
        print(self.beg_date, self.end_date, self.beg_date_pre)
        self.period_name = period_name

        self.mg_fee_ratio = mg_fee_ratio / 250
        self.close_unadjust = Stock().read_factor_h5("Price_Unadjust")
        self.adjust_factor = Stock().read_factor_h5("AdjustFactor")

    def get_fund_pct(self):

        """ 产品某一段时间内的涨跌幅，专户公募分开 """

        if self.type == "专户":
            fund_pct = MfcData().get_mfc_private_fund_nav(self.fund_name)
            fund_pct['基金涨跌幅'] = fund_pct['累计复权净值'].pct_change()
            fund_pct = fund_pct[['累计复权净值', '基金涨跌幅']]
            fund_pct = fund_pct.dropna()
            fund_pct = fund_pct.loc[self.beg_date_pre:self.end_date, :]
        else:
            fund_pct = MfcData().get_mfc_public_fund_nav(self.fund_code)
            fund_pct = fund_pct[['NAV_ADJ', 'NAV_ADJ_RETURN1']]
            fund_pct['NAV_ADJ_RETURN1'] = fund_pct['NAV_ADJ'].pct_change()
            fund_pct.columns = ['累计复权净值', '基金涨跌幅']
            fund_pct = fund_pct.dropna()
            fund_pct = fund_pct.loc[self.beg_date_pre:self.end_date, :]

        return fund_pct

    def get_index_pct(self):

        """ 指数某一段时间内的涨跌幅 """

        index_pct = Index().get_index_factor(self.index_code, self.beg_date_pre, self.end_date)
        index_pct['PCT'] = index_pct['CLOSE'].pct_change()
        index_pct.columns = ['指数收盘', '指数涨跌幅']
        index_pct = index_pct.dropna()

        return index_pct

    def get_fund_asset(self):

        """
        得到某只基金资产、指数涨跌幅、基金涨跌幅
        总资产包括 净值、基金份额、单位净值；股票、债券、现金、回购资产；买卖金额；股票债券浮动金额、总盈亏金额
        """

        fund_asset = MfcData().get_fund_asset_period(self.fund_name, self.beg_date_pre, self.end_date)
        fund_pct = self.get_fund_pct()
        index_pct = self.get_index_pct()

        # 数据合并
        data = pd.concat([fund_pct, index_pct, fund_asset], axis=1)
        data = data.dropna(subset=['基金涨跌幅', '指数涨跌幅'])
        print(data.head())

        if len(data) <= 0:
            data = None
        else:
            data['单位净值'] = data['净值'] / data['基金份额']
            data['昨日净值'] = data['净值'].shift(1)
            data['昨日基金份额'] = data['基金份额'].shift(1)
            data['昨日单位净值'] = data['单位净值'].shift(1)
        return data

    def get_futures_holding(self, date, name):

        """ 读取期货持仓数据 """

        if name == "股指期货多头":
            state = "多仓"
        else:
            state = "空仓"

        try:
            security = MfcData().get_fund_security(date)
            security_data = security[security['基金名称'] == self.fund_name]
            security_data = security_data[security_data['证券类别'] == '股指期货']
            security_data = security_data[security_data['持仓多空标志'] == state]
            security_data = security_data[['基金名称', '证券名称', '持仓', '证券代码', '最新价', '市值', '持仓多空标志']]
            security_data['价格'] = security_data['市值'] / security_data['持仓'] / 200.0
            security_data.index = security_data['证券代码'].values
            security_data = security_data[['证券名称', '市值', '价格', '持仓']]
            return security_data
        except Exception as e:
            print(e)
            return None

    def cal_futures_return(self, date, cal_type="close", name="股指期货多头"):

        """
        1、根据当日和前一日持仓信息，计算股指期货涨跌 （多头、空头）
        2、只用了收盘价计算，没有用交易价格
        3、持仓文件中的最新价=期货收盘价；市值=持仓数量*持仓结算价*200
        4、得到 当日收盘资产 和 股指期货收益
        """

        # Holding Data
        pre_date = Date().get_trade_date_offset(date, -1)
        security = self.get_futures_holding(date, name)
        security.columns = ['CodeName', 'TodayMV', 'TodayPrice', 'TodayHold']
        security_pre = self.get_futures_holding(pre_date, name)
        security.columns = ['YesTodayCodeName', 'YesTodayMV', 'YesTodayPrice', 'YesTodayHold']

        if security is None:
            print("%s %s %s 数据为空" % (self.fund_name, date, name))
            return np.nan, np.nan
        if security_pre is None:
            print("%s %s %s 数据为空" % (self.fund_name, pre_date, name))
            return np.nan, np.nan

        data = pd.concat([security, security_pre], axis=1)
        data = data.dropna(subset=['YesTodayMV'])

        if len(data) > 0:

            price_change = (data['TodayPrice'] - data['YesTodayPrice']) * 200
            data['StockReturn'] = data['YesTodayHold'] * price_change
            stock_asset = data['TodayMV'].sum()
            data = data.dropna(subset=['StockReturn'])
            stock_return = data['StockReturn'].sum()
            self.save_file_asset_daily(data, name, cal_type, date)
            print("%s %s %s 计算完成" % (self.fund_name, date, name))

        else:
            stock_return = 0
            stock_asset = 0
            print("%s %s %s 数据为零" % (self.fund_name, date, name))

        return stock_return, stock_asset

    def get_stock_price(self, date):

        """ 读取股票价格数据 """
        try:
            close_date = self.close_unadjust[date]
            factor_date = self.adjust_factor[date]
            return close_date, factor_date
        except Exception as e:
            print(e)
            return None, None

    def get_stock_holding(self, date):

        """ 读取股票持仓数据"""

        try:
            security = MfcData().get_fund_security(date)
            security_data = security[security['基金名称'] == self.fund_name]
            security_data = security_data[security_data['证券类别'] == '股票']
            security_data = security_data[['基金名称', '证券名称', '持仓', '证券代码']]
            security_data['证券代码'] = security_data['证券代码'].map(CodeFormat().stock_code_add_postfix)
            security_data.index = security_data['证券代码'].values
            security_data = security_data[['证券名称', '持仓']]
            return security_data
        except Exception as e:
            print(e)
            return None

    def get_stock_trading(self, date):

        """ 读取股票交易数据 """

        try:
            trade = MfcData().get_trade_statement(date)
            trade_data = trade[trade['基金名称'] == self.fund_name]
            trade_data = trade_data[trade_data['资产类别'] == '股票资产']
            trade_data = trade_data[['基金名称', '证券名称', '成交数量', '市场成交均价', '委托方向', '证券代码']]
            trade_data['证券代码'] = trade_data['证券代码'].map(CodeFormat().stock_code_add_postfix)
            trade_data.index = trade_data['证券代码'].values
            trade_data = trade_data[['成交数量', '市场成交均价', '委托方向']]
            trade_data.columns = ['TradeVol', 'TradePrice', 'SellOrBuy']
            trade_data = trade_data[~trade_data.index.duplicated()]
            sell_code_list = list(trade_data[trade_data['SellOrBuy'] == "卖出"].index)
            trade_data.loc[sell_code_list, 'TradeVol'] = - trade_data.loc[sell_code_list, 'TradeVol']
            return trade_data
        except Exception as e:
            print(e)
            return None

    def cal_new_stock_return(self, date, cal_type="close", name="新股"):

        """
        计算当日基金资产中有多少钱是新股波动带来的
        有两种 计算方式
        1、新股以当日收盘价卖出(close)  或者继续当日持有 新股收益 = 昨日收盘数量 * 当日收盘价格
        2、新股以当日均价卖出(average)  或者继续当日持有
           分别计算当日新买入股票的收益 这两日持仓未变动的股票的收益 和当日卖出股票的收益
        返回当日资产项，和收益波动
        这里计算时， 因为新股上市当天的前一天没有价格，所以当天收益为0
        """

        # Get Holding Data
        pre_date = Date().get_trade_date_offset(date, -1)
        security = self.get_stock_holding(date)
        security.columns = ['CodeName', 'TodayVol']
        security_pre = self.get_stock_holding(pre_date)
        security_pre.columns = ['YesTodayCodeName', 'YesTodayVol']

        # Get Pricing Data
        close_date, factor_date = self.get_stock_price(date)
        close_date_pre, factor_date_pre = self.get_stock_price(pre_date)
        adjust_factor = factor_date / factor_date_pre
        price_data = pd.concat([close_date, close_date_pre, adjust_factor], axis=1)
        price_data.columns = ['Close', 'PreClose', 'AdjustFactor']

        # except Exception as eion
        if (security is None) or (security_pre is None) or (close_date is None) or (close_date_pre is None):
            print("%s %s %s 数据为空" % (self.fund_name, date, name))
            return np.nan, np.nan

        if cal_type == 'average':

            # Get Trading Data
            trade = self.get_stock_trading(date)
            if trade is None:
                print("%s %s %s 数据为空" % (self.fund_name, date, name))
                return np.nan, np.nan

            data = pd.concat([security, trade, security_pre, price_data, self.ipo_data], axis=1)
            data = data.dropna(subset=['TodayVol'])

            sell_code_list = list(data[data['SellOrBuy'] == "卖出"].index)
            buy_code_list = list(data[data['SellOrBuy'] == "买入"].index)

            data[['TradeVol', 'TodayVol']] = data[['TradeVol', 'TodayVol']].fillna(0.0)
            data['HoldVol'] = data['TodayVol']
            today_vol = data.loc[buy_code_list, 'TodayVol']
            trade_vol = data.loc[buy_code_list, 'TradeVol']
            data.loc[buy_code_list, 'HoldVol'] = today_vol - trade_vol
            price_change = data['Close'] * data['AdjustFactor'] - data['PreClose']
            data['HoldReturn'] = data['HoldVol'] * price_change

            buy_vol = data.loc[buy_code_list, 'TradeVol'].abs()
            buy_return = buy_vol * (data.loc[buy_code_list, 'Close'] - data.loc[buy_code_list, 'TradePrice'])
            data.loc[buy_code_list, "BuyReturn"] = buy_return

            sell_vol = data.loc[sell_code_list, 'TradeVol'].abs()
            sell_price = data.loc[sell_code_list, 'TradePrice'] * data.loc[sell_code_list, 'AdjustFactor']
            sell_return = sell_vol * (sell_price - data.loc[sell_code_list, 'PreClose'])
            data.loc[sell_code_list, "SellReturn"] = sell_return

            columns = ['HoldReturn', 'BuyReturn', 'SellReturn']
            data[columns] = data[columns].fillna(0.0)
            data['StockReturn'] = data[columns].sum(axis=1)

        else:

            data = pd.concat([security_pre, security, price_data, self.ipo_data], axis=1)
            data = data.dropna(subset=['YesTodayVol'])
            data['AdjustPreClose'] = data['PreClose'] / data['AdjustFactor']
            data['CloseChange'] = data['Close'] - data['AdjustPreClose']
            data['StockReturn'] = data['YesTodayVol'] * data['CloseChange']

        ipo_date = Date().get_trade_date_offset(date, -self.ipo_days)
        data = data[data['IpoDate'] <= date]
        data = data[data['IpoDate'] >= ipo_date]
        stock_asset = (data['Close'] * data['TodayVol']).sum()
        data = data.dropna(subset=['StockReturn'])

        if len(data) > 0:

            # Save File
            stock_return = data['StockReturn'].sum()
            self.save_file_asset_daily(data, name, cal_type, date)
            print("%s %s %s 计算完成" % (self.fund_name, date, name))

        else:
            stock_return = 0.0
            stock_asset = 0.0
            print("%s %s %s 数据为零" % (self.fund_name, date, name))

        return stock_return, stock_asset

    def cal_stock_fee(self, date):

        """
        计算股票的 管理托管费（当日净值*管理费率）
        交易佣金（当日股票成交额*交易费率，包括新股）
        """

        date_pre = Date().get_trade_date_offset(date, -1)
        try:
            total_asset_pre = MfcData().get_fund_asset(date_pre)
            trade = self.get_stock_trading(date)
        except Exception as e:
            print(e)
            return np.nan, np.nan

        total_asset_fund = total_asset_pre[total_asset_pre['基金名称'] == self.fund_name]
        try:
            mg_fee = - total_asset_fund['净值'].values[0] * self.mg_fee_ratio
        except Exception as e:
            print(e)
            mg_fee = np.nan

        trade_asset = (trade['TradePrice'] * trade['TradeVol'].abs()).sum()
        trade_fee = - trade_asset * self.double_fee_ratio / 2.0
        return mg_fee, trade_fee

    def cal_stock_return(self, date, cal_type="close", name="股票"):

        """
        1、计算当日净值变动中 有多少是股票（非新股）涨跌所带来的
           这里需要注意到是股票 送转分红 带来的影响 （利用前后两日的复权因子）

        股票涨跌收益 有两种 计算方式
        1、1 股票以当日收盘价买卖  或者继续当日持有 股票收益 = 昨日收盘数量 * 当日收盘价格
        1、2 股票以当日均价买卖    或者继续当日持有 股票收益 = 当日持有股票收益 + 当日卖出股票收益 + 当日买入股票收益
             分别计算当日新买入股票的收益 这两日持仓未变动的股票的收益 和当日卖出股票的收益
        """
        # Get Holding Data
        pre_date = Date().get_trade_date_offset(date, -1)
        security = self.get_stock_holding(date)
        security.columns = ['CodeName', 'TodayVol']
        security_pre = self.get_stock_holding(pre_date)
        security_pre.columns = ['YesTodayCodeName', 'YesTodayVol']

        # Get Pricing Data
        close_date, factor_date = self.get_stock_price(date)
        close_date_pre, factor_date_pre = self.get_stock_price(pre_date)
        adjust_factor = factor_date / factor_date_pre
        price_data = pd.concat([close_date, close_date_pre, adjust_factor], axis=1)
        price_data.columns = ['Close', 'PreClose', 'AdjustFactor']

        # except Exception as eion
        if (security is None) or (security_pre is None) or (close_date is None) or (close_date_pre is None):
            print("%s %s %s 数据为空" % (self.fund_name, date, name))
            return np.nan, np.nan

        if cal_type == 'average':

            # Get Trading Data
            trade = self.get_stock_trading(date)
            if trade is None:
                print("%s %s %s 数据为空" % (self.fund_name, date, name))
                return np.nan, np.nan

            data = pd.concat([security, trade, security_pre, price_data, self.ipo_data], axis=1)
            stock_asset = (data['Close'] * data['TodayVol']).sum()
            data = data.dropna(subset=['YesTodayVol'])

            sell_code_list = list(data[data['SellOrBuy'] == "卖出"].index)
            buy_code_list = list(data[data['SellOrBuy'] == "买入"].index)

            data[['TradeVol', 'TodayVol']] = data[['TradeVol', 'TodayVol']].fillna(0.0)
            data['HoldVol'] = data['TodayVol']
            today_vol = data.loc[buy_code_list, 'TodayVol']
            trade_vol = data.loc[buy_code_list, 'TradeVol']
            data.loc[buy_code_list, 'HoldVol'] = today_vol - trade_vol
            price_change = data['Close'] * data['AdjustFactor'] - data['PreClose']
            data['HoldReturn'] = data['HoldVol'] * price_change

            buy_vol = data.loc[buy_code_list, 'TradeVol'].abs()
            buy_return = buy_vol * (data.loc[buy_code_list, 'Close'] - data.loc[buy_code_list, 'TradePrice'])
            data.loc[buy_code_list, "BuyReturn"] = buy_return

            sell_vol = data.loc[sell_code_list, 'TradeVol'].abs()
            sell_price = data.loc[sell_code_list, 'TradePrice'] * data.loc[sell_code_list, 'AdjustFactor']
            sell_return = sell_vol * (sell_price - data.loc[sell_code_list, 'PreClose'])
            data.loc[sell_code_list, "SellReturn"] = sell_return

            columns = ['HoldReturn', 'BuyReturn', 'SellReturn']
            data[columns] = data[columns].fillna(0.0)
            data['StockReturn'] = data[columns].sum(axis=1)

            data = data.dropna(subset=['StockReturn'])
            ipo_date = Date().get_trade_date_offset(date, -self.ipo_days)
            data = data[data['IpoDate'] < ipo_date]
            data = data[data['IpoDate'] <= date]

        else:
            data = pd.concat([security, security_pre, price_data, self.ipo_data], axis=1)
            stock_asset = (data['Close'] * data['TodayVol']).sum()
            data['AdjustPreClose'] = data['PreClose'] / data['AdjustFactor']
            price_change = data['Close'] - data['AdjustPreClose']
            data['StockReturn'] = data['YesTodayVol'] * price_change

            data = data.dropna(subset=['StockReturn'])
            ipo_date = Date().get_trade_date_offset(date, -self.ipo_days)
            data = data[data['IpoDate'] < ipo_date]
            data = data[data['IpoDate'] <= date]

        if len(data) > 0:

            stock_return = data['StockReturn'].sum()
            self.save_file_asset_daily(data, name, cal_type, date)
            print("%s %s %s 计算完成" % (self.fund_name, date, name))
            return stock_return, stock_asset

        else:
            print("%s %s %s 数据为零" % (self.fund_name, date, name))
            return 0, 0

    def cal_barra_exposure_return(self):

        """ 计算满仓 基金暴露、指数暴露、超额暴露、因子收益、基金超额暴露收益 """

        # 参数
        type_list = ["STYLE", "COUNTRY", "INDUSTRY"]

        # 得到基金（满仓）相对于跟踪指数（满仓）超额暴露
        exposure_fund = MfcData().get_mfc_holding_barra_exposure(self.fund_name, self.beg_date_pre, self.end_date)
        exposure_index = Index().get_index_exposure(self.index_code, self.beg_date_pre, self.end_date, type_list)
        exposure_excess = exposure_fund.sub(exposure_index)
        exposure_excess = exposure_excess.dropna()

        # 添加 Country Factor = 1.0
        factor_name = Barra().get_factor_name(type_list=["COUNTRY"])
        factor_name = list(factor_name["NAME_EN"].values)
        exposure_excess[factor_name] = 1.0

        # 前一天的 Exposure 对应后一天的 Factor Return
        exposure_excess.index = exposure_excess.index.map(lambda x: Date().get_trade_date_offset(x, 1))

        # 取得当日的 Factor Return
        factor_return = Barra().get_factor_return(self.beg_date, self.end_date, type_list)

        # 计算超额暴露带来的收益部分
        [exposure, factor_return] = FactorOperate().make_same_index_columns([exposure_excess, factor_return])
        fund_risk_factor_return = exposure.mul(factor_return)

        # 调整列的位置
        factor_name = Barra().get_factor_name(type_list=type_list)
        factor_name = list(factor_name["NAME_EN"].values)
        fund_risk_factor_return = fund_risk_factor_return[factor_name]

        # 分别计算 Style Industry RiskFactor = Style + Industry
        factor_name = Barra().get_factor_name(type_list=['STYLE'])
        factor_name = list(factor_name["NAME_EN"].values)
        fund_risk_factor_return['Style'] = fund_risk_factor_return[factor_name].sum(axis=1)

        factor_name = Barra().get_factor_name(type_list=['INDUSTRY'])
        factor_name = list(factor_name["NAME_EN"].values)
        fund_risk_factor_return['Industry'] = fund_risk_factor_return[factor_name].sum(axis=1)

        factor_name = Barra().get_factor_name(type_list=type_list)
        factor_name = list(factor_name["NAME_EN"].values)
        fund_risk_factor_return['RiskFactor'] = fund_risk_factor_return[factor_name].sum(axis=1)

        # 整理返回区间内的所有数据=基金暴露+指数暴露+超额暴露+因子收益+基金超额暴露收益
        fund_risk_factor_return = fund_risk_factor_return.loc[self.beg_date:self.end_date, :]
        exposure = exposure.loc[self.beg_date:self.end_date, :]
        factor_return = factor_return.loc[self.beg_date:self.end_date, :]

        fund_risk_factor_return /= 100.0
        factor_return /= 100.0

        self.save_file_excel(fund_risk_factor_return, "Barra", "基金风格收益", "0.00%")
        self.save_file_excel(factor_return, "Barra", "风格因子收益", "0.00%")
        self.save_file_excel(exposure, "Barra", "基金超额暴露", "0.000")
        self.save_file_excel(exposure_fund, "Barra", "基金暴露", "0.000")
        self.save_file_excel(exposure_index, "Barra", "指数暴露", "0.000")

    def save_file_asset_daily(self, data, name, cal_type, date):

        """ 资产收益（股票、新股、期货）计算过程文件存储 """

        sub_path = os.path.join(self.data_path, self.fund_name, "资产收益", name)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        file = "%s收益分解_%s_%s_%s.xlsx" % (name, cal_type, self.fund_name, date)
        file_name = os.path.join(sub_path, file)

        num_format_pd = pd.DataFrame([], columns=data.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00'

        excel = WriteExcel(file_name)
        worksheet = excel.add_worksheet(self.fund_name)
        excel.write_pandas(data, worksheet,
                           begin_row_number=0, begin_col_number=0,
                           num_format_pd=num_format_pd, color="red", fillna=True)
        excel.close()

    def save_file_summary(self):

        """ 将一段时间内的归因总结写入文件 """

        unit_nav_daliy = self.read_file_excel("拆分", "单位净值", self.beg_date, self.end_date)
        pct_daliy = self.read_file_excel("拆分", "收益率", self.beg_date, self.end_date)
        excess_exposure = self.read_file_excel("Barra", "基金超额暴露", self.beg_date, self.end_date)
        fund_risk_return = self.read_file_excel("Barra", "基金风格收益", self.beg_date, self.end_date)
        risk_factor_return = self.read_file_excel("Barra", '风格因子收益', self.beg_date, self.end_date)

        # Result
        index = ['资产盈亏', '股票盈亏', '新股盈亏',
                 '固收其他盈亏', '日内交易盈亏',
                 '期货多头盈亏', '期货空头盈亏',
                 '管理托管费用', '交易印花费用',
                 '基准盈亏', '超额盈亏', '择时盈亏', '选股盈亏',
                 'Alpha', 'Style',
                 'Industry', '全仓选股盈亏']

        change_index = ['基金整体', '股票部分', '新股部分',
                        '固收+其他部分', "日内交易部分",
                        '期货多头', '期货空头',
                        '管理托管', '交易印花', '股票基准',
                        '股票超额', '股票择时', '股票选股',
                        'Alpha', 'Barra风格', 'Barra行业', '全仓股票选股']

        unit_nav_sum = unit_nav_daliy[index].sum()
        pct_sum = ((pct_daliy[index] + 1.0).cumprod() - 1.0).iloc[-1, :]

        result = pd.concat([unit_nav_sum, pct_sum], axis=1)
        result.index = change_index

        result.loc['股票平均仓位', :] = unit_nav_daliy['股票仓位'].mean()
        result.loc['归因开始时间', :] = unit_nav_daliy.index[0]
        result.loc['归因结束时间', :] = unit_nav_daliy.index[-1]
        result.columns = ["净值拆分", '收益率拆分']

        # Barra
        type_list = ["STYLE", "INDUSTRY"]
        factor_name = Barra().get_factor_name(type_list=type_list)
        factor_name = list(factor_name["NAME_EN"].values)

        barra = pd.DataFrame([], index=factor_name, columns=['基金超额暴露', '因子区间收益率', '基金暴露因子收益'])
        barra.loc[factor_name, "基金超额暴露"] = excess_exposure.loc[:, factor_name].mean().values
        barra.loc[factor_name, "因子区间收益率"] = risk_factor_return.loc[:, factor_name].sum().values
        barra.loc[factor_name, "基金暴露因子收益"] = fund_risk_return.loc[:, factor_name].sum().values

        type_list = ["STYLE"]
        factor_name = Barra().get_factor_name(type_list=type_list)
        factor_name = list(factor_name["NAME_EN"].values)
        style_barra = barra.loc[factor_name, :]
        style_barra = style_barra.sort_values(by=['基金暴露因子收益'], ascending=False)
        style_barra.loc['Barra风格汇总', "基金暴露因子收益"] = style_barra["基金暴露因子收益"].sum()

        type_list = ["INDUSTRY"]
        factor_name = Barra().get_factor_name(type_list=type_list)
        factor_name = list(factor_name["NAME_EN"].values)
        industry_barra = barra.loc[factor_name, :]
        industry_barra = industry_barra.sort_values(by=['基金暴露因子收益'], ascending=False)
        industry_barra.loc['Barra行业汇总', "基金暴露因子收益"] = industry_barra["基金暴露因子收益"].sum()

        # 备注部分
        notes = pd.DataFrame([], index=["基金整体=", "股票部分=", "股票超额=", "股票选股="], columns=["备注"])
        notes.loc["基金整体=", "备注"] = "基金整体=股票部分+新股部分+固收其他部分+日内交易部分+管理托管+交易印花"
        notes.loc["日内交易部分=", "备注"] = "日内交易部分=当日交易均价和收盘价的差带来的盈亏"
        notes.loc["股票部分=", "备注"] = "股票部分=股票基准+股票超额"
        notes.loc["股票超额=", "备注"] = "股票超额=股票择时+股票选股"
        notes.loc["股票选股=", "备注"] = "股票选股=Alpha+Barra风格+Barra行业"

        # Save File
        save_path = os.path.join(self.data_path, self.fund_name, "阶段归因")
        file = '%s_归因汇总_%s.xlsx' % (self.fund_name, self.period_name)
        file_name = os.path.join(save_path, file)
        print(file_name)

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        excel = WriteExcel(file_name)
        worksheet = excel.add_worksheet(self.fund_name)

        # Result
        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        num_format_pd.loc['format', ['净值拆分']] = '0.0000'

        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)

        # Notes
        begin_row_number = len(style_barra) + 2
        for i in range(len(notes.index)):
            excel.insert_merge_range(worksheet, begin_row_number + i, 5,
                                     begin_row_number + i, 8, notes.loc[notes.index[i], "备注"])

        num_format_pd = pd.DataFrame([], columns=style_barra.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        num_format_pd.loc['format', ['基金超额暴露']] = '0.0000'
        excel.write_pandas(style_barra, worksheet, begin_row_number=0, begin_col_number=5,
                           num_format_pd=num_format_pd, color="blue", fillna=True)

        num_format_pd = pd.DataFrame([], columns=industry_barra.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        num_format_pd.loc['format', ['基金超额暴露']] = '0.0000'
        excel.write_pandas(industry_barra, worksheet, begin_row_number=0, begin_col_number=10,
                           num_format_pd=num_format_pd, color="blue", fillna=True)

        excel.close()

    def save_file_excel(self, new_data, type, name, num_format):

        """
        将一段时间内的每日拆分写入文件（增量写入）
        将一段时间内的每日暴露写入文件（增量写入）
        """

        if len(new_data) > 0:

            save_path = os.path.join(self.data_path, self.fund_name, "每日汇总")
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            file = '%s_%s_%s.xlsx' % (self.fund_name, type, name)
            file_name = os.path.join(save_path, file)
            print("写入", file_name)

            if os.path.exists(file_name):
                old_data = pd.read_excel(file_name, index_col=[0])
                old_data.index = old_data.index.map(str)
                data = FactorOperate().pandas_add_row(old_data, new_data)
            else:
                data = new_data

            num_format_pd = pd.DataFrame([], columns=data.columns, index=['format'])
            num_format_pd.loc['format', :] = num_format

            excel = WriteExcel(file_name)
            worksheet = excel.add_worksheet(self.fund_name)
            excel.write_pandas(data, worksheet, begin_row_number=0, begin_col_number=0,
                               num_format_pd=num_format_pd, color="red", fillna=True)
            excel.close()
        else:
            save_path = os.path.join(self.data_path, self.fund_name, "每日汇总")
            file = '%s_%s_%s.xlsx' % (self.fund_name, type, name)
            file_name = os.path.join(save_path, file)
            print("写入数据为0", file_name)

    def read_file_excel(self, type, name, beg_date, end_date):

        """
        读取一段时间内的每日拆分文件
        读取一段时间内的每日暴露文件
        """

        save_path = os.path.join(self.data_path, self.fund_name, "每日汇总")
        file = '%s_%s_%s.xlsx' % (self.fund_name, type, name)
        file_name = os.path.join(save_path, file)
        old_data = pd.read_excel(file_name, index_col=[0])
        old_data.index = old_data.index.map(str)
        old_data = old_data.loc[beg_date:end_date, :]
        return old_data

    def attribution_date(self, data, date):

        """ 得到某只基金当天归因 """

        print('########## 计算 %s ############' % date)

        # 按照收盘价 计算 新股盈亏 和股票盈亏
        new_stock_return, new_stock_asset = self.cal_new_stock_return(date, "close", "新股")
        stock_return, stock_asset = self.cal_stock_return(date, "close", "股票")

        data.loc[date, '新股盈亏'] = new_stock_return
        data.loc[date, '股票盈亏'] = stock_return

        # 按照交易价格计算 计算 新股盈亏 和股票盈亏 并计算管理托管费 交易印花费
        new_stock_return, new_stock_asset = self.cal_new_stock_return(date, "average", "新股")
        stock_return, stock_asset = self.cal_stock_return(date, "average", "股票")
        mg_fee, trade_fee = self.cal_stock_fee(date)

        data.loc[date, '新股盈亏均价'] = new_stock_return
        data.loc[date, '股票盈亏均价'] = stock_return
        data.loc[date, '新股资产'] = new_stock_asset
        data.loc[date, '股票资产'] = stock_asset
        data.loc[date, '管理托管费用'] = mg_fee
        data.loc[date, '交易印花费用'] = trade_fee

        # 按照收盘价格计算  期货空头盈亏 和期货多头盈亏
        futures_return, futures_asset = self.cal_futures_return(date, "close", "股指期货多头")
        data.loc[date, '期货多头盈亏'] = futures_return
        data.loc[date, '期货多头资产'] = futures_asset

        futures_return, futures_asset = self.cal_futures_return(date, "close", "股指期货空头")
        data.loc[date, '期货空头盈亏'] = futures_return
        data.loc[date, '期货空头资产'] = futures_asset

        return data

    def attribution_fund(self):

        """ 得到某只基金归因 """

        print(" %s开始归因 %s %s " % (self.fund_name, self.beg_date, self.end_date))
        data = self.get_fund_asset()

        if data is None:
            print(" %s归因数据长度为0 %s %s " % (self.fund_name, self.beg_date, self.end_date))
            return None

        for i_date in range(len(data)):
            data = self.attribution_date(data, data.index[i_date])

        # 计算股票仓位 股票涨跌幅
        data = data[data['股票资产'] >= 0.0]
        data['股票仓位'] = data['股票资产'] / data['净值']
        data['昨日股票仓位'] = data['股票仓位'].shift(1)
        data['昨日股票资产'] = data['股票资产'].shift(1)

        date_list = data.loc[:, '昨日股票资产'] != 0.0
        data.loc[date_list, "股票涨跌幅"] = data.loc[date_list, '股票盈亏'] / data.loc[date_list, '昨日股票资产']
        date_list = data.loc[:, '昨日股票资产'] == 0.0
        data.loc[date_list, "股票涨跌幅"] = np.nan

        # 资产盈亏 = 股票盈亏 + 新股盈亏 + 债券其他 + 托管管理费 + 交易印花费 + 日内交易盈亏
        cols = ['管理托管费用', '交易印花费用', '股票盈亏', '新股盈亏',
                '股票盈亏均价', '新股盈亏均价', '期货多头盈亏', '期货空头盈亏']
        data[cols] = data[cols].fillna(0.0)

        # 日内交易盈亏 = 股票盈亏 - 股票盈亏均价 + 新股盈亏 - 新股盈亏均价
        data['资产盈亏'] = data['基金涨跌幅'] * data['昨日净值']
        data['日内交易盈亏'] = - data['股票盈亏'] + data['股票盈亏均价'] - data['新股盈亏'] + data['新股盈亏均价']
        data['汇总盈亏'] = data['管理托管费用'] + data['交易印花费用'] + data['股票盈亏']
        data['汇总盈亏'] += data['新股盈亏'] + data['日内交易盈亏'] + data['期货多头盈亏'] + data['期货空头盈亏']
        data['固收其他盈亏'] = data['资产盈亏'] - data['汇总盈亏']

        # 股票盈亏 = 基准盈亏 + 超额盈亏
        data['基准盈亏'] = data['指数涨跌幅'] * data['昨日净值'] * self.index_code_ratio
        data['超额盈亏'] = data['昨日股票仓位'] * data['股票涨跌幅'] * data['昨日净值'] - data['基准盈亏']

        # 超额盈亏 = 择时（资产配置能力） + 选股能力
        data['择时盈亏'] = (data['昨日股票仓位'] - self.index_code_ratio) * data['指数涨跌幅'] * data['昨日净值']
        data['选股盈亏'] = data['昨日股票仓位'] * (data['股票涨跌幅'] - data['指数涨跌幅']) * data['昨日净值']
        data['全仓选股盈亏'] = (data['股票涨跌幅'] - data['指数涨跌幅']) * data['昨日净值']

        # drop
        data = data.dropna(subset=['昨日单位净值'])
        data = data[data['昨日单位净值'] != 0.0]
        data = data.fillna(0.0)

        # 风格行业暴露
        self.cal_barra_exposure_return()
        fund_risk_return = self.read_file_excel("Barra", "基金风格收益", self.beg_date, self.end_date)

        for i_col in range(len(fund_risk_return.columns)):
            col = fund_risk_return.columns[i_col]
            data[col] = fund_risk_return[col] * data['昨日股票资产']

        data['Alpha'] = data['选股盈亏'] - data['Industry']
        data['Alpha'] = data['Alpha'] - data['Style']

        self.save_file_excel(data, "拆分", "净值", "0.00")

        # 需要重新计算的列名
        columns = ['资产盈亏', '管理托管费用', '交易印花费用', '股票盈亏', '新股盈亏', "汇总盈亏",
                   '期货多头盈亏', '期货空头盈亏', '固收其他盈亏', '日内交易盈亏',
                   '基准盈亏', '超额盈亏', '择时盈亏', '选股盈亏', '全仓选股盈亏']

        columns.extend(fund_risk_return.columns)
        columns.extend(["Alpha"])

        # 以单位净值计算
        for col in columns:
            data[col] /= data['昨日基金份额']
        self.save_file_excel(data, "拆分",  "单位净值", "0.000")

        # 以收益率计算
        for col in columns:
            data[col] /= data['昨日单位净值']
        self.save_file_excel(data, "拆分",  "收益率", "0.00%")
        self.save_file_summary()

    def update_data(self):

        """ 更新归因需要的数据 """

        today = datetime.today().strftime("%Y%m%d")
        beg_date = Date().get_trade_date_offset(today, -40)

        Barra().load_barra_data()
        MfcData().cal_mfc_private_fund_nav_all()
        MfcData().load_mfc_public_fund_nav()

        param = MfcData().get_mfc_fund_info()
        param.index = param.Name

        for i_fund in range(0, len(param)):
            fund_name = param.index[i_fund]
            MfcData().cal_mfc_holding_barra_exposure_perieds(fund_name, beg_date, today)

        date_series = Date().get_trade_date_series(beg_date, today)
        for date in date_series:
            Index().make_weight_mixed(date)

        Index().cal_index_exposure("000300.SH", beg_date, today)
        Index().cal_index_exposure("000905.SH", beg_date, today)
        Index().cal_index_exposure("881001.WI", beg_date, today)
        Index().cal_index_exposure("中证500+创业板综+中小板综", beg_date, today)

    def attribution_all_fund(self, date_list):

        """ 归因所有基准不为空的基金 给定所有时间段 """

        param = MfcData().get_mfc_fund_info()
        param.index = param.Name
        param = param.dropna(subset=['Index'])
        print(param.index)

        for i_date in range(len(date_list)):

            beg_date = date_list[i_date][0]
            end_date = date_list[i_date][1]
            period_name = date_list[i_date][2]

            for i_fund in range(0, len(param)):

                fund_name = param.index[i_fund]
                index_code_ratio = param.loc[fund_name, "Index_Ratio"]
                fund_code = param.loc[fund_name, "Code"]
                index_code = param.loc[fund_name, "Index"]
                type = param.loc[fund_name, "Type"]
                trust_fee = param.loc[fund_name, "TrusteeShipFeeRatio"]
                mg_fee = param.loc[fund_name, "MgFeeRatio"]
                mg_fee_ratio = trust_fee + mg_fee

                self.get_info(index_code_ratio, index_code, fund_code, fund_name,
                              type, beg_date, end_date, period_name, mg_fee_ratio)
                self.attribution_fund()

    def attribution_one_fund(self):

        """ 测试单个基金归因 """

        # fund_name = '建行中国人寿多策略管理计划'
        # beg_date = '20190101'
        # end_date = '20190312'
        # period_name = "2019年至今（20190312）"

        fund_name = '建行中国人寿固收组合管理计划'
        beg_date = '20190101'
        end_date = '20190312'
        period_name = "2019年至今（20190312）"

        param = MfcData().get_mfc_fund_info()
        param.index = param.Name
        param = param.dropna(subset=['Index'])

        index_code_ratio = param.loc[fund_name, "Index_Ratio"]
        fund_code = param.loc[fund_name, "Code"]
        index_code = param.loc[fund_name, "Index"]
        type = param.loc[fund_name, "Type"]
        trust_fee = param.loc[fund_name, "TrusteeShipFeeRatio"]
        mg_fee = param.loc[fund_name, "MgFeeRatio"]
        mg_fee_ratio = trust_fee + mg_fee

        self.get_info(index_code_ratio, index_code, fund_code, fund_name,
                      type, beg_date, end_date, period_name, mg_fee_ratio)
        self.attribution_fund()


if __name__ == '__main__':

    self = AttributionFund()
    date_list = [['20190101', '20190329', "2019年1-3月"]]
    self.update_data()
    self.attribution_all_fund(date_list)
    # self.attribution_one_fund()
