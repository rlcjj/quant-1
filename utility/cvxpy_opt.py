import cvxpy as cvx
import numpy as np
import matplotlib.pyplot as plt


class CvxpySample():

    """
    利用cvxpy进行优化 举例
    """

    def __init__(self):
        pass

    def sample1(self):

        # 带约束的回归 变量是一个向量

        m = 10
        n = 5
        np.random.seed(1)
        A = np.random.randn(m, n)
        b = np.random.randn(m)

        # Construct the problem.
        x = cvx.Variable(n)
        objective = cvx.Minimize(cvx.sum_squares(A * x - b))
        constraints = [0 <= x, x <= 1]
        prob = cvx.Problem(objective, constraints)
        prob.solve()

        print("status:", prob.status)
        print("optimal value", prob.value)
        print("x value", x.value)
        print("dual_value", constraints[0].dual_value)

    def sample2(self):

        # 变量是一个标量

        # Create two scalar optimization variables.
        x = cvx.Variable()
        y = cvx.Variable()

        # Create two constraints.
        constraints = [x + y == 1,
                       x - y >= 1]

        # Form objective.
        obj = cvx.Minimize((x - y) ** 2)

        # Form and solve problem.
        prob = cvx.Problem(obj, constraints)
        prob.solve()  # Returns the optimal value.
        print("status:", prob.status)
        print("optimal value", prob.value)
        print("optimal var", x.value, y.value)

    def sample3(self):

        # lasso

        # Problem data.
        n = 15
        m = 10
        np.random.seed(1)
        A = np.random.randn(n, m)
        b = np.random.randn(n)
        # gamma must be nonnegative due to DCP rules.
        gamma = cvx.Parameter(nonneg=True)  # 非负约束的参数

        # Construct the problem.
        x = cvx.Variable(m)
        error = cvx.sum_squares(A * x - b)
        obj = cvx.Minimize(error + gamma * cvx.norm(x, 1))
        prob = cvx.Problem(obj)

        # Construct a trade-off curve of ||Ax-b||^2 vs. ||x||_1
        sq_penalty = []
        l1_penalty = []
        x_values = []
        gamma_vals = np.logspace(-4, 6)

        # 10e-4 --> 10e6 这里默认50个

        for val in gamma_vals:
            gamma.value = val
            prob.solve()
            # Use expr.value to get the numerical value of
            # an expression in the problem.
            sq_penalty.append(error.value)
            l1_penalty.append(cvx.norm(x, 1).value)
            x_values.append(x.value)


    def sample4(self):

        # 马科维茨有效前沿
        np.random.seed(1)
        n = 10
        mu = np.abs(np.random.randn(n, 1))
        Sigma = np.random.randn(n, n)
        Sigma = Sigma.T.dot(Sigma)

        w = cvx.Variable(n)
        gamma = cvx.Parameter(nonneg=True)
        ret = mu.T * w
        risk = cvx.quad_form(w, Sigma)
        prob = cvx.Problem(cvx.Maximize(ret - gamma * risk),
                           [cvx.sum(w) == 1, w >= 0])

        SAMPLES = 100
        risk_data = np.zeros(SAMPLES)
        ret_data = np.zeros(SAMPLES)
        gamma_vals = np.logspace(-2, 3, num=SAMPLES)

        for i in range(SAMPLES):
            gamma.value = gamma_vals[i]
            prob.solve(solver=cvx.ECOS)
            risk_data[i] = np.sqrt(risk.value)
            ret_data[i] = ret.value

        markers_on = [29, 40]
        fig = plt.figure()
        ax = fig.add_subplot(111)
        plt.plot(risk_data, ret_data, 'g-')
        for marker in markers_on:
            plt.plot(risk_data[marker], ret_data[marker], 'bs')
            ax.annotate(r"$\gamma = %.2f$" % gamma_vals[marker], xy=(risk_data[marker] + .08, ret_data[marker] - .03))
        for i in range(n):
            plt.plot(np.sqrt(Sigma[i][i]), mu[i], 'ro')
        plt.xlabel('Standard deviation')
        plt.ylabel('Return')
        plt.show()

    def sample5(self):

        # 换手约束
        np.random.seed(1)
        n = 10

        Sigma = np.random.randn(n, n)
        Sigma = Sigma.T.dot(Sigma)

        orig_weight = [0.15, 0.25, 0.15, 0.05, 0.20, 0, 0.1, 0, 0.1, 0]
        w = cvx.Variable(n)

        mu = np.abs(np.random.randn(n, 1))
        ret = mu.T * w

        lambda_ = cvx.Parameter(nonneg=True)
        lambda_.value = 5

        risk = cvx.quad_form(w, Sigma)

        constraints = [cvx.sum(w) == 1, w >= 0, cvx.sum(cvx.abs(w - orig_weight)) <= 0.30]
        constraints.append([])
        prob = cvx.Problem(cvx.Maximize(ret - lambda_ * risk), constraints)
        prob.solve()

        print('Solver Status : ', prob.status)
        print('Weights opt :', w.value)

    def sample6(self):

        # 限制向量的某个元素
        x = cvx.Variable(5)
        constraints = [x[3] >= 3, x >= 0]
        problem = cvx.Problem(cvx.Minimize(cvx.sum(x)), constraints)
        problem.solve()
        x.value

    def sample7(self):

        # 约束股票个数很难 只能通过优化

        np.random.seed(1)
        n = 2000
        hold_number = 100
        bench_number = 150

        mu = np.random.randn(n, 1)
        Sigma = np.random.randn(n, n)
        Sigma = Sigma.T.dot(Sigma)

        orig_weight = list(np.abs(np.random.randn(hold_number,)))
        orig_weight /= sum(orig_weight)
        orig_weight = orig_weight.tolist()
        orig_weight.extend(np.zeros((n-hold_number,)).tolist())
        orig_weight = np.array(orig_weight)

        bench_weight = list(np.abs(np.random.randn(bench_number,)))
        bench_weight /= sum(bench_weight)
        bench_weight = bench_weight.tolist()
        bench_weight.extend(np.zeros((n-bench_number,)).tolist())
        bench_weight = np.array(bench_weight)

        w = cvx.Variable(n)
        gamma = cvx.Parameter(nonneg=True)
        gamma.value = 0.05
        ret = mu.T * w
        risk = cvx.quad_form(w, Sigma)
        prob = cvx.Problem(cvx.Maximize(ret - gamma * risk),
                           [cvx.sum(w) == 0,
                            w + bench_weight >= 0.000,
                            cvx.sum(cvx.abs(w + bench_weight - orig_weight)) <= 0.30,
                           ])
        prob.solve()

        print("status:", prob.status)
        print("optimal value", prob.value)
        print("w value", w.value + bench_weight)
        weight_tor = 0.001
        import pandas as pd
        w_real = pd.DataFrame(w.value + bench_weight, columns=['weight'])
        print(w_real['weight'].sum())
        print(w_real['weight'].count())
        print(w_real[w_real['weight'] > weight_tor]['weight'].count())
        print(w_real[w_real['weight'] > weight_tor]['weight'].sum())

if __name__ == '__main__':

    CvxpySample().sample1()
    CvxpySample().sample2()
    CvxpySample().sample3()
    CvxpySample().sample4()
    CvxpySample().sample5()

