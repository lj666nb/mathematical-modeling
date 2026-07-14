#!/usr/bin/env python3
"""Generate all category JSON files for knowledge base."""
import json, os

out = 'frontend/src/data/categories'
os.makedirs(out, exist_ok=True)

cats = []

# ====== 1. 优化模型 ======
cats.append(('01_optimization.json', {
    'id': 'optimization', 'name': '优化模型', 'color': '#165DFF',
    'description': '在给定约束条件下，寻找使目标函数达到最优（最大或最小）的决策方案。',
    'definition': '优化模型研究如何在有限资源下做出最优决策。核心三要素：决策变量（可控因素）、目标函数（优化指标）、约束条件（限制条件）。广泛应用于生产计划、物流调度、投资组合等领域。',
    'algorithms': [
        {
            'name': '单纯形法', 'brief': '线性规划经典算法，在多面体顶点间迭代寻优',
            'description': '单纯形法（Simplex Method）由 George Dantzig 于1947年提出，是求解线性规划问题的核心算法。基本思想：线性规划最优解必在可行域顶点达到，因此只需在顶点间沿目标函数改善方向迭代移动。每次迭代称为转轴（pivot），从一个基本可行解移到相邻的另一个。实际应用极其高效，可处理成千上万个变量和约束。',
            'formulas': [
                {'name': '标准型', 'latex': 'min c^T x  s.t.  Ax = b, x >= 0', 'explanation': '通过引入松弛变量将不等式约束转化为等式约束，构造初始单纯形表。'},
                {'name': '最优性条件（Reduced Cost）', 'latex': 'c_j = c_j - c_B^T B^{-1} a_j >= 0', 'explanation': '所有非基变量的检验数非负时达到最优（对于最小化问题）。'}
            ],
            'code': '"""单纯形法 - 两阶段法实现"""\nimport numpy as np\n\ndef simplex(c, A, b):\n    """min c^T x  s.t. Ax <= b, x >= 0"""\n    m, n = A.shape\n    # 加入松弛变量构造初始单纯形表\n    tableau = np.zeros((m + 1, n + m + 1))\n    tableau[:m, :n] = A\n    tableau[:m, n:n+m] = np.eye(m)\n    tableau[:m, -1] = b.flatten()\n    tableau[-1, :n] = c\n    basic = list(range(n, n + m))\n\n    while True:\n        obj = tableau[-1, :-1]\n        if np.all(obj >= -1e-10):\n            break\n        enter = np.argmin(obj)\n        col = tableau[:-1, enter]\n        rhs = tableau[:-1, -1]\n        ratios = np.where(col > 1e-10, rhs / col, np.inf)\n        if np.all(ratios == np.inf):\n            raise ValueError("解无界")\n        leave = np.argmin(ratios)\n        # 转轴\n        pivot = tableau[leave, enter]\n        tableau[leave] /= pivot\n        for i in range(len(tableau)):\n            if i != leave:\n                tableau[i] -= tableau[i, enter] * tableau[leave]\n        basic[leave] = enter\n\n    x = np.zeros(n)\n    for i, bv in enumerate(basic):\n        if bv < n:\n            x[bv] = tableau[i, -1]\n    return x, tableau[-1, -1]\n\n# 示例: max Z = 40x1+30x2, s.t. 2x1+x2<=100, 3x1+4x2<=120\nc = [-40, -30]\nA = [[2, 1], [3, 4]]\nb = [100, 120]\nx, obj = simplex(c, A, b)\nprint(f"A产量={x[0]:.1f}, B产量={x[1]:.1f}, 最大利润={-obj:.1f}")',
            'steps': [
                '将问题转化为标准型（min c^T x, Ax=b, x>=0）',
                '构造初始单纯形表，确定初始基可行解',
                '计算检验数（Reduced Cost），判断是否最优',
                '若未达最优，选最小检验数对应变量入基',
                '用最小比值法确定出基变量',
                '执行转轴运算更新单纯形表，重复步骤3-6'
            ],
            'useCases': ['生产计划优化', '资源分配问题', '运输问题', '配料问题'],
            'tips': '实际应用推荐 SciPy 的 linprog 或 Gurobi/CPLEX，手写单纯形法主要用于理解算法原理。'
        },
        {
            'name': '内点法', 'brief': '从可行域内部逼近最优解，适合大规模稀疏问题',
            'description': '内点法（Interior Point Method）由 Karmarkar 于1984年提出，具有多项式时间复杂度。与单纯形法沿边界迭代不同，内点法从可行域内部出发，通过障碍函数（barrier function）阻止解触碰边界，逐步逼近最优解。核心思想是用牛顿法求解一系列扰动后的 KKT 条件。对于大规模稀疏线性规划（变量数>10万），内点法通常显著快于单纯形法。',
            'formulas': [
                {'name': '对数障碍问题', 'latex': 'min c^T x - mu sum ln x_i, Ax = b, x > 0', 'explanation': 'mu>0为障碍参数，趋于0时障碍问题解趋于原问题解。对数项阻止变量接近0。'},
                {'name': '中心路径方程', 'latex': 'A^T y + s = c, Ax = b, XSe = mu*e', 'explanation': 'Primal-Dual内点法的核心KKT方程组，用牛顿法迭代求解。'}
            ],
            'code': '"""内点法 - SciPy HiGHS求解器"""\nimport numpy as np\nfrom scipy.optimize import linprog\n\nnp.random.seed(42)\nn, m = 200, 100\nc = np.random.randn(n)\nA = np.random.randn(m, n)\nb = A @ np.abs(np.random.randn(n)) + 1\n\nresult = linprog(c, A_ub=A, b_ub=b, method="highs")\nprint(f"最优值: {result.fun:.4f}, 迭代: {result.nit}")',
            'steps': ['选择初始内点 x>0 和障碍参数 mu0', '用牛顿法求解当前mu对应的KKT条件', '减小mu = sigma*mu（sigma=0.1）', '以前一步解为初始点重复', 'mu足够小时停止'],
            'useCases': ['大规模线性规划（>10000变量）', '二次规划', '半定规划（SDP）', '锥优化'],
            'tips': 'SciPy的HiGHS求解器同时使用单纯形法和内点法。中小规模用单纯形法，大规模稀疏用内点法。'
        },
        {
            'name': '遗传算法', 'brief': '模拟自然进化的智能优化算法，适合复杂非线性优化',
            'description': '遗传算法（Genetic Algorithm, GA）由 John Holland 于1975年提出，模拟自然界适者生存的进化机制。将解编码为染色体（二进制串或实数向量），通过选择（适应度高的个体更可能存活）、交叉（两个父代交换基因片段产生后代）和变异（随机改变某些基因）不断迭代进化种群。GA不依赖梯度信息，适合求解黑箱优化、多峰函数和组合优化问题。',
            'formulas': [
                {'name': '轮盘赌选择概率', 'latex': 'P(i) = f_i / sum_j f_j', 'explanation': '个体被选中的概率正比于其适应度，适应度越高越可能被选中繁殖。'}
            ],
            'code': '"""遗传算法 - 求解Rastrigin函数最小值"""\nimport numpy as np\n\ndef rastrigin(x):\n    """全局最小值 f(0,...,0) = 0"""\n    return 10*len(x) + sum(x**2 - 10*np.cos(2*np.pi*x))\n\npop_size, dim, gens = 100, 5, 200\nlb, ub = -5.12, 5.12\npop = np.random.uniform(lb, ub, (pop_size, dim))\nbest_x, best_f = None, np.inf\n\nfor gen in range(gens):\n    fit = np.array([1/(1+rastrigin(ind)) for ind in pop])\n    elite = pop[np.argmax(fit)]\n    if (f := rastrigin(elite)) < best_f:\n        best_f, best_x = f, elite.copy()\n    prob = fit / fit.sum()\n    new_pop = [elite]\n    while len(new_pop) < pop_size:\n        p1, p2 = pop[np.random.choice(pop_size, 2, p=prob)]\n        alpha = np.random.rand(dim)\n        child = alpha*p1 + (1-alpha)*p2\n        mask = np.random.rand(dim) < 0.05\n        child[mask] += np.random.normal(0, 0.5, mask.sum())\n        new_pop.append(np.clip(child, lb, ub))\n    pop = np.array(new_pop[:pop_size])\n\nprint(f"最优解: {best_x.round(4)}")\nprint(f"函数值: {best_f:.6f} (理论最小值=0)")',
            'steps': [
                '编码：将解表示为染色体（二进制/实数编码）',
                '初始化种群：随机生成 N 个个体',
                '适应度评估：计算每个个体的适应度值',
                '选择：按适应度比例选出父代（轮盘赌/锦标赛选择）',
                '交叉：父代染色体交换基因片段产生子代',
                '变异：子代基因以低概率随机改变',
                '精英保留后重复步骤3-6直到收敛'
            ],
            'useCases': ['函数优化（非凸/多峰/不可微）', 'TSP/VRP路线规划', '参数标定', '排产调度'],
            'tips': '关键调参：种群大小(50-200)、交叉率(0.7-0.9)、变异率(0.01-0.1)。精英保留策略能加速收敛。约束问题用罚函数法。'
        },
        {
            'name': '模拟退火', 'brief': '模拟物理退火过程，以一定概率接受劣解跳出局部最优',
            'description': '模拟退火（Simulated Annealing, SA）由 Kirkpatrick 等人于1983年提出，灵感来自固体物理中的退火过程——加热金属到高温后缓慢冷却，原子达到最低能量态。算法从高温开始，以概率 exp(-Delta_E/T) 接受劣解（Metropolis准则），温度T逐步降低，接受劣解的概率也逐渐变小，最终收敛到全局最优。SA理论上能以概率1收敛到全局最优，适合离散/组合优化。',
            'formulas': [
                {'name': 'Metropolis接受准则', 'latex': 'P(accept) = 1 if Delta_E < 0 else exp(-Delta_E / T)', 'explanation': 'Delta_E为目标差。T高时大概率接受劣解（探索），T低时几乎只接受优解（开采）。'},
                {'name': '指数冷却', 'latex': 'T_{k+1} = alpha * T_k, alpha in (0.7, 0.99)', 'explanation': 'alpha越接近1冷却越慢、搜索越充分但耗时越长。'}
            ],
            'code': '"""模拟退火 - 求解TSP问题"""\nimport numpy as np\n\nnp.random.seed(42)\nN = 30; cities = np.random.rand(N, 2) * 100\n\ndef total_dist(route):\n    return sum(np.linalg.norm(cities[route[i]]-cities[route[(i+1)%N]]) for i in range(N))\n\nroute = list(range(N)); np.random.shuffle(route)\ncurr_d = total_dist(route)\nbest_route, best_d = route[:], curr_d\nT = 1000\n\nwhile T > 0.01:\n    i, j = sorted(np.random.choice(N, 2, replace=False))\n    new = route[:i] + route[i:j+1][::-1] + route[j+1:]\n    new_d = total_dist(new)\n    if new_d < curr_d or np.random.rand() < np.exp(-(new_d-curr_d)/T):\n        route, curr_d = new, new_d\n        if curr_d < best_d:\n            best_route, best_d = route[:], curr_d\n    T *= 0.995\n\nprint(f"最短距离: {best_d:.1f}")',
            'steps': [
                '随机生成初始解 x0，设初始高温 T0',
                '在当前解邻域随机产生新解 x_prime',
                '计算Delta_E = f(x_prime) - f(x)',
                '若Delta_E<0接受新解；否则以概率exp(-Delta_E/T)接受',
                '降温T = alpha*T，回到步骤2直到T足够小'
            ],
            'useCases': ['旅行商问题（TSP）', 'VLSI电路布局', '作业车间调度', '图像恢复'],
            'tips': '初始温度要足够高使接受率>0.8，冷却速率alpha选0.9-0.99。可与2-opt等局部搜索结合。'
        },
        {
            'name': '粒子群优化', 'brief': '模拟鸟群觅食的群体智能算法，粒子共享信息协同搜索',
            'description': '粒子群优化（Particle Swarm Optimization, PSO）由 Kennedy 和 Eberhart 于1995年提出，灵感来自鸟群或鱼群的群体觅食行为。每个粒子代表一个候选解，在搜索空间中飞行。粒子的速度更新同时受自身历史最佳位置（pbest，认知分量）和群体全局最佳位置（gbest，社会分量）的影响。PSO参数少、收敛快、易实现，是连续优化问题的首选元启发式算法之一。',
            'formulas': [
                {'name': '速度更新方程', 'latex': 'v_i = w*v_i + c1*r1*(p_i-x_i) + c2*r2*(g-x_i)', 'explanation': 'w为惯性权重（平衡探索与开发），c1/c2为学习因子，r1/r2为[0,1]随机数，p_i为个体最优，g为全局最优。'},
                {'name': '位置更新', 'latex': 'x_i = x_i + v_i', 'explanation': '粒子沿速度方向移动，通常对位置施加边界约束。'}
            ],
            'code': '"""粒子群优化 - Ackley函数"""\nimport numpy as np\n\ndef ackley(x):\n    n = len(x)\n    return -20*np.exp(-0.2*np.sqrt(np.mean(x**2))) - np.exp(np.mean(np.cos(2*np.pi*x))) + 20 + np.e\n\nn_p, dim = 50, 10\nx = np.random.uniform(-32, 32, (n_p, dim))\nv = np.random.uniform(-1, 1, (n_p, dim))\npbest_x = x.copy()\npbest_f = np.array([ackley(xi) for xi in x])\ngbest_x = x[np.argmin(pbest_f)].copy()\n\nfor t in range(200):\n    r1, r2 = np.random.rand(n_p, dim), np.random.rand(n_p, dim)\n    v = 0.7*v + 1.5*r1*(pbest_x-x) + 1.5*r2*(gbest_x-x)\n    x = np.clip(x + v, -32, 32)\n    f = np.array([ackley(xi) for xi in x])\n    better = f < pbest_f\n    pbest_x[better] = x[better]; pbest_f[better] = f[better]\n    if pbest_f.min() < pbest_f.min():\n        gbest_x = pbest_x[np.argmin(pbest_f)].copy()\n\nprint(f"最优值: {pbest_f.min():.6f} (理论最小值=0)")',
            'steps': [
                '初始化粒子群：随机位置 x_i 和速度 v_i',
                '评估每个粒子的适应度',
                '更新个体最优（pbest）和全局最优（gbest）',
                '按速度更新方程计算每个粒子的新速度',
                '更新粒子位置，施加边界约束',
                '重复步骤2-5直到迭代完成或收敛'
            ],
            'useCases': ['连续函数优化', '神经网络权重训练', 'PID控制器参数整定', '天线阵列优化'],
            'tips': '惯性权重w建议从0.9线性递减到0.4（动态权重比固定权重效果好）。多目标优化用MOPSO。约束问题用罚函数法。'
        }
    ]
}))

# ====== 2. 预测模型 ======
cats.append(('02_prediction.json', {
    'id': 'prediction', 'name': '预测模型', 'color': '#00B42A',
    'description': '基于历史数据建立数学模型，对未来趋势或未知数据进行推断和预测。',
    'definition': '预测模型通过分析历史数据中的规律和模式，建立输入与输出之间的映射关系，对未知数据或未来趋势做出推断。核心在于捕捉数据中的趋势、季节性和随机波动。',
    'algorithms': [
        {
            'name': 'ARIMA/SARIMA', 'brief': '最经典的时间序列预测模型，通过差分和自回归移动平均建模',
            'description': 'ARIMA(p,d,q)模型由三个部分组成：AR(p)自回归（当前值与过去p个值的关系）、I(d)差分（使非平稳序列变平稳）、MA(q)移动平均（当前值与过去q个误差的关系）。SARIMA在此基础上加入季节性成分(P,D,Q,s)，是经济预测、销量预测等场景的首选基线模型。建模关键步骤：平稳性检验(ADF)→确定d→ACF/PACF图定阶p,q→残差白噪声检验。',
            'formulas': [
                {'name': 'ARIMA(p,d,q)', 'latex': 'Phi(B)(1-B)^d X_t = Theta(B) * epsilon_t', 'explanation': 'B为滞后算子(B*X_t=X_{t-1})，d为差分阶数，Phi和Theta分别为AR和MA多项式。'},
                {'name': 'AIC准则', 'latex': 'AIC = -2*ln(L) + 2k', 'explanation': 'L为似然函数值，k为参数个数。AIC越小模型越好，平衡拟合优度和复杂度。'}
            ],
            'code': '"""ARIMA时间序列预测"""\nimport pandas as pd\nimport numpy as np\nfrom statsmodels.tsa.arima.model import ARIMA\n\n# 模拟36个月销售额（趋势+季节性+噪声）\nnp.random.seed(42)\nt = np.arange(36)\ntrend = 100 + 2 * t\nseasonal = 30 * np.sin(2 * np.pi * t / 12)\nnoise = np.random.normal(0, 10, 36)\nsales = trend + seasonal + noise\n\n# 拟合ARIMA(1,1,1)\nmodel = ARIMA(sales, order=(1, 1, 1))\nfitted = model.fit()\nprint(fitted.summary())\n\n# 预测未来6个月\nforecast = fitted.forecast(steps=6)\nprint(f"未来6个月预测: {forecast.round(1)}")',
            'steps': ['平稳性检验（ADF检验/观察时序图）', '若不平稳，进行差分直到平稳（确定d）', '绘制ACF和PACF图确定p和q', '拟合ARIMA模型并检验残差是否为白噪声', '使用AIC/BIC比较多个候选模型', '向前预测并计算置信区间'],
            'useCases': ['销售额/客流量预测', '股票价格走势分析', '宏观经济指标预测', '库存需求预测'],
            'tips': '使用pmdarima库的auto_arima()可自动搜索最优(p,d,q)。季节性数据用SARIMA，设置seasonal_order=(P,D,Q,s)。'
        },
        {
            'name': 'Holt-Winters指数平滑', 'brief': '同时捕捉水平、趋势、季节性的三指数平滑方法',
            'description': 'Holt-Winters方法（也称三指数平滑）是处理带趋势和季节性时间序列的经典方法。由三个平滑方程组成：水平项l_t（序列当前"基线"）、趋势项b_t（增长/下降速率）、季节项s_t（周期性波动模式）。分为加法模型（季节波动幅度恒定）和乘法模型（季节波动幅度随水平变化），后者更适合经济数据。',
            'formulas': [
                {'name': '加法模型预测', 'latex': 'y_{t+h} = l_t + h*b_t + s_{t-m+h}', 'explanation': 'l_t水平、b_t趋势、s_t季节，h为预测步数，m为季节周期长度。'},
                {'name': '水平更新', 'latex': 'l_t = alpha*(y_t-s_{t-m}) + (1-alpha)*(l_{t-1}+b_{t-1})', 'explanation': 'alpha为水平平滑参数(0~1)，越大对新观测越敏感。'}
            ],
            'code': '"""Holt-Winters指数平滑预测"""\nimport numpy as np\nfrom statsmodels.tsa.holtwinters import ExponentialSmoothing\n\n# 模拟带季节性的季度数据\nnp.random.seed(42)\nt = np.arange(48)\ntrend = 50 + 0.5 * t\nseasonal = 15 * np.sin(2 * np.pi * t / 4)  # 周期=4\nnoise = np.random.normal(0, 5, 48)\ndata = trend + seasonal + noise\n\n# Holt-Winters加法模型\nmodel = ExponentialSmoothing(\n    data, seasonal_periods=4,\n    trend="add", seasonal="add"\n)\nfitted = model.fit()\nforecast = fitted.forecast(8)\nprint(f"未来8期预测: {forecast.round(1)}")',
            'steps': ['确定季节周期m（如月度数据m=12）', '选择加法或乘法模型（观察季节波动幅度）', '估计初始水平/趋势/季节值', '通过最小化预测误差优化alpha/beta/gamma', '向前预测并计算预测区间'],
            'useCases': ['零售季度销售预测', '旅游客流量预测', '电力负荷预测'],
            'tips': '当季节波动幅度随数据水平增长时用乘法模型，恒定用加法模型。statsmodels的ExponentialSmoothing支持自动优化参数。'
        },
        {
            'name': 'Prophet', 'brief': 'Facebook开源的时间序列预测工具，自动处理节假日和变点',
            'description': 'Prophet由Facebook于2017年开源，采用广义加法模型(GAM)：y(t)=g(t)+s(t)+h(t)+epsilon，即趋势+季节+节假日+噪声。最大优势在于：(1)全自动化，无需手动调参；(2)鲁棒性强，自动处理缺失值和异常值；(3)支持自定义节假日效应和变点检测；(4)提供不确定性区间。特别适合业务预测场景（日/周/月数据均可）。',
            'formulas': [
                {'name': '趋势模型', 'latex': 'g(t) = (k + a(t)^T*delta)*t + (m + a(t)^T*gamma)', 'explanation': '分段线性趋势，delta为趋势变化量，a(t)指示变点位置。自动检测趋势转折点。'},
                {'name': '季节模型', 'latex': 's(t) = sum_{n=1}^N [a_n*cos(2*pi*n*t/P) + b_n*sin(2*pi*n*t/P)]', 'explanation': '傅里叶级数建模周期季节性，N越大越灵活。P为周期（年=365.25，周=7）。'}
            ],
            'code': '"""Prophet时间序列预测"""\nimport pandas as pd\nimport numpy as np\nfrom prophet import Prophet\n\n# 模拟2年日度数据\nnp.random.seed(42)\ndates = pd.date_range("2024-01-01", periods=730, freq="D")\ntrend = np.linspace(100, 200, 730)\nweekly = 10 * np.sin(2*np.pi*np.arange(730)/7)\nyearly = 20 * np.sin(2*np.pi*np.arange(730)/365.25)\ndata = trend + weekly + yearly + np.random.normal(0, 5, 730)\n\ndf = pd.DataFrame({"ds": dates, "y": data})\nmodel = Prophet(yearly_seasonality=True, weekly_seasonality=True)\nmodel.fit(df)\n\nfuture = model.make_future_dataframe(periods=90)\nforecast = model.predict(future)\nprint(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail())',
            'steps': ['准备两列数据：ds(日期)和y(目标值)', '创建Prophet模型，指定季节性和节假日', 'model.fit()训练模型', 'model.make_future_dataframe()创建未来日期', 'model.predict()生成预测和置信区间', 'model.plot_components()可视化趋势/季节分解'],
            'useCases': ['业务KPI预测', '网站流量预测', '产品需求预测', '财务指标预测'],
            'tips': 'Prophet对缺失值、异常值和趋势变化很鲁棒。添加中国节假日用Prophet(holidays=holidays_df)。预测不确定性区间来自趋势的MCMC采样。'
        },
        {
            'name': 'LSTM/GRU', 'brief': '深度学习时序预测模型，擅长捕捉长期依赖和非线性模式',
            'description': 'LSTM（长短期记忆网络）通过三个门控单元（遗忘门、输入门、输出门）解决RNN的长程梯度消失问题。GRU（门控循环单元）是其简化版，合并遗忘和输入门为更新门，参数更少训练更快。对于复杂非线性时序模式，LSTM/GRU通常优于传统统计方法，但需要更多数据和调参。',
            'formulas': [
                {'name': 'LSTM门控方程', 'latex': 'f_t=sigma(W_f*[h_{t-1},x_t]), i_t=sigma(W_i*[h_{t-1},x_t]), o_t=sigma(W_o*[h_{t-1},x_t])', 'explanation': '遗忘门f决定丢弃什么信息，输入门i决定存储什么新信息，输出门o决定输出什么。sigma为sigmoid函数。'},
                {'name': 'GRU更新方程', 'latex': 'z_t=sigma(W_z*[h_{t-1},x_t]), r_t=sigma(W_r*[h_{t-1},x_t])', 'explanation': 'z_t更新门控制历史信息保留比例，r_t重置门控制忽略多少历史。比LSTM少一个门。'}
            ],
            'code': '"""LSTM多步时间序列预测 - PyTorch"""\nimport numpy as np\nimport torch\nimport torch.nn as nn\n\n# 模拟数据\nnp.random.seed(42)\ndata = np.sin(np.linspace(0, 20*np.pi, 1000)) + 0.1*np.random.randn(1000)\n\n# 创建滑动窗口数据集\ndef create_sequences(data, seq_len=50):\n    X, y = [], []\n    for i in range(len(data)-seq_len):\n        X.append(data[i:i+seq_len])\n        y.append(data[i+seq_len])\n    return np.array(X), np.array(y)\n\nX, y = create_sequences(data, 50)\nX = torch.FloatTensor(X).unsqueeze(-1)  # [samples, seq_len, features=1]\ny = torch.FloatTensor(y).unsqueeze(-1)\n\nclass LSTMPredictor(nn.Module):\n    def __init__(self, input_size=1, hidden=64, layers=2):\n        super().__init__()\n        self.lstm = nn.LSTM(input_size, hidden, layers, batch_first=True)\n        self.fc = nn.Linear(hidden, 1)\n\n    def forward(self, x):\n        out, _ = self.lstm(x)\n        return self.fc(out[:, -1, :])\n\nmodel = LSTMPredictor()\noptimizer = torch.optim.Adam(model.parameters(), lr=0.001)\nloss_fn = nn.MSELoss()\n\nfor epoch in range(100):\n    model.train()\n    optimizer.zero_grad()\n    loss = loss_fn(model(X[:800]), y[:800])\n    loss.backward()\n    optimizer.step()\n\nmodel.eval()\nwith torch.no_grad():\n    pred = model(X[800:])\n    mse = loss_fn(pred, y[800:])\nprint(f"测试集MSE: {mse.item():.4f}")',
            'steps': ['数据预处理：归一化/标准化到[0,1]或N(0,1)', '创建滑动窗口：用过去N个时间步预测未来M步', '设计LSTM网络：输入层→LSTM层(含Dropout)→全连接输出层', '训练：Adam优化器+MSE损失，早停防止过拟合', '评估：在测试集上计算RMSE/MAE/MAPE'],
            'useCases': ['股票价格预测', '能源负荷预测', '交通流量预测', '自然语言处理(文本生成)'],
            'tips': '数据量少(<1000)时LSTM不如ARIMA。必须归一化输入。使用Dropout(0.2-0.5)防止过拟合。GRU训练更快但LSTM在长序列上效果略好。'
        },
        {
            'name': 'XGBoost', 'brief': '梯度提升树模型，表格数据预测的王者算法',
            'description': 'XGBoost（eXtreme Gradient Boosting）由陈天奇于2016年提出，是Kaggle竞赛中获奖最多的算法之一。相比传统GBDT，XGBoost引入了正则化项防止过拟合、列采样、加权分位数草图等技术，训练速度和精度都大幅提升。对于表格数据的回归/分类任务，XGBoost通常优于深度学习方法，且可解释性更好（特征重要性+SHAP值）。',
            'formulas': [
                {'name': '目标函数', 'latex': 'Obj = sum_i L(y_i, yhat_i) + sum_k Omega(f_k)', 'explanation': '第一项为损失函数（如MSE），第二项为正则化项（叶子节点数+L2正则），防止过拟合。'},
                {'name': '二阶泰勒展开', 'latex': 'Obj^{(t)} = sum_i [g_i*f_t(x_i) + 0.5*h_i*f_t(x_i)^2] + Omega(f_t)', 'explanation': 'g_i和h_i分别为一阶和二阶梯度，XGBoost用二阶信息比GBDT更精确。'}
            ],
            'code': '"""XGBoost时间序列预测（特征工程方法）"""\nimport numpy as np\nimport pandas as pd\nimport xgboost as xgb\nfrom sklearn.metrics import mean_squared_error\n\n# 模拟数据\nnp.random.seed(42)\nt = np.arange(200)\ny = 10 + 0.5*t + 5*np.sin(t/10) + np.random.normal(0, 3, 200)\n\n# 特征工程：滞后特征+滚动统计\ndef make_features(data, lags=[1,2,3,7,14]):\n    df = pd.DataFrame({"y": data})\n    for lag in lags:\n        df[f"lag_{lag}"] = df["y"].shift(lag)\n    df["rolling_mean_7"] = df["y"].shift(1).rolling(7).mean()\n    df["rolling_std_7"] = df["y"].shift(1).rolling(7).std()\n    return df.dropna()\n\ndf = make_features(y)\nX = df.drop("y", axis=1).values\ny_target = df["y"].values\n\n# 训练/测试分割\ntrain_n = 150\nmodel = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1)\nmodel.fit(X[:train_n], y_target[:train_n])\npred = model.predict(X[train_n:])\nprint(f"测试RMSE: {np.sqrt(mean_squared_error(y_target[train_n:], pred)):.3f}")',
            'steps': ['特征工程：构造滞后特征(lag1/lag7/lag30)、滚动统计(mean/std)、时间特征(月/星期/季度)', '划分训练集和测试集（时序数据不能随机划分！）', '训练XGBoost模型并调参（max_depth/learning_rate/n_estimators）', '特征重要性分析，筛选有效特征', '在测试集上评估，必要时做残差分析'],
            'useCases': ['销量/需求预测', '房价预测', '客户流失预测', '信用评分卡'],
            'tips': '时序预测需特别注意：不能随机交叉验证！用时间序列交叉验证(TimeSeriesSplit)。特征工程比模型调参更重要。学习率0.01-0.1，max_depth 3-7。'
        }
    ]
}))

# ====== 3. 评价模型 ======
cats.append(('03_evaluation.json', {
    'id': 'evaluation', 'name': '评价模型', 'color': '#FF7D00',
    'description': '建立评价指标体系，对多个备选方案进行综合排序或优劣判断。',
    'definition': '评价模型用于对多个对象或方案进行综合评判和排序。核心步骤：建立评价指标体系→指标标准化（无量纲化）→确定权重→综合评分与排序。广泛应用于供应商选择、绩效评估、城市排名等场景。',
    'algorithms': [
        {
            'name': 'TOPSIS', 'brief': '逼近理想解排序法，根据方案与正负理想解的距离进行排序',
            'description': 'TOPSIS（Technique for Order Preference by Similarity to Ideal Solution）由 Hwang 和 Yoon 于1981年提出。核心思想：最优方案应同时最接近正理想解（各指标最优值）且最远离负理想解（各指标最差值）。通过计算每个方案的相对贴近度进行排序，贴近度越接近1越好。TOPSIS对样本量和指标数无严格限制，计算简单直观。',
            'formulas': [
                {'name': '贴近度计算', 'latex': 'S_i = D_i^- / (D_i^+ + D_i^-)', 'explanation': 'D_i+为方案i到正理想解的欧氏距离，D_i-为到负理想解的距离。S_i在[0,1]之间，越接近1越优。'},
                {'name': '加权距离', 'latex': 'D_i^+ = sqrt(sum_j w_j*(z_{ij}-z_j^+)^2)', 'explanation': 'w_j为第j个指标的权重（可用熵权法/AHP确定），z_{ij}为标准化后的指标值。'}
            ],
            'code': '"""TOPSIS综合评价 - 供应商选择"""\nimport numpy as np\n\n# 5个供应商×4个指标（价格、质量、交货准时率、售后服务）\ndata = np.array([\n    [120, 0.85, 0.92, 0.78],\n    [100, 0.90, 0.88, 0.85],\n    [135, 0.82, 0.95, 0.72],\n    [110, 0.88, 0.85, 0.90],\n    [125, 0.86, 0.90, 0.80],\n])\ndirections = [-1, 1, 1, 1]  # -1成本型，1效益型\n\n# 正向化\nX = data.copy()\nfor j, d in enumerate(directions):\n    if d == -1:\n        X[:, j] = X[:, j].max() - X[:, j]\n\n# 向量归一化\nX_norm = X / np.sqrt((X**2).sum(axis=0))\n\n# 熵权法\np = X_norm / X_norm.sum(axis=0)\nE = -np.sum(p * np.log(p + 1e-10), axis=0) / np.log(len(X_norm))\nw = (1 - E) / (1 - E).sum()\nprint(f"权重: {w.round(4)}")\n\n# TOPSIS\nbest = np.max(X_norm * w, axis=0)\nworst = np.min(X_norm * w, axis=0)\nd_best = np.sqrt(((X_norm * w - best)**2).sum(axis=1))\nd_worst = np.sqrt(((X_norm * w - worst)**2).sum(axis=1))\nS = d_worst / (d_best + d_worst)\nrank = np.argsort(-S) + 1\nfor i, r in enumerate(rank):\n    print(f"排名{r}: 供应商{i+1} (贴近度={S[i]:.4f})")',
            'steps': ['建立评价矩阵：m个方案×n个指标', '指标正向化：成本型指标转化为效益型', '标准化消除量纲（向量归一化或极差变换）', '确定权重（熵权法/AHP/CRITIC）', '计算加权标准化矩阵', '确定正/负理想解', '计算各方案贴近度并排序'],
            'useCases': ['供应商/合作伙伴选择', '城市宜居度排名', '投资项目评估', '教学质量评估'],
            'tips': 'TOPSIS要求指标间独立（无强相关性）。当指标数远大于方案数时，先用PCA降维。结合熵权法可实现完全客观评价。'
        },
        {
            'name': '熵权法', 'brief': '基于数据信息熵的客观赋权方法，指标差异越大权重越高',
            'description': '熵权法的核心思想来自信息论：信息熵衡量数据的不确定性。某个指标下各方案的数值差异越大（信息熵越小），说明该指标提供的区分信息越多，权重应越高。反之，若各方案在某指标上数值相同（熵=1），则该指标对区分方案无贡献，权重为0。熵权法完全基于数据本身，避免了主观偏差。',
            'formulas': [
                {'name': '信息熵', 'latex': 'E_j = -(1/ln m) * sum_i p_{ij} * ln(p_{ij})', 'explanation': 'm为方案数，p_{ij}为第i个方案在第j个指标上的比重。E_j在[0,1]之间，越小信息量越大。'},
                {'name': '熵权', 'latex': 'w_j = (1 - E_j) / sum_k (1 - E_k)', 'explanation': '1-E_j为信息效用值。权重之和为1。'}
            ],
            'code': '"""熵权法 - 客观权重计算"""\nimport numpy as np\n\n# 标准化评价矩阵 (5方案×4指标)\nX = np.array([\n    [0.8, 0.6, 0.9, 0.7],\n    [0.9, 0.8, 0.7, 0.9],\n    [0.6, 0.9, 0.8, 0.6],\n    [0.7, 0.7, 0.9, 0.8],\n    [0.9, 0.5, 0.6, 0.9],\n])\n\n# 计算比重矩阵\nP = X / X.sum(axis=0)\n\n# 计算各指标信息熵\nn = len(X)\nE = -np.sum(P * np.log(P + 1e-10), axis=0) / np.log(n)\n\n# 熵权\nW = (1 - E) / (1 - E).sum()\nfor j, (e, w) in enumerate(zip(E, W)):\n    print(f"指标{j+1}: 熵={e:.4f}, 权重={w:.4f}")',
            'steps': ['指标标准化（消除量纲和正负向差异）', '计算各方案在各指标下的比重p_{ij}', '计算每个指标的信息熵E_j', '计算信息效用值d_j=1-E_j', '归一化得到权重w_j=d_j/sum(d_j)'],
            'useCases': ['多指标综合评价中的权重确定', '与TOPSIS/VIKOR等方法配合使用', '特征筛选（剔除低权重指标）'],
            'tips': '熵权法要求各指标值非负。需先处理负向指标（正向化）。所有方案在某指标上相等时熵为1、权重为0，这是合理的（该指标无区分力）。'
        },
        {
            'name': 'AHP层次分析法', 'brief': '通过两两比较构建判断矩阵，将主观判断量化为权重',
            'description': 'AHP（Analytic Hierarchy Process）由 Thomas Saaty 于1970年代提出。核心是将复杂决策问题分解为目标层→准则层→方案层三个层次，通过两两比较（1-9标度法）构建判断矩阵，计算特征向量得到权重，并通过一致性比率CR检验判断的合理性。AHP适合指标数量较少（<9个）且需要融合专家经验的主观评价场景。',
            'formulas': [
                {'name': '两两比较矩阵', 'latex': 'A = [a_{ij}], a_{ij}=1/a_{ji}, a_{ii}=1', 'explanation': 'a_{ij}表示指标i相对j的重要性（1=同等，3=稍重要，5=明显重要，7=强烈重要，9=极端重要）。'},
                {'name': '一致性检验', 'latex': 'CR = CI/RI, CI=(lambda_max-n)/(n-1)', 'explanation': 'lambda_max为最大特征值，n为矩阵阶数，RI为随机一致性指标。CR<0.1通过检验。'}
            ],
            'code': '"""AHP层次分析法"""\nimport numpy as np\n\n# 判断矩阵（4个指标的两两比较）\nA = np.array([\n    [1,   3,   5,   7],\n    [1/3, 1,   3,   5],\n    [1/5, 1/3, 1,   3],\n    [1/7, 1/5, 1/3, 1],\n])\n\n# 特征向量法求权重（和积法）\ncol_sum = A.sum(axis=0)\nB = A / col_sum  # 归一化\nw = B.mean(axis=1)  # 行平均=权重\n\n# 一致性检验\nn = len(A)\nlambda_max = ((A @ w) / w).mean()\nCI = (lambda_max - n) / (n - 1)\nRI_dict = {1:0, 2:0, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41}\nCR = CI / RI_dict[n]\n\nprint(f"权重: {w.round(4)}")\nprint(f"lambda_max={lambda_max:.4f}, CI={CI:.4f}, CR={CR:.4f}")\nprint("一致性检验:" + ("通过" if CR < 0.1 else "不通过"))',
            'steps': ['建立递阶层次结构（目标-准则-方案）', '构造两两比较判断矩阵（1-9标度）', '计算权重向量（特征向量法/和积法）', '一致性检验（CR<0.1通过）', '层次总排序（各层权重合成）'],
            'useCases': ['供应商选择', '投资决策', '人才评价', '政策方案评估'],
            'tips': '每层指标数不超过9个（超过会导致判断不一致）。多位专家打分时取几何平均。CR>0.1需重新调整判断矩阵。AHP可与其他方法结合（AHP-TOPSIS）。'
        }
    ]
}))

# ====== 4. 分类与聚类 ======
cats.append(('04_classification.json', {
    'id': 'classification-clustering', 'name': '分类与聚类', 'color': '#722ED1',
    'description': '将数据按其特征分门别类。分类是监督学习（已知类别标签），聚类是无监督学习（自动发现自然分组）。',
    'definition': '分类是根据已知标签的训练数据学习判别规则，对新样本预测类别。聚类是在无标签情况下，根据样本间相似性自动将数据划分为若干组，使组内相似、组间差异最大。两者是数据挖掘的两大核心任务。',
    'algorithms': [
        {
            'name': '逻辑回归', 'brief': '最基础的二分类模型，输出概率值，可解释性强',
            'description': '逻辑回归虽然名字带"回归"，实际上是分类模型。通过 Sigmoid 函数将线性组合 z=beta_0+beta_1*x_1+... 映射到 (0,1) 区间，输出 P(y=1|x) 的概率。决策边界是线性的，适合特征与目标呈单调关系的场景。作为分类问题的基线模型，逻辑回归计算快、可解释性强（系数即特征影响方向）。',
            'formulas': [
                {'name': 'Sigmoid函数', 'latex': 'P(y=1|x) = 1 / (1 + exp(-z)), z = beta_0 + sum beta_i*x_i', 'explanation': 'z为线性组合，通过Sigmoid映射为概率。P>0.5判为1类，<0.5判为0类。'},
                {'name': '对数似然损失', 'latex': 'L = -sum [y_i*ln(p_i) + (1-y_i)*ln(1-p_i)]', 'explanation': '交叉熵损失，衡量预测概率与真实标签的差距。通过梯度下降最小化。'}
            ],
            'code': '"""逻辑回归 - 信用卡违约预测"""\nimport numpy as np\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.metrics import accuracy_score, roc_auc_score\n\nnp.random.seed(42)\nn = 1000\nX = np.random.randn(n, 5)\n# 生成标签：前两个特征+噪声决定违约概率\ny = (X[:,0] + 2*X[:,1] + np.random.randn(n)*0.5 > 0).astype(int)\n\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)\n\nmodel = LogisticRegression()\nmodel.fit(X_train, y_train)\ny_prob = model.predict_proba(X_test)[:, 1]\ny_pred = model.predict(X_test)\n\nprint(f"准确率: {accuracy_score(y_test, y_pred):.3f}")\nprint(f"AUC: {roc_auc_score(y_test, y_prob):.3f}")\nprint(f"特征系数: {model.coef_[0].round(4)}")',
            'steps': ['数据预处理：标准化/归一化特征', '划分训练集和测试集', '训练逻辑回归模型', '评估：准确率/AUC/混淆矩阵/F1', '解释：系数符号表示特征影响方向'],
            'useCases': ['信用违约预测', '疾病诊断', '垃圾邮件检测', '用户点击率预估'],
            'tips': '特征共线性会影响系数解释，用VIF检验。对于非线性关系，可构造多项式特征或使用GBDT。类别不平衡时设置class_weight="balanced"。'
        },
        {
            'name': 'K-means聚类', 'brief': '最经典的聚类算法，将数据划分为K个簇，最小化簇内平方和',
            'description': 'K-means由 Lloyd 于1957年提出，是最广泛使用的聚类算法。核心思想：随机选K个初始质心→将每个点分配到最近的质心→重新计算质心→重复直到收敛。算法简单高效（O(n*K*d)），但需要预设K值，对初始质心敏感，只能发现球形簇。',
            'formulas': [
                {'name': '聚类目标函数', 'latex': 'min sum_{k=1}^K sum_{x in C_k} ||x - mu_k||^2', 'explanation': '最小化每个点到其所属簇质心的平方距离之和（簇内平方和WCSS）。'},
                {'name': '质心更新', 'latex': 'mu_k = (1/|C_k|) * sum_{x in C_k} x', 'explanation': '质心为簇内所有点的均值。每次迭代后重新计算。'}
            ],
            'code': '"""K-means客户分群+肘部法则\"\"\"\nimport numpy as np\nfrom sklearn.cluster import KMeans\nfrom sklearn.preprocessing import StandardScaler\nimport matplotlib.pyplot as plt\n\n# 模拟RFM数据\nnp.random.seed(42)\nn = 500\nrfm = np.column_stack([\n    np.random.exponential(30, n),   # Recency\n    np.random.poisson(8, n),        # Frequency\n    np.random.normal(500, 150, n)   # Monetary\n])\n\nX = StandardScaler().fit_transform(rfm)\n\n# 肘部法则选K\ninertias = []\nfor k in range(1, 11):\n    km = KMeans(n_clusters=k, random_state=42, n_init=10)\n    km.fit(X)\n    inertias.append(km.inertia_)\n\n# K=3聚类\nkmeans = KMeans(n_clusters=3, random_state=42, n_init=10)\nlabels = kmeans.fit_predict(X)\nprint(f"各簇样本数: {np.bincount(labels)}\")\nprint(f"质心: {kmeans.cluster_centers_.round(3)}")',
            'steps': ['数据标准化（必须做！距离算法对尺度敏感）', '肘部法则或轮廓系数确定最优K值', '随机初始化K个质心', '分配：每个点到最近质心', '更新：重新计算各簇质心', '重复4-5直到质心不再变化或达最大迭代'],
            'useCases': ['客户分群/用户画像', '图像压缩（颜色量化）', '文档聚类', '异常检测（远离簇心的点）'],
            'tips': '必须标准化数据！K-means对异常值敏感（质心会被拉偏）。用K-means++初始化改善收敛质量。非球形簇用DBSCAN或谱聚类。'
        },
        {
            'name': 'DBSCAN', 'brief': '基于密度的聚类算法，可发现任意形状簇并自动识别噪声',
            'description': 'DBSCAN（Density-Based Spatial Clustering of Applications with Noise）由 Ester 等人于1996年提出。核心是密度可达概念：ε-邻域内包含至少MinPts个点的称为核心点，核心点之间通过密度可达连接形成簇，无法连接到任何簇的点标记为噪声。DBSCAN不需要预设簇数K，可发现任意形状的簇，天然具有异常检测能力。',
            'formulas': [
                {'name': '核心点定义', 'latex': 'N_eps(p) = {q in D | dist(p,q) <= eps}, |N_eps(p)| >= MinPts', 'explanation': '以p为中心、eps为半径的邻域内至少有MinPts个点，则p为核心点。'},
                {'name': '密度可达', 'latex': 'p->q iff chain p=p1,...,pn=q, p_{i+1} in N_eps(p_i), p_i is core', 'explanation': '存在一系列核心点连接p和q，则q从p密度可达。同一簇内所有点相互密度连通。'}
            ],
            'code': '"""DBSCAN聚类 - 任意形状簇发现"""\nimport numpy as np\nfrom sklearn.cluster import DBSCAN\nfrom sklearn.datasets import make_moons\n\n# 生成月牙形数据（K-means无法正确聚类）\nX, _ = make_moons(n_samples=300, noise=0.08, random_state=42)\n\n# DBSCAN聚类\nmodel = DBSCAN(eps=0.2, min_samples=5)\nlabels = model.fit_predict(X)\n\nn_clusters = len(set(labels)) - (1 if -1 in labels else 0)\nn_noise = list(labels).count(-1)\nprint(f"发现{ n_clusters}个簇, {n_noise}个噪声点")\nprint(f"簇标签分布: {np.bincount(labels + 1)}")',
            'steps': ['选择合适的距离度量（欧氏/曼哈顿/余弦）', '确定eps和MinPts参数（k-distance图）', '找出所有核心点', '从核心点出发，通过密度可达扩展簇', '标记无法连接到任何簇的点为噪声'],
            'useCases': ['地理空间聚类', '异常检测/欺诈发现', '图像分割', '社交网络社区发现'],
            'tips': 'eps和MinPts的选择至关重要：用k-distance图（k=MinPts）找肘点确定eps。数据维度高时用PCA降维后再聚类。数据密度差异大时DBSCAN效果差。'
        }
    ]
}))

# ====== 5. 微分方程 ======
cats.append(('05_differential.json', {
    'id': 'differential-equations', 'name': '微分方程', 'color': '#F53F3F',
    'description': '用微分方程描述系统的动态变化规律，是连续系统建模的核心工具。',
    'definition': '微分方程模型通过建立变量变化率之间的关系来描述系统的动态行为。常微分方程（ODE）描述单变量随时间变化，偏微分方程（PDE）描述多变量时空演化。广泛应用于人口动力学、传染病建模、物理过程模拟等。',
    'algorithms': [
        {
            'name': 'Euler法', 'brief': '最基础的ODE数值解法，用差分近似微分',
            'description': 'Euler法是最简单的一阶数值求解方法。核心思想：将连续时间离散为步长h，用当前点的导数近似下一时刻的值：y_{n+1}=y_n+h*f(t_n,y_n)。实现极其简单但精度较低（一阶），全局误差为O(h)。适合教学理解数值求解原理，实际应用推荐RK4。',
            'formulas': [
                {'name': 'Euler递推公式', 'latex': 'y_{n+1} = y_n + h * f(t_n, y_n)', 'explanation': 'h为步长，f(t,y)=dy/dt。本质是用矩形面积近似积分。步长越小精度越高但计算量越大。'},
                {'name': '局部截断误差', 'latex': 'e_n = O(h^2)', 'explanation': '每步误差正比于h^2，经过N步后全局误差累积为O(h)。'}
            ],
            'code': '"""Euler法求解ODE - Logistic增长模型"""\nimport numpy as np\nimport matplotlib.pyplot as plt\n\n# dN/dt = r*N*(1-N/K)\ndef logistic(t, N, r=0.5, K=1000):\n    return r * N * (1 - N / K)\n\n# Euler法\ndef euler(f, y0, t_span, h):\n    t0, t_end = t_span\n    ts = np.arange(t0, t_end + h, h)\n    ys = np.zeros(len(ts))\n    ys[0] = y0\n    for i in range(len(ts) - 1):\n        ys[i+1] = ys[i] + h * f(ts[i], ys[i])\n    return ts, ys\n\nts, ys = euler(logistic, y0=10, t_span=(0, 20), h=0.5)\nprint(f"最终种群: {ys[-1]:.0f} (容量K=1000)")',
            'steps': ['确定微分方程 dy/dt = f(t,y) 和初值 y(t0)=y0', '选择步长h（步长越小精度越高但计算量越大）', '从t0开始，y_{n+1}=y_n+h*f(t_n,y_n)迭代', '直到到达终止时间t_end'],
            'useCases': ['教学演示', '快速原型验证', '简单ODE的粗略估计'],
            'tips': 'Euler法精度低，不建议用于实际项目。步长过大可能导致数值不稳定（解发散）。改进的Euler法（中点法）精度提升为二阶。'
        },
        {
            'name': 'Runge-Kutta(RK4)', 'brief': '四阶ODE求解器，精度和效率的黄金平衡点',
            'description': '四阶Runge-Kutta法（RK4）是求解ODE最常用的方法。每步计算4个斜率估计值（起点的k1、中点的k2和k3、终点的k4），加权平均得到最终斜率。全局误差为O(h^4)，精度远高于Euler法且实现仍较简单。RK4是SciPy odeint的默认方法，适合绝大多数非刚性ODE问题。',
            'formulas': [
                {'name': 'RK4递推公式', 'latex': 'y_{n+1} = y_n + (h/6)*(k1+2k2+2k3+k4)', 'explanation': 'k1=h*f(t_n,y_n), k2=h*f(t_n+h/2,y_n+k1/2), k3=h*f(t_n+h/2,y_n+k2/2), k4=h*f(t_n+h,y_n+k3)。'},
                {'name': '全局误差', 'latex': 'e_{global} = O(h^4)', 'explanation': '步长减半，误差约减小16倍。h=0.01时可得较高精度。'}
            ],
            'code': '"""RK4法求解SIR传染病模型"""\nimport numpy as np\n\ndef sir(t, y, beta=0.3, gamma=0.1):\n    S, I, R = y\n    N = S + I + R\n    return [-beta*S*I/N, beta*S*I/N - gamma*I, gamma*I]\n\ndef rk4(f, y0, t_span, h):\n    t0, t_end = t_span\n    ts = np.arange(t0, t_end + h, h)\n    ys = np.zeros((len(ts), len(y0)))\n    ys[0] = y0\n    for i in range(len(ts) - 1):\n        t, y = ts[i], ys[i]\n        k1 = np.array(f(t, y))\n        k2 = np.array(f(t + h/2, y + h*k1/2))\n        k3 = np.array(f(t + h/2, y + h*k2/2))\n        k4 = np.array(f(t + h, y + h*k3))\n        ys[i+1] = y + h/6 * (k1 + 2*k2 + 2*k3 + k4)\n    return ts, ys\n\nts, ys = rk4(sir, [9999, 1, 0], (0, 100), h=0.1)\npeak_day = ts[np.argmax(ys[:,1])]\nprint(f"感染峰值: 第{peak_day:.0f}天, 最大感染人数: {ys[:,1].max():.0f}")',
            'steps': ['定义ODE系统 y\'=f(t,y) 和初值', '选择步长h（常用0.01-0.1）', '每步计算k1(起点斜率)、k2/k3(中点斜率)、k4(终点斜率)', '加权平均更新y_{n+1}', '重复直到终止时间'],
            'useCases': ['天体轨道模拟', '化学反应动力学', '电路仿真', 'SIR/SEIR传染病建模'],
            'tips': 'RK4是刚性不大的ODE问题的首选方法。对于刚性ODE（如化学反应中快慢时间尺度混合），用隐式方法（如odeint的BDF求解器）。SciPy推荐用solve_ivp代替odeint。'
        },
        {
            'name': '有限差分法', 'brief': '求解偏微分方程(PDE)的核心数值方法，将导数离散化为差分',
            'description': '有限差分法（Finite Difference Method）将连续的PDE在空间和时间上离散化为网格，用差分商(f(x+h)-f(x))/h近似导数，将PDE转化为代数方程组。Crank-Nicolson隐格式是无条件稳定的经典格式，广泛用于热传导方程。FDM概念直观、实现方便，是PDE数值求解的入门首选。',
            'formulas': [
                {'name': '中心差分(二阶精度)', 'latex': 'f\'\'(x) \\approx (f(x+h) - 2f(x) + f(x-h)) / h^2', 'explanation': '用三点近似二阶导数，截断误差O(h^2)。比前向/后向差分精度高。'},
                {'name': 'Crank-Nicolson格式', 'latex': '(u^{n+1}_j-u^n_j)/dt = 0.5*(D_xx u^{n+1}_j + D_xx u^n_j)', 'explanation': '时间上取两步平均，无条件稳定。每个时间步需求解三对角线性方程组。'}
            ],
            'code': '"""有限差分法 - 一维热传导方程"""\nimport numpy as np\n\n# du/dt = alpha * d^2u/dx^2, x in [0,L], t in [0,T]\nL, T, alpha = 1.0, 0.5, 0.01\nnx, nt = 50, 500\ndx, dt = L/(nx-1), T/nt\nx = np.linspace(0, L, nx)\n\n# 初始条件: 中间高温\ntemp = np.sin(np.pi * x / L)\ntemp_new = temp.copy()\n\n# FTCS显式格式\nfor n in range(nt):\n    for i in range(1, nx-1):\n        temp_new[i] = temp[i] + alpha*dt/dx**2 * (temp[i+1] - 2*temp[i] + temp[i-1])\n    temp = temp_new.copy()\n\nprint(f"最终温度分布: 中心={temp[nx//2]:.3f}, 边缘={temp[0]:.3f}")',
            'steps': ['确定求解域和边界条件（Dirichlet/Neumann）', '网格剖分：空间步长dx和时间步长dt', '选择差分格式（显式/隐式/Crank-Nicolson）', '稳定性条件检查（显式FTCS: dt <= dx^2/(2*alpha)）', '逐时间步求解线性方程组'],
            'useCases': ['热传导模拟', '扩散过程', '期权定价（Black-Scholes方程）', '波动方程'],
            'tips': '显式格式有条件稳定，需满足CFL条件。隐式格式无条件稳定但需求解方程组。Crank-Nicolson兼顾精度和稳定性。'
        }
    ]
}))

# ====== 6. 统计模型 ======
cats.append(('06_statistics.json', {
    'id': 'statistics', 'name': '统计模型', 'color': '#0FC6C2',
    'description': '基于概率统计理论，从数据中推断总体特征、检验假设、发现变量间关系。',
    'definition': '统计模型运用概率论和数理统计方法，通过样本数据对总体进行推断。包括描述统计（数据概括）、推断统计（参数估计/假设检验）和关系建模（回归/方差分析）。是所有数据分析和建模的基础。',
    'algorithms': [
        {
            'name': 'OLS回归', 'brief': '最小二乘线性回归，通过最小化残差平方和估计回归系数',
            'description': '普通最小二乘法（Ordinary Least Squares）是回归分析的基础。核心是通过最小化 sum(y_i - yhat_i)^2 来估计回归系数 beta。OLS有解析解 beta_hat = (X^T X)^{-1} X^T y，不需要迭代。OLS是BLUE（最佳线性无偏估计），前提是满足高斯-马尔可夫假设（线性、满秩、外生性、同方差、无自相关）。',
            'formulas': [
                {'name': 'OLS估计量', 'latex': 'beta_hat = (X^T X)^{-1} X^T y', 'explanation': '最小化残差平方和的解析解。X需满秩（无完全共线性）。'},
                {'name': 'R方决定系数', 'latex': 'R^2 = 1 - SS_res / SS_tot', 'explanation': '模型解释的变异比例，0~1之间。越高拟合越好但要注意过拟合。'}
            ],
            'code': '"""OLS回归 - 房价预测"""\nimport numpy as np\nimport statsmodels.api as sm\n\nnp.random.seed(42)\nn = 200\narea = np.random.normal(120, 30, n)\nage = np.random.uniform(0, 30, n)\nrooms = np.random.randint(2, 6, n)\nprice = 50 + 2.5*area - 1.2*age + 15*rooms + np.random.normal(0, 20, n)\n\nX = sm.add_constant(np.column_stack([area, age, rooms]))\nmodel = sm.OLS(price, X).fit()\nprint(model.summary().tables[1])  # 系数表',
            'steps': ['探索性数据分析（散点图、相关性矩阵）', '拟合OLS模型', '检查残差（正态性、同方差、独立性）', '检查多重共线性（VIF<10）', '解释系数并做显著性检验'],
            'useCases': ['房价预测', '销售影响因素分析', '薪酬差异分析', '实验数据分析'],
            'tips': '使用statsmodels（提供完整统计推断）而非sklearn（侧重预测）。异方差时用稳健标准误（HC1/HC3）。离群值用Cook距离检测。'
        },
        {
            'name': '主成分分析(PCA)', 'brief': '最常用的降维方法，将高维数据投影到方差最大的方向',
            'description': 'PCA（Principal Component Analysis）通过正交变换将可能相关的变量转换为线性无关的主成分。第一主成分捕获数据最大方差方向，第二主成分与第一正交且捕获剩余最大方差，以此类推。PCA可用于降维（保留前k个主成分）、可视化（降到2/3维）和去噪（丢弃小方差成分）。',
            'formulas': [
                {'name': '协方差矩阵特征分解', 'latex': 'Sigma = Q * Lambda * Q^T', 'explanation': 'Lambda为特征值对角阵(方差)，Q的列为特征向量(主成分方向)。'},
                {'name': '方差解释率', 'latex': 'ratio_k = sum_{i=1}^k lambda_i / sum_{j=1}^p lambda_j', 'explanation': '前k个主成分解释的总方差比例。通常取累计>85%或通过碎石图肘点选k。'}
            ],
            'code': '"""PCA降维与可视化"""\nimport numpy as np\nfrom sklearn.decomposition import PCA\nfrom sklearn.preprocessing import StandardScaler\n\n# 模拟高维数据\nnp.random.seed(42)\nX = np.random.randn(200, 10)\nX[:, 0] = X[:, 0]*3  # 第1个特征方差大\nX[:, 1] = X[:, 0]*0.8 + X[:, 1]*0.5  # 特征1和2相关\n\nX_scaled = StandardScaler().fit_transform(X)\n\n# PCA降维\npca = PCA()\npca.fit(X_scaled)\nprint(f"各成分方差解释率: {pca.explained_variance_ratio_.round(4)}")\nprint(f"前3个成分累计: {pca.explained_variance_ratio_[:3].sum():.2%}")',
            'steps': ['数据标准化（PCA对尺度敏感！）', '计算协方差矩阵或直接SVD分解', '按特征值大小排序，选择前k个主成分', '将原始数据投影到主成分空间', '可视化并解释主成分含义'],
            'useCases': ['高维数据可视化', '特征降维/去噪', '基因表达数据分析', '问卷数据压缩'],
            'tips': '必须先标准化！PCA对异常值敏感。主成分是原始特征的线性组合，解释性较差——可用载荷矩阵辅助理解。对于非线性结构，用t-SNE/UMAP。'
        },
        {
            'name': '贝叶斯推断', 'brief': '基于贝叶斯定理的统计推断方法，融合先验知识和观测数据',
            'description': '贝叶斯推断与频率学派的核心区别在于将参数视为随机变量（有概率分布）。通过贝叶斯定理 P(theta|D) = P(D|theta)*P(theta)/P(D) 将先验信念P(theta)与数据似然P(D|theta)结合，得到后验分布P(theta|D)。贝叶斯方法天然支持不确定性量化（后验分布本身即答案），适合小样本和需要融入领域知识的场景。',
            'formulas': [
                {'name': '贝叶斯定理', 'latex': 'P(theta|D) = P(D|theta)*P(theta) / P(D)', 'explanation': '后验正比于似然×先验。P(D)为边缘似然（归一化常数），通常难以计算。'},
                {'name': '共轭先验', 'latex': 'Beta后验 = Beta(alpha+成功数, beta+失败数)', 'explanation': 'Beta分布是二项分布的共轭先验，后验同样是Beta分布，可解析求解。'}
            ],
            'code': '"""贝叶斯推断 - A/B测试转化率分析"""\nimport numpy as np\nfrom scipy import stats\n\n# 对照组A: 1000次展示, 100次点击\n# 实验组B: 1000次展示, 130次点击\nalpha_prior, beta_prior = 1, 1  # 无信息先验Beta(1,1)\n\n# 后验分布\nposterior_A = stats.beta(alpha_prior + 100, beta_prior + 900)\nposterior_B = stats.beta(alpha_prior + 130, beta_prior + 870)\n\n# B优于A的概率（蒙特卡洛估计）\nn_samples = 100000\nsamples_A = posterior_A.rvs(n_samples)\nsamples_B = posterior_B.rvs(n_samples)\nprob_b_better = (samples_B > samples_A).mean()\nprint(f"B转化率高于A的概率: {prob_b_better:.1%}")',
            'steps': ['确定似然函数（数据生成过程）', '选择先验分布（无信息先验/共轭先验/领域知识）', '计算后验分布（解析解/MCMC采样/变分推断）', '后验分析：均值/中位数/可信区间', '后验预测检查验证模型'],
            'useCases': ['A/B测试分析', '医学试验（小样本推断）', '信用风险评估', '气候变化归因'],
            'tips': '先验的选择会影响结论，需做先验敏感性分析。小数据时贝叶斯优势明显。对于复杂模型用MCMC（PyMC/Stan），简单模型可用共轭先验求解析解。'
        }
    ]
}))

# ====== 7. 图论与网络 ======
cats.append(('07_graphtheory.json', {
    'id': 'graph-theory', 'name': '图论与网络', 'color': '#F7BA1E',
    'description': '用节点和边抽象表示实体间的关系，研究网络结构、路径优化和传播动力学。',
    'definition': '图论模型将现实世界中的实体抽象为节点（顶点），关系抽象为边。通过研究图的拓扑性质和算法，解决路径规划、网络优化、社区发现等问题。在交通、社交网络、通信等领域有广泛应用。',
    'algorithms': [
        {
            'name': 'Dijkstra算法', 'brief': '求单源最短路径的贪心算法，要求边权非负',
            'description': 'Dijkstra算法由 Edsger Dijkstra 于1956年提出，是图论中最著名的算法之一。采用贪心策略：维护已确定最短距离的节点集合S，每次从未处理的节点中选择距离源点最近的节点加入S，并松弛其邻居的距离。使用优先队列（堆）可将复杂度优化到 O((V+E)log V)。',
            'formulas': [
                {'name': '松弛操作', 'latex': 'd[v] = min(d[v], d[u] + w(u,v))', 'explanation': '若通过u到v的距离比已知的d[v]更短，则更新。这是所有最短路径算法的核心操作。'}
            ],
            'code': '"""Dijkstra最短路径"""\nimport networkx as nx\n\nG = nx.Graph()\nedges = [("A","B",5), ("A","C",3), ("B","D",2), ("D","F",8), ("E","F",2)]\nfor u, v, w in edges:\n    G.add_edge(u, v, weight=w)\n\npath = nx.dijkstra_path(G, "A", "F", weight="weight")\ndist = nx.dijkstra_path_length(G, "A", "F", weight="weight")\nprint("最短路径:", " -> ".join(path), "距离=", dist)',
            'steps': ['初始化：源点距离=0，其他=无穷，所有节点未访问', '选择未访问节点中距离最小的u', '标记u为已访问', '对u的每个邻居v：若d[u]+w(u,v) < d[v]，更新d[v]', '重复2-4直到目标节点被访问'],
            'useCases': ['地图导航（GPS路径规划）', '网络路由协议（OSPF）', '游戏AI寻路', '物流配送路径优化'],
            'tips': '边权必须非负！负权边用Bellman-Ford算法。稠密图用邻接矩阵（O(V^2)），稀疏图用堆优化（O(E log V)）。NetworkX提供了完整实现。'
        },
        {
            'name': 'PageRank', 'brief': 'Google创始算法，通过随机游走模型评估节点重要性',
            'description': 'PageRank由 Larry Page 和 Sergey Brin 于1998年提出，是Google搜索引擎的基石。核心思想：一个网页的重要性取决于链接到它的其他网页的数量和质量。从随机冲浪模型出发，用户以概率d点击链接、以概率1-d随机跳转，平稳分布即为PageRank值。PageRank本质是图的平稳分布，可通过幂迭代求解。',
            'formulas': [
                {'name': 'PageRank迭代公式', 'latex': 'PR(p_i) = (1-d)/N + d * sum_{p_j in M(p_i)} PR(p_j)/L(p_j)', 'explanation': 'd为阻尼系数（通常0.85），M(p_i)为链接到p_i的页面集合，L(p_j)为p_j的出链数。'}
            ],
            'code': '"""PageRank - 社交网络影响力分析"""\nimport numpy as np\nimport networkx as nx\n\n# 创建社交网络\nG = nx.DiGraph()\nedges = [\n    (1,2), (2,3), (3,1),  # 三角形\n    (1,4), (4,5), (5,6), (6,4),  # 另一个圈子\n    (3,4)  # 桥梁\n]\nG.add_edges_from(edges)\n\npr = nx.pagerank(G, alpha=0.85)\nfor node, score in sorted(pr.items(), key=lambda x: -x[1]):\n    print(f"节点{node}: PageRank={score:.4f}")',
            'steps': ['构建有向图（节点=网页/用户，边=链接/关注关系）', '初始化所有节点PR值为1/N', '迭代更新：新PR = (1-d)/N + d*sum(入链PR/出度数)', '重复直到收敛（PR变化<阈值）'],
            'useCases': ['搜索引擎网页排序', '社交网络意见领袖识别', '学术论文引用分析', '蛋白质相互作用网络关键蛋白识别'],
            'tips': '阻尼系数d通常取0.85。死胡同节点（无出链）需特殊处理。对于无向图，PageRank退化为度中心性。NetworkX的pagerank函数支持个性化向量。'
        }
    ]
}))

# ====== 8. 随机模型 ======
cats.append(('08_stochastic.json', {
    'id': 'stochastic', 'name': '随机模型', 'color': '#168CFF',
    'description': '引入随机性和概率分布描述系统中的不确定性，包括蒙特卡洛模拟、马尔可夫链等。',
    'definition': '随机模型与确定性模型相对，显式引入随机变量和概率分布来描述系统的不确定性。核心思想是通过大量随机采样或概率转移来推断系统的统计行为。广泛应用于金融风险、排队系统、可靠性工程等领域。',
    'algorithms': [
        {
            'name': '蒙特卡洛模拟', 'brief': '通过大量随机采样近似计算确定性问题的数值解',
            'description': '蒙特卡洛方法（Monte Carlo）由 Ulam 和 von Neumann 于1940年代在曼哈顿计划中发展。核心思想：用大量随机样本的统计量近似确定性量。经典例子是用随机投点估计pi值。广泛应用于积分计算、风险分析(VaR)、物理模拟、优化等领域。误差收敛速度为 O(1/sqrt(N))，与维度无关——这是蒙特卡洛在高维问题中的独特优势。',
            'formulas': [
                {'name': 'MC积分估计', 'latex': 'I \\approx (b-a)/N * sum_{i=1}^N f(X_i), X_i ~ U(a,b)', 'explanation': '在[a,b]区间均匀采样N个点，用样本均值近似积分。高维积分MC方法远优于数值积分。'},
                {'name': '误差界', 'latex': '|error| \\approx sigma / sqrt(N)', 'explanation': 'sigma为f的标准差。精度正比于1/sqrt(N)，要提高1位小数需100倍样本。'}
            ],
            'code': '"""蒙特卡洛 - pi估计 + VaR风险分析"""\nimport numpy as np\n\n# 1. 投点法估计pi\nN = 100_000\nx, y = np.random.uniform(-1, 1, N), np.random.uniform(-1, 1, N)\ninside = x**2 + y**2 <= 1\npi_est = 4 * inside.sum() / N\nprint(f"pi估计: {pi_est:.6f} (误差: {abs(pi_est-np.pi):.6f})")\n\n# 2. VaR (Value at Risk) 投资风险分析\nnp.random.seed(42)\nreturns = np.random.normal(0.001, 0.02, (10000, 252))  # 10000个情景,252个交易日\nannual_returns = (1 + returns).prod(axis=1) - 1\nVaR_95 = np.percentile(annual_returns, 5)\nprint(f"95% VaR: {VaR_95:.2%} (有95%把握年损失不超过{-VaR_95:.2%})")',
            'steps': ['定义输入随机变量的概率分布', '从分布中大量采样（N>=10000）', '将每组样本代入模型计算输出', '汇总输出分布（均值/分位数/直方图）', '分析结果的统计精度（标准误差）'],
            'useCases': ['金融风险VaR/CVaR计算', '定积分/高维积分', '物理粒子输运模拟', '项目工期风险评估(PERT)'],
            'tips': '样本量N越大精度越高（误差~1/sqrt(N)）。使用拉丁超立方采样或Sobol序列（拟蒙特卡洛）可加速收敛。对于罕见事件概率估计，用重要性采样。'
        },
        {
            'name': 'MCMC', 'brief': '马尔可夫链蒙特卡洛，从复杂后验分布中采样的核心工具',
            'description': 'MCMC（Markov Chain Monte Carlo）是贝叶斯统计计算的核心工具。当后验分布P(theta|D)没有解析形式时，MCMC通过构造一条以目标分布为平稳分布的马尔可夫链来采样。Metropolis-Hastings算法是MCMC的基础：提议新状态→以概率 min(1, (后验比)*(提议比)) 接受→链收敛后样本近似来自目标分布。',
            'formulas': [
                {'name': 'MH接受概率', 'latex': 'alpha = min(1, P(theta_new|D)/P(theta_old|D) * q(theta_old|theta_new)/q(theta_new|theta_old))', 'explanation': '第一项为后验比（似然比×先验比），第二项为提议比（非对称提议时需调整）。对称提议时仅为后验比。'},
                {'name': 'Gelman-Rubin收敛诊断', 'latex': 'R_hat = sqrt( (W + B/W) / W ) < 1.1', 'explanation': '多链比较：W为链内方差，B为链间方差。R_hat接近1说明链已收敛。'}
            ],
            'code': '"""MCMC - Metropolis-Hastings估计正态均值后验"""\nimport numpy as np\nfrom scipy import stats\n\n# 数据: 观测值\nnp.random.seed(42)\ndata = np.random.normal(5, 2, 50)  # 真实均值=5, 标准差=2\n\n# MCMC采样\nn_iter = 20000\nchain = np.zeros(n_iter)\ncurrent = np.mean(data)  # 初始值\n\nfor i in range(n_iter):\n    # 提议：从正态分布中采样新值\n    proposal = current + np.random.normal(0, 0.5)\n    # 计算对数后验 (已知方差=4, 先验~N(0,10))\n    def log_posterior(mu):\n        log_lik = np.sum(stats.norm.logpdf(data, mu, 2))\n        log_prior = stats.norm.logpdf(mu, 0, 10)\n        return log_lik + log_prior\n    # MH接受/拒绝\n    log_alpha = log_posterior(proposal) - log_posterior(current)\n    if np.log(np.random.rand()) < log_alpha:\n        current = proposal\n    chain[i] = current\n\n# 后验分析（去除burn-in）\nburn_in = 2000\nposterior = chain[burn_in:]\nprint(f"后验均值: {posterior.mean():.3f}")\nprint(f"95%可信区间: [{np.percentile(posterior, 2.5):.3f}, {np.percentile(posterior, 97.5):.3f}]")',
            'steps': ['定义目标分布（后验=似然×先验）', '选择提议分布（常用正态随机游走）', '采样：提议新状态→计算接受概率→接受/拒绝', '预烧期(burn-in)：丢弃前若干迭代（链未收敛）', '收敛诊断：多链R_hat、迹图、自相关图', '后验分析：基于后验样本计算均值/分位数等'],
            'useCases': ['贝叶斯参数估计', '复杂后验分布采样', '隐变量模型推断', '物理系统配分函数估计'],
            'tips': '提议步长至关重要：太大接受率低（链不动），太小探索慢。目标接受率：单变量~0.44，多变量~0.23。实际应用推荐使用PyMC/Stan（自动调优+诊断）。'
        }
    ]
}))

print(f"Defined {len(cats)} categories")
print("Writing JSON files...")
for fname, data in cats:
    path = os.path.join(out, fname)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  {fname} -> {data['name']} ({len(data['algorithms'])} algorithms)")

print("Done!")
