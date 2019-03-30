from quant.stock.index_exposure import IndexBarraExposure
from quant.stock.index_factor import IndexFactor
from quant.stock.index_weight import IndexWeight


class Index(IndexFactor, IndexWeight, IndexBarraExposure):

    def __init__(self):

        IndexFactor.__init__(self)
        IndexWeight.__init__(self)
        IndexBarraExposure.__init__(self)


if __name__ == "__main__":

    from datetime import datetime
    index = Index()
    date = '20181121'

    # Index Factor
    #############################################################################
    index.load_index_factor("000300.SH", "20171231", datetime.today())
    print(index.get_index_factor("000905.SH", "20180601", datetime.today()))

    # Index Weight
    #############################################################################
    # index.load_weight_from_ftp_date("000905.SH", date)
    index.load_weight_from_wind_date("000016.SH", date)
    index.load_weight_china_index_date(date)
    print(index.get_weight_date("000300.SH", date))

    # Index Exposure
    #############################################################################
    index.cal_index_exposure("000016.SH", beg_date="20041229", end_date="20171229")
    print(index.get_index_exposure_date("000300.SH", "20171231"))
