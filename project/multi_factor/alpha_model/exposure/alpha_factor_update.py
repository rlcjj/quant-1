import os
import pandas as pd
from datetime import datetime

from quant.data.data import Data
from quant.stock.date import Date
from quant.utility.write_excel import WriteExcel
from quant.project.multi_factor.alpha_model.exposure.alpha_factor import AlphaFactor


class AlphaFactorUpdate(Data):

    """ 更新计算全部Alpha因子 """

    def __init__(self):

        Data.__init__(self)
        self.sub_data_path = r'stock_data\alpha_model\factor\param'
        self.data_path = os.path.join(self.primary_data_path, self.sub_data_path)

    @staticmethod
    def update_alpha_factor(beg_date=None, end_date=None):

        """ 开始更新最近Alpha数据 """

        if end_date is None:
            end_date = datetime.today().strftime("%Y%m%d")
        if beg_date is None:
            beg_date = Date().get_trade_date_offset(end_date, -60)

        from quant.project.multi_factor.alpha_model.exposure.alpha_daily_tsrank9 import AlphaDailyTsRank9
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_amount_ir import AlphaAmountIR
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_amount_ln_20d import AlphaAmountLn20d
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_amount_ln_120d import AlphaAmountLn120d
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ar2p import AlphaAR2P
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ar2e import AlphaAR2E
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_asset_yoy import AlphaAssetYoY
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_at_bias import AlphaATBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_average_holder import AlphaAverageHolder
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_bp import AlphaBP
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_cfno2ev import AlphaCFNO2EV
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_cfno_yoy import AlphaCFNOYoY
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_cp import AlphaCP
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_dividend_12m import AlphaDividend12m
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ep import AlphaEP
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ep_ttm import AlphaEPTTM
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_gb_bias import AlphaGBBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_gpr_qoq import AlphaGprQoQ
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_gross_ep import AlphaGrossEP
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_gross_profit_yoy import AlphaGrossProfitYoY
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_illiquidity import AlphaIlliquidity
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_illiquidity_bias import AlphaIlliquidityBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_income2ev import AlphaIncome2EV
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_income_yoy import AlphaIncomeYoY
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_inflow2freep import AlphaInflow2FreeP
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_momentum_1m import AlphaMomentum1m
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_momentum_6m import AlphaMomentum6m
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_momentum_bias import AlphaMomentumBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_profit_ttm_qoq import AlphaProfitTTMQoQ
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_profit_yoy import AlphaProfitYoY
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_profit_yoy_bias import AlphaProfitYoYBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_resistance import AlphaResistance
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_retain2p import AlphaRetain2P
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_roa import AlphaROA
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_roe import AlphaROE
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_roe_ttm import AlphaROETTM
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_rsi import AlphaRSI
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_skewness import AlphaSkewness
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_sp_ttm import AlphaSPTTM
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ths_bias import AlphaTHSBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_ths import AlphaTHS
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_to_bias import AlphaTOBias
        from quant.project.multi_factor.alpha_model.exposure.alpha_factor_to_bias_6m import AlphaTOBias6m

        AlphaDailyTsRank9().cal_factor_exposure(beg_date, end_date)
        AlphaAmountIR().cal_factor_exposure(beg_date, end_date)
        AlphaAmountLn20d().cal_factor_exposure(beg_date, end_date)
        AlphaAmountLn120d().cal_factor_exposure(beg_date, end_date)
        AlphaAR2P().cal_factor_exposure(beg_date, end_date)
        AlphaAR2E().cal_factor_exposure(beg_date, end_date)
        AlphaAssetYoY().cal_factor_exposure(beg_date, end_date)
        AlphaATBias().cal_factor_exposure(beg_date, end_date)
        AlphaAverageHolder().cal_factor_exposure(beg_date, end_date)
        AlphaBP().cal_factor_exposure(beg_date, end_date)
        AlphaCFNO2EV().cal_factor_exposure(beg_date, end_date)
        AlphaCFNOYoY().cal_factor_exposure(beg_date, end_date)
        AlphaCP().cal_factor_exposure(beg_date, end_date)
        AlphaDividend12m().cal_factor_exposure(beg_date, end_date)
        AlphaEP().cal_factor_exposure(beg_date, end_date)
        AlphaEPTTM().cal_factor_exposure(beg_date, end_date)
        AlphaGBBias().cal_factor_exposure(beg_date, end_date)
        AlphaGprQoQ().cal_factor_exposure(beg_date, end_date)
        AlphaGrossEP().cal_factor_exposure(beg_date, end_date)
        AlphaGrossProfitYoY().cal_factor_exposure(beg_date, end_date)
        AlphaIlliquidity().cal_factor_exposure(beg_date, end_date)
        AlphaIlliquidityBias().cal_factor_exposure(beg_date, end_date)
        AlphaIncome2EV().cal_factor_exposure(beg_date, end_date)
        AlphaIncomeYoY().cal_factor_exposure(beg_date, end_date)
        AlphaInflow2FreeP().cal_factor_exposure(beg_date, end_date)
        AlphaMomentum1m().cal_factor_exposure(beg_date, end_date)
        AlphaMomentum6m().cal_factor_exposure(beg_date, end_date)
        AlphaMomentumBias().cal_factor_exposure(beg_date, end_date)
        AlphaProfitTTMQoQ().cal_factor_exposure(beg_date, end_date)
        AlphaProfitYoY().cal_factor_exposure(beg_date, end_date)
        AlphaProfitYoYBias().cal_factor_exposure(beg_date, end_date)
        AlphaResistance().cal_factor_exposure(beg_date, end_date)
        AlphaRetain2P().cal_factor_exposure(beg_date, end_date)
        AlphaROA().cal_factor_exposure(beg_date, end_date)
        AlphaROE().cal_factor_exposure(beg_date, end_date)
        AlphaROETTM().cal_factor_exposure(beg_date, end_date)
        AlphaRSI().cal_factor_exposure(beg_date, end_date)
        AlphaSkewness().cal_factor_exposure(beg_date, end_date)
        AlphaSPTTM().cal_factor_exposure(beg_date, end_date)
        AlphaTHSBias().cal_factor_exposure(beg_date, end_date)
        AlphaTHS().cal_factor_exposure(beg_date, end_date)
        AlphaTOBias().cal_factor_exposure(beg_date, end_date)
        AlphaTOBias6m().cal_factor_exposure(beg_date, end_date)

    def check_alpha_factor_update_date(self):

        """ 检查所有Alpha因子最后更新时间 """

        factor_name_list = AlphaFactor().get_all_alpha_factor_name()
        result = pd.DataFrame([], columns=['开始日期', '结束日期'], index=factor_name_list)

        for i in range(0, len(factor_name_list)):

            factor_name = factor_name_list[i]
            try:
                print("######### 检查更新日期 %s 数据 ############" % factor_name)
                factor = AlphaFactor().get_alpha_factor_exposure(factor_name)
                factor = factor.T.dropna(how='all').T
                result.loc[factor_name, '开始日期'] = factor.columns[0]
                result.loc[factor_name, '结束日期'] = factor.columns[-1]
                result.loc[factor_name, "最后一天有效数据个数"] = factor.iloc[:, -1].count()
                result.loc[factor_name, "最后一天股票个数"] = len(factor.iloc[:, -1])
                result.loc[factor_name, "最后一天有效数据比率"] = factor.iloc[:, -1].count() / len(factor.iloc[:, -1])
            except Exception as e:
                result.loc[factor_name, '开始日期'] = ""
                result.loc[factor_name, '结束日期'] = ""
                result.loc[factor_name, "最后一天有效数据个数"] = ""
                result.loc[factor_name, "最后一天股票个数"] = ""
                result.loc[factor_name, "最后一天有效数据比率"] = ""
                print("########### %s 检查更新数据 为空 ！！！###########" % factor_name)

        out_file = os.path.join(self.data_path, "AlphaFactorUpdateDate.xlsx")
        we = WriteExcel(out_file)
        ws = we.add_worksheet("更新数据")

        num_format_pd = pd.DataFrame([], columns=result.columns, index=['format'])
        num_format_pd.loc['format', :] = '0'
        num_format_pd.loc['format', ['最后一天有效数据比率']] = '0.00%'
        we.write_pandas(result, ws, begin_row_number=0, begin_col_number=1,
                        num_format_pd=num_format_pd, color="blue", fillna=True)

        we.close()


if __name__ == '__main__':

    self = AlphaFactorUpdate()
    self.update_alpha_factor()
    self.check_alpha_factor_update_date()
