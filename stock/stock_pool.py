from quant.stock.stock_forbid_pool import StockForbidPool
from quant.stock.stock_invest_pool import StockInvestPool


class StockPool(StockForbidPool, StockInvestPool):

    """
    股票池

    因子模型的步骤
    1、确定股票基准：基准需要长期向上，有可配置的价值、具有经济学逻辑
    2、确定可选股票池（***）：股票池的确定对风险模型和Alpha模型很重要
    3、风险模型：不同股票池的风险因素可能不一致
    4、Alpha模型：不同股票池的有效ALpha也可能不一致
    5、因子合成和组合优化

    """

    def __init__(self):

        StockInvestPool.__init__(self)
        StockForbidPool.__init__(self)


if __name__ == '__main__':

    # StockPool
    ################################################################################
    self = StockPool()
