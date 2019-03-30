import pandas as pd
import numpy as np
import scipy.optimize as sco


class AssetAllocation(object):

    """
    给出资产预期收益率和波动率
    返回风险平价、马科维茨模型对资产权重的分配
    """

    def __init__(self):
        pass

    def cal_markowitz_weights(self, alpha, cov, tag_alpha, w_low, w_up):

        """
        限制条件，权重之和为1，目标收益率一定的情况下，组合波动率最小
        """

        # 参数举例
        #####################################################################################
        # alpha = pd.DataFrame([0.2, 0.1, 0.05], index=["S1", 'S2', 'S3'], columns=["alpha"])
        # cov = pd.DataFrame([[0.23, 0.05, 0.08],
        #                     [0.05, 0.14, 0.04],
        #                     [0.08, 0.04, 0.06]],
        #                    index=["S1", 'S2', 'S3'], columns=["S1", 'S2', 'S3'])
        #
        # tag_alpha = 0.12
        # w_low = 0.0
        # w_up = 0.5

        # 计算
        #####################################################################################
        alpha_values = alpha.values
        cov_values = cov.values
        number = len(alpha_values)

        bnds = tuple((w_low, w_up) for x in range(number))

        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(x * alpha_values) - tag_alpha})

        def portfoliovar(w):
            return np.dot(np.dot(w.T, cov_values), w)

        opt = sco.minimize(portfoliovar, number * [1. / number], method='SLSQP', bounds=bnds, constraints=cons)

        weight = opt['x'].round(3)
        weight = pd.DataFrame(weight, index=alpha.index, columns=["weight"])
        weight = pd.concat([weight, alpha], axis=1)
        real_alpha = (weight["weight"] * weight["alpha"]).sum()
        w = weight["weight"].values
        real_var = np.dot(np.dot(w.T, cov_values), w)
        return weight, real_alpha, real_var

    def cal_risk_parity_weights(self, cov):

        """
        采用文章 Efficient Algorithms for Computing Risk Parity Portfolio Weights

        """
        # 参数举例
        #####################################################################################
        # alpha = pd.DataFrame([0.2, 0.1, 0.05], index=["S1", 'S2', 'S3'], columns=["alpha"])
        # cov = pd.DataFrame([[0.23, 0.05, 0.08],
        #                     [0.05, 0.14, 0.04],
        #                     [0.08, 0.04, 0.06]],
        #                    index=["S1", 'S2', 'S3'], columns=["S1", 'S2', 'S3'])

        #####################################################################################
        # 资产种类 N
        N = len(cov)

        # 差值 dist 初始化 和循环计算的最小值
        dist = 1.0
        dist_min = 0.0001

        # y初始化 y中包含了资产权重 w 和 参数lamb
        y = np.zeros((N + 1, 1))
        y[:N] = 1.0 / N
        y[N] = 0.5

        # 循环计算权重 直到 dist<= 0.00001
        while dist > dist_min:

            w = y[:N]
            lamb = y[N]
            w_1 = 1.0 / w
            w_2 = 1.0 / w / w

            # F是函数值
            F = np.zeros((N + 1, 1))
            F[:N] = np.dot(cov, w) - lamb * w_1
            F[N] = np.sum(w) - 1.0

            # J是雅可比行列式
            J = np.zeros((N + 1, N + 1))

            # D是对角元素为 1/w 的对角矩阵
            D = np.zeros((N, N))
            for p in range(0, N):
                D[p, p] = w_2[p, 0]

            # J计算
            J[:N, :N] = cov + lamb * D
            J[:N, N] = - w_1.T
            J[N, :N] = 1.0
            y_next = y - np.dot(np.linalg.inv(J), F)

            # 上次计算和本次计算的差值
            dist = np.sqrt(np.sum(np.square(y - y_next)))
            y = y_next

        weight = list(map(lambda x: np.round(x, 4), y[0:N, 0]))
        weight = pd.DataFrame(weight, index=cov.index, columns=["weight"])
        return weight

if __name__ == "__main__":

    alpha = pd.DataFrame([0.2, 0.1, 0.05], index=["S1", 'S2', 'S3'])
    cov = pd.DataFrame([[0.23, 0.05, 0.08],
                        [0.05, 0.14, 0.04],
                        [0.08, 0.04, 0.06]],
                       index=["S1", 'S2', 'S3'], columns=["S1", 'S2', 'S3'])

    print(AssetAllocation().cal_risk_parity_weights(cov))



