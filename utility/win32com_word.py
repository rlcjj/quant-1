from win32com.client import Dispatch
import win32com
import os


class Win32ComWord(object):

    """
    利用Win32com操纵 Word 只能在windows系统运行
    还可以利用docx进行Word文档操作
    """

    def __init__(self, file_name):

        self.wordApp = win32com.client.Dispatch('Word.Application')
        self.wordApp.Visible = 0
        self.wordApp.DisplayAlerts = 0
        self.file_name = file_name
        if not os.path.exists(file_name):
            self.doc = self.wordApp.Documents.Add()
        else:
            self.doc = self.wordApp.Documents.Open(file_name)

    def insert_para(self, strContent, font="仿宋_GB2312", size=12, space=12, align=0):

        """ 插入段 """

        p = self.doc.Paragraphs.Add()
        p.Range.Font.Name = font
        p.Range.Font.Size = size
        p.Range.ParagraphFormat.Alignment = align
        p.Range.ParagraphFormat.LineSpacing = space
        p.Range.InsertBefore(strContent)

    def add_footer(self, text, align=1, page_number=False, size=10, font="仿宋_GB2312"):

        """ 页脚 """

        self.doc.Sections(1).Footers(1).Range.Text = text
        self.doc.Sections(1).Footers(1).Range.Font.Size = size
        self.doc.Sections(1).Footers(1).Range.Font.Name = font
        self.doc.Sections(1).Footers(1).Range.ParagraphFormat.Alignment = align
        if page_number:
            self.doc.Sections(1).Footers(1).PageNumbers.Add()

    def insert_title(self, strContent):

        """ 插入标题 """

        self.insert_para(align=1, strContent=strContent, size=12, space=18)

    def save(self):

        """ 文件存储 """

        self.doc.SaveAs(self.file_name)

    def close(self):

        """ 关闭工作薄 """

        self.doc.Close()
        self.wordApp.Quit()

if __name__ == '__main__':

    from faker import Faker
    fake = Faker(locale='zh_CN')

    save_path = 'C:\\Users\\doufucheng\\OneDrive\\Desktop\\'
    file = os.path.join(save_path, 'WordSample.docx')
    word = Win32ComWord(file)

    word.insert_title(fake.sentence(4))
    word.insert_para(fake.paragraph())
    word.insert_para(fake.paragraph())
    word.add_footer("页脚")
    word.save()
    word.close()

