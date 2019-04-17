import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.fund.fund import Fund
from quant.stock.date import Date
from quant.stock.index import Index
from quant.utility.write_excel import WriteExcel
from quant.utility.financial_series import FinancialSeries


class MfcManagerMoney(Data):

    """
    基金经理津贴计算
    1、每半年计算一次
    2、前4个季度评分在85以上或者前8个季度在80分以上均可
    3、绝对收益（指数型为超额收益）排名、跟踪误差排名、IR排名

    分位数和得分对应关系（前90%满分，后10%零分，之间线性打分）
    收益的排名是按照绝对收益取排名
    IR中的超额收益是按照各自的基准
    暂时没有考虑仓位
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\mfc_manager_money'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    def update_data(self):

        """ 下载数据 需要更新 富时指数的数据 """

        today = datetime.today()
        beg_date = Date().get_trade_date_offset(today, -120)
        Index().load_index_factor("000907.CSI", beg_date, today)

    def cal_fund_index(self, fund_pool_name, my_index_code, my_fund_code, beg_date, end_date):

        """
        计算某只基金所在基金池的各项指标（包括基金收益、基金基准收益、超额收益、跟踪误差及信息比率） 剔除新基金
        """

        fund_pool = Fund().get_fund_pool_all(date="20181231", name=fund_pool_name)
        fund_pool = fund_pool[fund_pool['setupdate'] < beg_date]
        fund_pool = list(fund_pool['wind_code'].values)

        fund_pool.append(my_fund_code)
        result = pd.DataFrame([], index=fund_pool)
        data = Fund().get_fund_factor("Repair_Nav")

        for i in range(0, len(fund_pool)):

            fund_code = fund_pool[i]
            if fund_code == my_fund_code:
                index_code = my_index_code
            else:
                index_code = "881001.WI"

            print(fund_code, index_code, beg_date, end_date)

            try:
                fund = pd.DataFrame(data[fund_code])
                index = Index().get_index_factor(index_code, attr=["CLOSE"])
                fs = FinancialSeries(pd.DataFrame(fund), pd.DataFrame(index))
                fund_return = fs.get_interval_return_annual(beg_date, end_date)
                bench_return = fs.get_interval_return_benchmark(beg_date, end_date)
                excess_return = fs.get_interval_excess_return(beg_date, end_date)
                tracking_error = fs.get_interval_tracking_error(beg_date, end_date)
                ir = excess_return / tracking_error

                result.loc[fund_code, "基准收益"] = bench_return
                result.loc[fund_code, "基金收益"] = fund_return
                result.loc[fund_code, "超额收益"] = - bench_return + fund_return
                result.loc[fund_code, "跟踪误差"] = tracking_error
                result.loc[fund_code, "信息比率"] = ir

            except Exception as e:
                print(e)

        result = result.dropna()
        result = result[~result.index.duplicated()]
        result = result.sort_values(by=['基金收益'], ascending=False)
        result['收益名次'] = range(1, len(result) + 1)
        result['收益排名'] = result['收益名次'].map(lambda x: str(x) + '/' + str(len(result)))
        file = "%s_%s_%s_%s.csv" % (fund_pool_name, my_fund_code, beg_date, end_date)
        file = os.path.join(self.data_path, 'data', file)
        result.to_csv(file)

    def cal_all_fund_index(self, beg_date, end_date):

        """ 计算所有基金的指标 """

        file = os.path.join(self.data_path, "基金经理考核范围.xlsx")
        all_data = pd.read_excel(file, index_col=[0])
        all_data.index = all_data['代码']

        for i_fund in range(0, len(all_data)):

            fund_code = all_data.index[i_fund]
            index_code = all_data.loc[fund_code, "基准代码"]
            fund_pool_name = all_data.loc[fund_code, "考核分类"]
            self.cal_fund_index(fund_pool_name, index_code, fund_code, beg_date, end_date)

    @staticmethod
    def score_fund_index(s):

        """  分位数和得分对应关系（前90%满分，后10%零分，之间线性打分） """

        if s >= 0.9:
            val = 1.0
        elif s < 0.1:
            val = 0.0
        else:
            val = 1.25 * s - 0.125

        return val

    def get_fund_index(self, fund_pool_name, my_fund_code, beg_date, end_date, fund_type):

        """
        得到某只基金的得分
        1、所在基金池的 收益 超额收益 跟踪误差及IR
        2、每项打分
        3、汇总打分
        """

        try:
            file = "%s_%s_%s_%s.csv" % (fund_pool_name, my_fund_code, beg_date, end_date)
            file = os.path.join(self.data_path, 'data', file)
            data = pd.read_csv(file, index_col=[0], encoding='gbk')
            data = data[~data.index.duplicated()]
            data['绝对收益排名百分比'] = data['基金收益'].rank(ascending=True) / len(data)
            data['跟踪误差排名百分比'] = data['跟踪误差'].rank(ascending=False) / len(data)
            data['信息比率排名百分比'] = data['信息比率'].rank(ascending=True) / len(data)
            data['绝对收益得分'] = data['绝对收益排名百分比'].map(self.score_fund_index)
            data['跟踪误差得分'] = data['跟踪误差排名百分比'].map(self.score_fund_index)
            data['信息比率得分'] = data['信息比率排名百分比'].map(self.score_fund_index)

            if fund_type == "主动风格":
                data['总分'] = data['绝对收益得分'] * 0.75 + data['跟踪误差得分'] * 0.25 + data['信息比率得分'] * 0.0
            elif fund_type == "主动量化":
                data['总分'] = data['绝对收益得分'] * 0.40 + data['跟踪误差得分'] * 0.20 + data['信息比率得分'] * 0.40
            elif fund_type == "主动":
                data['总分'] = data['绝对收益得分'] * 0.75 + data['跟踪误差得分'] * 0.15 + data['信息比率得分'] * 0.10
            elif fund_type == "指数":
                data['总分'] = data['绝对收益得分'] * 0.60 + data['跟踪误差得分'] * 0.40 + data['信息比率得分'] * 0.00
            result = pd.DataFrame(data.loc[my_fund_code, :]).T
        except Exception as e:
            print(e)
            result = pd.DataFrame([])

        return result

    def get_all_fund_index(self, beg_date, end_date):

        """ 得到所有基金的得分数据汇总 """

        file = os.path.join(self.data_path, "基金经理考核范围.xlsx")
        all_data = pd.read_excel(file, index_col=[0])
        all_data.index = all_data['代码']
        result = pd.DataFrame([])

        for i_fund in range(0, len(all_data)):

            my_fund_code = all_data.index[i_fund]
            fund_pool_name = all_data.loc[my_fund_code, "考核分类"]
            fund_type = all_data.loc[my_fund_code, "类型2"]
            add_data = self.get_fund_index(fund_pool_name, my_fund_code, beg_date, end_date, fund_type)
            result = pd.concat([result, add_data], axis=0)

        result = pd.concat([all_data, result], axis=1)
        result = result.drop(labels=['代码', '考核标准', '收益名次', '仓位'], axis=1)
        file = os.path.join(self.data_path, "基金得分_%s_%s.xlsx" % (beg_date, end_date))

        excel = WriteExcel(file)
        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0.00%'
        num_format_pd.loc['format', ['信息比率']] = '0.00'
        num_format_pd.loc['format', ['现任经理管理开始日']] = '0'

        sheet_name = "%s_%s" % (beg_date, end_date)
        worksheet = excel.add_worksheet(sheet_name)
        excel.write_pandas(result, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="red", fillna=True)


if __name__ == '__main__':

    my_fund_code = "162201.OF"
    beg_date = "20180101"
    end_date = "20181231"
    fund_pool_name = "偏股混合型基金"
    return_type = "超额收益"
    my_index_code = "FTSE成长"
    new_fund_date = beg_date
    self = MfcManagerMoney()

    # self.cal_fund_index(fund_pool_name, my_index_code, my_fund_code, beg_date, end_date)
    # self.cal_all_fund_index(beg_date, end_date)
    self.get_all_fund_index(beg_date, end_date)
