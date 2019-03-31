import pandas as pd


class FactorOperate(object):

    """
    使用对象  Series 或者 DataFrame

    同行列：使得两个拥有相同的行和列
    去重行和列：数据去掉相同的行或者列
    覆盖相加：新的数据覆盖旧的数据 没有被覆盖的地方保留

    make_same_index_columns()

    """

    def __init__(self):
        pass

    @staticmethod
    def make_same_index_columns(data_list=[]):

        """
        对多个 Series 或者 DataFrame 类型的数据 取相同的行列
        """

        if len(data_list) == 0:
            return pd.Series([])

        elif len(data_list) == 1:
            return data_list[0].copy()

        elif type(data_list[0]) == pd.Series:

            for i_data in range(len(data_list)):

                data = data_list[i_data]
                data_copy = data.copy()
                if i_data == 0:
                    index_list = list(set(data_copy.index))
                else:
                    index_list = list(set(index_list) & set(data_copy.index))

            index_list.sort()
            data_result_list = []

            for i_data in range(len(data_list)):

                data = data_list[i_data]
                data_copy = data.copy()
                data_same = data_copy[index_list]
                data_result_list.append(data_same)

            return data_result_list

        elif type(data_list[0]) == pd.DataFrame:

            for i_data in range(len(data_list)):

                data = data_list[i_data]
                data_copy = data.copy()
                if i_data == 0:
                    index_list = list(set(data_copy.index))
                else:
                    index_list = list(set(index_list) & set(data_copy.index))

            for i_data in range(len(data_list)):

                data = data_list[i_data]
                data_copy = data.copy()
                if i_data == 0:
                    columns_list = list(set(data_copy.columns))
                else:
                    columns_list = list(set(columns_list) & set(data_copy.columns))

            index_list.sort()
            columns_list.sort()

            data_result_list = []

            for i_data in range(len(data_list)):
                data = data_list[i_data]
                data_copy = data.copy()
                data_same = data_copy.ix[index_list, columns_list]
                data_result_list.append(data_same)

            return data_result_list

        else:
            print(" Type of Data can not make same index and columns ")
            return None

    @staticmethod
    def drop_duplicated(data):

        ind_none_duplicated = ~data.index.duplicated(keep='first')
        col_none_duplicated = ~data.columns.duplicated(keep='first')
        data = data.loc[ind_none_duplicated, col_none_duplicated]
        return data

    def pandas_add_row(self, old_data, new_data):

        """
        增加新的 pandas 行，若有则覆盖 若没有则增加
        列取两者的并集
        """

        old_data = self.drop_duplicated(old_data)
        new_data = self.drop_duplicated(new_data)

        old_columns = set(old_data.columns)
        new_columns = set(new_data.columns)
        old_index = set(old_data.index)
        new_index = set(new_data.index)

        add_index = list(new_index - old_index)
        and_index = list(old_index & new_index)

        add_columns = list(new_columns - old_columns)
        and_columns = list(old_columns & new_columns)

        and_index.sort()
        add_index.sort()

        print(' ReWrite Index At ', list(and_index))
        print(' Add New Index At ', list(add_index))

        # 重复的行覆盖 新的行合并 新的列合并
        old_data.loc[and_index, and_columns] = new_data.loc[and_index, and_columns]
        res = pd.concat([old_data, new_data.ix[add_index, and_columns]], axis=0)
        res = pd.concat([res, new_data.ix[:, add_columns]], axis=1)

        res = res.sort_index()
        res = res.T.sort_index().T
        res = res.dropna(how='all')

        return res

if __name__ == '__main__':

    """ 举例 """

    data = pd.DataFrame([[1, 'hh'], [3, 'kk'], [4, 'll']],
                        index=pd.date_range(start='20171229', periods=3), columns=['int', 'str'])

    data_add = pd.DataFrame([], index=pd.date_range(start='20171230', periods=4), columns=['int', 'str', 'nan'])
    data_add['int'] = 10
    data_add['str'] = 'str'
    data_add['nan'] = 'hhh'

    print(FactorOperate().drop_duplicated(data))
    print(FactorOperate().drop_duplicated(data_add))
    print(FactorOperate().pandas_add_row(data, data_add))

