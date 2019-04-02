import os
import shutil
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.mfc.mfc_data import MfcData

from quant.project.multi_factor.alpha_model.exposure.alpha_factor_bp import AlphaBP
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_roe import AlphaROE
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_income_yoy import AlphaIncomeYoY
from quant.project.multi_factor.alpha_model.exposure.alpha_factor_profit_yoy import AlphaProfitYoY

from quant.project.my_timer.monthly.fund_advertise_report.inside_active_report import InsideActiveReport
from quant.project.my_timer.monthly.fund_advertise_report.inside_passive_report import InsidePassiveReport
from quant.project.my_timer.monthly.fund_advertise_report.institution_active_report import InstitutionActiveReport
from quant.project.my_timer.monthly.fund_advertise_report.institution_passive_report import InstitutionPassiveReport


class AdvertiseReport(Data):

    """
    每日生成基金宣传单页
    每月手动发送给个各个部门领导同事
    """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'mfcteda_data\fund_report\advertise_report'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)
        self.web_path = r'\\10.1.0.7\rd\※※金融工程部数据产品※※\# 基金季报月报\基金宣传单页'
        self.param_file = os.path.join(self.data_path, r"参数", '宣传单页参数表.xlsx')
        self.web_param_file = os.path.join(self.web_path, r"参数", '宣传单页参数表.xlsx')
        print(self.param_file)
        print(self.web_param_file)

    @staticmethod
    def update_data(date):

        """更新数据"""

        # 更新日期
        beg_date = Date().get_trade_date_offset(date, -5)
        end_date = date

        # 更新因子数据（原始和alpha）
        Stock().load_h5_primary_factor()

        AlphaBP().cal_factor_exposure(beg_date, end_date)
        AlphaROE().cal_factor_exposure(beg_date, end_date)
        AlphaProfitYoY().cal_factor_exposure(beg_date, end_date)
        AlphaIncomeYoY().cal_factor_exposure(beg_date, end_date)

        # 更新基金净值 和 持仓数据 指数价格数据
        # Fund().load_fund_holding_all("19991231", datetime.today())
        MfcData().load_mfc_public_fund_nav()
        update_end_date = datetime.today().strftime("%Y%m%d")
        update_beg_date = Date().get_trade_date_offset(update_end_date, -5)

        Index().load_index_factor(index_code='H00985.CSI', beg_date=update_beg_date, end_date=update_end_date)
        Index().load_index_factor(index_code="885001.WI", beg_date=update_beg_date, end_date=update_end_date)
        Index().load_index_factor(index_code="000300.SH", beg_date=update_beg_date, end_date=update_end_date)
        Index().load_index_factor(index_code="000905.SH", beg_date=update_beg_date, end_date=update_end_date)

    def generate_excel_institution(self, date):

        """ 生成 Excel 机构版 """

        # 参数表
        param = pd.read_excel(self.param_file, index_col=[0])
        param = param.T
        comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                                 ["中证全指全收益", 'H00985.CSI']]

        # 机构-主动量化
        param_active = param[param['基金类型'] == '主动量化']

        for i in range(0, len(param_active)):

            fund_code = param_active.index[i]
            fund_name = param_active.loc[fund_code, "基金名称"]
            print(fund_name, "excel", '机构')
            fund_strategy = param_active.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
            fund_manager = param_active.loc[fund_code, "基金经理"]
            report = InstitutionActiveReport()
            report.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                                  comparsion_bench_list, date, fund_manager)
            report.write_excel()

        # 机构-指数
        param_passive = param[param['基金类型'] == '指数']

        for i in range(0, len(param_passive)):

            fund_code = param_passive.index[i]
            fund_name = param_passive.loc[fund_code, "基金名称"]
            print(fund_name, "excel", '机构')
            bench_code = param_passive.loc[fund_code, "指数代码"]
            fund_strategy = param_passive.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
            fund_manager = param_passive.loc[fund_code, "基金经理"]

            report = InstitutionPassiveReport()
            report.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                                  bench_code, date, fund_manager)
            report.write_excel()

    def generate_excel_inside(self, date):

        """ 生成Excel 内部版 """

        param = pd.read_excel(self.param_file, index_col=[0])
        param = param.T
        comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                                 ["中证全指全收益", 'H00985.CSI']]

        # 内部-主动量化
        param_active = param[param['基金类型'] == '主动量化']

        if date < "20190109":
            param_active = param_active.drop("162212.OF")

        for i in range(0, len(param_active)):

            fund_code = param_active.index[i]
            fund_name = param_active.loc[fund_code, "基金名称"]
            print(fund_name, "excel", 'inside')
            inside_fund_name = param_active.loc[fund_code, "内部名称"]
            fund_strategy = param_active.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
            fund_manager = param_active.loc[fund_code, "基金经理"]
            report = InsideActiveReport()
            report.get_input_data(fund_code, fund_name, inside_fund_name,
                                  fund_strategy, asset_allocation_strategy,
                                  comparsion_bench_list, date, fund_manager)
            report.write_excel()

        # 内部-指数
        param_passive = param[param['基金类型'] == '指数']
        for i in range(0, len(param_passive)):
            fund_code = param_passive.index[i]
            fund_name = param_passive.loc[fund_code, "基金名称"]
            print(fund_name, "excel", '内部版')
            inside_fund_name = param_passive.loc[fund_code, "内部名称"]
            bench_code = param_passive.loc[fund_code, "指数代码"]
            fund_strategy = param_passive.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
            fund_manager = param_passive.loc[fund_code, "基金经理"]
            report = InsidePassiveReport()
            report.get_input_data(fund_code, fund_name, inside_fund_name,
                                fund_strategy, asset_allocation_strategy,
                                bench_code, date, fund_manager)
            report.write_excel()

    def generate_word_inside(self, date):

        """ 生成word 内部版 """

        param = pd.read_excel(self.param_file, index_col=[0])
        param = param.T
        comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                                 ["中证全指全收益", 'H00985.CSI']]

        # 内部-主动量化
        param_active = param[param['基金类型'] == '主动量化']

        if date < "20190109":
            param_active = param_active.drop("162212.OF")

        for i in range(0, len(param_active)):
            fund_code = param_active.index[i]
            fund_name = param_active.loc[fund_code, "基金名称"]
            print(fund_name, "excel", 'inside')
            inside_fund_name = param_active.loc[fund_code, "内部名称"]
            fund_strategy = param_active.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
            fund_manager = param_active.loc[fund_code, "基金经理"]
            report = InsideActiveReport()
            report.get_input_data(fund_code, fund_name, inside_fund_name,
                                fund_strategy, asset_allocation_strategy,
                                comparsion_bench_list, date, fund_manager)
            report.write_word()

        # 内部-指数
        param_passive = param[param['基金类型'] == '指数']
        for i in range(0, len(param_passive)):
            fund_code = param_passive.index[i]
            fund_name = param_passive.loc[fund_code, "基金名称"]
            print(fund_name, "word", '内部版')
            inside_fund_name = param_passive.loc[fund_code, "内部名称"]
            bench_code = param_passive.loc[fund_code, "指数代码"]
            fund_strategy = param_passive.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
            fund_manager = param_passive.loc[fund_code, "基金经理"]
            report = InsidePassiveReport()
            report.get_input_data(fund_code, fund_name, inside_fund_name,
                                fund_strategy, asset_allocation_strategy,
                                bench_code, date, fund_manager)
            report.write_word()

    def generate_word_institution(self, date):

        """ 生成Word 机构版"""

        # 参数表
        param = pd.read_excel(self.param_file, index_col=[0])
        param = param.T
        comparsion_bench_list = [["偏股混合型基金", '885001.WI'],
                                 ["中证全指全收益", 'H00985.CSI']]

        # 机构-主动量化
        param_active = param[param['基金类型'] == '主动量化']
        for i in range(0, len(param_active)):
            fund_code = param_active.index[i]
            fund_name = param_active.loc[fund_code, "基金名称"]
            print(fund_name, "word", "机构版")
            fund_strategy = param_active.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_active.loc[fund_code, "配置策略"]
            fund_manager = param_active.loc[fund_code, "基金经理"]

            report = InstitutionActiveReport()
            report.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                                  comparsion_bench_list, date, fund_manager)
            report.write_word()

        # 机构-指数
        param_passive = param[param['基金类型'] == '指数']
        for i in range(0, len(param_passive)):

            fund_code = param_passive.index[i]
            fund_name = param_passive.loc[fund_code, "基金名称"]
            print(fund_name, "word")
            bench_code = param_passive.loc[fund_code, "指数代码"]
            fund_strategy = param_passive.loc[fund_code, "投资策略"]
            asset_allocation_strategy = param_passive.loc[fund_code, "配置策略"]
            fund_manager = param_passive.loc[fund_code, "基金经理"]

            report = InstitutionPassiveReport()
            report.get_input_data(fund_code, fund_name, fund_strategy, asset_allocation_strategy,
                                  bench_code, date, fund_manager)
            report.write_word()

    def copyfile(self, date):

        """
        机构版文件上传网盘
        内部板文件上传网盘
        """

        trade_day = Date().get_trade_date_offset(date, 0)
        my_path = InsidePassiveReport().data_path
        my_sub_path = os.path.join(my_path, trade_day)

        param = pd.read_excel(self.param_file, index_col=[0])
        param = param.T

        web_sub_path = os.path.join(self.web_path, "机构版")

        for i in range(0, len(param)):
            fund_code = param.index[i]
            fund_name = param.loc[fund_code, "基金名称"]
            print(fund_name)
            file = "机构_%s.docx" % fund_name
            web_file = os.path.join(web_sub_path, file)
            my_file = os.path.join(my_sub_path, file)
            shutil.copyfile(my_file, web_file)
            file = "机构_%s.xlsx" % fund_name
            web_file = os.path.join(web_sub_path, file)
            my_file = os.path.join(my_sub_path, file)
            shutil.copyfile(my_file, web_file)

        web_sub_path = os.path.join(self.web_path, "内部版")

        for i in range(0, len(param)):
            fund_code = param.index[i]
            fund_name = param.loc[fund_code, "基金名称"]
            print(fund_name)
            file = "内部_%s.docx" % fund_name
            web_file = os.path.join(web_sub_path, file)
            my_file = os.path.join(my_sub_path, file)
            shutil.copyfile(my_file, web_file)
            file = "内部_%s.xlsx" % fund_name
            web_file = os.path.join(web_sub_path, file)
            my_file = os.path.join(my_sub_path, file)
            shutil.copyfile(my_file, web_file)

    def load_param(self):

        """ 下载参数文件 """
        shutil.copyfile(self.web_param_file, self.param_file)


if __name__ == '__main__':

    date = "20190329"
    today = datetime.today().strftime("%Y%m%d")
    date = Date().get_trade_date_offset(today, -1)

    self = AdvertiseReport()
    self.load_param()
    self.update_data(date)
    self.generate_excel_institution(date)
    self.generate_word_institution(date)
    self.generate_excel_inside(date)
    self.generate_word_inside(date)
    self.copyfile(date)

    # 每天自动更新
    # 每月 手动发送邮件给各部门的同事
