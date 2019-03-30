import os
from ftplib import FTP
from quant.stock.date import Date


class MyFtp(object):

    """
    连接FTP服务器 用来下载上传数据文件
    默认为公司FTP服务器 也可以调整为其他FTP(如中证指数ftp)

    connect()
    close()
    load_file()
    load_file_folder_change_name()
    upload_file()
    """

    def __init__(self,
                 ip="10.253.0.70",
                 port=21,
                 user_name='doufucheng',
                 user_password="Mfcteda2018!!"):

        self.ip = str(ip)
        self.port = int(port)
        self.user_name = user_name
        self.user_password = user_password
        self.ftp = None

    def connect(self):

        """ 联接服务器 """

        self.ftp = FTP()
        self.ftp.encoding = 'utf-8'
        self.ftp.connect(self.ip, self.port)
        self.ftp.login(self.user_name, self.user_password)

    def close(self):

        """ 关闭连接 """

        self.ftp.close()

    def load_file(self, ftp_file, local_file):

        """ 下载文件 """

        print('Begin DownLoading %s ......' % ftp_file)
        ftp_path = os.path.dirname(ftp_file)
        file_name = os.path.basename(ftp_file)
        self.ftp.cwd(ftp_path)
        file_list = self.ftp.nlst()

        if file_name in file_list:
            buf_size = 1024
            fp = open(local_file, 'wb')
            self.ftp.retrbinary('RETR ' + ftp_file, fp.write, buf_size)
        else:
            print(" No Exist File in FTP ")

    def load_file_folder_change_name(self, ftp_path, local_path, ftp_file_list, local_file_list):

        """ 下载文件夹 并更改文件名 """

        for i_file in range(len(ftp_file_list)):

            ftp_file = ftp_file_list[i_file]
            local_file = local_file_list[i_file]
            ftp_file = os.path.join(ftp_path, ftp_file)
            local_file = os.path.join(local_path, local_file)
            self.load_file(ftp_file, local_file)

    def upload_file(self, ftp_file, local_file):

        """ 上传文件 """

        print('Begin UpLoading %s ......' % ftp_file)
        ftp_path = os.path.dirname(ftp_file)
        file_name = os.path.basename(ftp_file)
        try:
            self.ftp.cwd(ftp_path)
        except Exception as e:
            self.ftp.mkd(ftp_path)
            self.ftp.cwd(ftp_path)
        buf_size = 1024
        fp = open(local_file, 'rb')
        self.ftp.storbinary('STOR ' + file_name, fp, buf_size)

    def upload_folder(self, ftp_folder):

        """ 上传文件夹 """

        print('Begin UpLoading %s ......' % ftp_folder)
        try:
            self.ftp.cwd(ftp_folder)
        except Exception as e:
            self.ftp.mkd(ftp_folder)
            self.ftp.cwd(ftp_folder)

if __name__ == '__main__':

    from quant.mfc.mfc_data import MfcData
    from datetime import datetime

    date = Date().change_to_str(datetime.today())

    ftp_path = os.path.join(MfcData().ftp_path, date)
    local_path = os.path.join(MfcData().data_path, date)

    if not os.path.exists(local_path):
        os.mkdir(local_path)

    ftp = MyFtp()
    ftp.connect()
