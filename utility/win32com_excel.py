from win32com.client import DispatchEx
from PIL import ImageGrab
import pythoncom
import os


class Win32ComExcel(object):

    """
    利用Win32com操纵Excel表格，可以对原有的Excel表格操作，利用xlsxwriter只能进行覆盖操作
    可以截屏Excel

    catch_screen()
    """

    def __init__(self):

        # kill_cilent()
        # pythoncom.CoInitialize()  # 多线程初始化
        self.excel = DispatchEx("Excel.Application")  # 启动excel
        self.excel.Visible = True  # 可视化
        self.excel.DisplayAlerts = False  # 是否显示警告
        self.workbooks = None
        self.worksheet = None

    def read_workbook(self, filename):

        """ 打开Excel """
        self.workbooks = self.excel.Workbooks.Open(filename)

    def read_worksheet(self, sheetname):

        """ 选择sheet """
        self.worksheet = self.workbooks.Sheets(sheetname)

    def catch_screen(self, screen_area, path, name):

        """ Excel截屏操作 """

        # 这里使用的时候注意要保证所有EXCEL文件关闭 后台也没有EXCEL进程
        self.worksheet.Range(screen_area).CopyPicture()  # 复制图片区域
        self.worksheet.Paste(self.worksheet.Range('F2'))  # 粘贴 ws.Paste(ws.Range('B1'))  # 将图片移动到具体位置
        self.excel.Selection.ShapeRange.Name = name  # 将刚刚选择的Shape重命名，避免与已有图片混淆
        self.worksheet.Shapes(name).Copy()  # 选择图片
        img = ImageGrab.grabclipboard()  # 获取剪贴板的图片数据
        print(type(img), img)
        img_name = os.path.join(path, name + ".png")
        img.save(img_name)  # 保存图片

    def save(self, root_path, name):

        """ 文件另存为 copy.xlsx """
        self.workbooks.SaveAs(os.path.join(root_path, name))

    def close(self):

        """ 关闭工作薄 不保存"""
        # 总是不能完全关闭进程

        self.workbooks.Close(SaveChanges=0)
        self.excel.Quit()
        # del self
        # pythoncom.CoUninitialize()  # 多进程释放资源
        # kill_cilent("EXCEL.EXE")

        # del self.workbooks, self.excel  # wb为打开的工作表
        # gc.collect()  # 马上内存就释放了。


if __name__ == '__main__':

    # 生成Excel表
    file_name = "C:\\Users\\doufucheng\\OneDrive\\Desktop\\读写EXCEL测试.xlsx"
    sheet_name = "读写EXCEL测试"
    save_path = 'C:\\Users\\doufucheng\\OneDrive\\Desktop\\'

    win32comexcel = Win32ComExcel()
    win32comexcel.read_workbook(file_name)
    win32comexcel.read_worksheet(sheet_name)
    win32comexcel.catch_screen("B2:D10", save_path, 'screen')
    # win32comexcel.catch_screen("B3:D11", save_path, 'screen2')
    win32comexcel.close()

