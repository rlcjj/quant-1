from datetime import datetime

from quant.utility.write_excel import WriteExcel

from data.mfc.mfc_table import *


def write_public_zz500(end_date, save_path):

    # 参数
    ###########################################################################################
    fund_name = '泰达宏利中证500'
    fund_code = '162216.OF'
    fund_type = "公募"

    benchmark_code = '000905.SH'
    benchmark_name = '中证500'
    benchmark_ratio = 0.95

    setup_date = '20141013'
    today = datetime.strptime(end_date, "%Y%m%d")
    before_1y = datetime(year=today.year - 1, month=today.month, day=today.day).strftime("%Y%m%d")
    before_2y = datetime(year=today.year - 2, month=today.month, day=today.day).strftime("%Y%m%d")
    before_3y = datetime(year=today.year - 3, month=today.month, day=today.day).strftime("%Y%m%d")

    date_array = np.array([["2019年", '20190101', end_date, '20180930'],
                           ["2018年", "20180101", '20181231', "20170930"],
                           ["2017年", "20170101", '20171231', "20160930"],
                           ["2016年", "20160101", "20161231", "20150930"],
                           ["2015年", "20150101", "20151231", "20150101"],
                           ["管理(20141003)以来", setup_date, end_date, setup_date],
                           ["2015年以来", "20150101", end_date, setup_date],
                           ["过去1年", before_1y, end_date, before_1y],
                           ["过去2年", before_2y, end_date, before_2y],
                           ["过去3年", before_3y, end_date, before_3y],
                           ])

    benchmark_array = np.array([["沪深300", "000300.SH"],
                                ["中证500", "000905.SH"],
                                ["WIND全A", '881001.WI']])

    from quant.fund.fund import Fund
    fund_pct = Fund().get_fund_factor("Repair_Nav_Pct")
    bench_pct = Fund().get_fund_factor("Fund_Bench_Pct") * 100

    # 准备文件
    ###########################################################################################
    file_name = os.path.join(save_path, "OutFile", fund_name + '.xlsx')
    sheet_name = fund_name
    excel = WriteExcel(file_name)
    worksheet = excel.add_worksheet(sheet_name)

    # 写入基金表现 和基金排名
    ###########################################################################################
    performance_table = MfcTable().cal_summary_table_sample(fund_name, fund_code, fund_type, date_array, benchmark_array)
    rank0 = FundRank().rank_fund_array2(fund_pct, bench_pct, fund_code, date_array, "wind", excess=False)
    rank1 = FundRank().rank_fund_array2(fund_pct, bench_pct, fund_code, date_array, "被动指数型基金", excess=True)
    rank2 = FundRank().rank_fund_array2(fund_pct, bench_pct, fund_code, date_array, "指数型基金", excess=True)
    rank3 = FundRank().rank_fund_array2(fund_pct, bench_pct, fund_code, date_array, "中证500基金", excess=True)
    performance_table = pd.concat([performance_table, rank0, rank1, rank2, rank3], axis=0)

    col_number = 1
    num_format_pd = pd.DataFrame([], columns=performance_table.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(performance_table, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="red", fillna=True)
    col_number = col_number + performance_table.shape[1] + 2

    # 写入增强基金表现
    ###########################################################################################
    performance_table = MfcTable().cal_summary_table_enhanced_fund(fund_name, fund_code,
                                                                   fund_type, date_array,
                                                                   benchmark_code, benchmark_name, benchmark_ratio)

    num_format_pd = pd.DataFrame([], columns=performance_table.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(performance_table, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="red", fillna=True)
    col_number = col_number + performance_table.shape[1] + 2

    # 读取基金和基准时间序列
    ###########################################################################################
    fund_data = MfcData().get_mfc_nav(fund_code, fund_name, fund_type)

    benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
    fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data))

    # 写入超额收益时间序列
    ###########################################################################################
    excess_cum_return = fs.get_cum_excess_return_series(setup_date, end_date)

    num_format_pd = pd.DataFrame([], columns=excess_cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(excess_cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 超额收益图
    ###########################################################################################
    chart_name = fund_name + "累计超额收益（20141013管理以来）"
    insert_pos = 'B12'
    excel.line_chart_one_series_with_linear_plot(worksheet, 0, col_number, excess_cum_return,
                                                 chart_name, insert_pos, sheet_name)

    col_number = col_number + excess_cum_return.shape[1] + 2

    # 写入基金收益时间序列
    ###########################################################################################
    benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
    fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data))
    cum_return = fs.get_fund_and_bencnmark_cum_return_series(setup_date, end_date)

    num_format_pd = pd.DataFrame([], columns=cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 写入基金收益时间序列图
    ############################################################################################
    series_name = [fund_name, benchmark_name]
    chart_name = fund_name + "累计收益（20141013管理以来）"
    insert_pos = 'B26'
    excel.line_chart_time_series_plot(worksheet, 0, col_number, cum_return,
                                      series_name, chart_name, insert_pos, sheet_name)
    # 写入超额收益时间序列
    ###########################################################################################
    excess_cum_return = fs.get_cum_excess_return_series("20150101", end_date)

    num_format_pd = pd.DataFrame([], columns=excess_cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(excess_cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 超额收益图
    ###########################################################################################
    chart_name = fund_name + "累计超额收益（2015年以来）"
    insert_pos = 'B40'
    excel.line_chart_one_series_with_linear_plot(worksheet, 0, col_number, excess_cum_return,
                                                 chart_name, insert_pos, sheet_name)

    col_number = col_number + excess_cum_return.shape[1] + 2

    # 写入基金收益时间序列
    ###########################################################################################
    benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
    fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data))
    cum_return = fs.get_fund_and_bencnmark_cum_return_series("20150101", end_date)

    num_format_pd = pd.DataFrame([], columns=cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 写入基金收益时间序列图
    ############################################################################################
    series_name = [fund_name, benchmark_name]
    chart_name = fund_name + "累计收益（2015年以来）"
    insert_pos = 'B55'
    excel.line_chart_time_series_plot(worksheet, 0, col_number, cum_return,
                                      series_name, chart_name, insert_pos, sheet_name)

    excel.close()
    ###########################################################################################
    return True


if __name__ == '__main__':

    from quant.data.data import Data
    save_path = os.path.join(Data().primary_data_path, "mfcteda_data\performance")
    end_date = '20181130'
    write_public_zz500(end_date, save_path)
