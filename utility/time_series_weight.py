import numpy as np


class TimeSeriesWeight(object):

    def __init__(self):
        pass

    @staticmethod
    def exponential_weight(number, half_life):

        """
        指数加权权重 权重为等比数列
        """
        # number = 20
        # half_life = 5

        alpha = 1 - np.exp(np.log(0.5) / half_life)

        weight_list = []

        for i in range(int(number)):
            weight = (1 - alpha) ** (number - i)
            weight_list.append(weight)

        weight_array = np.array(weight_list)
        weight_array = weight_array / weight_array.sum()

        return weight_array

if __name__ == '__main__':

    print(TimeSeriesWeight().exponential_weight(20, 5))