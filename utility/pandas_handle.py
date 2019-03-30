import pandas as pd
import numpy as np

# https://www.cnblogs.com/HixiaoDi/p/7739621.html

# pandas 的操作
date_index = pd.date_range(start="20190101", end="20190131")
data_num = np.random.rand(len(date_index), 1)
data = pd.DataFrame(data_num, index=date_index, columns=['num'])
data['type'] = np.random.choice(['a', 'b', 'c'], size=(len(date_index), 1))
data['type2'] = np.random.choice(['d', 'e', 'f', 'g'], size=(len(date_index), 1))

# set_index 设置多重索引
# re_index 重命名
# reset_index 解索引
data = data.set_index(['type2', 'type'])
data_reset = data.reset_index()

# 按照那个索引进行排序
data = data.sort_index()
data = data.sort_index(level=1)

data_sum = data.sum(level='type2')
# slice(None) 表示所有
data_select = data.loc[('f', 'a'), :]
data_select = data.loc[('f', 'a'), :]
