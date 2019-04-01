import xlsxwriter
import pandas as pd
import numpy as np
from xlsxwriter.utility import *


class WriteExcel(object):

    """
    利用xlsxwriter在Excel写入数据
    # https://xlsxwriter.readthedocs.io/chart.html
    # https://xlsxwriter.readthedocs.io/
    """

    def __init__(self,
                 filename="C:\\Users\\doufucheng\\OneDrive\\Desktop\\读写EXCEL测试.xlsx"):

        self.filename = filename
        self.workbook = xlsxwriter.Workbook(filename)
        self.worksheet = ""

    @staticmethod
    def is_number(s):

        """
        判断是否是数字
        print(is_number('foo'))  # False
        print(is_number('-1.37'))  # True
        print(is_number('1e3'))  # True
        """

        try:
            float(s)
            return True
        except Exception as e:
            print(e)
        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except Exception as e:
            print(e)
        return False

    def add_worksheet(self, sheet_name):

        """ 添加Sheet页 """
        worksheet = self.workbook.add_worksheet(sheet_name)
        return worksheet

    def close(self):

        """ 关闭Excel """
        self.workbook.close()

    @staticmethod
    def change_row_col_to_cell(row, col):

        """ 根据行列数字转化成为Excel位置 0 0 --> A1 """
        cell = xl_rowcol_to_cell(row, col)
        return cell

    @staticmethod
    def change_pandas_index(df):

        """ 将Index变成首列 """
        df = df.copy()
        df["index"] = df.index
        col = list(range(len(df.columns) - 1))
        col.insert(0, len(df.columns) - 1)
        df = df.iloc[:, col]
        return df

    def write_pandas(self, data, worksheet, begin_row_number=0, begin_col_number=1,
                     num_format_pd=None, color="orange", fillna=True, need_index=True,
                     need_header=True, header_font_color="black",
                     cell_delta=0.4, cell_basic=3.5, cell_len_list=[]):

        """ dataframe写入Excel """

        if num_format_pd is None:
            num_format_pd = pd.DataFrame([], columns=data.columns, index=['format'])
            for i_col in range(len(data.columns)):
                col = data.columns[i_col]
                if (self.is_number(data.ix[0, col])) and (max(data.ix[:, col]) < 10):
                    num_format_pd.ix['format', col] = '0.00%'
                else:
                    num_format_pd.ix['format', :] = '0.00'

        if need_index:
            data = data.copy()
            data = self.change_pandas_index(data)
            num_format_pd = self.change_pandas_index(num_format_pd)
            num_format_pd.loc['format', 'index'] = ""

        if fillna:
            for i_col in range(len(data.columns)):
                col = data.columns[i_col]
                if type(data.ix[0, col]) in [np.int, np.float]:
                    data[col] = data[col].fillna(0.0)
                    data[col] = data[col].replace(-np.inf, 0)
                    data[col] = data[col].replace(np.inf, 0)
                else:
                    data[col] = data[col].fillna("")

        col_number = data.shape[1]

        # 表头格式
        format_header = self.workbook.add_format()
        format_header.set_font_size(9)
        format_header.set_font_name("微软雅黑")
        format_header.set_align('center')
        format_header.set_border(1)
        format_header.set_align('vcenter')
        format_header.set_shrink()
        format_header.set_bold(1)
        format_header.set_bg_color(color)
        format_header.set_font_color(header_font_color)

        # 写入行表头
        if need_header:
            worksheet.write_row(begin_row_number, begin_col_number, data.columns.values, format_header)
            begin_row_number += 1

        # 循环写入列
        for c in range(col_number):

            # 格式
            format_text = self.workbook.add_format()
            format_text.set_font_size(9)
            format_text.set_font_name("微软雅黑")
            format_text.set_align('center')
            format_text.set_align('vcenter')
            format_text.set_border(1)
            format_text.set_shrink()
            format_text.set_num_format(num_format_pd.iloc[0, c])

            worksheet.write_column(begin_row_number, begin_col_number + c, data.iloc[:, c].values, format_text)

            # 如果是字符串的话 考虑表格宽度
            if type(data.iloc[0, c]) == np.str:

                if len(cell_len_list) == 0:
                    try:
                        col_len = len(data.columns[c].encode('utf-8'))
                    except Exception as e:
                        col_len = 5
                    text_len = max(list(data.iloc[:, c].map(lambda x: len(str(x).encode('utf-8')))))
                    cell_len = cell_basic + cell_delta * max(col_len, text_len)

                else:
                    cell_len = cell_len_list[c]

                column = xl_col_to_name(begin_col_number + c)
                column = column + ":" + column
                worksheet.set_column(column, cell_len)
            else:

                if len(cell_len_list) == 0:
                    try:
                        col_len = len(data.columns[c].encode('utf-8'))
                    except Exception as e:
                        col_len = 5
                    cell_len = 3.5 + 0.4 * col_len
                else:
                    cell_len = cell_len_list[c]

                column = xl_col_to_name(begin_col_number + c)
                column = column + ":" + column
                worksheet.set_column(column, cell_len)

        return True

    def chart_columns_plot(self, worksheet, sheet_name, series_name, chart_name, insert_pos,
                           cat_beg, cat_end, val_beg_list, val_end_list):

        """ 在Excel表中柱形图的图表 """

        column_chart = self.workbook.add_chart({'type': 'column'})
        color_list = ["#000080", "#990000", "#336600"]

        for i in range(len(val_beg_list)):
            column_chart.add_series({
                'name': series_name[i],
                'categories': '=%s!%s:%s' % (sheet_name, cat_beg, cat_end),
                'values': '=%s!%s:$%s' % (sheet_name, val_beg_list[i], val_end_list[i]),
                'color': color_list[i],
                'fill': {
                    'color': color_list[i]
                },
            })

        column_chart.set_title({'name': chart_name,
                                'name_font': {
                                  'name': '微软雅黑', 'size': 12}
                              })
        worksheet.insert_chart(insert_pos, column_chart)


    def line_chart_time_series_plot(self, worksheet, row_number, col_number, data_pd,
                                     series_name, chart_name, insert_pos, sheet_name):

        """ 在Excel表中画时间序列的图表 """

        line_chart = self.workbook.add_chart({'type': 'line'})
        color_list = ["#000080", "#990000", "#336600"]
        print("len", len(data_pd.columns))

        for i in range(len(data_pd.columns)):

            line_chart.add_series(
                {'name': series_name[i],
                 'categories': [sheet_name, row_number + 1, col_number, row_number + len(data_pd), col_number],
                 'values': [sheet_name, row_number + 1, col_number + i + 1, row_number + len(data_pd), col_number + i + 1],
                 'line': {
                     'color': color_list[i],
                     'width': 1.5}
                 })

        #######################################################################################
        line_chart.set_style(11)
        line_chart.set_title({'name': chart_name,
                              'name_font': {
                                  'name': '微软雅黑', 'size': 12}
                              })

        #######################################################################################
        line_chart.set_x_axis({'num_font': {'name': '微软雅黑', 'size': 8, 'rotation': -45},
                               'minor_gridlines': {'visible': False},
                               'major_gridlines': {'visible': False},
                               'date_axis': True,
                               'num_format': 'dd/mm/yyyy',
                               'interval_tick': 10
                               })
        line_chart.set_y_axis({'num_font': {'name': '微软雅黑', 'size': 8},
                               'minor_gridlines': {'visible': False},
                               'major_gridlines': {'visible': False}
                               })
        #######################################################################################
        line_chart.set_legend({'position': 'bottom',
                               'font': {'name': '微软雅黑', 'size': 10},
                               })

        #######################################################################################
        worksheet.insert_chart(insert_pos, line_chart)
        #######################################################################################
        return True

    def line_chart_one_series_with_linear_plot(self, worksheet, row_number, col_number, data,
                                               chart_name, insert_pos, sheet_name):

        """ 在Excel表中画时间序列的图表（带有趋势线） """

        line_chart = self.workbook.add_chart({'type': 'line'})

        line_chart.add_series({
            'name': None,
            'categories': [sheet_name, row_number + 1, col_number, len(data) + row_number, col_number],
            'values': [sheet_name, row_number + 1, col_number + 1, len(data) + row_number, col_number + 1],
            'line': { 'width': 1.5},
            'trendline': {'type': 'linear',
                          'line': {
                              'color': '#990000',
                              'width': 0.5,
                              'dash_type': 'long_dash'}
                          }})
        line_chart.set_style(11)
        line_chart.set_title({'name': chart_name,
                              'name_font': {
                                  'name': '微软雅黑', 'size': 12}
                              })
        line_chart.set_x_axis({'num_font': {'name': '微软雅黑', 'size': 8, 'rotation': -45},
                               'minor_gridlines': {'visible': False},
                               'major_gridlines': {'visible': False},
                               'date_axis': True,
                               'num_format': 'dd/mm/yyyy',
                               'interval_tick': 10
                               })
        line_chart.set_y_axis({'num_font': {'name': '微软雅黑', 'size': 8},
                               'minor_gridlines': {'visible': False},
                               'major_gridlines': {'visible': False}
                               })
        line_chart.set_legend({'none': True})
        worksheet.insert_chart(insert_pos, line_chart)
        return True

    def rewtite_cell_format(self, worksheet, row, col, data, num_format="0.00", align="center"):

        """ 改变某个单元格的格式 """

        format_text = self.workbook.add_format()
        format_text.set_font_size(9)
        format_text.set_font_name("微软雅黑")
        format_text.set_align(align)
        format_text.set_align('vcenter')
        format_text.set_border(1)
        format_text.set_shrink()
        format_text.set_num_format(num_format)
        worksheet.write(row, col, data, format_text)

    def insert_merge_range(self, worksheet, first_row, first_col, last_row, last_col, data):

        """ 合并单元格 """

        format_text = self.workbook.add_format()
        format_text.set_font_size(9)
        format_text.set_font_name("微软雅黑")
        format_text.set_align('center')
        format_text.set_align('vcenter')
        format_text.set_border(1)
        format_text.set_shrink()
        format_text.set_num_format("0.00")
        worksheet.merge_range(first_row, first_col, last_row, last_col, data, format_text)

    def conditional_format(self, worksheet, first_row, frist_col, last_row, last_cl,
                           options=None, reverse=False):

        """
        条件格式
        https://xlsxwriter.readthedocs.io/working_with_conditional_formats.html
        options.type = 3_color_scale 为颜色不一样（默认）
        options.type = data_bar 为长度不一样
        """
        if options is None:
            options = {'type': '3_color_scale',
                       'min_color': "#82D900",
                       # 'mid_color': '#FFFFFF',
                       'max_color': "#FF0000",
                       'max_value': 1.6,
                       # 'mid_value': 0.0,
                       'min_value': - 1.6,
                       }
        if reverse:
            options = {'type': '3_color_scale',
                       'min_color': "#FF0000",
                       # 'mid_color': '#FFFFFF',
                       'max_color': "#82D900",
                       'max_value': 1.6,
                       # 'mid_value': 0.0,
                       'min_value': - 1.6,
                       }
            # options = {'type': 'data_bar'}

        worksheet.conditional_format(first_row, frist_col, last_row, last_cl, options)

    def generate_excel_sample(self):

        # 生成数据
        data = pd.DataFrame([], index=pd.date_range(start='20171231', end='20180430'))
        data.index = data.index.map(lambda x: x.strftime('%Y-%m-%d'))
        data['数字'] = np.random.random((data.shape[0], 1)) * 100
        data['Ratio'] = np.random.random((data.shape[0], 1))
        data['整数'] = list(map(int, np.random.random((data.shape[0], 1)) * 100))
        data['字符串'] = '中文测试'

        num_format_pd = pd.DataFrame([], columns=data.columns, index=['format'])
        num_format_pd.ix['format', :] = '0.00%'

        # write pandas
        sheet_name = "读写EXCEL测试"
        worksheet = self.add_worksheet(sheet_name)
        self.write_pandas(data, worksheet, begin_row_number=0, begin_col_number=1,
                           num_format_pd=num_format_pd, color="orange", fillna=True)

        # conditional_format
        self.chart_columns_plot(worksheet, sheet_name, series_name="序列标题", chart_name="柱形图标题", insert_pos="G2",
                                 cat_beg="B2", cat_end="B10", val_beg="D2", val_end="D10")

        self.conditional_format(worksheet, 1, 2, len(data), 3, None)
        self.conditional_format(worksheet, 1, 4, len(data), 4, {'type': 'data_bar'})

        # insert_merge_range
        notes = pd.DataFrame([], index=["基金整体=", "股票部分=", "股票超额=", "股票选股="], columns=["备注"])
        notes.loc["基金整体=", "备注"] = "基金整体=股票部分+新股部分+固收其他部分+日内交易问题+管理托管+交易印花"
        notes.loc["股票部分=", "备注"] = "股票部分=股票基准+股票超额"
        notes.loc["股票超额=", "备注"] = "股票超额=股票择时+股票选股"
        notes.loc["股票选股=", "备注"] = "股票选股=Alpha+Barra风格+Barra行业"

        begin_row_number = 1
        begin_col_number = 7
        end_col_number = 11

        for i in range(len(notes.index)):
            self.insert_merge_range(worksheet, begin_row_number + i, begin_col_number,
                                     begin_row_number + i, end_col_number, notes.loc[notes.index[i], "备注"])

        self.close()
        return self.filename, sheet_name


if __name__ == '__main__':

    self = WriteExcel()
    self.generate_excel_sample()

