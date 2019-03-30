from fund.fund_rank import *
from mfc.mfc_table import *
from quant.utility.write_excel import WriteExcel


def write_quant12(end_date, save_path):

    # 参数
    ###########################################################################################
    fund_name = '光大量化组合12号'
    fund_code = fund_name
    fund_type = "专户"

    benchmark_code = "000905.SH"
    benchmark_name = "中证500"

    setup_date = "20160714"
    date_array = np.array([["2019年", '20190101', end_date],
                           ["2018年", "20180101", '20181231'],
                           ["2017年", "20170101", '20171231'],
                           ["成立(20160714)至2016年末", setup_date, '20161231'],
                           ["成立(20160714)以来", setup_date, end_date]])

    benchmark_array = np.array([["沪深300", "000300.SH"],
                                ["中证500", "000905.SH"],
                                ["股票型基金", '885012.WI'],
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
    col_number = 1
    num_format_pd = pd.DataFrame([], columns=performance_table.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(performance_table, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="red", fillna=True)
    col_number = col_number + performance_table.shape[1] + 2

    # 写入增强基金表现
    ###########################################################################################
    performance_table = MfcTable().cal_summary_table_enhanced_fund(fund_name, fund_code,
                                                        fund_type, date_array, benchmark_code, benchmark_name)

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
    chart_name = fund_name + "累计超额收益（成立以来）"
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
    chart_name = fund_name + "累计收益（成立以来）"
    insert_pos = 'B26'
    excel.line_chart_time_series_plot(worksheet, 0, col_number, cum_return,
                                      series_name, chart_name, insert_pos, sheet_name)
    excel.close()
    ###########################################################################################
    return True


if __name__ == '__main__':

    from quant.data.data import Data
    save_path = os.path.join(Data().primary_data_path, "mfcteda_data\performance")
    end_date = '20181130'
    write_quant12(end_date, save_path)
