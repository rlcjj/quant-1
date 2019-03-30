import os
import pandas as pd
from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.code_format import CodeFormat


class MfcGetData(Data):

    """
    读取泰达宏利管理基金基本情况

    读取本地持仓数据
    get_fund_asset()
    get_fund_security()
    get_group_security()
    get_trade_statement()

    读取 公募 专户 净值数据
    get_fund_nav()

    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def get_fund_asset(self, date):

        """ 基金资产 """

        date_int = Date().change_to_str(date)
        file = os.path.join(self.data_path, 'mfc_holding\\基金资产', '基金资产_' + str(date_int) + '.csv')
        data = pd.read_csv(file, encoding='gbk', thousands=',')
        return data

    def get_fund_security(self, date):

        """ 基金证券 """

        date_int = Date().change_to_str(date)
        file = os.path.join(self.data_path, 'mfc_holding\\基金证券', '基金证券_' + str(date_int) + '.csv')
        data = pd.read_csv(file, encoding='gbk', thousands=',')
        data = data.dropna(subset=['基金名称'])

        data = data.set_index([data['基金名称'], data['证券名称']])
        data = data.loc[~data.index.duplicated(), :]

        if date > "20180701":
            data = data.reset_index(drop=True)
            return data
        else:
            file_old = os.path.join(self.data_path, 'mfc_holding\\基金证券OLD', '基金证券_' + str(date_int) + '.csv')
            data_old = pd.read_csv(file_old, encoding='gbk', thousands=',')
            data_old = data_old.dropna(subset=['基金名称'])
            data_old = data_old.set_index([data_old['基金名称'], data_old['证券名称']])
            data_old = data_old.loc[~data_old.index.duplicated(), :]

            if "市值比净值(%)" in data.columns:
                data_old = data_old[['持仓多空标志', '证券类别']]
            else:
                data_old = data_old[['市值比净值(%)', '持仓多空标志', '证券类别']]

            data_total = pd.concat([data, data_old], axis=1)
            data_total = data_total.loc[:, ~data_total.columns.duplicated()]
            data_total = data_total.reset_index(drop=True)
            return data_total

    def get_group_security(self, date):

        """ 组合证券 """

        date_int = Date().change_to_str(date)
        file = os.path.join(self.data_path, 'mfc_holding\\组合证券', '组合证券_' + str(date_int) + '.csv')
        data = pd.read_csv(file, encoding='gbk', thousands=',')
        return data

    def get_trade_statement(self, date):

        """ 成交回报 """

        date_int = Date().change_to_str(date)
        file = os.path.join(self.data_path, 'mfc_holding\\成交回报', '成交回报_' + str(date_int) + '.csv')
        data = pd.read_csv(file, encoding='gbk', thousands=',')
        return data

    def get_mfc_fund_info(self):

        """ 泰达基金整体信息 """

        file = os.path.join(self.data_path, "static_data", "Fund_Info.xlsx")
        data = pd.read_excel(file)
        return data

    def get_mfc_manage_info(self):

        """ 泰达基金整体信息 """

        file = os.path.join(self.data_path, "static_data", "Manage_Fund_Name.xlsx")
        data = pd.read_excel(file, encoding='gbk')
        return data

    def get_mfc_fund_name(self, fund_code):

        """ 泰达基金名称列表 """

        data = self.get_mfc_fund_info()
        data = data[data['Code'] == fund_code]
        result = data['Name'].values[0]
        return result

    def get_fund_asset_period(self, fund_name, beg_date, end_date, columns=None):

        """ 一段时间 基金资产的部分列的情况 """

        date_series = Date().get_trade_date_series(beg_date, end_date)
        if columns is None:
            columns = ['基金编号', '基金名称', '净值', '基金份额', '单位净值',
                       '股票资产', '债券资产', '当前现金余额', '回购资产', '基金资产',
                       '股票当日浮动盈亏', '债券当日浮动盈亏', '基金当日浮动盈亏',
                       '当日股票总盈亏金额', '当日债券总盈亏金额',
                       '当日买金额', '当日卖金额']
            columns = ['基金编号', '基金名称', '净值', '基金份额', '单位净值']

        result = pd.DataFrame([], index=date_series, columns=columns)

        for i in range(len(date_series)):
            date = date_series[i]

            # if fund_name == '泰达宏利沪深300' and date <= "20180315":
            #     fund_name = "泰达宏利财富大盘300"

            try:
                asset = self.get_fund_asset(date)
                asset = asset[asset['基金名称'] == fund_name]
                asset.index = [date]
                result.loc[date, columns] = asset.loc[date, columns]
            except Exception as e:
                pass
        result = result.dropna(how='all')
        return result

    def get_mfc_public_fund_nav(self, fund_code):

        """ 公募基金复权净值 """

        file = os.path.join(self.data_path, "nav\public_fund", fund_code + "_Nav.csv")
        nav_data = pd.read_csv(file, index_col=[0], encoding='gbk')
        nav_data.index = nav_data.index.map(str)
        return nav_data

    def get_mfc_private_fund_nav(self, fund_name):

        """ 专户基金复权净值 """

        file = os.path.join(self.data_path, "nav\private_fund", fund_name + "_Nav.csv")
        nav_data = pd.read_csv(file, index_col=[0], encoding='gbk')
        nav_data.index = nav_data.index.map(str)
        return nav_data

    def get_mfc_stock_ratio(self, fund_name, date):

        """ 基金股票仓位 """

        data = self.get_fund_asset(date)
        data = data[data['基金名称'] == fund_name]
        result = float(data['股票资产/净值(%)'].values[0] / 100)
        return result

    def get_manager_fund(self):

        """ 每个人管理的基金 """
        file = os.path.join(self.data_path, "static_data", "Manage_Fund_Name.xlsx")
        data = pd.read_excel(file, encoding='gbk')
        return data

    def get_fund_stock_weight(self, fund_name, date):

        """ 某天某只基金的股票持仓 """

        data = self.get_fund_security(date)
        data = data[data['基金名称'] == fund_name]
        data.index = data['证券代码'].map(CodeFormat().stock_code_add_postfix)
        weight = pd.DataFrame(data['市值比净值(%)'])
        weight.columns = ['Weight']
        weight = weight.sort_values(by=['Weight'], ascending=False)
        weight.index.name = "Code"
        print(len(weight))

        return weight

    def get_mfc_nav(self, fund_code, fund_name, fund_type):

        """ 泰达基金产品每日净值（公募 专户） """

        if fund_type == "公募":
            fund_data = self.get_mfc_public_fund_nav(fund_code)
            fund_data = pd.DataFrame(fund_data['NAV_ADJ'])
        elif fund_type == "专户":
            fund_data = self.get_mfc_private_fund_nav(fund_name)
            fund_data = pd.DataFrame(fund_data['累计复权净值'])
            fund_data.columns = ['NAV_ADJ']
        else:
            print("%s不存在", fund_type)
            fund_data = pd.DataFrame()
        return fund_data


if __name__ == '__main__':

    fund_name = '泰达逆向策略'
    date = '20171229'
    fund_id = 38
    fund_code = '229002.OF'

    # print(MfcGetData().get_mfc_fund_info())
    # print(MfcGetData().get_fund_security(date))
    # print(MfcGetData().get_fund_asset(date))
    # print(MfcGetData().get_group_security(date))
    # print(MfcGetData().get_trade_statement(date))
    #
    # print(MfcGetData().get_fund_asset_period(fund_id, "20171229", "20180120"))
    # print(MfcGetData().get_mfc_private_fund_nav(fund_name))
    # print(MfcGetData().get_mfc_public_fund_nav(fund_code))
    # print(MfcGetData().get_mfc_stock_ratio(fund_name, date))

    self = MfcGetData()

