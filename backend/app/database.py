"""
============================================================
数据库模块 - SQLite + SQLAlchemy 异步引擎
应用场景：轻量化数据持久化，无需额外数据库容器
============================================================
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import os

from app.config import settings

# 确保数据目录存在
os.makedirs("data", exist_ok=True)

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明基类"""
    pass


async def get_db() -> AsyncSession:
    """获取数据库会话的依赖注入函数"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """
    初始化数据库表结构
    首次启动时自动建表，并插入默认实验题库数据
    """
    from app.models.models import Experiment

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

        # 数据库迁移：为已有 competition_task 表添加 S6/S7 列（如不存在）
        from sqlalchemy import text as sa_text
        migration_columns = [
            ("evidence_gate", "S6证据门禁报告(JSON)"),
            ("draft_paper", "S7论文草稿(JSON元信息)"),
            ("format_check", "S7格式检查报告(JSON)"),
        ]
        for col_name, col_comment in migration_columns:
            try:
                await conn.execute(
                    sa_text(f"ALTER TABLE competition_task ADD COLUMN {col_name} TEXT DEFAULT ''")
                )
            except Exception:
                pass  # 列已存在

    # 检查是否需要初始化题库数据
    async with async_session_factory() as session:
        # --- 默认用户 ---
        from app.services.auth_service import hash_password
        from app.models.models import User

        result = await session.execute(text("SELECT COUNT(*) FROM user"))
        user_count = result.scalar()
        if user_count == 0:
            default_user = User(
                username="guoketg",
                password_hash=hash_password("123456"),
                role="admin",
                display_name="默认管理员",
            )
            session.add(default_user)
            await session.commit()
            print("✅ 默认管理员账号已创建 (guoketg / 123456)")

        # --- 默认题库 ---
        result = await session.execute(text("SELECT COUNT(*) FROM experiment"))
        count = result.scalar()
        if count == 0:
            # 使用 ORM 插入默认数学建模实验题库数据
            default_experiments = [
                # ===== 优化模型（3题）=====
                Experiment(subject='优化模型', title='线性规划——生产计划优化',
                    description='某工厂生产A、B两种产品，每件A产品利润300元，消耗原料甲2kg、乙3kg；每件B产品利润400元，消耗原料甲4kg、乙2kg。每天原料甲可用120kg、乙可用100kg。请建立线性规划模型，确定最优生产方案使利润最大化，并用Python求解。',
                    reference_points='["线性规划","目标函数","约束条件","单纯形法","灵敏度分析"]', difficulty=2,
                    template_code='import numpy as np\nfrom scipy.optimize import linprog\n\n# 目标函数系数（求最大化，linprog默认最小化，取负）\nc = [-300, -400]  # 每件A利润300，B利润400\n\n# 约束条件矩阵\nA = [[2, 4],   # 原料甲：2x1 + 4x2 <= 120\n     [3, 2]]   # 原料乙：3x1 + 2x2 <= 100\nb = [120, 100]\n\n# 变量边界 x1>=0, x2>=0\nbounds = [(0, None), (0, None)]\n\n# 求解线性规划\nresult = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method=\'highs\')\n\nif result.success:\n    x1, x2 = result.x\n    print(f"最优方案：生产A产品{x1:.1f}件，B产品{x2:.1f}件")\n    print(f"最大利润：{-result.fun:.1f}元")\nelse:\n    print("求解失败:", result.message)'),

                Experiment(subject='优化模型', title='整数规划——投资组合选择',
                    description='某投资者有资金100万元，现有5个项目可选。每个项目有固定投资额和预期收益。目标是在不超过总资金的条件下，选择一组项目使总收益最大。请建立0-1整数规划的数学模型并求解。',
                    reference_points='["整数规划","0-1规划","分支定界法","背包问题"]', difficulty=3,
                    template_code='import numpy as np\nfrom scipy.optimize import linprog\n\n# 5个项目的投资额（万元）和预期收益（万元）\ncosts = [25, 30, 40, 35, 20]\nprofits = [50, 65, 80, 70, 35]\ntotal_budget = 100  # 总资金\n\n# 提示：使用 pulp 或 ortools 求解整数规划\n# 或者手动实现分支定界算法\n\n# 请在下方编写0-1整数规划的求解代码\n# TODO: 定义决策变量 x[i] ∈ {0,1}，表示是否选择第i个项目\n# TODO: 约束条件：sum(costs[i] * x[i]) <= total_budget\n# TODO: 目标函数：max sum(profits[i] * x[i])\n\nprint("请完成整数规划求解代码")'),

                Experiment(subject='优化模型', title='多目标优化——车辆路径规划',
                    description='某物流公司需要为3辆卡车规划配送路线，服务10个客户点。目标：(1)最小化总行驶距离；(2)最小化车辆使用数；(3)平衡各车辆的工作量。请将多目标问题转化为单目标（如加权法或ε-约束法），设计数学模型并求解。',
                    reference_points='["多目标优化","Pareto最优","加权法","VRP问题","网络流"]', difficulty=5,
                    template_code='import numpy as np\nimport matplotlib.pyplot as plt\n\n# 10个客户点坐标 (x, y) + 仓库坐标 (0, 0)\nnp.random.seed(42)\ncustomers = np.random.rand(10, 2) * 100\ndepot = np.array([50, 50])\n\n# 计算距离矩阵\ndef distance(p1, p2):\n    return np.sqrt(np.sum((p1 - p2) ** 2))\n\n# TODO: 建立VRP数学模型\n# TODO: 设计目标函数（加权法：w1*总距离 + w2*车辆数 + w3*不平衡度）\n# TODO: 求解并可视化路线\n\n# 可视化客户点分布\nplt.figure(figsize=(8, 8))\nplt.scatter(depot[0], depot[1], c=\'red\', s=200, marker=\'s\', label=\'仓库\')\nplt.scatter(customers[:, 0], customers[:, 1], c=\'blue\', s=100, label=\'客户\')\nfor i, (x, y) in enumerate(customers):\n    plt.annotate(f\'C{i+1}\', (x, y), xytext=(5, 5), textcoords=\'offset points\')\nplt.legend()\nplt.title(\'客户点分布图\')\nplt.show()'),

                # ===== 预测模型（2题）=====
                Experiment(subject='预测模型', title='时间序列预测——城市月均气温',
                    description='利用过去60个月的气温数据，建立ARIMA时间序列预测模型，预测未来12个月的月均气温。要求：(1)数据平稳性检验；(2)确定ARIMA(p,d,q)参数；(3)模型检验与残差分析；(4)给出预测值和置信区间。',
                    reference_points='["ARIMA","时间序列","平稳性检验","ACF/PACF","残差分析"]', difficulty=4,
                    template_code='import numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom statsmodels.tsa.arima.model import ARIMA\nfrom statsmodels.graphics.tsaplots import plot_acf, plot_pacf\n\n# 生成模拟气温数据（带季节性和趋势）\nnp.random.seed(42)\nt = np.arange(60)\ntrend = 15 + 0.02 * t  # 缓慢上升趋势\nseasonal = 10 * np.sin(2 * np.pi * t / 12)  # 年周期\nnoise = np.random.normal(0, 2, 60)  # 随机波动\ntemperatures = trend + seasonal + noise\n\n# TODO: 绘制时序图，观察趋势和季节性\n# TODO: 进行ADF平稳性检验，必要时差分\n# TODO: 绘制ACF/PACF图确定p, q\n# TODO: 训练ARIMA模型\n# TODO: 预测未来12个月并绘制置信区间\n\nplt.figure(figsize=(12, 5))\nplt.plot(t, temperatures, label=\'历史气温\')\nplt.xlabel(\'月份\'); plt.ylabel(\'气温(°C)\')\nplt.title(\'月均气温时间序列\')\nplt.legend(); plt.show()'),

                Experiment(subject='预测模型', title='灰色预测——城市人口增长模型',
                    description='某城市过去10年人口数据（万人）：[856, 873, 892, 913, 935, 958, 982, 1007, 1033, 1060]。使用灰色预测GM(1,1)模型预测未来5年人口变化趋势，并分析模型精度（后验差检验）。',
                    reference_points='["GM(1,1)","灰色预测","累加生成","后验差检验","小样本预测"]', difficulty=3,
                    template_code='import numpy as np\n\n# 原始数据序列（10年人口，单位：万人）\nx0 = np.array([856, 873, 892, 913, 935, 958, 982, 1007, 1033, 1060])\n\n# 步骤1：级比检验（判断是否适合灰色预测）\ndef level_ratio_test(data):\n    n = len(data)\n    lambdas = data[:-1] / data[1:]\n    lower = np.exp(-2 / (n + 1))\n    upper = np.exp(2 / (n + 1))\n    print(f"级比范围: [{lower:.4f}, {upper:.4f}]")\n    print(f"级比值: {lambdas}")\n    return np.all((lambdas >= lower) & (lambdas <= upper))\n\nprint("级比检验结果:", level_ratio_test(x0))\n\n# TODO: 步骤2：一次累加生成(1-AGO)\n# TODO: 步骤3：构造数据矩阵B和数据向量Y\n# TODO: 步骤4：求解参数a, b（发展系数和灰作用量）\n# TODO: 步骤5：建立GM(1,1)预测模型\n# TODO: 步骤6：预测未来5年并计算后验差比值C和小误差概率P'),

                # ===== 评价模型（2题）=====
                Experiment(subject='评价模型', title='层次分析法(AHP)——高校综合评价',
                    description='使用层次分析法对4所高校进行综合排名。评价准则包括：教学质量、科研水平、师资力量、就业率、校园环境。请构建层次结构模型、构造判断矩阵、计算权重向量、进行一致性检验，最终给出综合排名。',
                    reference_points='["AHP","判断矩阵","特征向量","一致性检验","CR值"]', difficulty=3,
                    template_code='import numpy as np\n\n# 评价准则列表\ncriteria = [\'教学质量\', \'科研水平\', \'师资力量\', \'就业率\', \'校园环境\']\nn_criteria = len(criteria)\nn_alternatives = 4  # 4所高校\n\n# TODO: 步骤1——构造准则层判断矩阵（5×5，两两比较）\n# 使用Saaty 1-9标度法\njudgment_matrix = np.array([\n    [1, 3, 2, 1/2, 5],\n    [1/3, 1, 1/2, 1/4, 2],\n    [1/2, 2, 1, 1/3, 3],\n    [2, 4, 3, 1, 6],\n    [1/5, 1/2, 1/3, 1/6, 1]\n])\n\n# TODO: 步骤2——计算权重向量（特征向量法）\ndef calculate_weights(matrix):\n    eigenvalues, eigenvectors = np.linalg.eig(matrix)\n    max_eigenvalue = np.max(eigenvalues.real)\n    weights = eigenvectors[:, np.argmax(eigenvalues.real)].real\n    weights = weights / np.sum(weights)  # 归一化\n    return weights, max_eigenvalue\n\n# TODO: 步骤3——一致性检验\n# CI = (λmax - n) / (n - 1)\n# CR = CI / RI[n]\n# 当CR < 0.1时通过一致性检验\n\n# TODO: 步骤4——方案层评价（对每所高校在各准则下打分，计算综合得分）\nprint("请完成AHP评价模型代码")'),

                Experiment(subject='评价模型', title='TOPSIS法——供应商选择决策',
                    description='某制造企业需从6家供应商中选择最佳合作伙伴。评价指标包括：价格(成本型)、质量合格率(效益型)、交货准时率(效益型)、售后服务评分(效益型)、距离(成本型)。使用TOPSIS法（逼近理想解排序法）进行综合评价和排序。',
                    reference_points='["TOPSIS","理想解","负理想解","熵权法","归一化"]', difficulty=3,
                    template_code='import numpy as np\n\n# 6个供应商 × 5个评价指标的数据矩阵\n# 行：供应商S1-S6；列：价格(元), 合格率(%), 准时率(%), 服务分, 距离(km)\ndata = np.array([\n    [120, 98, 95, 85, 50],\n    [100, 95, 90, 78, 80],\n    [135, 99, 88, 92, 30],\n    [110, 92, 98, 70, 60],\n    [125, 97, 93, 88, 45],\n    [105, 94, 85, 75, 70]\n])\n\n# 指标类型：1=效益型（越大越好），0=成本型（越小越好）\nindicator_type = [0, 1, 1, 1, 0]\n\n# TODO: 步骤1——数据正向化（成本型指标取倒数或差值）\n# TODO: 步骤2——矩阵归一化（向量归一化法）\n# TODO: 步骤3——确定正理想解A+和负理想解A-\n# TODO: 步骤4——计算各方案到正负理想解的距离\n# TODO: 步骤5——计算相对贴近度C_i并排序\n\nprint("6家供应商TOPSIS评价分析")\nprint("=" * 40)\n# 在此完成TOPSIS计算代码'),

                # ===== 分类与聚类模型（1题）=====
                Experiment(subject='分类与聚类', title='K-means聚类——客户群体细分',
                    description='某电商平台收集了200位客户的年消费金额和购物频次数据。使用K-means聚类算法将客户分为3-5个群体（如高价值、中等、低价值客户），分析各群体的特征，为企业制定差异化营销策略提供依据。',
                    reference_points='["K-means","肘部法则","轮廓系数","客户细分","数据标准化"]', difficulty=2,
                    template_code='import numpy as np\nimport matplotlib.pyplot as plt\nfrom sklearn.cluster import KMeans\nfrom sklearn.preprocessing import StandardScaler\n\n# 生成模拟客户数据\nnp.random.seed(42)\nn_customers = 200\n# 聚类1：高消费高频次（高价值客户）\nc1 = np.random.multivariate_normal([15000, 25], [[3000, 5], [5, 15]], 40)\n# 聚类2：中等消费中频次\nc2 = np.random.multivariate_normal([8000, 12], [[2000, 3], [3, 8]], 80)\n# 聚类3：低消费低频次\nc3 = np.random.multivariate_normal([3000, 5], [[1000, 2], [2, 5]], 80)\n\nX = np.vstack([c1, c2, c3])\n\n# 数据标准化\nscaler = StandardScaler()\nX_scaled = scaler.fit_transform(X)\n\n# TODO: 步骤1——使用肘部法则确定最佳聚类数k\n# TODO: 步骤2——使用轮廓系数验证k的选择\n# TODO: 步骤3——执行K-means聚类\n# TODO: 步骤4——可视化聚类结果并分析各群体特征\n\nplt.figure(figsize=(10, 6))\nplt.scatter(X[:, 0], X[:, 1], alpha=0.6)\nplt.xlabel(\'年消费金额(元)\'); plt.ylabel(\'年购物频次(次)\')\nplt.title(\'客户消费数据分布\')\nplt.show()'),

                # ===== 微分方程模型（1题）=====
                Experiment(subject='微分方程', title='SIR传染病传播模型',
                    description='使用SIR仓室模型模拟传染病在人群中的传播过程。设总人口N=10000，初始感染者I₀=10，恢复者R₀=0。感染率β=0.3/天，恢复率γ=0.1/天。请：(1)建立SIR微分方程组；(2)用数值方法（如龙格-库塔法）求解；(3)分析峰值时间和规模；(4)讨论防控措施效果。',
                    reference_points='["SIR模型","常微分方程","龙格-库塔法","传染病动力学","R₀基本再生数"]', difficulty=4,
                    template_code='import numpy as np\nimport matplotlib.pyplot as plt\nfrom scipy.integrate import odeint\n\n# SIR模型参数\nN = 10000      # 总人口\nI0 = 10        # 初始感染者\nR0 = 0         # 初始恢复者\nS0 = N - I0 - R0  # 初始易感者\nbeta = 0.3     # 感染率（每人每天有效接触数）\ngamma = 0.1    # 恢复率（1/平均感染期）\nR0_value = beta / gamma  # 基本再生数\n\nprint(f"基本再生数 R₀ = {R0_value:.2f}")\n\n# SIR微分方程组\ndef sir_deriv(y, t, N, beta, gamma):\n    S, I, R = y\n    dSdt = -beta * S * I / N\n    dIdt = beta * S * I / N - gamma * I\n    dRdt = gamma * I\n    return [dSdt, dIdt, dRdt]\n\n# TODO: 使用odeint求解微分方程组\n# TODO: 绘制S(t), I(t), R(t)随时间变化曲线\n# TODO: 找到感染峰值I_max和对应时间t_peak\n# TODO: 讨论β和γ变化对疫情的影响\n\n# 时间范围\nt = np.linspace(0, 160, 1000)  # 160天\n\nprint("请完成SIR模型求解与可视化代码")'),

                # ===== 统计模型（1题）=====
                Experiment(subject='统计模型', title='多元回归分析——房价影响因素',
                    description='收集了某城市100套住宅的房价及5个影响因素数据：面积(m²)、卧室数、房龄(年)、距市中心距离(km)、周边学校数量。请建立多元线性回归模型：(1)分析各因素与房价的相关性；(2)检验模型显著性和各回归系数；(3)诊断多重共线性(VIF)；(4)给出回归方程并预测。',
                    reference_points='["多元线性回归","显著性检验","VIF","残差诊断","R²决定系数"]', difficulty=3,
                    template_code='import numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.metrics import r2_score, mean_squared_error\n\n# 生成模拟房价数据\nnp.random.seed(42)\narea = np.random.normal(100, 30, 100)       # 面积\nbedrooms = np.random.randint(1, 5, 100)      # 卧室数\nage = np.random.exponential(15, 100)          # 房龄\ndistance = np.random.gamma(5, 2, 100)         # 距市中心距离\nschools = np.random.poisson(3, 100)           # 周边学校数量\n\n# 房价 = 50 + 0.8*面积 + 5*卧室 - 0.3*房龄 - 2*距离 + 8*学校 + 噪声\nprice = 50 + 0.8*area + 5*bedrooms - 0.3*age - 2*distance + 8*schools + np.random.normal(0, 15, 100)\n\n# 构造DataFrame\ndf = pd.DataFrame({\'面积\': area, \'卧室数\': bedrooms, \'房龄\': age,\n                   \'距市中心\': distance, \'学校数\': schools, \'房价\': price})\n\n# TODO: 步骤1——绘制相关性热力图\n# TODO: 步骤2——建立多元线性回归模型\n# TODO: 步骤3——检验回归系数显著性（t检验）\n# TODO: 步骤4——计算VIF诊断多重共线性\n# TODO: 步骤5——残差分析和模型诊断\n\nprint(df.describe())\nprint("请完成多元回归分析代码")'),

                # ===== 图论与网络模型（1题）=====
                Experiment(subject='图论与网络', title='最短路径——城市地铁换乘优化',
                    description='某城市地铁网络共有12个站点和17条线路连接。请：(1)建立地铁网络的图论模型；(2)使用Dijkstra算法计算任意两站间的最短路径；(3)考虑换乘时间惩罚（每次换乘+3分钟）；(4)设计最优出行路线推荐系统。',
                    reference_points='["Dijkstra算法","最短路径","邻接矩阵","图论","网络优化"]', difficulty=3,
                    template_code='import numpy as np\nimport heapq\n\n# 地铁站名称\nstations = [\'A\', \'B\', \'C\', \'D\', \'E\', \'F\', \'G\', \'H\', \'I\', \'J\', \'K\', \'L\']\nn = len(stations)\n\n# 邻接矩阵（INF表示不连通）\nINF = float(\'inf\')\n# 路段行驶时间（分钟）\nedges = [\n    (0, 1, 5), (0, 2, 8), (1, 2, 3), (1, 3, 7), (1, 4, 6),\n    (2, 4, 4), (2, 5, 9), (3, 4, 2), (3, 6, 5), (4, 5, 3),\n    (4, 6, 6), (4, 7, 4), (5, 7, 7), (6, 7, 3), (6, 8, 8),\n    (7, 8, 5), (7, 9, 6), (8, 9, 4), (8, 10, 7), (9, 10, 3),\n    (9, 11, 5), (10, 11, 4)\n]\n\n# 构建邻接矩阵\nadj = np.full((n, n), INF)\nfor u, v, w in edges:\n    adj[u][v] = adj[v][u] = w\n\n# TODO: 实现Dijkstra算法\ndef dijkstra(adj, start):\n    n = len(adj)\n    dist = [INF] * n\n    dist[start] = 0\n    visited = [False] * n\n    prev = [-1] * n  # 记录路径\n    \n    # 在此完成Dijkstra算法核心代码\n    \n    return dist, prev\n\n# TODO: 实现路径回溯函数\ndef get_path(prev, end):\n    path = []\n    # 回溯得到最短路径\n    return path\n\n# TODO: 考虑换乘惩罚的改进算法\n# 输入起点和终点，输出最优路线和预计用时\nprint("请完成地铁换乘优化代码")'),

                # ===== 随机模型（1题）=====
                Experiment(subject='随机模型', title='蒙特卡洛模拟——金融期权定价',
                    description='使用蒙特卡洛方法模拟股票价格路径，对欧式看涨期权进行定价。设当前股价S₀=100，波动率σ=0.2，无风险利率r=0.05，到期时间T=1年，执行价K=105。请：(1)模拟10000条股价路径；(2)计算期权价格；(3)分析模拟次数对定价精度的影响；(4)与Black-Scholes公式解对比。',
                    reference_points='["蒙特卡洛模拟","几何布朗运动","期权定价","Black-Scholes","收敛性分析"]', difficulty=4,
                    template_code='import numpy as np\nimport matplotlib.pyplot as plt\nfrom scipy.stats import norm\n\n# 参数设置\nS0 = 100      # 当前股价\nK = 105       # 执行价\nsigma = 0.2   # 波动率\nr = 0.05      # 无风险利率\nT = 1.0       # 到期时间（年）\nn_paths = 10000  # 模拟路径数\nn_steps = 252    # 时间步数（交易日）\n\n# TODO: 步骤1——使用几何布朗运动模拟股价路径\n# dS = r*S*dt + sigma*S*dW\n# S(t+dt) = S(t) * exp((r - sigma^2/2)*dt + sigma*sqrt(dt)*Z)\n\ndt = T / n_steps\n\n# 生成随机路径\nnp.random.seed(42)\nZ = np.random.standard_normal((n_paths, n_steps))\nS = np.zeros((n_paths, n_steps + 1))\nS[:, 0] = S0\n\n# TODO: 模拟价格路径\nfor t in range(1, n_steps + 1):\n    pass  # 在此完成价格路径模拟\n\n# TODO: 步骤2——计算期权 payoff = max(S_T - K, 0)\n# 贴现到现值：C = exp(-rT) * mean(payoff)\n\n# TODO: 步骤3——绘制模拟路径和分析收敛性\n\n# Black-Scholes公式参考值\ndef black_scholes_call(S, K, T, r, sigma):\n    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))\n    d2 = d1 - sigma*np.sqrt(T)\n    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)\n\nbs_price = black_scholes_call(S0, K, T, r, sigma)\nprint(f"Black-Scholes理论价格: {bs_price:.4f}")\nprint("请完成蒙特卡洛模拟定价代码")'),
            ]

            for exp in default_experiments:
                session.add(exp)
            await session.commit()
            print("✅ 默认实验题库数据已初始化")

    print("✅ 数据库初始化完成")


async def close_database():
    """关闭数据库连接"""
    await engine.dispose()
