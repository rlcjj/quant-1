import os
import shutil

from quant.data.data import Data
from quant.utility.hdf_mfc import HdfMfc
from quant.utility.factor_operate import FactorOperate


class StockFactorData(Data):

    """
    下载、读取、写入股票因子h5文件
    """

    def __init__(self):

        Data.__init__(self)
        self.load_path = r'\\10.3.12.202\fe\matlab_data\InputData'
        self.load_path2 = r'\\10.3.12.202\fe\primary_data\hdf\primary_data'

    def load_h5_primary_factor(self):

        """ 从网盘下载 h5 primary factor """

        sub_path_list = ["WindData\DailyMarketData", "WindData\DailyReportData",
                         "WindData\IndustryData", 'WindData\PredictData', 'WindData\ReportData',
                         "ExternalData\\NetworkData", "ExternalData\GogoalData"]

        for i_sub_path in range(len(sub_path_list)):
            sub_path = sub_path_list[i_sub_path]
            path = os.path.join(self.load_path, sub_path)
            file_list = os.listdir(path)
            file_list = list(filter(lambda x: 'h5' in x, file_list))
            for i_file in range(len(file_list)):
                file = file_list[i_file]
                old_file = os.path.join(path, file)
                new_file = os.path.join(self.get_h5_path(), file)
                print("Loading Factor h5 %s " % old_file)
                shutil.copyfile(old_file, new_file)

        sub_path_list = ["choice", "finance", "finance_daily", 'fund', 'gogoal',
                         "indicies", "macro", 'market', 'network', 'option', 'predict', 'weight']

        for i_sub_path in range(len(sub_path_list)):
            sub_path = sub_path_list[i_sub_path]
            path = os.path.join(self.load_path2, sub_path)
            file_list = os.listdir(path)
            file_list = list(filter(lambda x: 'h5' in x, file_list))
            for i_file in range(len(file_list)):
                file = file_list[i_file]
                old_file = os.path.join(path, file)
                new_file = os.path.join(self.get_h5_path(), file)
                print("Loading Factor h5 %s " % old_file)
                shutil.copyfile(old_file, new_file)

    def get_h5_path(self, type='mfc_primary'):

        """ 获取H5文件的路径 """

        if type in ['mfc_primary', 'mfc_alpha']:
            sub_data_path = r'stock_data\stock_factor\hdf'
        elif type == 'my_alpha':
            sub_data_path = r'stock_data\alpha_model\factor\hdf'
        else:
            sub_data_path = ''

        data_path_factor = os.path.join(self.primary_data_path, sub_data_path)
        return data_path_factor

    def read_factor_h5(self, factor_name, path=None, data_type='f'):

        """ 读取 H5 Stock Factor文件 """

        if path is None:
            path = self.get_h5_path()

        # 读取数据
        file = os.path.join(path, '%s.h5' % factor_name)
        print("Read Data From %s" % file)

        if os.path.exists(file):
            factor_data = HdfMfc().read_hdf_factor(file, type=data_type)
        else:
            print("%s no exists" % factor_name)
            factor_data = None
        return factor_data

    def write_factor_h5(self, data, factor_name, path=None, data_type='f'):

        """ 写入 H5 Stock Factor文件 """

        if path is None:
            path = self.get_h5_path(type='my_alpha')

        file = os.path.join(path, '%s.h5' % factor_name)

        # 检查数据结构
        #############################################################################
        # index --> code columns --> date

        data.index = data.index.map(str)
        data.columns = data.columns.map(str)
        if data.columns[0][0] not in ["1", "2"]:
            print(" Data Columns in not Date ")
        data = data.T.dropna(how='all').T

        # 写入H5数据
        #############################################################################

        if not os.path.exists(file):
            print(" The File %s Not Exist, Saving ... " % file)
            HdfMfc().write_hdf_factor(file, data)
        else:
            old_data = self.read_factor_h5(factor_name, path, data_type)
            old_data = old_data.T
            new_data = data.T
            save_data = FactorOperate().pandas_add_row(old_data=old_data, new_data=new_data)
            save_data = save_data.T
            save_data = save_data.T.dropna(how='all').T
            print(" The File %s Exist, Saving... " % file)
            HdfMfc().write_hdf_factor(file, save_data, type=data_type)

if __name__ == '__main__':

    """ 读取 H5 Stock Factor文件 """
    self = StockFactorData()
    # path = StockFactorData().get_h5_path('mfc_primary')
    # data = StockFactorData().read_factor_h5("PriceCloseAdjust", path)
    # print(data)
    #
    # """ 写入 H5 Stock Factor文件 """
    # path = StockFactorData().get_h5_path('my_alpha')
    # factor_name = "PriceCloseAdjust"
    # StockFactorData().write_factor_h5(data, factor_name, path)

    """ 下载 H5 Stock Factor文件 """
    StockFactorData().load_h5_primary_factor()


