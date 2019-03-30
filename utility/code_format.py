import numpy as np


class CodeFormat(object):

    """ 基金、股票代码后缀操作 """

    def __init__(self):
        pass

    @staticmethod
    def fund_code_add_postfix(code):

        """ 添加wind基金后缀 .OF """

        if type(code) in [np.float]:
            code = int(code)

        code_str = str(code)
        code_str = code_str.strip()
        code_str = code_str[0:6]

        if len(code_str) < 6:
            code_str = (6 - len(code_str)) * "0" + code_str + ".OF"
        else:
            code_str += ".OF"
        return code_str

    @staticmethod
    def stock_code_add_postfix(code):

        """ 添加wind股票后缀 .SH .SZ """

        if type(code) in [np.float]:
            code = int(code)

        code_str = str(code)
        code_str = code_str.strip()
        code_str = code_str[0:6]

        if len(code_str) < 6:
            code_str = (6 - len(code_str)) * "0" + code_str
        if code_str[0] in ['6', "T", "7", "8", "9"]:
            code_str += '.SH'
        else:
            code_str += '.SZ'
        return code_str

    def stock_code_drop_postfix(self, code):

        """ 去掉wind股票后缀 .SZ .SH """

        code_str = self.stock_code_add_postfix(code)
        code_str = code_str[0:6]
        return code_str

    def fund_code_drop_postfix(self, code):

        """ 去掉wind基金后缀 .OF """

        code_str = self.fund_code_add_postfix(code)
        code_str = code_str[0:6]
        return code_str

    def get_stcok_market(self, code):

        """ 得到股票的市场（后缀）SZ SH"""

        code = self.stock_code_add_postfix(code)
        market = code[7:9]
        return market

    def get_gem_stock(self, code):

        """ 是否是创业板股票 """

        code = self.stock_code_add_postfix(code)

        if code[0:3] == "300":
            return 1
        else:
            return 0

    def change_normal_to_ipo_apply_code(self, code):

        """ 将普通代码转换成为新股申购代码 """
        """ 沪市要变换 深市不会变化"""

        """
        （1）发行时申购代码为730***，申购款冻结代码为740***，配号代码为741***，该股票上市代码为600***
        （2）发行时申购代码为780***，申购款冻结代码为790***，配号代码为791***，该股票上市代码为601***
        （3）发行时申购代码为732***，申购款冻结代码为734***，配号代码为736***，该股票上市代码为603***
        """

        stock_code = self.stock_code_add_postfix(code)[0:6]

        if stock_code[0:3] == '600':
            stock_code = '730' + stock_code[3:6]
        elif stock_code[0:3] == '601':
            stock_code = '780' + stock_code[3:6]
        elif stock_code[0:3] == '603':
            stock_code = '732' + stock_code[3:6]
        else:
            stock_code = stock_code
        return stock_code

    def change_ipo_apply_code_to_normal(self, code):

        """ 将新股申购代码转化为普通代码 """
        """ 沪市要变换 深市不会变化"""

        """
        （1）发行时申购代码为730***，申购款冻结代码为740***，配号代码为741***，该股票上市代码为600***
        （2）发行时申购代码为780***，申购款冻结代码为790***，配号代码为791***，该股票上市代码为601***
        （3）发行时申购代码为732***，申购款冻结代码为734***，配号代码为736***，该股票上市代码为603***
        """

        stock_code = self.stock_code_add_postfix(code)[0:6]

        if stock_code[0:3] == '730':
            stock_code = '600' + stock_code[3:6]
        elif stock_code[0:3] == '780':
            stock_code = '601' + stock_code[3:6]
        elif stock_code[0:3] == '732':
            stock_code = '603' + stock_code[3:6]
        else:
            stock_code = stock_code
        return stock_code

if __name__ == "__main__":

    print(CodeFormat().fund_code_add_postfix("  000002"))
    print(CodeFormat().fund_code_add_postfix(2))
    print(CodeFormat().fund_code_add_postfix("  002"))

    print(CodeFormat().stock_code_add_postfix("T00002"))
    print(CodeFormat().stock_code_add_postfix(300223))
    print(CodeFormat().stock_code_add_postfix("  600002"))
    print(CodeFormat().stock_code_add_postfix(23))

    print(CodeFormat().get_stcok_market(2))
    print(CodeFormat().stock_code_add_postfix(2.0))
    print(CodeFormat().get_gem_stock("300001.SZ"))
    print(CodeFormat().get_gem_stock("000001.SZ"))


