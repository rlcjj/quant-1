import h5py
import pandas as pd
import os
import numpy as np


class HdfMfc(object):

    """
    泰达 格式的 hdf 文件的读取和写入
    hdf 有三个部分 Code Date 和 Factor Data 本身
    """

    def __init__(self):

        self.filename = ""
        self.dsname = ""
        self.codestr = 'CodeStr'
        self.datestr = 'DateStr'

    def read_hdf_code(self):

        """ 读取Code """

        f = h5py.File(self.filename, 'a')
        codestr = f['CodeStr'][...][0]
        f.close()
        codestr_utf = list(map(lambda x: x.decode(encoding="utf-8"), list(codestr)))
        codestr_format = codestr_utf
        return codestr_format

    def read_hdf_date(self):

        """ 读取Date """

        f = h5py.File(self.filename, 'a')
        datestr = f['DateStr'][...][0]
        f.close()
        datestr_utf = list(map(lambda x: x.decode(encoding="utf-8"), list(datestr)))
        return datestr_utf

    def read_hdf_data(self, dsname, type='f'):

        """ 读取Factor Data """

        f = h5py.File(self.filename, 'a')
        data = f[dsname][...]
        f.close()
        data_pd = pd.DataFrame(data)
        if type == 's':
            data = data_pd.applymap(lambda x: x.decode(encoding="utf-8")).values
        else:
            data = data_pd.values
        return data

    def read_hdf_factor(self, filename, type='f'):

        """ 读取Factor 转化成为DataFactor """

        self.filename = filename
        filepath, tempfilename = os.path.split(filename)
        dsname, extension = os.path.splitext(tempfilename)
        self.dsname = dsname

        index = self.read_hdf_code()
        columns = self.read_hdf_date()
        data = self.read_hdf_data(dsname, type=type)
        data_pd = pd.DataFrame(data, index=index, columns=columns)
        data_pd.columns = data_pd.columns.map(str)
        data_pd.index = data_pd.index.map(str)

        return data_pd

    def write_hdf_data(self, filename, dsname, data, type='f', clevel=9, cmethod="gzip"):

        """ 写入 h5 data """

        f = h5py.File(filename)

        if type == 'f':
            dt = np.float64
        elif type == 's':
            dt = h5py.special_dtype(vlen=bytes)
        else:
            print(' The Type of Data is Illegal! ')

        if dsname in ['CodeStr', 'DateStr']:
            f.create_dataset(dsname, shape=(1, len(data)), data=data,
                             compression=cmethod, compression_opts=clevel, dtype=dt)
        else:
            f.create_dataset(dsname, shape=data.shape, data=data,
                             compression=cmethod, compression_opts=clevel, dtype=dt)
        f.close()

    def write_hdf_factor(self, filename, data, type='f'):

        """ 写入 h5 factor """

        self.filename = filename
        filepath, tempfilename = os.path.split(filename)
        dsname, extension = os.path.splitext(tempfilename)
        self.dsname = dsname

        if os.path.exists(filename):
            os.remove(filename)

        import re
        zhmodel = re.compile(u'[\u4e00-\u9fa5]')
        match = zhmodel.search(filename)
        if match:
            print(" 文件路径包含中文 %s" % filename)

        data.index = data.index.map(str)
        data.columns = data.columns.map(str)

        code_str = data.index.values
        date_str = data.columns.values

        factor = data.astype(np.float64).values

        self.write_hdf_data(filename, 'CodeStr', code_str, type='s')
        self.write_hdf_data(filename, 'DateStr', date_str, type='s')
        self.write_hdf_data(filename, dsname, factor, type=type)

    def rename(self, filename, change_filename):

        """ 重命名 h5 factor """

        data_pd = self.read_hdf_factor(filename)
        os.remove(filename)
        self.write_hdf_factor(change_filename, data_pd)

    def save_csv(self, filename, change_filename):

        """ 变成CSV文件 """

        data_pd = self.read_hdf_factor(filename)
        data_pd.to_csv(change_filename)

if __name__ == '__main__':

    from quant.stock.stock import Stock
    path = Stock().get_h5_path(type='mfc_primary')
    factor_name = 'Pct_chg'
    filename = os.path.join(path, factor_name + '.h5')
    print(filename)

    self = HdfMfc()
    data = self.read_hdf_factor(filename)
    print(data)
    self.write_hdf_factor(filename, data)
