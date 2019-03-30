
class Data(object):

    """
    所有数据的母类，定义了数据的主路径
    不同位置的工程，数据存储目录不一致，考虑创建 .gitignore 文件
    https://www.cnblogs.com/wcwnina/p/9112364.html
    """

    def __init__(self):

        self.primary_data_path = r'E:\Data'


if __name__ == "__main__":

    print(Data().primary_data_path)
