from fund.fund_rank import *
from mfc.mfc_table import *
from quant.utility.write_excel import WriteExcel


def write_public_jl(end_date, save_path):

    # 参数
    ###########################################################################################
    fund_name = '泰达宏利集利'
    fund_code = '162210.OF'
    fund_type = "公募"

    benchmark_code = '885007.WI'
    benchmark_name = "混合债券二级基金指数"
    benchmark_code_2 = "000300.SH"
    benchmark_name_2 = "沪深300"
    benchmark_ratio = 0.95

    setup_date = '20160926'
    date_array = np.array([["2019年", '20190101', end_date, '20180930'],
                           ["2018年", "20180101", '20181231', "20170930"],
                           ["2017年", "20170101", '20171231', "20160930"],
                           ["2016年", setup_date, '20161231', setup_date],
                           ["成立(20160926)以来", setup_date, end_date, setup_date]])

    benchmark_array = np.array([["沪深300", "000300.SH"],
                                ["WIND全A", "881001.WI"],
                                ["中证全债", "H11001.CSI"],
                                ["二级债基金指数", '885007.WI']
                                ])

    from quant.fund.fund import Fund
    fund_pct = Fund().get_fund_factor("Repair_Nav_Pct")
    bench_pct = Fund().get_fund_factor("Fund_Bench_Pct") * 100

    # 准备文件
    ###########################################################################################
    file_name = os.path.join(save_path, "OutFile", fund_name + '.xlsx')
    sheet_name = fund_name
    excel = WriteExcel(file_name)
    worksheet = excel.add_worksheet(sheet_name)

    # 基金表现和排名
    ###########################################################################################
    performance_table = MfcTable().cal_summary_table(fund_name, fund_code, fund_type, date_array, benchmark_array)
    rank1 = FundRank().rank_fund_array2(fund_pct, bench_pct, fund_code, date_array, "wind", excess=False)
    performance_table = pd.concat([performance_table, rank1], axis=0)

    col_number = 1
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
    cum_return = fs.get_fund_and_bencnmark_cum_return_series(setup_date, end_date)

    benchmark_data = Index().get_index_factor(benchmark_code_2, attr=["CLOSE"])
    fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame(benchmark_data))
    cum_return2 = fs.get_bencnmark_cum_return_series(setup_date, end_date)

    # 写入基金和基准时间序列
    ###########################################################################################
    cum_return = pd.concat([cum_return, cum_return2], axis=1)
    cum_return.columns = [fund_name, benchmark_name, benchmark_name_2]
    cum_return = cum_return.dropna()

    num_format_pd = pd.DataFrame([], columns=cum_return.columns, index=['format'])
    num_format_pd.ix['format', :] = '0.00%'
    excel.write_pandas(cum_return, worksheet, begin_row_number=0, begin_col_number=col_number,
                       num_format_pd=num_format_pd, color="blue", fillna=True)

    # 基金和基准时间序列图
    ###########################################################################################

    chart_name = fund_name + "累计收益（成立以来）"
    series_name = [fund_name, benchmark_name, benchmark_name_2]
    insert_pos = 'B24'
    excel.line_chart_time_series_plot(worksheet, 0, col_number, cum_return,
                                      series_name, chart_name, insert_pos, sheet_name)
    excel.close()
    ###########################################################################################
    return True


if __name__ == '__main__':

    from quant.data.data import Data
    save_path = os.path.join(Data().primary_data_path, "mfcteda_data\performance")
    end_date = '20181130'
    write_public_jl(end_date, save_path)