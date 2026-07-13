"""
============================================================
知识库服务 — 数学建模 8 大分类教学知识库
============================================================
"""
from __future__ import annotations

# ============================================================
# 知识库静态数据 — 8 大模型分类
# 每类包含：定义、核心公式、适用场景、例题、推荐算法
# ============================================================

KNOWLEDGE_BASE = {
    "优化模型": {
        "id": "optimization",
        "name": "优化模型",
        "icon": "trend-charts",
        "color": "#165DFF",
        "description": "在给定约束条件下，寻找使目标函数达到最优（最大或最小）的决策方案。是数学建模中应用最广泛的模型类型之一。",
        "definition": "优化模型（Optimization Model）是研究如何在有限资源下做出最优决策的数学模型。它由三个核心要素组成：**决策变量**（可以控制的因素）、**目标函数**（想要最大化或最小化的指标）和**约束条件**（必须满足的限制）。",
        "core_formulas": [
            {
                "name": "线性规划标准型",
                "latex": "\\min \\; \\mathbf{c}^T\\mathbf{x} \\quad \\text{s.t.} \\quad A\\mathbf{x} \\leq \\mathbf{b}, \\; \\mathbf{x} \\geq 0",
                "explanation": "c 为目标系数向量，A 为约束矩阵，b 为右端常数向量，x 为决策变量。"
            },
            {
                "name": "多目标优化",
                "latex": "\\min \\; (f_1(\\mathbf{x}), f_2(\\mathbf{x}), \\ldots, f_k(\\mathbf{x})) \\quad \\text{s.t.} \\quad \\mathbf{x} \\in X",
                "explanation": "同时优化多个可能冲突的目标函数，通常使用加权法或 Pareto 最优解处理。"
            },
            {
                "name": "整数规划",
                "latex": "\\min \\; \\mathbf{c}^T\\mathbf{x} \\quad \\text{s.t.} \\quad A\\mathbf{x} \\leq \\mathbf{b}, \\; x_i \\in \\mathbb{Z}^+",
                "explanation": "决策变量限制为整数，常见于人员分配、设施选址等离散决策问题。"
            }
        ],
        "scenarios": [
            "生产计划与资源分配（如工厂排产、原材料采购）",
            "物流路径规划（如车辆调度、配送中心选址）",
            "投资组合优化（如最大化收益、最小化风险）",
            "人员排班与任务分配",
            "供应链网络设计"
        ],
        "example": {
            "title": "生产计划优化",
            "problem": "某工厂生产 A、B 两种产品。每件 A 利润 40 元，需 2 小时加工 + 3kg 原料；每件 B 利润 30 元，需 1 小时加工 + 4kg 原料。每天加工能力 100 小时，原料 120kg。如何安排生产使利润最大？",
            "solution": "设 x₁ 为 A 产量，x₂ 为 B 产量 → max Z = 40x₁ + 30x₂，约束：2x₁ + x₂ ≤ 100, 3x₁ + 4x₂ ≤ 120, x₁,x₂ ≥ 0。用单纯形法或 SciPy linprog 求解。"
        },
        "algorithms": ["单纯形法", "内点法", "分支定界法", "遗传算法", "模拟退火", "粒子群优化"],
        "tools": ["SciPy (linprog)", "PuLP", "CVXPY", "Gurobi", "CPLEX"],
        "code_template": '''\"\"\"线性规划 — 生产计划优化示例\"\"\"
import numpy as np
from scipy.optimize import linprog

# 目标函数系数 (minimize c^T x)
c = [-40, -30]  # 利润最大化 → 取负号转化为最小化

# 不等式约束 A x <= b
A = [[2, 1],      # 加工时间约束
     [3, 4]]      # 原料约束
b = [100, 120]

# 变量边界 x >= 0
bounds = [(0, None), (0, None)]

# 求解
result = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')

print(f"最优解: A={result.x[0]:.1f}, B={result.x[1]:.1f}")
print(f"最大利润: {-result.fun:.1f} 元")
print(f"是否成功: {result.success}")
'''
    },
    "预测模型": {
        "id": "prediction",
        "name": "预测模型",
        "icon": "data-analysis",
        "color": "#00B42A",
        "description": "基于历史数据建立数学模型，对未来趋势或未知数据进行推断和预测。广泛应用于经济、气象、交通等领域。",
        "definition": "预测模型（Prediction Model）是通过分析历史数据中的规律和模式，建立输入与输出之间的映射关系，从而对未知数据或未来趋势做出推断的数学模型。核心在于捕捉数据中的趋势、季节性和随机波动。",
        "core_formulas": [
            {
                "name": "ARIMA 模型",
                "latex": "\\Phi(B)(1-B)^d X_t = \\Theta(B)\\varepsilon_t",
                "explanation": "B 为滞后算子，d 为差分阶数，Φ 和 Θ 分别为自回归和移动平均多项式。ARIMA(p,d,q) 是最经典的时序预测模型。"
            },
            {
                "name": "指数平滑（Holt-Winters）",
                "latex": "\\hat{y}_{t+h} = l_t + h \\cdot b_t + s_{t-m+h_m^+}",
                "explanation": "l_t 为水平项，b_t 为趋势项，s_t 为季节项，同时捕捉三个维度的时间序列特征。"
            },
            {
                "name": "回归预测",
                "latex": "\\hat{y} = \\beta_0 + \\beta_1 x_1 + \\cdots + \\beta_p x_p + \\varepsilon",
                "explanation": "建立因变量与多个自变量之间的线性/非线性关系，通过最小二乘法估计参数 β。"
            }
        ],
        "scenarios": [
            "销售量/客流量预测（零售、交通）",
            "股票价格/汇率走势预测（金融）",
            "气温/降雨量预测（气象）",
            "用电负荷预测（能源）",
            "疫情传播趋势预测（公共卫生）"
        ],
        "example": {
            "title": "月度销售额预测",
            "problem": "某电商平台有过去 36 个月的销售额数据，呈现出明显的上升趋势和年末旺季的季节性波动。请预测未来 6 个月的销售额。",
            "solution": "使用 Holt-Winters 三指数平滑模型 → 分解趋势、季节性、残差三个分量 → 模型拟合后向前预测 6 步 → 用 RMSE 和 MAPE 评估预测精度。"
        },
        "algorithms": ["ARIMA/SARIMA", "Holt-Winters 指数平滑", "Prophet", "LSTM/GRU", "XGBoost", "随机森林回归"],
        "tools": ["statsmodels", "prophet", "scikit-learn", "TensorFlow/PyTorch", "pmdarima"],
        "code_template": '''"""时序预测 — ARIMA 销售额预测示例"""
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt

# 模拟36个月的销售额数据（带趋势+季节性）
np.random.seed(42)
t = np.arange(36)
trend = 100 + 2 * t
seasonal = 30 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 10, 36)
sales = trend + seasonal + noise

# 拟合 ARIMA(1,1,1) 模型
model = ARIMA(sales, order=(1, 1, 1))
fitted = model.fit()
print(fitted.summary())

# 预测未来6个月
forecast = fitted.forecast(steps=6)
print(f"未来6个月预测: {forecast.round(1)}")

# 可视化
plt.figure(figsize=(10, 4))
plt.plot(range(36), sales, 'b-', label='历史数据')
plt.plot(range(36, 42), forecast, 'r--', label='预测')
plt.legend(); plt.title('销售额预测'); plt.show()
'''
    },
    "评价模型": {
        "id": "evaluation",
        "name": "评价模型",
        "icon": "tickets",
        "color": "#FF7D00",
        "description": "建立评价指标体系，对多个备选方案进行综合排序或优劣判断。核心是权重确定和综合评价方法的选择。",
        "definition": "评价模型（Evaluation Model）是用于对多个对象或方案进行综合评判和排序的数学模型。核心步骤包括：建立评价指标体系 → 指标标准化（无量纲化）→ 确定权重 → 综合评分与排序。",
        "core_formulas": [
            {
                "name": "TOPSIS 综合评价",
                "latex": "S_i = \\frac{D_i^-}{D_i^+ + D_i^-}, \\quad D_i^+ = \\sqrt{\\sum_{j}(z_{ij}-z_j^+)^2}",
                "explanation": "D_i⁺ 和 D_i⁻ 分别为方案 i 到正理想解和负理想解的欧氏距离，S_i 越接近 1 越好。"
            },
            {
                "name": "熵权法（客观赋权）",
                "latex": "w_j = \\frac{1 - E_j}{\\sum_{k}(1 - E_k)}, \\quad E_j = -\\frac{1}{\\ln n}\\sum_i p_{ij}\\ln p_{ij}",
                "explanation": "E_j 为第 j 个指标的信息熵，熵越小说明指标差异越大、权重应越高。"
            },
            {
                "name": "AHP 判断矩阵",
                "latex": "A\\mathbf{w} = \\lambda_{\\max}\\mathbf{w}, \\quad CR = \\frac{CI}{RI} < 0.1",
                "explanation": "通过两两比较构建判断矩阵 A，最大特征值对应特征向量为权重，CR 一致性比率需 < 0.1。"
            }
        ],
        "scenarios": [
            "供应商/合作伙伴选择与评价",
            "教学质量/企业绩效评估",
            "风险评估与信用评级",
            "城市宜居度/竞争力排名",
            "产品方案选优"
        ],
        "example": {
            "title": "供应商综合评价",
            "problem": "从价格、质量、交货准时率、售后服务 4 个维度评价 5 家候选供应商。前两个指标越小越好，后两个越大越好。请给出综合排名。",
            "solution": "构建评价矩阵 → 正向化处理（成本型→效益型）→ 标准化去量纲 → 熵权法确定各指标客观权重 → TOPSIS 计算各供应商贴近度 → 排序。"
        },
        "algorithms": ["TOPSIS", "熵权法", "AHP（层次分析法）", "VIKOR", "CRITIC", "灰色关联分析", "模糊综合评价"],
        "tools": ["NumPy", "pandas", "SciPy", "自定义实现"],
        "code_template": '''"""TOPSIS-熵权法 — 供应商综合评价示例"""
import numpy as np
import pandas as pd

# 评价矩阵：5个供应商 × 4个指标（价格、质量、准时率、售后）
data = np.array([
    [120, 0.85, 0.92, 0.78],
    [100, 0.90, 0.88, 0.85],
    [135, 0.82, 0.95, 0.72],
    [110, 0.88, 0.85, 0.90],
    [125, 0.86, 0.90, 0.80],
])

# 指标方向: 1=效益型(越大越好), -1=成本型(越小越好)
directions = [-1, 1, 1, 1]

# Step 1: 正向化（成本型取倒数或min-max翻转）
X = data.copy()
for j, d in enumerate(directions):
    if d == -1:
        X[:, j] = X[:, j].max() - X[:, j]  # 或 1/data[:,j]

# Step 2: 标准化（向量归一化）
X_norm = X / np.sqrt((X**2).sum(axis=0))

# Step 3: 熵权法计算权重
p = X_norm / X_norm.sum(axis=0)
E = -np.sum(p * np.log(p + 1e-10), axis=0) / np.log(len(X_norm))
w = (1 - E) / (1 - E).sum()
print(f"熵权法权重: {w.round(4)}")

# Step 4: TOPSIS 计算贴近度
best = np.max(X_norm * w, axis=0)
worst = np.min(X_norm * w, axis=0)
d_best = np.sqrt(((X_norm * w - best)**2).sum(axis=1))
d_worst = np.sqrt(((X_norm * w - worst)**2).sum(axis=1))
S = d_worst / (d_best + d_worst)

ranking = np.argsort(-S) + 1
for i, r in enumerate(ranking):
    print(f"排名{r}: 供应商{i+1} (贴近度={S[i]:.4f})")
'''
    },
    "分类与聚类": {
        "id": "classification-clustering",
        "name": "分类与聚类",
        "icon": "grid",
        "color": "#722ED1",
        "description": "将数据按其特征分门别类。分类是监督学习（已知类别标签），聚类是无监督学习（自动发现数据中的自然分组）。",
        "definition": "分类（Classification）是根据已知标签的训练数据学习判别规则，对新样本预测类别。聚类（Clustering）是在无标签情况下，根据样本间相似性自动将数据划分为若干组，使组内相似、组间差异最大。",
        "core_formulas": [
            {
                "name": "逻辑回归（二分类）",
                "latex": "P(y=1|\\mathbf{x}) = \\frac{1}{1 + e^{-(\\beta_0 + \\beta_1 x_1 + \\cdots + \\beta_p x_p)}}",
                "explanation": "通过 Sigmoid 函数将线性组合映射到 (0,1)，输出概率值，常用于二分类问题的基线模型。"
            },
            {
                "name": "K-means 聚类目标",
                "latex": "\\min_{C_1,\\ldots,C_k} \\sum_{i=1}^k \\sum_{\\mathbf{x} \\in C_i} \\|\\mathbf{x} - \\boldsymbol{\\mu}_i\\|^2",
                "explanation": "最小化各类内部点到其质心的平方距离之和，C_i 为第 i 簇，μ_i 为其质心。"
            },
            {
                "name": "DBSCAN 密度定义",
                "latex": "N_\\varepsilon(p) = \\{q \\in D \\mid \\text{dist}(p,q) \\leq \\varepsilon\\}",
                "explanation": "ε-邻域内含 MinPts 个点以上为核心点，可发现任意形状的簇并自动识别噪声。"
            }
        ],
        "scenarios": [
            "垃圾邮件检测（二分类）",
            "信用风险评级（多分类）",
            "客户分群/用户画像（聚类）",
            "图像识别与物体检测",
            "异常检测（离群点识别）"
        ],
        "example": {
            "title": "客户价值分群",
            "problem": "某零售企业有 10000 名客户的消费数据（消费频次、平均客单价、最近购买时间等），请将客户分为高/中/低价值三个群体，制定差异化营销策略。",
            "solution": "RFM 特征提取（Recency/Frequency/Monetary）→ 标准化 → K-means 聚类 (k=3) → 轮廓系数评估聚类质量 → 分析各群特征 → 制定营销策略。"
        },
        "algorithms": ["逻辑回归", "决策树/随机森林", "SVM", "KNN", "K-means", "DBSCAN", "层次聚类", "GMM"],
        "tools": ["scikit-learn", "XGBoost/LightGBM", "TensorFlow/PyTorch", "pandas", "matplotlib"],
        "code_template": '''"""K-means 聚类 — 客户价值分群示例"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# 模拟客户RFM数据 (Recency, Frequency, Monetary)
np.random.seed(42)
n = 500
rfm = np.column_stack([
    np.random.exponential(30, n),   # Recency（距上次购买天数）
    np.random.poisson(8, n),        # Frequency（购买次数）
    np.random.normal(500, 150, n)   # Monetary（总消费金额）
])

# 标准化
scaler = StandardScaler()
X = scaler.fit_transform(rfm)

# 肘部法则 — 确定最优k
inertias = []
for k in range(1, 11):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X)
    inertias.append(km.inertia_)

# 聚类 (k=3)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = kmeans.fit_predict(X)
sil = silhouette_score(X, labels)
print(f"轮廓系数: {sil:.3f}")

# 可视化结果
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(range(1, 11), inertias, 'bo-'); axes[0].set_title('肘部法则')
scatter = axes[1].scatter(rfm[:, 0], rfm[:, 2], c=labels, cmap='viridis')
axes[1].set_xlabel('Recency'); axes[1].set_ylabel('Monetary')
plt.colorbar(scatter); plt.show()
'''
    },
    "微分方程": {
        "id": "differential-equations",
        "name": "微分方程",
        "icon": "connection",
        "color": "#F53F3F",
        "description": "用微分方程描述系统的动态变化规律，是连续系统建模的核心工具。涵盖常微分方程 (ODE) 和偏微分方程 (PDE)。",
        "definition": "微分方程模型（Differential Equation Model）通过建立变量变化率之间的关系来描述系统的动态行为。常微分方程（ODE）描述单变量随时间变化，偏微分方程（PDE）描述多变量时空演化。",
        "core_formulas": [
            {
                "name": "Logistic 增长模型",
                "latex": "\\frac{dN}{dt} = rN\\left(1 - \\frac{N}{K}\\right)",
                "explanation": "N 为种群数量，r 为内禀增长率，K 为环境容纳量。描述了有限资源条件下的 S 型增长。"
            },
            {
                "name": "SIR 传染病模型",
                "latex": "\\frac{dS}{dt} = -\\beta SI, \\quad \\frac{dI}{dt} = \\beta SI - \\gamma I, \\quad \\frac{dR}{dt} = \\gamma I",
                "explanation": "S/I/R 分别表示易感/感染/康复人群比例，β 为传染率，γ 为康复率。R₀ = β/γ 为基本再生数。"
            },
            {
                "name": "Lotka-Volterra 捕食模型",
                "latex": "\\frac{dx}{dt} = \\alpha x - \\beta xy, \\quad \\frac{dy}{dt} = \\delta xy - \\gamma y",
                "explanation": "x 为猎物数量，y 为捕食者数量。α/β/γ/δ 为模型参数，产生经典的周期性振荡解。"
            }
        ],
        "scenarios": [
            "人口增长与种群动力学",
            "传染病传播建模（SIR/SEIR 系列）",
            "药物在体内的扩散与代谢",
            "热传导与流体力学",
            "生态系统建模"
        ],
        "example": {
            "title": "疫情传播预测",
            "problem": "某城市人口 500 万，初始感染 100 人，传染率 β=0.3，康复率 γ=0.1。预测未来 100 天疫情发展趋势，评估防控措施效果。",
            "solution": "建立 SIR 模型 → 使用 SciPy odeint 数值求解微分方程组 → 绘制 S/I/R 时间变化曲线 → 通过改变 β 参数模拟戴口罩/隔离等干预效果。"
        },
        "algorithms": ["Euler 法", "Runge-Kutta (RK4)", "odeint/ode45", "有限差分法", "有限元法"],
        "tools": ["SciPy (odeint, solve_ivp)", "MATLAB", "SymPy (符号求解)", "FEniCS (FEM)"],
        "code_template": '''"""SIR 传染病模型 — 数值求解示例"""
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

def sir_model(y, t, beta, gamma):
    """SIR 微分方程组"""
    S, I, R = y
    dS = -beta * S * I
    dI = beta * S * I - gamma * I
    dR = gamma * I
    return [dS, dI, dR]

# 参数设定
N = 1_000_000       # 总人口
I0, R0 = 100, 0     # 初始感染和康复人数
S0 = N - I0 - R0
beta, gamma = 0.3, 0.1
R0_val = beta / gamma

t = np.linspace(0, 160, 1000)

# 数值求解
sol = odeint(sir_model, [S0/N, I0/N, R0/N], t, args=(beta, gamma))

# 可视化
plt.figure(figsize=(10, 5))
plt.plot(t, sol[:, 0], 'b-', label='易感者 S(t)')
plt.plot(t, sol[:, 1], 'r-', label='感染者 I(t)')
plt.plot(t, sol[:, 2], 'g-', label='康复者 R(t)')
plt.axvline(t[np.argmax(sol[:, 1])], color='gray', linestyle='--',
            label=f'感染峰值 (第{t[np.argmax(sol[:, 1])]:.0f}天)')
plt.xlabel('天数'); plt.ylabel('比例')
plt.title(f'SIR模型 (R0={R0_val:.1f})')
plt.legend(); plt.grid(alpha=0.3); plt.show()
'''
    },
    "统计模型": {
        "id": "statistics",
        "name": "统计模型",
        "icon": "pie-chart",
        "color": "#0FC6C2",
        "description": "基于概率统计理论，从数据中推断总体特征、检验假设、发现变量间关系。是所有数据分析与建模的基础。",
        "definition": "统计模型（Statistical Model）运用概率论和数理统计方法，通过样本数据对总体进行推断。包括描述统计（数据概括）、推断统计（参数估计/假设检验）和关系建模（回归/方差分析）。",
        "core_formulas": [
            {
                "name": "多元线性回归",
                "latex": "\\mathbf{y} = X\\boldsymbol{\\beta} + \\boldsymbol{\\varepsilon}, \\quad \\hat{\\boldsymbol{\\beta}} = (X^TX)^{-1}X^T\\mathbf{y}",
                "explanation": "最小二乘估计（OLS）最小化残差平方和，X 为设计矩阵（含截距列），β 为回归系数。"
            },
            {
                "name": "假设检验（t 检验）",
                "latex": "t = \\frac{\\bar{x} - \\mu_0}{s / \\sqrt{n}} \\sim t(n-1)",
                "explanation": "检验样本均值是否与假设值 μ₀ 有显著差异，p < 0.05 通常拒绝原假设。"
            },
            {
                "name": "贝叶斯定理",
                "latex": "P(\\theta|D) = \\frac{P(D|\\theta) \\cdot P(\\theta)}{P(D)}",
                "explanation": "后验概率 ∝ 似然 × 先验概率。贝叶斯方法允许将先验知识融入建模过程。"
            }
        ],
        "scenarios": [
            "影响因素分析（如广告支出对销售额的影响）",
            "A/B 测试与实验设计",
            "产品质量控制与抽样检验",
            "保险精算与风险评估",
            "问卷调查数据分析"
        ],
        "example": {
            "title": "房价影响因素分析",
            "problem": "收集了 500 套房屋的面积、房龄、卧室数、地段评分和售价数据。分析哪些因素对房价影响最大，并建立预测模型。",
            "solution": "探索性数据分析（EDA）→ 相关性矩阵 → 逐步回归筛选变量 → 多元线性回归 → 检查 VIF（多重共线性）→ 残差诊断 → 交叉验证评估。"
        },
        "algorithms": ["OLS 回归", "岭回归/LASSO", "方差分析 (ANOVA)", "主成分分析 (PCA)", "因子分析", "贝叶斯推断"],
        "tools": ["statsmodels", "scikit-learn", "SciPy (stats)", "R 语言", "pandas"],
        "code_template": '''"""多元线性回归 — 房价预测示例"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# 模拟房价数据
np.random.seed(42)
n = 200
area = np.random.normal(120, 30, n)        # 面积 (m²)
age = np.random.uniform(0, 30, n)          # 房龄 (年)
rooms = np.random.randint(2, 6, n)         # 卧室数
score = np.random.uniform(3, 10, n)        # 地段评分

# 真实房价 (含噪声)
price = 50 + 2.5*area - 1.2*age + 15*rooms + 8*score + np.random.normal(0, 20, n)

X = np.column_stack([area, age, rooms, score])
y = price

# OLS 回归
X_sm = sm.add_constant(X)
model = sm.OLS(y, X_sm).fit()
print(model.summary())

# 预测评估
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
X_train_sm = sm.add_constant(X_train)
model2 = sm.OLS(y_train, X_train_sm).fit()
y_pred = model2.predict(sm.add_constant(X_test))
print(f"R² = {r2_score(y_test, y_pred):.3f}")
print(f"RMSE = {np.sqrt(mean_squared_error(y_test, y_pred)):.1f} 万元")
'''
    },
    "图论与网络": {
        "id": "graph-theory",
        "name": "图论与网络",
        "icon": "share",
        "color": "#F7BA1E",
        "description": "用节点和边抽象表示实体间的关系，研究网络结构、路径优化和传播动力学。在交通、社交网络、通信等领域有广泛应用。",
        "definition": "图论模型（Graph Theory Model）将现实世界中的实体抽象为**节点**（顶点），实体间的关系抽象为**边**（连接）。通过研究图的拓扑性质和算法，解决路径规划、网络优化、社区发现等问题。",
        "core_formulas": [
            {
                "name": "Dijkstra 最短路径",
                "latex": "d[v] = \\min_{u \\in S} \\{d[u] + w(u,v)\\}, \\quad v \\in V\\setminus S",
                "explanation": "贪心策略：每次从未处理节点中选择距离最小的进行松弛操作。时间复杂度 O(V²) 或 O(E log V)。"
            },
            {
                "name": "最大流最小割定理",
                "latex": "\\max_{flow} |f| = \\min_{cut} c(S,T)",
                "explanation": "网络中从源点到汇点的最大流量等于最小割的容量。Ford-Fulkerson 算法通过增广路迭代求解。"
            },
            {
                "name": "PageRank",
                "latex": "PR(p_i) = \\frac{1-d}{N} + d \\sum_{p_j \\in M(p_i)} \\frac{PR(p_j)}{L(p_j)}",
                "explanation": "d 为阻尼系数（通常 0.85），M(p_i) 为链接到 p_i 的页面集合，L(p_j) 为 p_j 的出链数。"
            }
        ],
        "scenarios": [
            "最短路径导航（地图导航、物流配送）",
            "网络流优化（交通流、供水管网）",
            "社交网络分析（影响力传播、社区发现）",
            "通信网络设计（基站选址、路由优化）",
            "供应链网络结构优化"
        ],
        "example": {
            "title": "城市快递配送路径优化",
            "problem": "某快递站需要向城市内 30 个配送点派送货物，每两点间的行驶距离已知。求从站点出发访问所有配送点最后返回的最短路径。",
            "solution": "TSP（旅行商问题）建模 → 最近邻启发式算法求初始解 → 2-opt/3-opt 局部搜索优化 → 或使用遗传算法/蚁群算法寻优。"
        },
        "algorithms": ["Dijkstra", "Floyd-Warshall", "Kruskal/Prim (MST)", "Ford-Fulkerson", "PageRank", "社区发现 (Louvain)"],
        "tools": ["NetworkX", "igraph", "OR-Tools", "Gephi (可视化)", "Python 自定义"],
        "code_template": '''"""TSP 旅行商问题 — 最近邻启发式 + 2-opt 优化"""
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

# 随机生成30个城市坐标
np.random.seed(42)
coords = np.random.rand(30, 2) * 100

def distance_matrix(coords):
    n = len(coords)
    D = np.zeros((n, n))
    for i, j in combinations(range(n), 2):
        D[i][j] = D[j][i] = np.linalg.norm(coords[i] - coords[j])
    return D

def nearest_neighbor(D, start=0):
    n = len(D); unvisited = set(range(n)); unvisited.remove(start)
    path = [start]
    while unvisited:
        last = path[-1]
        nxt = min(unvisited, key=lambda v: D[last][v])
        path.append(nxt); unvisited.remove(nxt)
    return path

def path_length(D, path):
    return sum(D[path[i]][path[(i+1)%len(path)]] for i in range(len(path)))

def two_opt(D, path, iterations=500):
    best = path[:]; n = len(path)
    for _ in range(iterations):
        improved = False
        for i in range(n-1):
            for j in range(i+2, n):
                if j - i == n - 1: continue
                new = best[:i+1] + best[i+1:j+1][::-1] + best[j+1:]
                if path_length(D, new) < path_length(D, best):
                    best, improved = new, True; break
            if improved: break
        if not improved: break
    return best

D = distance_matrix(coords)
nn_path = nearest_neighbor(D)
opt_path = two_opt(D, nn_path)
print(f"最近邻: {path_length(D, nn_path):.1f}  → 2-opt: {path_length(D, opt_path):.1f}")

plt.plot(coords[opt_path + [opt_path[0]], 0], coords[opt_path + [opt_path[0]], 1], 'b-o', ms=4)
plt.title(f"TSP最优路径 (总长={path_length(D, opt_path):.1f})"); plt.show()
'''
    },
    "随机模型": {
        "id": "stochastic",
        "name": "随机模型",
        "icon": "loading",
        "color": "#168CFF",
        "description": "引入随机性和概率分布描述系统中的不确定性。包括蒙特卡洛模拟、马尔可夫链、排队论等经典方法。",
        "definition": "随机模型（Stochastic Model）与确定性模型相对，在建模中显式引入随机变量和概率分布来描述系统的不确定性。核心思想是通过大量随机采样或概率转移来推断系统的统计行为。",
        "core_formulas": [
            {
                "name": "蒙特卡洛积分",
                "latex": "I = \\int_a^b f(x)dx \\approx \\frac{b-a}{N} \\sum_{i=1}^N f(X_i), \\quad X_i \\sim U(a,b)",
                "explanation": "通过在积分区间内随机采样 N 个点，用样本均值近似积分值，误差收敛速度为 O(1/√N)。"
            },
            {
                "name": "马尔可夫链转移",
                "latex": "P(X_{n+1}=j | X_n=i, X_{n-1}, \\ldots) = P(X_{n+1}=j | X_n=i) = p_{ij}",
                "explanation": "下一状态仅依赖当前状态（马尔可夫性），p_ij 为状态转移概率，P 为转移矩阵。"
            },
            {
                "name": "M/M/1 排队模型",
                "latex": "L = \\frac{\\rho}{1-\\rho}, \\quad W = \\frac{1}{\\mu-\\lambda}, \\quad \\rho = \\frac{\\lambda}{\\mu}",
                "explanation": "λ 为到达率，μ 为服务率，ρ 为系统利用率（须 < 1）。L 为平均队长，W 为平均等待时间。"
            }
        ],
        "scenarios": [
            "金融风险模拟（VaR、期权定价）",
            "排队系统优化（银行柜台、呼叫中心）",
            "库存管理（随机需求下的最优订货量）",
            "可靠性工程（设备故障与维修建模）",
            "演化博弈（随机扰动下的策略演化）"
        ],
        "example": {
            "title": "银行柜台服务优化",
            "problem": "某银行网点客户到达服从泊松分布（λ=20 人/小时），每个柜台服务时间服从指数分布（μ=12 人/小时）。需要设置几个柜台使平均等待时间不超过 5 分钟？",
            "solution": "M/M/c 排队模型 → 计算不同 c（柜台数）下的平均等待时间 W_q → ρ = λ/(cμ) < 1 为可行条件 → 找到满足 W_q < 5min 的最小 c。"
        },
        "algorithms": ["蒙特卡洛模拟", "MCMC (Metropolis-Hastings)", "Gibbs 采样", "排队论解析", "布朗运动模拟"],
        "tools": ["NumPy (random)", "PyMC", "SciPy (stats)", "SimPy (离散事件仿真)", "Stan"],
        "code_template": '''"""蒙特卡洛模拟 — π 值估计 + 投资风险 VaR 示例"""
import numpy as np
import matplotlib.pyplot as plt

# ===== 示例1: 蒙特卡洛估计 π =====
N = 100_000
x, y = np.random.uniform(-1, 1, N), np.random.uniform(-1, 1, N)
inside = x**2 + y**2 <= 1
pi_est = 4 * inside.sum() / N
print(f"π 估计值: {pi_est:.6f} (误差: {abs(pi_est - np.pi):.6f})")

# ===== 示例2: 投资组合 VaR (Value at Risk) =====
np.random.seed(42)
returns = np.random.normal(0.001, 0.02, (10000, 252))
annual_returns = (1 + returns).prod(axis=1) - 1
VaR_95 = np.percentile(annual_returns, 5)
print(f"95% VaR: {VaR_95:.2%} — 有95%把握年损失不超过 {-VaR_95:.2%}")

# 可视化
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.scatter(x[:2000], y[:2000], c=inside[:2000], s=1, cmap='coolwarm')
plt.title(f'MC估计 π ≈ {pi_est:.4f}'); plt.axis('equal')
plt.subplot(1, 2, 2)
plt.hist(annual_returns, bins=80, edgecolor='white', alpha=0.8)
plt.axvline(VaR_95, color='r', linestyle='--', label=f'95% VaR = {VaR_95:.2%}')
plt.title('投资组合年收益分布'); plt.legend(); plt.show()
'''
    }
}

# ============================================================
# 学习路径推荐 — 三阶段递进
# ============================================================

LEARNING_PATHS = [
    {
        "stage": "新手入门",
        "level": 1,
        "description": "适合数学建模零基础学习者，从基础模型开始建立建模思维",
        "models": ["统计模型", "优化模型", "评价模型"],
        "topics": [
            "数据描述统计与可视化",
            "线性规划入门（图解 + 单纯形法）",
            "加权评分与简单评价法",
            "一元/多元线性回归",
            "数学建模论文写作规范"
        ],
        "estimated_hours": 40
    },
    {
        "stage": "进阶提升",
        "level": 2,
        "description": "掌握更多模型类型和算法，能独立完成中等难度建模任务",
        "models": ["预测模型", "分类与聚类", "图论与网络", "微分方程"],
        "topics": [
            "时间序列分析与 ARIMA 建模",
            "分类算法实战（决策树/随机森林/SVM）",
            "聚类分析与客户分群",
            "图论最短路/最大流问题",
            "常微分方程数值求解",
            "TOPSIS/AHP 综合评价方法"
        ],
        "estimated_hours": 60
    },
    {
        "stage": "竞赛强化",
        "level": 3,
        "description": "面向数学建模竞赛的系统训练，涵盖完整的工作流和高级技巧",
        "models": ["随机模型", "微分方程", "预测模型", "优化模型"],
        "topics": [
            "蒙特卡洛模拟与随机优化",
            "传染病/种群动力学建模",
            "机器学习集成方法与调参",
            "多目标优化与 Pareto 前沿",
            "敏感性分析与模型检验",
            "竞赛论文结构与写作策略",
            "历年竞赛真题实战"
        ],
        "estimated_hours": 80
    }
]


def get_all_categories() -> list[dict]:
    """获取所有知识库分类摘要"""
    return [
        {
            "id": v["id"],
            "name": v["name"],
            "icon": v["icon"],
            "color": v["color"],
            "description": v["description"],
            "algorithm_count": len(v["algorithms"]),
            "scenario_count": len(v["scenarios"]),
        }
        for v in KNOWLEDGE_BASE.values()
    ]


def get_category(category_id: str) -> dict | None:
    """获取单个分类的完整知识"""
    for v in KNOWLEDGE_BASE.values():
        if v["id"] == category_id:
            return v
    return None


def search_knowledge(query: str) -> list[dict]:
    """全文搜索知识库"""
    q = query.lower()
    results = []
    for cat in KNOWLEDGE_BASE.values():
        score = 0
        if q in cat["name"].lower():
            score += 10
        if q in cat["description"].lower():
            score += 5
        for algo in cat["algorithms"]:
            if q in algo.lower():
                score += 3
        for scenario in cat["scenarios"]:
            if q in scenario.lower():
                score += 2
        if cat["example"]["title"].lower().find(q) >= 0 or q in cat["example"]["problem"].lower():
            score += 2
        if score > 0:
            results.append({
                "category_id": cat["id"],
                "category_name": cat["name"],
                "color": cat["color"],
                "score": score,
                "matched_in": "分类名称" if score >= 10 else "描述/算法/场景",
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_learning_paths() -> list[dict]:
    """获取学习路径"""
    return LEARNING_PATHS


# ============================================================
# 案例库 — 历年竞赛优秀论文解析
# ============================================================

CASE_LIBRARY = [
    {
        "id": "case-001",
        "title": "高温作业专用服装设计",
        "competition": "全国大学生数学建模竞赛",
        "year": 2018,
        "award": "国赛一等奖",
        "model_types": ["微分方程", "优化模型"],
        "summary": "设计高温环境下作业的专用服装，需综合考虑热传导、服装厚度和材料特性，建立多层热传导偏微分方程模型。",
        "problem_brief": "高温作业服由三层不同材料组成，已知各层参数和环境温度，要求确定服装的温度分布，并优化各层厚度使假人皮肤温度不超过安全阈值。",
        "modeling_approach": [
            "建立一维非稳态热传导偏微分方程（PDE），描述各层材料中的温度分布随时间的变化",
            "使用有限差分法（Crank-Nicolson 隐格式）对 PDE 进行数值离散和求解",
            "以服装总厚度最小为目标，皮肤温度阈值为约束，建立非线性规划模型",
            "通过参数扫描和梯度下降法优化各层厚度组合"
        ],
        "key_techniques": [
            "偏微分方程建模（热传导 Fourier 定律）",
            "Crank-Nicolson 有限差分格式",
            "非线性约束优化",
            "参数敏感性分析"
        ],
        "highlights": "论文将物理机理与数学优化完美结合，先从物理定律出发建立 PDE 模型，再转化为优化问题。数值求解采用稳定性好的 Crank-Nicolson 格式，确保了计算精度。",
        "takeaways": [
            "从物理定律出发建立方程，使模型有坚实的理论基础",
            "数值方法的选择直接影响模型精度和稳定性",
            "多目标问题可转化为单目标+约束的优化形式",
            "敏感性分析是验证模型鲁棒性的关键步骤"
        ]
    },
    {
        "id": "case-002",
        "title": "基于 TOPSIS-熵权法的城市宜居性评价",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2020,
        "award": "M奖（Meritorious Winner）",
        "model_types": ["评价模型", "统计模型"],
        "summary": "对全球 20 个主要城市的宜居性进行综合评价，从经济、环境、教育、医疗、交通 5 个维度构建指标体系，使用熵权-TOPSIS 模型进行排名。",
        "problem_brief": "建立城市宜居性评价模型，考虑多维度指标，对不同城市进行综合排序，并分析各指标对排名的贡献度。",
        "modeling_approach": [
            "构建 5 维度 18 个指标的评价体系，通过相关性分析筛选有效指标",
            "数据标准化：极差变换法消除量纲影响，正向化处理成本型指标",
            "熵权法客观赋权：根据数据本身的离散程度确定各指标权重",
            "TOPSIS 综合评价：计算各城市到正/负理想解的贴近度进行排序",
            "灵敏度分析：扰动各指标权重 ±10%，检验排序结果的稳定性"
        ],
        "key_techniques": [
            "熵权法（客观赋权，避免主观偏差）",
            "TOPSIS 综合评价法",
            "指标正向化与标准化",
            "灵敏度分析（OAT 方法）"
        ],
        "highlights": "该论文的亮点在于评价体系的系统性和方法的客观性。与常见的主观赋权（专家打分）不同，采用熵权法完全基于数据本身确定权重，使结果更加客观可信。",
        "takeaways": [
            "评价指标体系要覆盖全面且避免冗余（相关性检验）",
            "客观赋权法（熵权/CRITIC）比主观赋权更有说服力",
            "灵敏度分析是评价模型不可或缺的组成部分",
            "结果可视化（雷达图/排名字段）能大幅提升可读性"
        ]
    },
    {
        "id": "case-003",
        "title": "基于 ARIMA-LSTM 混合模型的电力负荷预测",
        "competition": "全国大学生数学建模竞赛",
        "year": 2021,
        "award": "国赛一等奖",
        "model_types": ["预测模型", "统计模型"],
        "summary": "预测某地区未来 7 天的电力负荷，创新性地结合 ARIMA 捕捉线性趋势和 LSTM 学习非线性残差，混合模型显著优于单一模型。",
        "problem_brief": "给定某地区过去 3 年的逐小时电力负荷数据以及天气数据，预测未来一周的逐小时负荷，要求考虑季节性、节假日效应和天气影响。",
        "modeling_approach": [
            "数据预处理：缺失值插补、异常值检测（3σ 原则）、时间特征工程",
            "ARIMA 模型捕捉负荷数据的线性趋势和季节性成分",
            "LSTM 神经网络学习 ARIMA 残差中的非线性模式和天气因素的影响",
            "Stacking 集成：ARIMA 预测值 + LSTM 残差预测 = 最终预测",
            "使用 RMSE、MAPE、MAE 三指标综合评估模型性能"
        ],
        "key_techniques": [
            "ARIMA/SARIMA 时间序列建模",
            "LSTM 深度学习（Keras/TensorFlow）",
            "残差学习与集成策略",
            "时间特征工程（哑变量编码节假日）"
        ],
        "highlights": "该论文的混合策略值得借鉴——不是简单地选择 ARIMA 或 LSTM，而是让各自做最擅长的事：ARIMA 处理线性部分，LSTM 处理非线性残差。这种'分工协作'的思想适用于很多建模场景。",
        "takeaways": [
            "单一模型各有利弊，混合/集成策略往往效果更好",
            "残差分析不仅能检验模型，还能指导模型改进方向",
            "特征工程（节假日、小时、天气）对时序预测至关重要",
            "多指标评估（RMSE+MAPE+MAE）比单一指标更有说服力"
        ]
    },
    {
        "id": "case-004",
        "title": "基于改进蚁群算法的物流配送路径优化",
        "competition": "全国大学生数学建模竞赛",
        "year": 2019,
        "award": "国赛二等奖",
        "model_types": ["图论与网络", "优化模型"],
        "summary": "针对多配送中心的车辆路径问题（MDVRP），提出改进的蚁群算法，引入自适应信息素挥发机制和 2-opt 局部搜索策略。",
        "problem_brief": "某物流企业在城市中有 3 个配送中心和 50 个客户点，多辆配送车从中心出发，完成配送后返回。要求总行驶距离最短，且满足车辆载重和时间窗约束。",
        "modeling_approach": [
            "建立 MDVRPTW（多中心带时间窗车辆路径问题）数学模型",
            "将多中心问题通过最近邻规则分解为多个单车场 VRP",
            "改进蚁群算法：自适应信息素挥发因子 ρ(t) = ρ₀·e^(-t/T)",
            "嵌入 2-opt 局部搜索对每只蚂蚁构造的路径进行精炼",
            "与遗传算法（GA）和模拟退火（SA）的结果进行对比分析"
        ],
        "key_techniques": [
            "车辆路径问题（VRP）建模",
            "改进蚁群算法（ACO）",
            "2-opt 局部搜索优化",
            "问题分解（Divide and Conquer）"
        ],
        "highlights": "将复杂的多中心问题分解为多个单中心子问题，降低了求解难度。蚁群算法的改进——自适应挥发因子——使算法前期探索能力强、后期收敛精度高。同时嵌入 2-opt 局部搜索有效弥补了蚁群算法后期效率低的问题。",
        "takeaways": [
            "复杂问题可以通过分治策略简化求解",
            "元启发式算法需要根据问题特点进行针对性改进",
            "多种优化策略的结合（ACO+2-opt）往往 1+1>2",
            "算法对比实验是证明方法优越性的重要手段"
        ]
    },
    {
        "id": "case-005",
        "title": "COVID-19 疫情传播 SEIR 模型与干预策略评估",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2021,
        "award": "F奖（Finalist）",
        "model_types": ["微分方程", "随机模型"],
        "summary": "建立改进的 SEIR 传染病动力学模型，引入隔离仓室和社会疏离参数，评估不同干预策略（封城、口罩、疫苗）对疫情发展的影响。",
        "problem_brief": "分析 COVID-19 疫情在不同国家的传播差异，量化非药物干预措施（NPI）的有效性，并为政策制定者提供科学建议。",
        "modeling_approach": [
            "建立 SEIRQ 模型：在经典 SEIR 基础上增加 Q（隔离）仓室",
            "引入时变传播率 β(t) = β₀·(1-α·mask_rate)·(1-β·lockdown_level)",
            "使用最小二乘法从实际数据反推模型参数（β₀, γ, σ 等）",
            "蒙特卡洛模拟 1000 次，考虑参数的随机不确定性",
            "情景分析：模拟无干预/仅口罩/仅封城/综合干预四种场景"
        ],
        "key_techniques": [
            "仓室模型（SEIRQ 扩展）",
            "时变参数估计（最小二乘拟合）",
            "蒙特卡洛不确定性量化",
            "情景分析与策略对比"
        ],
        "highlights": "该论文获得 Finalist 的核心原因在于模型的系统性和实际应用价值。不仅建立了数学模型，更通过情景分析将数学结果转化为政策建议，体现了数学建模'从问题中来，到问题中去'的核心精神。",
        "takeaways": [
            "经典模型（SEIR）可根据实际需求灵活扩展（增加 Q 仓室）",
            "参数不应设为常数，时变参数更贴近现实",
            "蒙特卡洛模拟是量化不确定性的有效手段",
            "好的建模论文应该回答现实问题，而非仅仅展示公式"
        ]
    },
    {
        "id": "case-006",
        "title": "基于 XGBoost 和随机森林的信贷违约预测",
        "competition": "全国大学生数学建模竞赛",
        "year": 2022,
        "award": "国赛一等奖",
        "model_types": ["分类与聚类", "统计模型"],
        "summary": "利用机器学习方法预测银行客户的信贷违约概率，通过特征工程和模型融合构建高精度评分卡模型，为银行风控提供决策支持。",
        "problem_brief": "某银行提供 30,000 条客户信贷记录（含违约标签），需要建立预测模型判断新申请客户是否会违约，并给出每个特征对违约概率的影响方向。",
        "modeling_approach": [
            "数据清洗：处理缺失值（多重插补）、异常值（箱线图法）、类别编码（WOE 编码）",
            "特征工程：IV 值筛选、相关性过滤、构造交叉特征（如负债率=负债/收入）",
            "模型训练：XGBoost + 随机森林 + LightGBM + 逻辑回归（基线）",
            "Stacking 集成：逻辑回归作为元学习器融合 3 个基模型的输出概率",
            "模型解释：SHAP 值分析各特征对违约概率的贡献方向和大小"
        ],
        "key_techniques": [
            "WOE/IV 特征编码与筛选",
            "XGBoost/LightGBM 梯度提升",
            "Stacking 模型融合",
            "SHAP 可解释性分析"
        ],
        "highlights": "该论文不仅追求高精度，更注重模型的可解释性。通过 SHAP 值分析让'黑箱'模型变得透明，满足了银行监管对风控模型可解释性的要求。Stacking 融合策略使 AUC 从单一模型的 0.86 提升到 0.91。",
        "takeaways": [
            "特征工程（WOE/IV/交叉特征）比模型选择更重要",
            "融合多个模型的优势（Stacking/Blending）可稳健提升精度",
            "SHAP/LIME 等可解释性工具让机器学习不再'黑箱'",
            "实际问题要考虑业务场景（银行需要可解释性，而不只是精度）"
        ]
    },
    {
        "id": "case-007",
        "title": "基于元胞自动机的森林火灾蔓延模拟",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2020,
        "award": "M奖（Meritorious Winner）",
        "model_types": ["机理/仿真", "随机模型"],
        "summary": "建立元胞自动机（CA）模型模拟森林火灾的蔓延过程，结合风向、湿度、地形等因素，评估不同灭火策略的效果。",
        "problem_brief": "澳大利亚森林大火造成了巨大的生态和经济损失。请建立数学模型模拟火势蔓延过程，评估不同因素（风速、湿度、地形坡度）对蔓延速度的影响，并为消防部门设计最优的隔离带布设方案。",
        "modeling_approach": [
            "建立二维元胞自动机模型，每个元胞状态为未燃/燃烧/已燃/隔离带",
            "设计状态转移规则：考虑 Moore 邻域（8邻居），转移概率 = f(风速, 方向, 湿度, 植被类型)",
            "风向影响通过各向异性概率权重实现：顺风方向转移概率 × α（风因子）",
            "引入地形因子：坡度 >30° 的区域火势蔓延速度加倍",
            "蒙特卡洛模拟 500 次，评估隔离带宽度和位置对灭火成功率的影响"
        ],
        "key_techniques": [
            "元胞自动机（Cellular Automata）",
            "各向异性概率转移",
            "蒙特卡洛模拟",
            "敏感性分析（Sobol 指数）"
        ],
        "highlights": "该论文用简单的元胞自动机规则模拟了复杂的火灾蔓延现象，体现了'复杂行为来自简单规则'的建模思想。各向异性概率转移巧妙地处理了风向的连续性与 CA 离散性之间的矛盾。",
        "takeaways": [
            "元胞自动机适合模拟具有空间扩散特性的现象（火灾、疫情、交通流）",
            "离散模型通过概率化可以逼近连续物理过程",
            "蒙特卡洛模拟是评估随机模型性能的标准方法",
            "灵敏度分析（Sobol/FAST）可以量化各因素的重要性排序"
        ]
    },
    {
        "id": "case-008",
        "title": "基于层次分析法与模糊评价的大学生综合素质评估",
        "competition": "全国大学生数学建模竞赛",
        "year": 2016,
        "award": "国赛一等奖",
        "model_types": ["评价模型"],
        "summary": "构建大学生综合素质多层次评价体系，将 AHP 主观赋权与模糊综合评价相结合，解决定性指标的量化评估问题。",
        "problem_brief": "高校需要综合评价学生的德、智、体、美、劳五方面素质，每方面包含多个定性指标（如'团队合作能力'、'创新能力'等）。请建立多层次的评价模型，给出综合得分的计算方法。",
        "modeling_approach": [
            "构建 3 层递阶层次结构：目标层（综合素质）→ 准则层（5个一级指标）→ 指标层（18个二级指标）",
            "使用 1-9 标度法构建判断矩阵，邀请 5 位专家打分后取几何平均",
            "计算判断矩阵的特征向量（和积法），得到各层权重，并进行一致性检验（CR < 0.1）",
            "对定性指标采用模糊综合评价：建立评语集 {优,良,中,及格,差}，构建模糊隶属度矩阵",
            "将 AHP 权重与模糊隶属度矩阵合成，得到最终评价等级（最大隶属度原则）"
        ],
        "key_techniques": [
            "层次分析法（AHP）",
            "判断矩阵与一致性检验（CR/CI 指标）",
            "模糊综合评价（Fuzzy Comprehensive Evaluation）",
            "隶属度函数设计"
        ],
        "highlights": "该论文巧妙结合了 AHP 的层次化权重确定和模糊数学处理不确定性的能力。一致性检验保证了专家判断的合理性，模糊隶属度则避免了'非好即坏'的硬性划分。该框架可推广到任何涉及定性指标的综合评价问题。",
        "takeaways": [
            "AHP 适用于多层次、多指标的评价问题，关键在于判断矩阵的一致性",
            "定性指标的量化和标准化是评价建模的核心难点",
            "模糊数学提供了一种处理'亦此亦彼'不确定性的优雅框架",
            "多种评价方法（AHP+模糊+TOPSIS）可以取长补短、交叉验证"
        ]
    },
    {
        "id": "case-009",
        "title": "基于 LSTM-Attention 的股票价格趋势预测",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2023,
        "award": "F奖（Finalist）",
        "model_types": ["预测模型"],
        "summary": "引入 Attention 机制改进 LSTM 模型，对金融时间序列中的关键时间点进行加权，提升股票趋势预测的准确性和可解释性。",
        "problem_brief": "利用过去 5 年的股票日线数据（开盘价、最高价、最低价、收盘价、成交量）以及宏观经济指标（利率、CPI、PMI），预测未来 30 个交易日的价格走势。",
        "modeling_approach": [
            "多变量时间序列建模：输入特征包括 5 个价格特征 + 3 个宏观经济指标 + 10 个技术指标（MACD, RSI, BOLL等）",
            "构建 LSTM-Attention 模型：双层 LSTM 提取时序特征 → Self-Attention 层对关键时间步加权",
            "Attention 权重可视化：展示模型在做出预测时最关注历史上哪些交易日",
            "消融实验：LSTM vs LSTM-Attention vs Transformer vs XGBoost 四模型对比",
            "使用 Walk-Forward Validation（滚动窗口验证）评估模型的样本外预测能力"
        ],
        "key_techniques": [
            "LSTM 长短期记忆网络",
            "Self-Attention 注意力机制",
            "Walk-Forward 交叉验证",
            "消融实验设计"
        ],
        "highlights": "该论文最大的创新在于 Attention 权重的可解释性应用——不仅能预测价格，还能告诉用户'模型认为历史上哪些时刻对当前预测最重要'。这种可解释的深度学习模型在金融领域有很高的实用价值。",
        "takeaways": [
            "Attention 机制不仅能提升精度，还能提供可解释性",
            "金融时间序列预测需要严格的样本外验证（Walk-Forward）",
            "消融实验是证明模型各组件有效性的标准方法",
            "宏观经济指标作为外生变量可显著提升预测的稳健性"
        ]
    },
    {
        "id": "case-010",
        "title": "基于遗传算法的火箭发射轨道优化",
        "competition": "全国大学生数学建模竞赛",
        "year": 2020,
        "award": "国赛一等奖",
        "model_types": ["优化模型", "微分方程"],
        "summary": "使用遗传算法（GA）求解火箭最优发射轨迹，在满足多约束条件下最小化燃料消耗，结合四阶 Runge-Kutta 法进行轨迹积分。",
        "problem_brief": "设计一枚火箭从地面发射至目标轨道的最优飞行轨迹。需要考虑推力大小和方向随时间的变化，同时满足最大过载、动压、热流密度和终端轨道参数等约束条件。",
        "modeling_approach": [
            "建立火箭 3-DOF 运动微分方程：d²r/dt² = (T + D + mg)/m，其中推力 T 的大小和方向为控制变量",
            "燃料消耗方程：dm/dt = -|T|/(Isp·g₀)，链接推力与剩余质量",
            "采用直接法参数化控制变量：将推力方向角 α(t) 和 β(t) 在时间网格上用分段线性函数逼近",
            "GA 优化：染色体编码为各时间节点上的 α、β 值 → 适应度 = 终端误差惩罚 + 燃料消耗",
            "每条染色体的轨迹评估通过四阶 Runge-Kutta 法（RK4）数值积分运动方程",
            "约束处理：最大过载、动压、热流密度约束通过外点罚函数法转化为适应度惩罚"
        ],
        "key_techniques": [
            "遗传算法（GA）全局优化",
            "龙格-库塔法（RK4）数值积分",
            "直接法轨迹优化",
            "外点罚函数约束处理",
            "多约束多目标优化"
        ],
        "highlights": "该论文将轨迹优化这个连续最优控制问题通过直接法离散化，然后用 GA 求解，避免了间接法（Pontryagin 极小值原理）的复杂推导。罚函数法统一处理多类约束，使算法实现简洁高效。",
        "takeaways": [
            "直接法将无限维的连续控制问题转化为有限维参数优化问题",
            "GA 适合复杂约束下的多峰优化问题，不易陷入局部最优",
            "Runge-Kutta 法是数值求解常微分方程的首选方法",
            "罚函数法提供了处理复杂约束的统一框架"
        ]
    },
    {
        "id": "case-011",
        "title": "基于谱聚类和 PageRank 的社交网络社区发现",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2017,
        "award": "F奖（Finalist）",
        "model_types": ["图论与网络", "分类与聚类"],
        "summary": "分析 Twitter 社交网络中的社区结构，结合谱聚类算法和改良的 PageRank 算法发现意见领袖和信息传播关键路径。",
        "problem_brief": "给定一个包含 50,000 个节点和 200,000 条边的 Twitter 社交网络（关注/转发关系），要求：(1) 发现网络中的社区结构；(2) 识别每个社区的意见领袖；(3) 分析信息如何在社区之间传播。",
        "modeling_approach": [
            "构建有向加权网络图：节点 = 用户，边 = 转发关系，权重 = 转发次数",
            "使用谱聚类（Spectral Clustering）进行社区检测：计算拉普拉斯矩阵 L = D - W，取前 k 个特征向量组成嵌入空间，K-Means 聚类",
            "改进的 PageRank 算法识别意见领袖：R(vi) = (1-d)/N + d·Σ(R(vj)/OutDeg(vj))，考虑内容原创率和互动率加权",
            "信息传播模型：基于 SIR 传播动力学在社区间的级联传播分析",
            "模块度（Modularity）Q 值评估社区划分质量"
        ],
        "key_techniques": [
            "谱聚类（Spectral Clustering）",
            "拉普拉斯矩阵与特征分解",
            "PageRank 中心性分析",
            "社区模块度（Modularity）评估",
            "传播级联模型"
        ],
        "highlights": "该论文将谱聚类（基于图论的全局结构）与 PageRank（基于随机游走的局部重要性）结合，既发现了社区，又识别了核心节点。模块度指标为社区数量的确定提供了理论依据，避免了主观设定。",
        "takeaways": [
            "谱聚类利用图拉普拉斯的谱性质，比 K-Means 更适合非凸簇",
            "PageRank 本质上是在图上进行随机游走的平稳分布",
            "模块度 Q 值提供了一种客观的社区划分质量度量",
            "复杂网络分析中，结构发现（社区）和功能分析（传播）往往相辅相成"
        ]
    },
    {
        "id": "case-012",
        "title": "基于主成分分析与判别分析的葡萄酒产地溯源",
        "competition": "全国大学生数学建模竞赛",
        "year": 2015,
        "award": "国赛二等奖",
        "model_types": ["统计模型", "分类与聚类"],
        "summary": "利用 PCA 降维和 Fisher 线性判别分析（LDA）对葡萄酒的理化指标进行分析，实现葡萄酒产地的准确溯源和品种鉴别。",
        "problem_brief": "不同产地的葡萄酒在风味和理化指标上存在差异。给定来自 3 个产区共 178 个葡萄酒样本的 13 项理化指标（酒精度、苹果酸、灰分、类黄酮等），要求建立模型判断未知样本的产地。",
        "modeling_approach": [
            "数据探索：箱线图分析各指标在 3 个产区间的分布差异，剔除异常值",
            "PCA 降维：13 维指标空间 → 前 2 个主成分（累计方差贡献率 72%），在 PC1-PC2 平面上可视化样本分布",
            "Fisher 线性判别分析：寻找使类间散度最大、类内散度最小的投影方向",
            "交叉验证：留一法（LOOCV）评估分类准确率 → 98.3%",
            "对比实验：LDA vs QDA vs KNN vs SVM 四分类器性能对比"
        ],
        "key_techniques": [
            "主成分分析（PCA）降维与可视化",
            "Fisher 线性判别分析（LDA）",
            "留一交叉验证（LOOCV）",
            "混淆矩阵与分类评估指标"
        ],
        "highlights": "该论文从数据探索到降维可视化再到分类建模，形成了一套完整的多元统计数据分析流程。PCA 可视化让读者直观看到 3 个产区在二维平面的分离程度，LDA 则在此基础上给出严格的分类边界。",
        "takeaways": [
            "PCA 是探索高维数据结构的最佳工具之一",
            "LDA 和 PCA 的区别：PCA 是无监督降维，LDA 是有监督降维（利用标签信息）",
            "LOOCV 在小样本场景下是可靠的性能评估方法",
            "对比多种分类器并分析其优劣是建模论文的基本功"
        ]
    },
    {
        "id": "case-013",
        "title": "基于马尔可夫链蒙特卡洛（MCMC）的传染病参数反演",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2016,
        "award": "O奖（Outstanding Winner）",
        "model_types": ["随机模型", "微分方程"],
        "summary": "使用贝叶斯框架和 MCMC 方法从有限的疫情观测数据中反演 SEIR 模型的关键参数（基本再生数 R₀、潜伏期、传染期），并量化参数估计的不确定性。",
        "problem_brief": "对于新出现的传染病，流行病学参数（如 R₀、潜伏期、传染期）通常未知且难以直接测量。给定某地区过去 60 天的每日新增病例数据，请建立方法估计这些关键参数，并给出参数的置信区间。",
        "modeling_approach": [
            "建立 SEIR 确定性模型作为前向模型：dS/dt = -βSI/N, dE/dt = βSI/N - σE, dI/dt = σE - γI, dR/dt = γI",
            "构建贝叶斯反演框架：P(θ|D) ∝ P(D|θ)·P(θ)，θ = {β, σ, γ} 为待估参数",
            "似然函数：假设每日新增病例服从 Poisson 分布，均值 = SEIR 模型预测值",
            "MCMC 采样：使用 Metropolis-Hastings 算法从后验分布中采样，4 条链各 50,000 次迭代",
            "收敛诊断：Gelman-Rubin 统计量 R̂ < 1.1，自相关图评估混合效果",
            "后验分析：R₀ = β/γ 的后验均值和 95% 可信区间"
        ],
        "key_techniques": [
            "贝叶斯统计推断",
            "MCMC（Metropolis-Hastings 算法）",
            "SEIR 仓室模型",
            "Gelman-Rubin 收敛诊断",
            "参数可识别性分析"
        ],
        "highlights": "该论文获得 Outstanding Winner（特等奖）的核心在于：将确定性的 SEIR 模型与概率化的贝叶斯推断有机结合，不仅给出了参数的最佳估计，还量化了不确定性。MCMC 的收敛诊断和可识别性分析体现了统计建模的严谨性。",
        "takeaways": [
            "贝叶斯方法可以将先验知识融入参数估计，适合信息稀缺场景",
            "MCMC 是贝叶斯计算的核心工具，关键是链的收敛性检查",
            "参数的不确定性量化（置信/可信区间）比点估计更有价值",
            "可识别性分析帮助判断是否所有参数都能从数据中唯一确定"
        ]
    },
    {
        "id": "case-014",
        "title": "基于 NSGA-II 多目标优化的城市充电桩选址",
        "competition": "全国大学生数学建模竞赛",
        "year": 2022,
        "award": "国赛一等奖",
        "model_types": ["优化模型", "图论与网络"],
        "summary": "使用 NSGA-II 算法求解电动汽车充电桩的多目标选址问题，在覆盖率和建设成本之间寻找 Pareto 最优解集。",
        "problem_brief": "某城市计划新建一批电动汽车充电桩。需要综合考虑：最大化覆盖的电动车用户数、最小化建设总成本、最小化用户前往充电桩的平均距离。此外，充电桩的选址还需考虑电网容量约束和城市规划限制。",
        "modeling_approach": [
            "建立 3 目标选址优化模型：Max f₁(x) = 覆盖用户数 / Min f₂(x) = 建设总成本 / Min f₃(x) = 用户平均出行距离",
            "将城市网格化（500m×500m），每个网格为候选选址点，基于路网距离（非欧氏距离）计算用户到充电桩的距离",
            "NSGA-II 求解：种群大小 200 → 非支配排序 → 拥挤度计算 → 锦标赛选择 → 模拟二进制交叉 + 多项式变异",
            "Pareto 前沿可视化：在 f₁-f₂-f₃ 三维空间中展示非支配解集",
            "使用 TOPSIS 从 Pareto 解集中选出折中最优方案，供决策者参考"
        ],
        "key_techniques": [
            "NSGA-II 多目标进化算法",
            "Pareto 最优理论",
            "非支配排序与拥挤度",
            "路网距离度量（Dijkstra 最短路径）",
            "TOPSIS 多属性决策"
        ],
        "highlights": "该论文将多目标优化问题不做人为加权（不简化为单目标），而是用 NSGA-II 完整求出 Pareto 前沿，保留了不同目标之间的 trade-off 信息。TOPSIS 在 Pareto 解集中进行二次决策，将数学优化与多属性决策理论无缝衔接。",
        "takeaways": [
            "多目标优化不应简单地加权求和——Pareto 前沿保留了完整的 trade-off 信息",
            "NSGA-II 是求解多目标优化的经典算法，核心机制是非支配排序和拥挤度",
            "路网距离（而非欧氏距离）是空间选址问题的合理度量",
            "Pareto 解集 + 决策方法（TOPSIS/AHP）= 完整的优化决策流程"
        ]
    },
    {
        "id": "case-015",
        "title": "基于 K-Means 和 DBSCAN 的客户分群与精准营销",
        "competition": "全国大学生数学建模竞赛",
        "year": 2018,
        "award": "国赛二等奖",
        "model_types": ["分类与聚类"],
        "summary": "对电商平台的客户消费行为数据进行聚类分析，结合 K-Means 和 DBSCAN 发现不同价值的客户群体，为精准营销策略提供数据支持。",
        "problem_brief": "某电商平台有 50 万条用户消费记录（含消费金额、频次、最近购买时间、商品品类偏好等）。请对客户进行分群，并为不同群体设计差异化的营销策略。",
        "modeling_approach": [
            "RFM 指标构建：Recency（最近消费至今）、Frequency（消费频次）、Monetary（消费金额）",
            "数据标准化后使用肘部法则和轮廓系数确定最优 K 值（K=5）",
            "K-Means 聚类：将客户分为 5 类 → 高价值/潜力/一般/低活跃/流失客户",
            "DBSCAN 补充分析：发现 K-Means 无法识别的非球形簇和异常点群",
            "每类客户特征画像：消费金额分布、购买时段偏好、品类偏好 → 精准营销建议"
        ],
        "key_techniques": [
            "RFM 客户价值模型",
            "K-Means 聚类（肘部法则 + 轮廓系数）",
            "DBSCAN 密度聚类（异常点检测）",
            "客户画像与营销策略映射"
        ],
        "highlights": "该论文将 K-Means（球形簇发现）和 DBSCAN（任意形状簇发现+噪声过滤）互补使用，全面捕捉了客户群体的分布特征。从聚类结果到营销策略的映射使数学模型直接产生了商业价值。",
        "takeaways": [
            "RFM 是客户分群的经典指标体系，简单有效",
            "K-Means 适合球形簇，DBSCAN 适合不规则簇——两者互补",
            "肘部法则和轮廓系数提供了客观的 K 值选择标准",
            "聚类只是手段，将聚类结果转化为可操作的业务建议才是目的"
        ]
    },
    {
        "id": "case-016",
        "title": "基于 Kriging 插值的全国空气质量空间分布估计",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2019,
        "award": "M奖（Meritorious Winner）",
        "model_types": ["统计模型", "机理/仿真"],
        "summary": "利用 Kriging 空间插值方法，基于有限监测站点的空气质量数据估计全国 PM2.5 浓度分布，并分析污染的空间传播特征。",
        "problem_brief": "全国有 1500 个空气质量监测站，但监测站点在空间上分布不均（东部密集、西部稀疏）。请建立空间统计模型，利用有限站点的观测数据，估计全国任意位置的 PM2.5 浓度，并给出估计的不确定性。",
        "modeling_approach": [
            "探索性空间数据分析：变异函数（Variogram）刻画 PM2.5 浓度的空间相关性随距离的衰减",
            "拟合理论变异函数模型：球状模型（Spherical）、指数模型（Exponential）、高斯模型（Gaussian），通过加权最小二乘选择最优模型",
            "普通 Kriging 插值：利用周围已知站点的加权线性组合估计未知点的浓度，权重由变异函数确定",
            "Kriging 方差作为不确定性度量：插值精度在站点密集区高、稀疏区低",
            "结合风场数据进行污染扩散分析：识别 PM2.5 的高污染传播通道"
        ],
        "key_techniques": [
            "Kriging 空间插值（地统计学核心方法）",
            "变异函数（Variogram）分析与拟合",
            "空间自相关分析（Moran's I）",
            "克里金方差不确定性量化"
        ],
        "highlights": "Kriging 区别于普通插值方法（如反距离加权 IDW）的核心优势在于：它不仅给出点估计，还给出估计方差（不确定性）。论文同时利用变异函数揭示了 PM2.5 的空间相关距离约为 200km，这对监测站布设优化有指导意义。",
        "takeaways": [
            "Kriging 是空间统计的核心方法，最佳线性无偏估计（BLUE）",
            "变异函数是空间建模的基础——刻画'距离越近越相似'的规律",
            "估计的不确定性（Kriging 方差）——这是普通插值提供不了的",
            "地统计学方法广泛适用于气象、环境、矿产、土壤等领域"
        ]
    },
    {
        "id": "case-017",
        "title": "基于博弈论的出租车定价与平台抽成策略",
        "competition": "全国大学生数学建模竞赛",
        "year": 2020,
        "award": "国赛一等奖",
        "model_types": ["优化模型", "随机模型"],
        "summary": "建立网约车平台、司机、乘客三方演化博弈模型，分析不同定价策略和平台抽成比例对市场均衡的影响。",
        "problem_brief": "网约车平台需要制定价格和抽成策略，平衡司机收入、乘客出行成本和平台利润。考虑高峰/平峰时段的需求差异，以及司机的接单决策对市场供给的影响，建立博弈模型分析最优定价策略。",
        "modeling_approach": [
            "构建三方演化博弈模型：平台选择抽成比例 r，司机选择是否接单（策略 S₁=接单, S₂=不接单），乘客选择出行方式（策略 C₁=网约车, C₂=公共交通）",
            "建立各方的收益矩阵：司机收益 = (1-r)×车费 - 成本(油费+时间)；乘客收益 = 时间价值 - 车费 - 等待时间成本；平台收益 = r×车费总和",
            "复制动态方程：dx/dt = x(1-x)(E₁ - E₂)，分析各策略比例的演化趋势",
            "求解演化稳定策略（ESS）：通过 Jacobian 矩阵特征值判断均衡点的稳定性",
            "数值仿真：分析抽成比例 r 在 [0.1, 0.4] 范围内变化时，三方收益和总社会福利的变化"
        ],
        "key_techniques": [
            "演化博弈论（Evolutionary Game Theory）",
            "复制动态方程",
            "演化稳定策略（ESS）",
            "纳什均衡与 Pareto 最优",
            "社会福利函数分析"
        ],
        "highlights": "该论文使用演化博弈论（而非经典博弈论）的分析框架，考虑了参与者策略选择的动态调整过程。通过复制动态方程揭示了平台定价策略调整如何引导市场从非均衡态逐步收敛到均衡态。",
        "takeaways": [
            "演化博弈论适合分析大规模群体在有限理性下的策略演化",
            "ESS（演化稳定策略）是比 Nash 均衡更符合现实的选择",
            "复制动态方程描述策略比例的演化，类似于种群生态学模型",
            "博弈模型中各方收益的精确刻画是模型可信度的基础"
        ]
    },
    {
        "id": "case-018",
        "title": "基于有限元法的桥梁结构受力分析与优化",
        "competition": "全国大学生数学建模竞赛",
        "year": 2014,
        "award": "国赛一等奖",
        "model_types": ["微分方程", "机理/仿真", "优化模型"],
        "summary": "使用有限元法（FEM）对悬索桥进行结构力学分析，计算桥面在车辆载荷下的应力和位移分布，并优化桥塔高度和缆索张力。",
        "problem_brief": "某悬索桥全长 800m，主跨 500m。在车辆载荷（30 辆 40 吨货车分布在桥上不同位置）作用下，分析桥面的最大位移和应力分布，并提出桥塔高度和缆索初始张力的优化方案。",
        "modeling_approach": [
            "建立悬索桥的简化力学模型：将桥面离散为 N 个梁单元，每个单元有 2 个节点，每个节点 3 个自由度（竖向位移、转角、轴向位移）",
            "组装总刚度矩阵 K：K = ΣKₑ（单元刚度矩阵），边界条件处理（桥塔处位移=0）",
            "载荷向量 F：30 辆车的位置和重量转化为节点载荷（等效节点力）",
            "求解线性方程组 KU = F：得到各节点的位移向量 U",
            "后处理：由位移计算各单元应变和应力（σ = Eε），绘制桥面弯矩图和剪力图",
            "优化：以桥面最大位移最小化 + 材料成本最小化为双目标，优化桥塔高度 h 和缆索初始张力 T₀"
        ],
        "key_techniques": [
            "有限元法（FEM）结构离散化",
            "刚度矩阵组装与边界条件处理",
            "结构力学（梁理论/弯矩/剪力）",
            "多目标优化（加权法 → 单目标）"
        ],
        "highlights": "该论文将复杂的连续体力学问题通过有限元离散转化为矩阵方程，体现了数值计算解决工程问题的核心范式。刚度矩阵的组装和边界条件处理是有限元法的精髓所在。",
        "takeaways": [
            "有限元法将无限自由度的连续体问题转化为有限自由度的离散问题",
            "刚度矩阵的组装是 FEM 的核心——'化整为零，积零为整'",
            "边界条件的正确处理是 FEM 求解精度的关键",
            "FEM 不仅用于结构力学，也广泛用于热传导、电磁场、流体力学等"
        ]
    },
    {
        "id": "case-019",
        "title": "基于深度强化学习的交通信号灯智能控制",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2022,
        "award": "M奖（Meritorious Winner）",
        "model_types": ["优化模型", "机理/仿真"],
        "summary": "使用深度 Q 网络（DQN）智能控制城市路口的交通信号灯，通过强化学习使信号灯学会根据实时车流量自适应调整红绿灯时长。",
        "problem_brief": "传统的固定配时信号灯无法应对实时变化的交通流。请设计一个智能信号灯控制系统，根据路口的实时车流量动态调整绿灯时长，以最小化车辆平均等待时间。",
        "modeling_approach": [
            "将路口建模为强化学习环境：状态 S = 各车道的排队车辆数 + 当前信号相位 + 已持续时间 / 动作 A = {保持当前相位, 切换到下一相位}",
            "奖励函数设计：r = -(总等待车辆数) - α×(相位切换惩罚)，鼓励减少等待且避免频繁切换",
            "DQN 算法：使用两个神经网络（Q-Network + Target-Network）+ 经验回放（Experience Replay）稳定训练",
            "在 SUMO 交通仿真平台上训练 500 episode，每个 episode 模拟 1 小时的交通流",
            "对比实验：DQN 控制 vs 固定配时 vs 感应控制（actuated）三种策略的车辆平均等待时间"
        ],
        "key_techniques": [
            "深度强化学习（DQN）",
            "Q-Learning 与 Bellman 方程",
            "经验回放（Experience Replay）",
            "SUMO 交通微观仿真",
            "奖励函数工程（Reward Shaping）"
        ],
        "highlights": "该论文将路口信号灯控制建模为马尔可夫决策过程（MDP），利用 DQN 让信号灯在与交通流的不断交互中自学最优策略。相比传统控制方法，DQN 控制的平均等待时间降低了 27%。",
        "takeaways": [
            "强化学习适合序列决策问题——每一步的决策影响未来状态",
            "奖励函数的设计决定了智能体学到的行为——需要平衡多个目标",
            "DQN 的两个关键技术：目标网络（稳定训练）和经验回放（打破数据相关性）",
            "交通仿真平台（SUMO/VISSIM）是交通类建模的验证基础设施"
        ]
    },
    {
        "id": "case-020",
        "title": "基于贝叶斯网络的教学质量因素分析",
        "competition": "全国大学生数学建模竞赛",
        "year": 2017,
        "award": "国赛二等奖",
        "model_types": ["统计模型", "评价模型"],
        "summary": "构建贝叶斯网络模型，分析影响高校教学质量的多因素因果关系，通过概率推理识别关键影响因素及其交互效应。",
        "problem_brief": "高校教学质量受多种因素影响（教师职称、教学方法、班级规模、学生基础、实验条件等）。请建立模型分析这些因素之间的因果关系及其对教学质量的影响程度。",
        "modeling_approach": [
            "基于专家知识和数据构建贝叶斯网络结构：节点 = 各影响因素 + 教学质量，有向边 = 因果关系",
            "结构学习：使用 Hill-Climbing 算法 + BIC 评分从数据中学习网络结构",
            "参数学习：给定结构，使用最大似然估计（MLE）学习条件概率表（CPT）",
            "概率推理：使用变量消元法（Variable Elimination）计算 P(教学质量高 | 某因素 = 某值)",
            "敏感性分析：依次设置每个因素为'最优'和'最差'状态，计算教学质量期望值的变化幅度"
        ],
        "key_techniques": [
            "贝叶斯网络（Bayesian Network）",
            "结构学习（Hill-Climbing + BIC 评分）",
            "条件概率表（CPT）参数估计",
            "概率推理（变量消元/信念传播）",
            "敏感性分析（Tornado 图）"
        ],
        "highlights": "贝叶斯网络区别于传统的回归分析，能直观展示因素之间的因果关系（有向无环图 DAG）和条件独立性。论文通过概率推理回答了'如果改善实验条件，教学质量提高的概率是多少？'这类反事实问题。",
        "takeaways": [
            "贝叶斯网络 = 图模型 + 概率推理，擅长表达因果关系",
            "结构学习可以从数据中发现变量间的依赖关系",
            "概率推理可以回答 what-if 和反事实问题",
            "Tornado 图是敏感性分析的直观可视化工具"
        ]
    }
]


def get_all_cases() -> list[dict]:
    """获取所有案例摘要"""
    return [
        {
            "id": c["id"],
            "title": c["title"],
            "competition": c["competition"],
            "year": c["year"],
            "award": c["award"],
            "model_types": c["model_types"],
            "summary": c["summary"],
        }
        for c in CASE_LIBRARY
    ]


def get_case_detail(case_id: str) -> dict | None:
    """获取单个案例的完整解析"""
    for c in CASE_LIBRARY:
        if c["id"] == case_id:
            return c
    return None


# ============================================================
# 历年真题库 — 数学建模竞赛历年真题
# ============================================================

EXAM_BANK = [
    {
        "id": "exam-001",
        "title": "高温作业专用服装设计",
        "competition": "全国大学生数学建模竞赛",
        "year": 2018,
        "topic": "A题",
        "difficulty": 4,
        "model_types": ["微分方程", "优化模型"],
        "summary": "设计高温环境下作业的专用服装，需综合考虑热传导、服装厚度和材料特性，建立多层热传导偏微分方程模型。",
        "problem_text": "在高温环境下工作时，人们需要穿着专用服装以避免灼伤。专用服装通常由三层织物材料构成，记为I、II、III层。设环境温度为75°C，假人皮肤外侧温度不超过47°C，且超过44°C的时间不超过5分钟。请建立数学模型解决以下问题：\n\n(1) 已知I层和III层厚度，确定II层的最优厚度，使皮肤温度满足约束；\n\n(2) 当II层厚度确定后，求I层和III层的最优厚度组合；\n\n(3) 综合考虑成本、隔热效果等因素，给出三层材料的最优厚度设计。",
        "key_concepts": ["热传导Fourier定律", "偏微分方程", "有限差分法", "非线性优化", "参数敏感性分析"],
        "data_attachment": "附件1：各层材料参数表（密度、比热容、热导率）；附件2：环境温度曲线",
        "solution_hints": [
            "建立一维非稳态热传导PDE模型",
            "使用Crank-Nicolson隐格式数值求解",
            "以总厚度最小为目标函数，温度阈值为约束",
            "通过参数扫描确定最优厚度组合"
        ]
    },
    {
        "id": "exam-002",
        "title": "车道被占用对城市道路通行能力的影响",
        "competition": "全国大学生数学建模竞赛",
        "year": 2013,
        "topic": "A题",
        "difficulty": 3,
        "model_types": ["统计模型", "机理/仿真"],
        "summary": "分析交通事故导致车道被占用对城市道路通行能力的影响，建立排队论与交通流模型。",
        "problem_text": "车道被占用是指因交通事故、路边停车、占道施工等因素导致车道或道路横断面通行能力在单位时间内降低的现象。请建立数学模型，分析以下问题：\n\n(1) 描述视频1中交通事故发生至撤离期间，事故所处横断面实际通行能力的变化过程；\n\n(2) 分析同一横断面交通事故所占车道不同对该横断面实际通行能力影响的差异；\n\n(3) 构建模型分析交通事故所影响的路段车辆排队长度与事故横断面实际通行能力、事故持续时间、路段上游车流量间的关系。",
        "key_concepts": ["交通流理论", "排队论", "通行能力", "回归分析", "仿真建模"],
        "data_attachment": "视频1：上游路口至事故路口的交通监控；视频2：另一事故的不同车道占用情况",
        "solution_hints": [
            "从视频中提取车流量、车速、排队长度等数据",
            "分析通行能力的时间变化趋势（分段线性或指数衰减）",
            "对比不同占用车道的通行能力差异",
            "建立排队长度与通行能力、上游流量的关系模型"
        ]
    },
    {
        "id": "exam-003",
        "title": "CT系统参数标定与成像",
        "competition": "全国大学生数学建模竞赛",
        "year": 2017,
        "topic": "A题",
        "difficulty": 5,
        "model_types": ["优化模型", "机理/仿真"],
        "summary": "利用已知结构的样品标定CT系统的参数，并利用标定后的系统对未知结构进行成像。",
        "problem_text": "CT（Computed Tomography）可以在不破坏样品的情况下，利用样品对射线能量的吸收特性对生物组织和工程材料进行断层成像。一种典型的二维CT系统如下图所示：\n\n(1) 根据给出的已知结构样品标定CT系统的参数（探测器单元间距、旋转中心位置等）；\n\n(2) 利用标定后的CT系统对未知结构进行成像，给出吸收率分布；\n\n(3) 分析标定精度对成像质量的影响，提出提高精度的方法。",
        "key_concepts": ["Radon变换", "反投影重建", "滤波反投影FBP", "参数标定", "图像重建"],
        "data_attachment": "附件1：已知吸收率分布模板的接收数据；附件2：未知结构的接收数据",
        "solution_hints": [
            "利用已知模板建立CT系统几何参数标定的数学模型",
            "使用Radon变换的正反问题建立成像模型",
            "实现滤波反投影（FBP）算法进行图像重建",
            "分析标定误差传递对重建图像质量的影响"
        ]
    },
    {
        "id": "exam-004",
        "title": "拍照赚钱的任务定价",
        "competition": "全国大学生数学建模竞赛",
        "year": 2017,
        "topic": "B题",
        "difficulty": 3,
        "model_types": ["评价模型", "预测/回归", "优化模型"],
        "summary": "设计「拍照赚钱」APP的任务定价方案，考虑任务完成率、用户活跃度和平台收益的平衡。",
        "problem_text": "「拍照赚钱」是移动互联网下的一种自助式服务模式。用户下载APP，注册成为会员，然后从APP上领取需要拍照的任务，赚取APP对任务所标定的酬金。\n\n(1) 分析当前定价方案的执行效果，说明任务未完成的原因；\n\n(2) 设计新的任务定价方案，提高任务完成率；\n\n(3) 考虑将任务打包发布，设计打包策略和定价方案。",
        "key_concepts": ["回归分析", "聚类分析", "定价策略", "供需平衡", "最优化"],
        "data_attachment": "附件1：已结束项目任务数据（位置、标价、完成情况）；附件2：会员位置数据",
        "solution_hints": [
            "分析任务完成率与价格、位置、时间等因素的关系",
            "基于距离成本定价模型（考虑会员到任务点的距离）",
            "引入价格弹性函数建立最优定价模型",
            "使用聚类方法进行任务打包优化"
        ]
    },
    {
        "id": "exam-005",
        "title": "食品质量安全的抽检策略",
        "competition": "美国大学生数学建模竞赛（MCM）",
        "year": 2019,
        "topic": "C题",
        "difficulty": 3,
        "model_types": ["统计模型", "优化模型", "评价模型"],
        "summary": "设计食品安全抽检策略，在有限资源下最大化食品安全风险检测的覆盖率。",
        "problem_text": "食品安全是关乎公众健康的重要议题。在预算有限的情况下，食品安全监管部门需要设计有效的抽检策略，以最大限度地发现和预防食品安全问题。请建立模型回答：\n\n(1) 根据历史抽检数据，识别食品安全风险的主要来源和分布特征；\n\n(2) 设计最优的抽检频率和样本分配方案，使风险发现率最大化；\n\n(3) 考虑不同食品类别和地区的风险差异，给出差异化的抽检策略。",
        "key_concepts": ["假设检验", "抽样理论", "风险分析", "资源分配优化", "贝叶斯统计"],
        "data_attachment": "历史食品安全抽检数据（食品类别、地区、检测项目、合格/不合格等）",
        "solution_hints": [
            "利用历史数据估计各食品类别的不合格率分布",
            "基于风险矩阵建立优先级排序模型",
            "建立抽样量分配的最优化模型（约束：总预算）",
            "使用贝叶斯方法动态更新风险估计"
        ]
    },
    {
        "id": "exam-006",
        "title": "系泊系统的设计",
        "competition": "全国大学生数学建模竞赛",
        "year": 2016,
        "topic": "A题",
        "difficulty": 4,
        "model_types": ["机理/仿真", "优化模型"],
        "summary": "设计海上浮标系泊系统，分析在不同海况下浮标的运动和锚链的受力。",
        "problem_text": "近浅海观测网的传输节点由浮标系统、系泊系统和水声通讯系统组成。请建立数学模型研究：\n\n(1) 在静水中，钢桶和各节钢管的倾斜角度、锚链形状、浮标的吃水深度和游动区域；\n\n(2) 在风速12m/s和24m/s、海水静止的情况下，分析浮标的运动和锚链的受力；\n\n(3) 考虑潮汐引起的海水深度变化，分析不同情况下系泊系统的工作状态。",
        "key_concepts": ["力学平衡", "悬链线方程", "流体力学", "多体动力学", "数值求解"],
        "data_attachment": "系泊系统各部件参数表（质量、长度、直径等）；锚链型号参数",
        "solution_hints": [
            "建立各节点受力平衡方程（重力、浮力、拉力、水流力）",
            "使用悬链线理论建立锚链形状模型",
            "迭代求解非线性方程组确定平衡状态",
            "分析不同风速下的系统响应和安全性"
        ]
    },
    {
        "id": "exam-007",
        "title": "机场出租车调度优化",
        "competition": "全国大学生数学建模竞赛",
        "year": 2019,
        "topic": "C题",
        "difficulty": 2,
        "model_types": ["优化模型", "预测/回归", "统计模型"],
        "summary": "优化机场出租车调度方案，平衡乘客等待时间和司机收益。",
        "problem_text": "机场出租车是城市交通的重要组成部分。出租车司机面临两个选择：A. 前往到达区排队等待载客；B. 空车返回市区，直接放弃排队。请建立数学模型：\n\n(1) 分析影响司机决策的因素，建立决策模型；\n\n(2) 收集国内某一机场的数据，验证模型的合理性；\n\n(3) 设计「优先权」机制，使得短途载客返回的司机能够获得某种「优先」排队权。",
        "key_concepts": ["排队论", "决策分析", "收益函数", "博弈论", "计算机模拟"],
        "data_attachment": "机场航班时刻表、乘客到达数据（需自行收集或假设）",
        "solution_hints": [
            "建立司机决策的收益函数（考虑等待时间、载客距离、空车成本）",
            "使用排队论分析等待时间与航班时刻的关系",
            "通过计算机模拟验证不同的调度策略",
            "设计短途优先机制提升整体效率"
        ]
    },
    {
        "id": "exam-008",
        "title": "太阳影子定位",
        "competition": "全国大学生数学建模竞赛",
        "year": 2015,
        "topic": "A题",
        "difficulty": 4,
        "model_types": ["机理/仿真", "优化模型"],
        "summary": "利用太阳影子视频数据确定拍摄地点和日期，建立日影定位数学模型。",
        "problem_text": "太阳影子的变化蕴含着丰富的信息。请建立数学模型解决以下问题：\n\n(1) 建立影子长度变化的数学模型，分析影子长度关于各参数的变化规律；\n\n(2) 根据某固定直杆在水平地面上的太阳影子顶点坐标数据，确定直杆所在地理位置；\n\n(3) 在问题(2)的基础上，若拍摄日期未知，同时确定地点和日期。",
        "key_concepts": ["天球坐标系", "太阳高度角", "方位角", "非线性最小二乘", "反问题"],
        "data_attachment": "附件1：某时刻影子顶点坐标数据；附件2-3：不同地点的影子坐标数据",
        "solution_hints": [
            "建立太阳位置的天文学模型（赤纬角、时角、太阳高度角）",
            "推导影子长度和方向与经纬度、时间的关系",
            "利用多时刻数据建立非线性方程组，最小二乘求解经纬度",
            "在未知日期时通过参数扫描确定最优解"
        ]
    },
    {
        "id": "exam-009",
        "title": "葡萄酒的评价",
        "competition": "全国大学生数学建模竞赛",
        "year": 2012,
        "topic": "A题",
        "difficulty": 2,
        "model_types": ["评价模型", "统计模型", "分类/识别"],
        "summary": "建立葡萄酒质量评价模型，分析评酒员评分的一致性和葡萄酒的理化指标与感官评价的关系。",
        "problem_text": "确定葡萄酒质量时，一般通过聘请一批有资质的评酒员进行品评。每个评酒员在对葡萄酒进行品尝后对其分类指标打分，然后求和得到总分，从而确定葡萄酒的质量。请建立数学模型：\n\n(1) 分析两组评酒员评分结果的显著性差异和可信度；\n\n(2) 根据酿酒葡萄的理化指标和葡萄酒的质量对葡萄进行分级；\n\n(3) 分析酿酒葡萄和葡萄酒的理化指标之间的联系。",
        "key_concepts": ["t检验/方差分析", "信度分析(α系数)", "主成分分析PCA", "聚类分析", "典型相关分析"],
        "data_attachment": "附件1：红/白葡萄酒评分表；附件2：酿酒葡萄理化指标；附件3：葡萄酒理化指标",
        "solution_hints": [
            "使用配对t检验或Wilcoxon检验比较两组评分差异",
            "计算Cronbach's α系数评估评分者信度",
            "PCA降维后聚类分析进行葡萄分级",
            "使用典型相关分析(CCA)探究葡萄与葡萄酒指标的联系"
        ]
    },
    {
        "id": "exam-010",
        "title": "公交线路的优化设计",
        "competition": "全国大学生数学建模竞赛",
        "year": 2007,
        "topic": "B题",
        "difficulty": 3,
        "model_types": ["图论与网络模型", "优化模型"],
        "summary": "优化城市公共交通网络，设计公交线路和换乘方案，提高运输效率。",
        "problem_text": "我国人民翘首企盼的「公交优先」战略正在逐步实施。为了实现「公交优先」，需要对公交网络进行优化设计。请建立数学模型：\n\n(1) 给出任意两站点之间的最佳公交线路选择模型，考虑换乘次数、时间、费用等因素；\n\n(2) 考虑地铁线路的引入，重新设计公交线路和换乘方案；\n\n(3) 对公交网络进行综合评价，提出优化建议。",
        "key_concepts": ["最短路径Dijkstra", "图论", "多目标优化", "网络流", "换乘优化"],
        "data_attachment": "北京市部分公交线路数据（站点、线路、运营时间）",
        "solution_hints": [
            "构建公交网络图模型（节点=站点，边=线路连接）",
            "使用改进Dijkstra算法求多目标最短路径",
            "考虑换乘惩罚因子平衡直达与换乘的权衡",
            "引入地铁后的多模式交通网络建模"
        ]
    },
]


def get_all_exams() -> list[dict]:
    """获取所有真题摘要"""
    return [
        {
            "id": e["id"],
            "title": e["title"],
            "competition": e["competition"],
            "year": e["year"],
            "topic": e["topic"],
            "difficulty": e["difficulty"],
            "model_types": e["model_types"],
            "summary": e["summary"],
        }
        for e in EXAM_BANK
    ]


def get_exam_detail(exam_id: str) -> dict | None:
    """获取单个真题的完整信息"""
    for e in EXAM_BANK:
        if e["id"] == exam_id:
            return e
    return None
