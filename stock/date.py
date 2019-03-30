import os
import calendar
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from quant.data.data import Data


class Date(Data):

    """
    1、交易日数据（日、周、月、季、半年、年）的下载，获取
    load_trade_date_series
    load_trade_date_series_all
    get_trade_date_series
    get_trade_date_offset
    get_trade_date_month_end_day
    get_trade_date_last_month_end_day

    2、普通日数据（日、周、月、季、半年、年）的获取
    get_normal_date_series
    get_normal_date_offset
    get_normal_date_month_end_day
    get_normal_date_last_month_end_day
    get_normal_date_month_first_day

    3、交易日的格式转化（str, date, int）
    change_to_str
    change_to_str_hyphen
    change_to_datetime
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'date_data'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

        self.beg_date = "1989-12-31"
        self.file_dict = {"D": 'trade_date_daily.csv',
                          "W": 'trade_date_weekly.csv',
                          "2W": "trade_date_double_weekly.csv",
                          "M": 'trade_date_monthly.csv',
                          "Q": 'trade_date_quarterly.csv',
                          "S": 'trade_date_semiannually.csv',
                          "Y": 'trade_date_yearly.csv'}

    def load_trade_date_series(self, period="D"):

        """ 下载交易日日期序列 """

        from WindPy import w
        w.start()

        if period == "2W":
            today = datetime.today().strftime('%Y-%m-%d')
            data = w.tdays(self.beg_date, today, "Period=" + "W")
            data_pd = pd.DataFrame(data.Data, index=['Trade_Date'], columns=data.Times).T
            data_pd['Trade_Date'] = data_pd['Trade_Date'].map(lambda x: x.strftime('%Y%m%d'))
            data_pd.index = data_pd.index.map(lambda x: x.strftime('%Y%m%d'))
            double_loc = list(filter(lambda x: x % 2 == 0, list(range(len(data_pd)))))
            loc_index = data_pd.index[double_loc]
            data_pd = data_pd.loc[loc_index, :]
        else:
            today = datetime.today().strftime('%Y-%m-%d')
            data = w.tdays(self.beg_date, today, "Period=" + str(period))
            data_pd = pd.DataFrame(data.Data, index=['Trade_Date'], columns=data.Times).T
            data_pd['Trade_Date'] = data_pd['Trade_Date'].map(lambda x: x.strftime('%Y%m%d'))
            data_pd.index = data_pd.index.map(lambda x: x.strftime('%Y%m%d'))

        if period in ['Q', 'S', 'Y']:
            data_pd = data_pd.iloc[0:-1, :]

        out_file = os.path.join(self.data_path, self.file_dict[period])
        print("Loading Date %s " % out_file)
        data_pd.to_csv(out_file)

    def load_trade_date_series_all(self):

        """ 下载所有频率的交易日日期序列 """

        self.load_trade_date_series(period="D")
        self.load_trade_date_series(period="W")
        self.load_trade_date_series(period="2W")
        self.load_trade_date_series(period="M")
        self.load_trade_date_series(period="Q")
        self.load_trade_date_series(period="S")
        self.load_trade_date_series(period="Y")

    def get_trade_date_series(self,
                              beg_date="1989-12-31",
                              end_date=datetime.today().strftime("%Y%m%d"),
                              period='D'):

        """ 得到交易日日期序列 """

        beg_date = self.change_to_str(beg_date)
        end_date = self.change_to_str(end_date)

        file = os.path.join(self.data_path, self.file_dict[period])
        date_data = pd.read_csv(file, index_col=[0], encoding='gbk')
        date_data['Trade_Date'] = date_data['Trade_Date'].map(str)
        date_data.index = date_data.index.map(str)
        date_series = list(date_data.loc[beg_date:end_date, "Trade_Date"].values)
        date_series.sort()
        # if period in ['Q', 'S', 'Y']:
        #     date_series = date_series[0:-1]
        # else:
        #     pass
        return date_series

    def get_trade_date_offset(self,
                              end_date=datetime.today().strftime("%Y%m%d"),
                              offset_num=0):

        """ 得到某个交易日的前后N个交易日的日期 """

        all_date = self.get_trade_date_series()
        all_date = pd.DataFrame(all_date, index=all_date)
        end_date = self.change_to_str(end_date)
        data_end_date = all_date.index[-1]
        if data_end_date < end_date:
            print(" The Input Date is Bigger Than Current Date.")
            return data_end_date

        data = all_date.ix[:end_date, :]
        last_trade_date = data.index[-1]
        last_trade_date_index = list(data.index).index(last_trade_date)
        offset_trade_date_index = last_trade_date_index + offset_num

        if offset_trade_date_index < 0:
            print(" The Offset Trade Date Index Smaller Than Zero.")
            offset_trade_date = all_date.index[0]
        elif offset_trade_date_index >= len(all_date):
            print(" The Offset Trade Date Index Bigger Than Current Date.")
            offset_trade_date = all_date.index[-1]
        else:
            offset_trade_date = all_date.index[offset_trade_date_index]
        return offset_trade_date

    def get_trade_date_month_end_day(self, date):

        """ 得到某个月最后一个交易日期 """

        date = self.get_normal_date_month_end_day(date)
        date_series = self.get_trade_date_series()
        date_series = pd.DataFrame(date_series, index=date_series)
        date_series = date_series.ix[:date, :]
        last_date = date_series.index[-1]
        return last_date

    def get_trade_date_last_month_end_day(self, date):

        """ 得到上个月最后一个交易日期 """

        date = self.get_normal_date_last_month_end_day(date)
        date_series = self.get_trade_date_series()
        date_series = pd.DataFrame(date_series, index=date_series)
        date_series = date_series.ix[:date, :]
        last_date = date_series.index[-1]
        return last_date

    def get_normal_date_series(self,
                              beg_date="1989-12-31",
                              end_date=datetime.today().strftime("%Y%m%d"),
                              period='D'):

        """ 得到普通日期序列 """

        beg_date = self.change_to_str(beg_date)
        end_date = self.change_to_str(end_date)

        if period in ['D']:
            date_series = pd.date_range(start=beg_date, end=end_date)
            date_series = list(date_series.map(lambda x: x.strftime('%Y%m%d')))
        # elif period in ['W', '2W']:
        #     date_series = self.get_trade_date_series(beg_date, end_date, period=period)
        elif period in ['M', 'Q', 'S', 'Y']:
            date_series_trade = self.get_trade_date_series(beg_date, end_date, period=period)
            date_series = list(map(self.get_normal_date_month_end_day, date_series_trade))
        else:
            date_series = None

        return date_series

    def get_normal_date_offset(self,
                               end_date=datetime.today().strftime("%Y%m%d"),
                               offset_num=0):

        """ 得到某个普通日的前后N个交易日的日期 """

        end_date = self.change_to_datetime(end_date)
        end_date = end_date + timedelta(offset_num)
        date_str = self.change_to_str(end_date)
        return date_str

    def get_normal_date_month_first_day(self, date):

        """ 得到当月第一个普通日 """

        date = self.change_to_datetime(date)
        date_str = self.change_to_str(datetime(date.year, date.month, 1))
        return date_str

    def get_normal_date_last_month_end_day(self, date):

        """ 得到上月最后一个普通日 """

        date = datetime.strptime(self.get_normal_date_month_first_day(date), '%Y%m%d') - timedelta(days=1)
        date_str = self.change_to_str(date)
        return date_str

    def get_normal_date_last_month_first_day(self, date):

        """ 得到上月第一个普通日 """

        last_month_end_date = self.get_normal_date_last_month_end_day(date)
        last_month_end_date = self.change_to_datetime(last_month_end_date)

        date = datetime(year=last_month_end_date.year, month=last_month_end_date.month, day=1)
        date_str = self.change_to_str(date)
        return date_str

    def get_normal_date_month_end_day(self, date):

        """ 得到当月最后一个普通日 """

        date = self.change_to_datetime(date)
        days = calendar.monthrange(date.year, date.month)[1]
        date_str = self.change_to_str(datetime(date.year, date.month, days))
        return date_str

    def get_stcok_same_publish_date(self, date):

        """ 得到股票统一财报披露日 """

        date = self.change_to_str(date)
        month = self.change_to_datetime(date).month
        year = self.change_to_datetime(date).year

        if month == 3:
            date_str = self.change_to_str(datetime(year, 5, 1))
        elif month == 6:
            date_str = self.change_to_str(datetime(year, 9, 1))
        elif month == 9:
            date_str = self.change_to_str(datetime(year, 11, 1))
        elif month == 12:
            date_str = self.change_to_str(datetime(year+1, 4, 30))
            date_str = self.get_trade_date_offset(date_str, 0)
        else:
            date_str = ""

        return date_str

    def get_last_fund_quarter_date(self, date):

        """ 获取最近的一个季报日 基金季报是15个工作日 """

        date_series = self.get_normal_date_series(period="Q")
        quarter_date = self.get_trade_date_offset(date, -15)
        date_series = pd.DataFrame(date_series, index=date_series)

        date_series = date_series[date_series <= quarter_date]
        date_series = date_series.dropna()

        result_date = date_series.index[-1]
        return result_date

    def get_last_fund_halfyear_date(self, date):

        """
        获取最近的一个半年报日
        基金半年报是60日(注意不是工作日,就是2个月)
        基金年报是90日(注意不是工作日,就是3个月)
        """

        date_series = Date().get_normal_date_series(period="S")
        month = self.change_to_datetime(date).month

        if month in [1, 2, 3, 4, 5, 6]:
            quarter_date = self.get_normal_date_offset(date, -90)
        else:
            quarter_date = self.get_normal_date_offset(date, -60)

        date_series = pd.DataFrame(date_series, index=date_series)
        date_series = date_series[date_series <= quarter_date]
        date_series = date_series.dropna()

        result_date = date_series.index[-1]
        return result_date

    def get_last_stock_year_report_date(self, date):

        """ 得到股票最近的年报日期 """

        cur_date = self.change_to_datetime(date)
        year = cur_date.year
        month = cur_date.month

        if month in [1, 2, 3, 4]:
            return datetime(year - 2, 12, 31).strftime("%Y%m%d")
        else:
            return datetime(year - 1, 12, 31).strftime("%Y%m%d")

    def get_last_stock_quarter_date(self, date):

        """ 得到股票最近的上个财报日期 """

        cur_date = self.change_to_datetime(date)
        year = cur_date.year
        month = cur_date.month

        if month in [1, 2, 3, 4]:
            return datetime(year - 1, 9, 30).strftime("%Y%m%d")
        elif month in [5, 6, 7, 8]:
            return datetime(year, 3, 31).strftime("%Y%m%d")
        elif month in [9, 10]:
            return datetime(year, 6, 30).strftime("%Y%m%d")
        elif month in [11, 12]:
            return datetime(year, 9, 30).strftime("%Y%m%d")
        else:
            print('month number is error')
            return None

    @staticmethod
    def change_to_str(date):

        """ 转化为 %Y%m%d 字符串样式 """

        if type(date) in [np.int, np.float]:
            date_int = str(int(date))
            return date_int

        try:
            date_int = datetime.strftime(date, '%Y%m%d')
            return date_int
        except Exception as e:
            pass

        try:
            date_int = datetime.strptime(str(date), '%Y-%m-%d').strftime('%Y%m%d')
            return date_int
        except Exception as e:
            pass

        try:
            date_int = datetime.strptime(str(date), '%Y/%m/%d').strftime('%Y%m%d')
            return date_int
        except Exception as e:
            pass

        return str(date)

    def get_trade_date_diff(self, beg_date, end_date):

        """ 得到交易日之间的间隔天数 """

        beg_date = self.get_trade_date_offset(beg_date, 0)
        end_date = self.get_trade_date_offset(end_date, 0)

        date_series = self.get_trade_date_series(beg_date, end_date)
        diff_number = date_series.index(end_date) - date_series.index(beg_date)
        return diff_number

    def change_to_str_hyphen(self, date):

        """ 转化为 %Y-%m-%d 字符串样式 """

        date = self.change_to_str(date)
        date = datetime.strptime(str(date), '%Y%m%d').strftime('%Y-%m-%d')
        return date

    def change_to_datetime(self, date):

        """ 转化为 datetime 样式 """

        date = self.change_to_str(date)
        date = datetime.strptime(str(date), '%Y%m%d')
        return date

    def get_period_number_for_year(self, period="W"):

        """ 1年之内有多少个星期、月等等 """

        dict = {"D": 250, "W": 50, "2W": 25, "M": 12}

        return dict[period]


if __name__ == '__main__':

    self = Date()

    """ 下载日期 """
    # self.load_trade_date_series_all()
    # self.load_trade_date_series("W")
    # self.load_trade_date_series("2W")

    """ 取得日期 """
    # print(self.get_trade_date_series('2007-12-31', datetime(2018, 12, 31), 'S'))
    # print(self.get_trade_date_offset(20180707, -20))
    # print(self.get_trade_date_last_month_end_day(20180707))
    # print(self.get_trade_date_month_end_day(20180707))
    # print(self.get_trade_date_offset(end_date="20040116", offset_num=10))

    # print(self.get_normal_date_series('2010/3/3', 20100306))
    # print(self.get_normal_date_last_month_end_day('2010/1/3'))
    # print(self.get_normal_date_month_end_day('2010/1/3'))
    # print(self.get_normal_date_month_first_day('2010/3/3'))

    """ 更改日期格式 """
    # print(self.change_to_str('2017-08-08'))
    # print(self.change_to_str('2017/8/8'))
    # print(self.change_to_str(20170808))
    # print(self.change_to_str('20170808'))
    # print(self.change_to_str(datetime(2017, 8, 8)))
    # print(self.get_last_fund_quarter_date("20180702"))

    """ 其他"""
    print(self.get_period_number_for_year("W"))
    print(self.get_period_number_for_year("M"))

