import zipfile
import os


class ZipFile(object):

    """
    文件、文件夹的压缩和解压缩
    """

    def __init__(self):
        pass

    def zip_folder(self, source_dir, output_filename):

        """
        将某个文件夹压缩成为一个文件（压缩文件夹下所有文件）
        """

        zipf = zipfile.ZipFile(output_filename, 'w')
        pre_len = len(os.path.dirname(source_dir))
        print("ZipFile %s into Folder%s" % (output_filename, source_dir))

        for parent, dirnames, filenames in os.walk(source_dir):
            for filename in filenames:
                pathfile = os.path.join(parent, filename)
                arcname = pathfile[pre_len:].strip(os.path.sep)  # 相对路径
                zipf.write(pathfile, arcname)
        zipf.close()

    def zip_file(self, source_dir, output_filename, zip_file_list):

        """
        将某个文件夹下一个或者多个文件压缩成为一个文件
        """

        zipf = zipfile.ZipFile(output_filename, 'w')

        for filename in zip_file_list:
            pathfile = os.path.join(source_dir, filename)
            arcname = filename
            zipf.write(pathfile, arcname)
        zipf.close()

    def unzip_file(self, zip_file, upzip_folder):

        """
        将某个文件夹下一个压缩文件解压缩在一个文件夹下
        """
        if not os.path.exists(upzip_folder):
            print("The UpZip Folder is Not Exist, We Create Folder")
            os.makedirs(upzip_folder)

        file_zip = zipfile.ZipFile(zip_file, 'r')
        for file in file_zip.namelist():
            file_zip.extract(file, upzip_folder)
        file_zip.close()
        # os.remove(zip_file)


if __name__ == '__main__':

    from quant.stock.date import Date

    # 压缩
    date_file_folder = Date().path
    desktop_path = r'C:\Users\doufucheng\OneDrive\Desktop'
    out_file = os.path.join(desktop_path, 'DateZip.zip')
    ZipFile().zip_folder(date_file_folder, out_file)

    # 解压缩
    zip_file = out_file
    upzip_folder = os.path.join(desktop_path, 'Date')
    ZipFile().unzip_file(zip_file, upzip_folder)
