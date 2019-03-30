from quant.stock.date import Date
from quant.stock.index import Index
from quant.stock.stock import Stock
from quant.stock.macro import Macro

from quant.project.multi_factor.risk_model.exposure.risk_factor_update import RiskFactorUpdate


class MultiFactorUpdate(object):

    """
    定时更新多因子模型
    包括风险模型 和 Alpha模型
    """

    def __init__(self):
        pass

    @staticmethod
    def load_data(beg_date, end_date):

        """ 下载所有风险因子需要的数据 """

        Stock().load_h5_primary_factor()
        Index().load_index_factor(index_code='881001.WI', beg_date=beg_date, end_date=end_date)
        Index().load_index_factor(index_code='000985.CSI', beg_date=beg_date, end_date=end_date)
        Macro().load_daily_risk_free_rate(beg_date, end_date)

    @staticmethod
    def cal_data(beg_date, end_date):

        """ 计算所有风险因子暴露 最浪费时间的是beta的计算 然后是resvol的计算 """

        RiskFactorUpdate().cal_risk_factor_exposure(beg_date, end_date)


if __name__ == '__main__':

    from datetime import datetime
    self = MultiFactorUpdate()

    end_date = datetime.today()
    beg_date = Date().get_trade_date_offset(end_date, -30)
    self.load_data(beg_date, end_date)

    end_date = datetime.today()
    beg_date = Date().get_trade_date_offset(end_date, -10)
    self.cal_risk_factor_exposure(beg_date, end_date)
