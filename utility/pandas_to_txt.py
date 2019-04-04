import pandas as pd


class PandasToTxt(object):

    def __init__(self):

        pass

    def to_txt(self, data, file):

        f = open(file, "w")
        l = len(data)
        n = len(data.columns)

        if data.index.name is None:
            index_name = ""
        else:
            index_name = data.index.name
        f.write(index_name)
        f.write('\t')

        for m in range(n):
            text = str(data.columns[m])
            f.write('\t')
            f.write(text)
        f.write('\n')

        for i in range(l):
            f.write(str(data.index[i]))
            f.write('\t')
            for m in range(n):
                text = str(data.iloc[i, m])
                f.write(text)
                f.write('\t')
            f.write('\n')
        f.close()

if __name__ == '__main__':

    self = PandasToTxt()

    from quant.stock.stock import Stock
    data = Stock().read_factor_h5("FCFF")
    data_date = pd.DataFrame(data[["20180930", "20181231"]])
    data_date = data_date.dropna()
    file = r'C:\Users\doufucheng\OneDrive\Desktop\fcff.txt'
    self.to_txt(data_date, file)
