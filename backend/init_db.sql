-- ============================================================
-- 数据库初始化 SQL 脚本
-- 应用场景：AI多智能体 × 数学建模智能教学平台
-- 数据库类型：SQLite（轻量无服务器，学生笔记本即可运行）
-- ============================================================

-- 用户表：支持学生、教师、管理员三级权限体系
-- 对应大赛评分点：完善的用户权限管理
CREATE TABLE IF NOT EXISTS "user" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,        -- 登录账号
    password_hash VARCHAR(256) NOT NULL,          -- 密码哈希（SHA256）
    role VARCHAR(20) NOT NULL DEFAULT 'student',  -- 角色：student/teacher/admin
    class_name VARCHAR(100) DEFAULT '',           -- 班级
    display_name VARCHAR(100) DEFAULT '',         -- 显示昵称
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户自定义LLM API配置表（大赛核心创新功能）
-- 每个用户独立配置自有大模型API，服务端不内置任何密钥
-- 对应大赛评分点：可自定义大模型API配置、密钥账户隔离存储
CREATE TABLE IF NOT EXISTS llm_user_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 所属用户ID
    config_name VARCHAR(100) NOT NULL DEFAULT '默认配置', -- 配置名称（支持多套）
    provider VARCHAR(50) NOT NULL,               -- 厂商：openai/deepseek/qwen/ernie-bot等
    api_key TEXT NOT NULL,                       -- API密钥（加密存储）
    base_url VARCHAR(500) NOT NULL DEFAULT '',    -- API地址
    model_name VARCHAR(100) NOT NULL DEFAULT '',  -- 模型名称
    temperature REAL DEFAULT 0.7,                -- 温度参数
    max_tokens INTEGER DEFAULT 4096,             -- 最大上下文长度
    is_active INTEGER DEFAULT 1,                 -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- 数学建模实验题库表
-- 对应大赛评分点：优化模型/预测模型/评价模型/微分方程/统计模型/图论/随机/聚类分类题库
CREATE TABLE IF NOT EXISTS experiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject VARCHAR(50) NOT NULL,                -- 模型分类：优化模型/预测模型/评价模型/分类与聚类/微分方程/统计模型/图论与网络/随机模型
    title VARCHAR(200) NOT NULL,                 -- 实验题目
    description TEXT NOT NULL,                   -- 实验要求描述
    reference_points TEXT,                       -- 参考知识点（JSON数组）
    difficulty INTEGER DEFAULT 1,                -- 难度等级 1-5
    template_code TEXT DEFAULT '',               -- 代码模板
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实训记录表：记录学生每次提交的代码与评测结果
-- 对应大赛评分点：实训过程记录、数据持久化
CREATE TABLE IF NOT EXISTS practice_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 学生用户ID
    experiment_id INTEGER NOT NULL,              -- 关联实验题目
    submitted_code TEXT NOT NULL,                -- 学生提交的代码
    language VARCHAR(20) DEFAULT 'python',       -- 编程语言
    score REAL DEFAULT 0,                        -- AI评分数值（0-100）
    feedback TEXT DEFAULT '',                     -- AI评测反馈
    status VARCHAR(20) DEFAULT 'submitted',      -- 状态：submitted/evaluated
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id) REFERENCES experiment(id) ON DELETE CASCADE
);

-- 智能体对话记录表
-- 对应大赛评分点：多智能体对话上下文管理、多轮对话记忆
CREATE TABLE IF NOT EXISTS agent_chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 用户ID
    agent_type VARCHAR(50) NOT NULL,             -- 智能体类型：code-review/training-guide/qa
    session_id VARCHAR(100) NOT NULL,            -- 会话ID（分组多轮对话）
    llm_config_id INTEGER DEFAULT NULL,          -- 使用的API配置ID
    user_message TEXT NOT NULL,                   -- 用户消息
    agent_message TEXT NOT NULL,                  -- 智能体回复
    metadata TEXT DEFAULT '{}',                   -- 附加元数据（JSON）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (llm_config_id) REFERENCES llm_user_config(id) ON DELETE SET NULL
);

-- 创建索引提升查询性能
CREATE INDEX IF NOT EXISTS idx_llm_config_user ON llm_user_config(user_id);
CREATE INDEX IF NOT EXISTS idx_experiment_subject ON experiment(subject);
CREATE INDEX IF NOT EXISTS idx_practice_record_user ON practice_record(user_id);
CREATE INDEX IF NOT EXISTS idx_practice_record_experiment ON practice_record(experiment_id);
CREATE INDEX IF NOT EXISTS idx_agent_chat_user ON agent_chat(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_chat_session ON agent_chat(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_chat_agent ON agent_chat(agent_type);

-- ============================================================
-- 初始化默认数学建模实验题库数据
-- ============================================================

-- 优化模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('优化模型', '线性规划——生产计划优化', '某工厂生产A、B两种产品，每件A产品利润300元，消耗原料甲2kg、乙3kg；每件B产品利润400元，消耗原料甲4kg、乙2kg。每天原料甲可用120kg、乙可用100kg。请建立线性规划模型，确定最优生产方案使利润最大化，并用Python求解。', '["线性规划","目标函数","约束条件","单纯形法","灵敏度分析"]', 2, 'import numpy as np\nfrom scipy.optimize import linprog\n\n# 目标函数系数（求最大化，linprog默认最小化，取负）\nc = [-300, -400]  # 每件A利润300，B利润400\n\n# 约束条件矩阵\nA = [[2, 4],   # 原料甲：2x1 + 4x2 <= 120\n     [3, 2]]   # 原料乙：3x1 + 2x2 <= 100\nb = [120, 100]\n\n# 变量边界 x1>=0, x2>=0\nbounds = [(0, None), (0, None)]\n\n# 求解线性规划\nresult = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method=''highs'')\n\nif result.success:\n    x1, x2 = result.x\n    print(f"最优方案：生产A产品{x1:.1f}件，B产品{x2:.1f}件")\n    print(f"最大利润：{-result.fun:.1f}元")\nelse:\n    print("求解失败:", result.message)'),
('优化模型', '整数规划——投资组合选择', '某投资者有资金100万元，现有5个项目可选。每个项目有固定投资额和预期收益。目标是在不超过总资金的条件下，选择一组项目使总收益最大。请建立0-1整数规划的数学模型并求解。', '["整数规划","0-1规划","分支定界法","背包问题"]', 3, 'import numpy as np\n\n# 5个项目的投资额（万元）和预期收益（万元）\ncosts = [25, 30, 40, 35, 20]\nprofits = [50, 65, 80, 70, 35]\ntotal_budget = 100  # 总资金\n\n# 请使用 pulp 或 ortools 求解0-1整数规划\n# 定义决策变量 x[i] ∈ {0,1}，表示是否选择第i个项目\n# 约束条件：sum(costs[i] * x[i]) <= total_budget\n# 目标函数：max sum(profits[i] * x[i])\n\nprint("请完成整数规划求解代码")'),
('优化模型', '多目标优化——车辆路径规划', '某物流公司需要为3辆卡车规划配送路线，服务10个客户点。目标：(1)最小化总行驶距离；(2)最小化车辆使用数；(3)平衡各车辆的工作量。请将多目标问题转化为单目标（如加权法），设计数学模型并求解。', '["多目标优化","Pareto最优","加权法","VRP问题","网络流"]', 5, 'import numpy as np\nimport matplotlib.pyplot as plt\n\n# 10个客户点坐标\nnp.random.seed(42)\ncustomers = np.random.rand(10, 2) * 100\ndepot = np.array([50, 50])\n\n# 可视化客户点分布\nplt.figure(figsize=(8, 8))\nplt.scatter(depot[0], depot[1], c=''red'', s=200, marker=''s'', label=''仓库'')\nplt.scatter(customers[:, 0], customers[:, 1], c=''blue'', s=100, label=''客户'')\nplt.legend()\nplt.title(''客户点分布图'')\nplt.show()\n\n# TODO: 建立VRP数学模型并求解');

-- 预测模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('预测模型', '时间序列预测——城市月均气温', '利用过去60个月的气温数据，建立ARIMA时间序列预测模型，预测未来12个月的月均气温。要求：(1)数据平稳性检验；(2)确定ARIMA(p,d,q)参数；(3)模型检验与残差分析；(4)给出预测值和置信区间。', '["ARIMA","时间序列","平稳性检验","ACF/PACF","残差分析"]', 4, 'import numpy as np\nimport matplotlib.pyplot as plt\nfrom statsmodels.tsa.arima.model import ARIMA\n\n# 生成模拟气温数据（带季节性和趋势）\nnp.random.seed(42)\nt = np.arange(60)\ntrend = 15 + 0.02 * t\nseasonal = 10 * np.sin(2 * np.pi * t / 12)\nnoise = np.random.normal(0, 2, 60)\ntemperatures = trend + seasonal + noise\n\nplt.figure(figsize=(12, 5))\nplt.plot(t, temperatures, label=''历史气温'')\nplt.xlabel(''月份''); plt.ylabel(''气温(°C)'')\nplt.title(''月均气温时间序列'')\nplt.legend(); plt.show()\n\n# TODO: ADF平稳性检验 → 差分 → ACF/PACF → ARIMA建模 → 预测'),
('预测模型', '灰色预测——城市人口增长模型', '某城市过去10年人口数据（万人）。使用灰色预测GM(1,1)模型预测未来5年人口变化趋势，并分析模型精度（后验差检验）。', '["GM(1,1)","灰色预测","累加生成","后验差检验","小样本预测"]', 3, 'import numpy as np\n\n# 原始数据序列（10年人口，单位：万人）\nx0 = np.array([856, 873, 892, 913, 935, 958, 982, 1007, 1033, 1060])\n\n# TODO: 级比检验 → 一次累加生成(1-AGO) → 构造B/Y矩阵\n# TODO: 求解参数a,b → 建立GM(1,1)模型 → 预测未来5年 → 后验差检验\nprint("请完成GM(1,1)灰色预测代码")');

-- 评价模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('评价模型', '层次分析法(AHP)——高校综合评价', '使用层次分析法对4所高校进行综合排名。评价准则包括：教学质量、科研水平、师资力量、就业率、校园环境。请构建层次结构模型、构造判断矩阵、计算权重向量、进行一致性检验，最终给出综合排名。', '["AHP","判断矩阵","特征向量","一致性检验","CR值"]', 3, 'import numpy as np\n\ncriteria = [''教学质量'', ''科研水平'', ''师资力量'', ''就业率'', ''校园环境'']\n\n# 准则层判断矩阵（5×5，Saaty 1-9标度法）\njudgment_matrix = np.array([\n    [1, 3, 2, 1/2, 5],\n    [1/3, 1, 1/2, 1/4, 2],\n    [1/2, 2, 1, 1/3, 3],\n    [2, 4, 3, 1, 6],\n    [1/5, 1/2, 1/3, 1/6, 1]\n])\n\n# TODO: 计算权重向量（特征向量法）\n# TODO: 一致性检验 CI=(λmax-n)/(n-1), CR=CI/RI\n# TODO: 方案层评价，计算各高校综合得分\nprint("请完成AHP评价模型代码")'),
('评价模型', 'TOPSIS法——供应商选择决策', '某制造企业需从6家供应商中选择最佳合作伙伴。评价指标包括：价格(成本型)、质量合格率(效益型)、交货准时率(效益型)、售后服务评分(效益型)、距离(成本型)。使用TOPSIS法进行综合评价和排序。', '["TOPSIS","理想解","负理想解","归一化","相对贴近度"]', 3, 'import numpy as np\n\n# 6个供应商 × 5个评价指标\n# 列：价格(元), 合格率(%), 准时率(%), 服务分, 距离(km)\ndata = np.array([\n    [120, 98, 95, 85, 50],\n    [100, 95, 90, 78, 80],\n    [135, 99, 88, 92, 30],\n    [110, 92, 98, 70, 60],\n    [125, 97, 93, 88, 45],\n    [105, 94, 85, 75, 70]\n])\n\n# 指标类型：1=效益型（越大越好），0=成本型（越小越好）\nindicator_type = [0, 1, 1, 1, 0]\n\n# TODO: 数据正向化 → 归一化 → 正负理想解 → 距离 → 相对贴近度 → 排序\nprint("6家供应商TOPSIS评价分析")');

-- 分类与聚类模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('分类与聚类', 'K-means聚类——客户群体细分', '某电商平台收集了200位客户的年消费金额和购物频次数据。使用K-means聚类算法将客户分为3-5个群体（如高价值、中等、低价值客户），分析各群体的特征，为企业制定差异化营销策略提供依据。', '["K-means","肘部法则","轮廓系数","客户细分","数据标准化"]', 2, 'import numpy as np\nimport matplotlib.pyplot as plt\nfrom sklearn.cluster import KMeans\nfrom sklearn.preprocessing import StandardScaler\n\n# 生成模拟客户数据\nnp.random.seed(42)\nc1 = np.random.multivariate_normal([15000, 25], [[3000, 5], [5, 15]], 40)\nc2 = np.random.multivariate_normal([8000, 12], [[2000, 3], [3, 8]], 80)\nc3 = np.random.multivariate_normal([3000, 5], [[1000, 2], [2, 5]], 80)\nX = np.vstack([c1, c2, c3])\n\n# 数据标准化\nscaler = StandardScaler()\nX_scaled = scaler.fit_transform(X)\n\n# TODO: 肘部法则确定k → 轮廓系数验证 → K-means聚类 → 可视化 → 群体特征分析\nplt.scatter(X[:, 0], X[:, 1], alpha=0.6)\nplt.xlabel(''年消费金额(元)''); plt.ylabel(''年购物频次(次)'')\nplt.title(''客户消费数据分布'')\nplt.show()');

-- 微分方程模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('微分方程', 'SIR传染病传播模型', '使用SIR仓室模型模拟传染病在人群中的传播。总人口N=10000，初始感染者I0=10。感染率β=0.3，恢复率γ=0.1。请：(1)建立SIR微分方程组；(2)用数值方法求解；(3)分析峰值时间和规模；(4)讨论防控措施效果。', '["SIR模型","常微分方程","龙格-库塔法","传染病动力学","R0基本再生数"]', 4, 'import numpy as np\nimport matplotlib.pyplot as plt\nfrom scipy.integrate import odeint\n\n# SIR模型参数\nN, I0, R0_init = 10000, 10, 0\nS0 = N - I0 - R0_init\nbeta, gamma = 0.3, 0.1\n\n# SIR微分方程组\ndef sir(y, t, N, beta, gamma):\n    S, I, R = y\n    dSdt = -beta * S * I / N\n    dIdt = beta * S * I / N - gamma * I\n    dRdt = gamma * I\n    return [dSdt, dIdt, dRdt]\n\n# TODO: 使用odeint求解 → 绘制S/I/R曲线 → 找峰值 → 参数敏感性分析\nt = np.linspace(0, 160, 1000)\nprint(f"基本再生数 R0 = {beta/gamma:.2f}")\nprint("请完成SIR模型求解代码")');

-- 统计模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('统计模型', '多元回归分析——房价影响因素', '收集了某城市100套住宅的房价及5个影响因素数据：面积、卧室数、房龄、距市中心距离、周边学校数量。请建立多元线性回归模型：(1)分析各因素相关性；(2)检验模型显著性；(3)诊断多重共线性(VIF)；(4)给出回归方程。', '["多元线性回归","显著性检验","VIF","残差诊断","R2决定系数"]', 3, 'import numpy as np\nimport pandas as pd\nfrom sklearn.linear_model import LinearRegression\n\nnp.random.seed(42)\narea = np.random.normal(100, 30, 100)\nbedrooms = np.random.randint(1, 5, 100)\nage = np.random.exponential(15, 100)\ndistance = np.random.gamma(5, 2, 100)\nschools = np.random.poisson(3, 100)\nprice = 50 + 0.8*area + 5*bedrooms - 0.3*age - 2*distance + 8*schools + np.random.normal(0, 15, 100)\n\ndf = pd.DataFrame({''面积'': area, ''卧室数'': bedrooms, ''房龄'': age,\n                   ''距市中心'': distance, ''学校数'': schools, ''房价'': price})\n\n# TODO: 相关性分析 → 多元回归 → t检验 → VIF诊断 → 残差分析\nprint(df.describe())\nprint("请完成多元回归分析代码")');

-- 图论与网络模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('图论与网络', '最短路径——城市地铁换乘优化', '某城市地铁网络共有12个站点和17条线路连接。请：(1)建立地铁网络的图论模型；(2)使用Dijkstra算法计算任意两站间的最短路径；(3)考虑换乘时间惩罚（每次换乘+3分钟）；(4)设计最优出行路线推荐系统。', '["Dijkstra算法","最短路径","邻接矩阵","图论","网络优化"]', 3, 'import numpy as np\nimport heapq\n\n# 12个站点\nstations = [''A'',''B'',''C'',''D'',''E'',''F'',''G'',''H'',''I'',''J'',''K'',''L'']\nINF = float(''inf'')\n\n# 路段行驶时间（分钟）\nedges = [(0,1,5),(0,2,8),(1,2,3),(1,3,7),(1,4,6),(2,4,4),(2,5,9),\n         (3,4,2),(3,6,5),(4,5,3),(4,6,6),(4,7,4),(5,7,7),(6,7,3),\n         (6,8,8),(7,8,5),(7,9,6),(8,9,4),(8,10,7),(9,10,3),(9,11,5),(10,11,4)]\n\n# 构建邻接矩阵\nadj = np.full((len(stations), len(stations)), INF)\nfor u, v, w in edges:\n    adj[u][v] = adj[v][u] = w\n\n# TODO: 实现Dijkstra算法 → 路径回溯 → 考虑换乘惩罚 → 路线推荐\nprint("请完成地铁换乘优化代码")');

-- 随机模型实验
INSERT INTO experiment (subject, title, description, reference_points, difficulty, template_code) VALUES
('随机模型', '蒙特卡洛模拟——金融期权定价', '使用蒙特卡洛方法模拟股票价格路径，对欧式看涨期权进行定价。当前股价S0=100，波动率σ=0.2，无风险利率r=0.05，到期时间T=1年，执行价K=105。请：(1)模拟10000条股价路径；(2)计算期权价格；(3)分析收敛性；(4)与Black-Scholes公式对比。', '["蒙特卡洛模拟","几何布朗运动","期权定价","Black-Scholes","收敛性分析"]', 4, 'import numpy as np\nimport matplotlib.pyplot as plt\nfrom scipy.stats import norm\n\n# 参数\nS0, K, sigma, r, T = 100, 105, 0.2, 0.05, 1.0\nn_paths, n_steps = 10000, 252\ndt = T / n_steps\n\n# Black-Scholes参考值\ndef bs_call(S, K, T, r, sigma):\n    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))\n    d2 = d1 - sigma*np.sqrt(T)\n    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)\n\nprint(f"BS理论价格: {bs_call(S0, K, T, r, sigma):.4f}")\n\nnp.random.seed(42)\n# TODO: 几何布朗运动模拟 → 计算payoff → 贴现 → 收敛性分析\nprint("请完成蒙特卡洛模拟定价代码")');
