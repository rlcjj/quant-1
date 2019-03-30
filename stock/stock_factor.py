from quant.utility.factor_preprocess import FactorPreProcess
from quant.stock.stock_factor_data import StockFactorData
from quant.stock.stock_factor_operate import StockFactorOperate


class StockFactor(StockFactorData,
                  StockFactorOperate,
                  FactorPreProcess):

    """
    包括
    读取写入 股票因子数据
    股票因子处理
    因子数据的预先处理
    """

    def __init__(self):

        StockFactorOperate.__init__(self)
        StockFactorData.__init__(self)
        FactorPreProcess.__init__(self)


if __name__ == '__main__':

    """ 读取 H5 Stock Factor文件 """
    path = StockFactorData().get_h5_path('mfc_primary')
    data = StockFactorData().read_factor_h5("PriceCloseAdjust", path)
    print(data)

    """ 写入 H5 Stock Factor文件 """
    path = StockFactorData().get_h5_path('my_alpha')
    factor_name = "PriceCloseAdjust"
    StockFactorData().write_factor_h5(data, factor_name, path)


