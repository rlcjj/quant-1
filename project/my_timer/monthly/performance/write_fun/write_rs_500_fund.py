from fund.fund_rank import *
from mfc.mfc_table import *
from quant.utility.write_excel import WriteExcel


def write_rs_500(end_date, save_path):

    ###########################################################################################
    fund_name = '建行中国人寿中证500管理计划'
    fund_code = fund_name
    fund_type = "专户"

    benchmark_code = "中证500全收益指数80%+固定收益1%"
    benchmark_name = "中证500全收益指数80%+固定收益1%"
    benchmark_code_2 = 'H00905.CSI'
    benchmark_name_2 = "中证500全收益指数"

    setup_date = '20151021'
    date_array = np.array([["2019年", '20190101', end_date],
                           ["2018年", "20180101", '20181231'],
                           ['20171110至今', "20171110", end_date],
                           ["2017年", "20170101", '20171231'],
                           ["2016年", "2016001", '20161231'],
                           ["2016年以来", "20160101", end_date],
                           ["成立以来", setup_date, end_date]])

    benchmark_array = np.array([["中证500全收益指数80%+固定收益1%", "中证500全收益指数80%+固定收益1%"],
                                ["中证500", "000905.SH"],
                                ["中证500全收益", 'H00905.CSI']])

    from quant.fund.fund import Fund
    fund_pct = Fund().get_fund_factor("Repair_Nav_Pct")
    bench_pct = Fund().get_fund_factor("Fund_Bench_Pct") * 100

    # 准备文件
    ###########################################################################################
    file_name = os.path.join(save_path, "OutFile", fund_name + '.xlsx')
    sheet_name = fund_name
    excel = WriteExcel(file_name)
    worksheet = excel.add_worksheet(sheet_name)

    # 写入增强基金表现 相对基准
    ###########################################################################################
    col_number = 1
    performance_table = MfcTable().cal_summary_table_enhanced_fund(fund_name, fund_code,
                                                                   fund_type, date_array, benchmark_code, benchmark_name)

    num_format_pd = pd.DataFrame([], columns=performance_table.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(performance_table, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="red", fillna=True)
    col_number = col_number + performance_table.shape[1] + 2

    # 写入增强基金表现  相对指数
    ###########################################################################################
    performance_table = MfcTable().cal_summary_table_enhanced_fund(fund_name, fund_code,
                                                                   fund_type, date_array,
                                                                   benchmark_code_2, benchmark_name_2)

    num_format_pd = pd.DataFrame([], columns=performance_table.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(performance_table, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="red", fillna=True)
    col_number = col_number + performance_table.shape[1] + 2

    # 读取基金和基准时间序列
    ###########################################################################################
    fund_data = MfcData().get_mfc_nav(fund_code, fund_name, fund_type)

    # 写入基金和基准收益时间序列 相对基准
    ###########################################################################################
    benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
    fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data))
    cum_return = fs.get_fund_and_bencnmark_cum_return_series(setup_date, end_date)

    num_format_pd = pd.DataFrame([], columns=cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 基金和基准收益图 相对基准
    ###########################################################################################
    series_name = [fund_name, benchmark_name]
    chart_name = fund_name + "相对基准（全收益80%+1%）累计超额收益（成立以来）"
    insert_pos = 'B16'
    excel.line_chart_time_series_plot(worksheet, 0, col_number, cum_return,
                                      series_name, chart_name, insert_pos, sheet_name)

    col_number = col_number + cum_return.shape[1] + 2

    daliy_return = fs.get_fund_benchmark_daily_return_series(setup_date, end_date)
    num_format_pd = pd.DataFrame([], columns=daliy_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(daliy_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    col_number = col_number + cum_return.shape[1] + 2

    # 写入基金和基准收益时间序列 相对基准
    ###########################################################################################
    benchmark_data = Index().get_index_factor(benchmark_code, attr=["CLOSE"])
    fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data))
    cum_return = fs.get_fund_and_bencnmark_cum_return_series("20160101", end_date)

    num_format_pd = pd.DataFrame([], columns=cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 基金和基准收益图 相对基准
    ###########################################################################################
    series_name = [fund_name, benchmark_name]
    chart_name = fund_name + "相对基准（全收益80%+1%）累计超额收益（2016年以来）"
    insert_pos = 'B32'
    excel.line_chart_time_series_plot(worksheet, 0, col_number, cum_return,
                                      series_name, chart_name, insert_pos, sheet_name)

    col_number = col_number + cum_return.shape[1] + 2

    # 写入基金和基准收益时间序列 相对指数
    ###########################################################################################
    benchmark_data = Index().get_index_factor(benchmark_code_2, attr=["CLOSE"])
    fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data))
    cum_return = fs.get_fund_and_bencnmark_cum_return_series(setup_date, end_date)

    num_format_pd = pd.DataFrame([], columns=cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 基金和基准收益图 相对指数
    ###########################################################################################
    series_name = [fund_name, benchmark_name_2]
    chart_name = fund_name + "相对500全收益指数累计超额收益（成立以来）"
    insert_pos = 'B48'
    excel.line_chart_time_series_plot(worksheet, 0, col_number, cum_return,
                                      series_name, chart_name, insert_pos, sheet_name)
    excel.close()
    ###########################################################################################
    return True

if __name__ == '__main__':

    from quant.data.data import Data
    save_path = os.path.join(Data().primary_data_path, "mfcteda_data\performance")
    end_date = '20181130'
    write_rs_500(end_date, save_path)