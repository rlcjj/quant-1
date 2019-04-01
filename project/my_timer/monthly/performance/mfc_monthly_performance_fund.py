from quant.project.my_timer.monthly.performance.write_fun.write_public_cfdp_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_chengzhang_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_fengxian_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_fxwy_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_gaige_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_ganggutong_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_hlxf_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_hs300_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_hyjx_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_jili_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_lcjz_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_lianghua_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_lxzxp_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_nixiang_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_pinzhi_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_qifu_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_ruixuan_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_ruizhi_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_sxqy_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_szyx_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_tongshun_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_wending_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_xlyx_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_xsl_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_yjqd_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_zhouqi_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_zxjy_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_zz500_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_public_zz500_fund_adjust import *
from quant.project.my_timer.monthly.performance.write_fun.write_quant_11_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_quant_12_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_quant_6_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_rs_duocelue_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_rs_gushou_fund import *
from quant.project.my_timer.monthly.performance.write_fun.write_zlhl_2018_fund import *


class MfcMonthlyPerformanceFund(Data):

    """ 泰达宏利金融工程部基金每个月的基金业绩表现 """

    def __init__(self):

        Data.__init__(self)
        self.data_path = os.path.join(self.primary_data_path, 'mfcteda_data\performance')

    def update_data(self):

        """ 更新计算基金业绩所需要的数据 """

        # 下载公募复权净值和计算专户复权净值
        ##########################################################################################
        MfcData().load_mfc_public_fund_nav()
        MfcData().load_mfc_fund_div()
        MfcData().cal_mfc_private_fund_nav_all()
        self.get_zz500_adjust()
        today = datetime.today()

        # 下载指数价格数据
        ##########################################################################################
        beg_date = Date().get_trade_date_offset(today, -30)
        Index().load_index_factor_all(beg_date=beg_date, end_date=today)

        # 合成指数价格数据
        ##########################################################################################
        index_code = "H00905.CSI"
        index_ratio = 0.8
        fix_return = 0.01
        make_index_name = "中证500全收益指数80%+固定收益1%"
        Index().make_index_with_fixed(fix_return, index_ratio, index_code, make_index_name)

        fix_return = 0.08
        index_ratio = 0.0
        index_code = 'H00905.CSI'
        make_index_name = '固定收益年化8%'
        Index().make_index_with_fixed(fix_return, index_ratio, index_code, make_index_name)

        fix_return = 0.00
        index_ratio = 0.6
        index_code = 'H00905.CSI'
        make_index_name = "中证500全收益指数60%"
        Index().make_index_with_fixed(fix_return, index_ratio, index_code, make_index_name)

        fix_return = 0.0625
        index_ratio = 0.0
        index_code = 'H00905.CSI'
        make_index_name = "固定收益年化6.52%"
        Index().make_index_with_fixed(fix_return, index_ratio, index_code, make_index_name)

        fix_return = 0.00
        index_ratio = 0.3
        index_code = 'H00905.CSI'
        make_index_name = "中证500全收益指数30%"
        Index().make_index_with_fixed(fix_return, index_ratio, index_code, make_index_name)

        # 基金净值数据
        ##########################################################################################
        Fund().load_fund_factor("Repair_Nav", "20180101", today)
        Fund().load_fund_factor("Repair_Nav_Pct", "20180101", today)
        Fund().load_fund_factor("Stock_Ratio", "20180101", today)

        # 基金和指数持仓数据应该每日下载 这里不用下载
        ##########################################################################################

        # 基金池 不用每次都更新
        ##########################################################################################
        # Fund().load_fund_pool_all("20181231")
        ##########################################################################################

    def get_zz500_adjust(self):

        """ 计算修正过后的中证500净值序列 """

        fund_code = "162216.OF"
        old_data = MfcData().get_mfc_public_fund_nav(fund_code)

        fund_code_adjust = "162216.OF_adjust"
        adjust_data = MfcData().get_mfc_public_fund_nav(fund_code_adjust)

        adjust_data = pd.concat([adjust_data['NAV_ADJ'], old_data['NAV_ADJ_RETURN1']], axis=1)

        for i in range(len(adjust_data) - 40, len(adjust_data)):
            date = adjust_data.index[i]
            pct = adjust_data.loc[date, "NAV_ADJ_RETURN1"] / 100 + 1
            adjust_data.loc[date, "NAV_ADJ"] = adjust_data.loc[adjust_data.index[i - 1], "NAV_ADJ"] * pct

        result = pd.DataFrame(adjust_data["NAV_ADJ"].values, index=adjust_data.index, columns=["NAV_ADJ"])
        path = MfcData().data_path
        file = os.path.join(path, "nav\public_fund", fund_code_adjust + "_Nav.csv")
        result.to_csv(file)

    def write_main(self, end_date):

        """ 计算每个基金业绩表现 """

        # 部门基金公募
        ####################################################################################
        save_path = self.data_path

        write_public_hs300(end_date, save_path)
        write_public_lh(end_date, save_path)
        write_public_zz500(end_date, save_path)
        write_public_zz500_adjust(end_date, save_path)
        write_public_yjqd(end_date, save_path)
        write_public_xsl(end_date, save_path)

        write_public_fxys(end_date, save_path)
        write_public_qf(end_date, save_path)
        write_public_rx(end_date, save_path)
        write_public_rz(end_date, save_path)
        write_public_pz(end_date, save_path)

        write_public_gg(end_date, save_path)
        write_public_nx(end_date, save_path)
        write_public_ts(end_date, save_path)
        write_public_jl(end_date, save_path)

        # 写入专户产品基金数据
        ####################################################################################
        write_quant6(end_date, save_path)
        write_quant12(end_date, save_path)
        write_quant11(end_date, save_path)
        write_zlhl2018(end_date, save_path)
        write_rs_duocelue(end_date, save_path)
        write_rs_gs(end_date, save_path)

        # 其他部门公募
        ####################################################################################
        write_public_sxqy(end_date, save_path)
        write_public_zxjy(end_date, save_path)
        write_public_chengzhang(end_date, save_path)
        write_public_zhouqi(end_date, save_path)
        write_public_wending(end_date, save_path)
        write_public_szyx(end_date, save_path)
        write_public_xlyx(end_date, save_path)
        write_public_hyjx(end_date, save_path)
        write_public_lxzxp(end_date, save_path)
        write_public_hlxf(end_date, save_path)
        write_public_lcjz(end_date, save_path)
        write_public_fxwy(end_date, save_path)
        write_public_ganggutong(end_date, save_path)

        # yx19 yx37 fp1 rs_500 已到期不用更新
        ####################################################################################

    def rank_all_fund(self, end_date):

        """ 部门所有基金业绩汇总 """

        path = MfcData().data_path
        file = os.path.join(path, "static_data", "mfcteda_public_fund.csv")
        public_code = pd.read_csv(file, index_col=[0], encoding='gbk', parse_dates=[4])
        public_code["任职日期"] = public_code["任职日期"].map(Date().change_to_str)

        for i in range(len(public_code)):

            fund_code = public_code.index[i]
            name = public_code.ix[i, "产品名称"]
            begin_date = public_code.ix[i, "任职日期"]
            rank_pool = public_code.ix[i, '排名池']
            excess = public_code.ix[i, '排名指标']
            new_fund_date = begin_date

            val_str, val_pct = FundRank().rank_fund(fund_code, rank_pool, begin_date, end_date, new_fund_date, excess)
            public_code.ix[i, '基金排名'] = val_str
            public_code.ix[i, '基金排名百分比'] = val_pct

            fund_data = MfcData().get_mfc_public_fund_nav(fund_code)
            fund_data = fund_data['NAV_ADJ']
            fs = FinancialSeries(pd.DataFrame(fund_data), pd.DataFrame([], columns=['nav']))
            public_code.ix[i, '任职回报'] = fs.get_interval_return(begin_date, end_date)
            print(name, val_str, val_pct)

        file = os.path.join(self.data_path, "OutFile", "Rank.csv")
        public_code.to_csv(file, index_col=[0], encoding='gbk')
        print("rank all fund")


if __name__ == '__main__':

    """ 泰达宏利金融工程部基金每个月的基金业绩表现 """

    end_date = Date().get_normal_date_last_month_end_day(datetime.today())
    print(end_date)
    self = MfcMonthlyPerformanceFund()
    self.update_data()
    self.write_main(end_date)
    self.rank_all_fund(end_date)

    """ 需要更新富时指数收益 """
    """ 出现的问题有 某些基金已关停 """
