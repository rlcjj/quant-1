import pandas as pd
from datetime import datetime
from quant.stock.date import Date


class StockFactorOperate(object):

    """
    财报季度数据 转化成为 Daily数据 主要分成两个步骤

    # 0、财报数据类型
    #############################################################
    # 存量数据（如总资产）
    # 单季度流量（单季度利润）
    # 本年度前N个季度总流量（ROIC当年累计）
    # 有些数据只有年度数据 例如 TaxRate 直接填充即可

    # 1、先变成 TTM 数据（最近4个单季度之和）
    #############################################################
    # 存量数据 不用变
    # 单季度流量 前4个季度相加
    # 累计前N个季度化成TTM :本年度前N个季度总流量 本季度 + 去年年报 - 其年同期本季度
      只有半年报和年报有数值 为了不使得最后结果为nan 补充1、3季度数值为0 (例如EBITDA)

    # 2、对应成 Daily 数据
    #############################################################
    # 根据同一财报数据
    # 根据最近披露的财报日期

    """

    def __init__(self):
        pass

    @staticmethod
    def fill_year_data(data):

        """ 对于只有年度数据有数值的公司 直接填充即可 """

        data = data.T
        data = data.fillna(limit=3, method='pad')
        data = data.T
        return data

    @staticmethod
    def change_single_quarter_to_ttm_quarter(data):

        """ 单季度化成TTM 前4个季度相加 """

        data = data.T
        data = data.rolling(window=4).sum()
        data = data.dropna(how='all')
        data = data.T
        return data

    def change_cum_quarter_to_ttm_quarter(self, data, type="quarter"):

        """
        累计前N个季度化成TTM :本年度前N个季度总流量 本季度 + 去年年报 - 其年同期本季度
        只有半年报和年报有数值 为了不使得最后结果为nan 补充1、3季度数值为0 (例如EBITDA)
        """

        if type == "halfyear":

            report_3_9 = list(filter(lambda x: x[5] in ["3", "9"], list(data.columns)))
            data.ix[:, report_3_9] = data.ix[:, report_3_9].fillna(0.0)

        result = pd.DataFrame([], index=data.index, columns=data.columns)

        for i_date in range(5, len(data.columns)):

            cur_date = data.columns[i_date]
            cur_datetime = Date().change_to_datetime(cur_date)

            last_year_date = datetime(cur_datetime.year - 1, cur_datetime.month, cur_datetime.day)
            last_year_date = Date().change_to_str(last_year_date)
            last_year_annual_date = datetime(cur_datetime.year - 1, 12, 31)
            last_year_annual_date = Date().change_to_str(last_year_annual_date)
            result[cur_date] = data[cur_date] + data[last_year_annual_date] - data[last_year_date]

        return result

    @staticmethod
    def change_quarter_to_daily_with_report_date(data, beg_date=None, end_date=None):

        """ 将季度数据转化为日度数据 按照统一季报时间 """

        if beg_date is None:
            beg_date = data.columns[0]
        if end_date is None:
            end_date = datetime.today()

        date_series = Date().get_trade_date_series(beg_date, end_date)
        result = pd.DataFrame([], columns=date_series, index=data.index)

        for i_date in range(len(date_series)):

            date_daily = date_series[i_date]
            date_quarter = Date().get_last_stock_quarter_date(date_daily)

            try:
                result[date_daily] = data[date_quarter]
                print("Calculate Daily Data at %s with %s " % (date_daily, date_quarter))
            except Exception as e:
                print("Calculate Daily Data at %s with %s Error" % (date_daily, date_quarter))

        result = result.dropna(how='all')
        return result

    @staticmethod
    def change_quarter_to_daily_with_disclosure_date(data, report_data, beg_date=None, end_date=None):

        """ 将季度数据转化为日度数据 按照披露季报时间 """

        data = data.dropna(how='all')
        report_data = report_data.dropna(how='all')

        if beg_date is None:
            beg_date = data.columns[0]
        if end_date is None:
            end_date = datetime.today()

        date_series = Date().get_trade_date_series(beg_date, end_date)
        date_series = list(set(report_data.columns) & set(date_series))
        date_series.sort()

        for i_date in range(len(date_series)):

            date_daily = date_series[i_date]
            report_data_val = report_data[date_daily]
            report_data_val = report_data_val.dropna()
            report_date_list = list(set(list(report_data_val.values)))
            print("Calculate Daily Data at %s with %s " % (date_daily, report_date_list))

            for i_set in range(len(report_date_list)):

                report_date_number = report_date_list[i_set]
                report_date = str(int(report_date_number))
                stock_index = list((report_data_val[report_data_val == report_date_number]).index.values)
                stock_index = list(set(stock_index) & set(data.index))
                stock_index.sort()

                try:
                    data_ttm = data.ix[stock_index, report_date]
                    data_ttm = pd.DataFrame(data_ttm.values, columns=[date_daily], index=data_ttm.index)
                except Exception as e:
                    data_ttm = pd.DataFrame([], columns=[date_daily])

                if i_set == 0:
                    res = data_ttm
                else:
                    res_add = data_ttm
                    res = pd.concat([res, res_add], axis=0)
                    res = res.loc[~res.index.duplicated(keep='first'), :]
                    index_sort = list(set(res.index))
                    index_sort.sort()
                    res = res.loc[index_sort, :]

            if i_date == 0:
                result = res
            else:
                result = pd.concat([result, res], axis=1)
        return result


if __name__ == '__main__':

    from quant.stock.stock_factor_data import StockFactorData

    beg_date = "20180101"

    # 单季度TTM
    data = StockFactorData().read_factor_h5("OperatingIncomeTotal")
    report_data = StockFactorData().read_factor_h5("ReportDateDaily")
    data = StockFactorOperate().change_single_quarter_to_ttm_quarter(data)
    data = StockFactorOperate().change_quarter_to_daily_with_disclosure_date(data, report_data, beg_date='20161231')
    print(data)
    data = StockFactorOperate().change_quarter_to_daily_with_report_date(data, beg_date=beg_date)
    print(data)

    # 当年流量存量（季度数据和半年报数据）
    data = StockFactorData().read_factor_h5("EBIT")
    data = StockFactorOperate().change_cum_quarter_to_ttm_quarter(data, "quarter")
    print(data)

    data = StockFactorData().read_factor_h5("EBITDA")
    data = StockFactorOperate().change_cum_quarter_to_ttm_quarter(data, "halfyear")
    print(data)

    # 年报数据
    data = StockFactorData().read_factor_h5("TaxRate")
    data = StockFactorOperate().fill_year_data(data)
    print(data)
