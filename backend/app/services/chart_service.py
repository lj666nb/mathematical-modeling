"""
============================================================
图表生成服务 — 数学建模竞赛 S3-S4 可视化
============================================================
基于 matplotlib + seaborn 生成论文级图表（PNG）
支持中文标签、多图表类型、自动排版
============================================================
"""
from __future__ import annotations

import io
import os
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# 配置 matplotlib 后端和中文字体
import matplotlib
matplotlib.use("Agg")  # 无 GUI 后端

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager

# ---- 中文字体配置 ----
# 尝试多个常见中文字体路径
_CHINESE_FONT_CANDIDATES = [
    "Noto Sans CJK SC",
    "Noto Sans SC",
    "WenQuanYi Micro Hei",
    "WenQuanYi Zen Hei",
    "SimHei",
    "Microsoft YaHei",
    "PingFang SC",
    "Heiti SC",
    "STHeiti",
    "AR PL UMing CN",
    "AR PL UKai CN",
    "DejaVu Sans",
]

_READY = False
_FONT_NAME = None

def _init_matplotlib():
    """初始化 matplotlib 中文支持"""
    global _READY, _FONT_NAME
    if _READY:
        return

    # 查找可用中文字体
    available = {f.name for f in font_manager.fontManager.ttflist}
    for candidate in _CHINESE_FONT_CANDIDATES:
        if candidate in available:
            _FONT_NAME = candidate
            break

    if _FONT_NAME:
        plt.rcParams["font.sans-serif"] = [_FONT_NAME, "DejaVu Sans"]
    else:
        # 回退：尝试使用 sans-serif
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]

    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
    plt.rcParams["figure.dpi"] = 200
    plt.rcParams["savefig.dpi"] = 200
    plt.rcParams["savefig.bbox"] = "tight"
    plt.rcParams["savefig.pad_inches"] = 0.2
    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.titlesize"] = 15
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["legend.fontsize"] = 9
    plt.rcParams["xtick.labelsize"] = 9
    plt.rcParams["ytick.labelsize"] = 9

    # Seaborn 样式
    try:
        import seaborn as sns
        sns.set_style("whitegrid")
        sns.set_palette("Set2")
    except ImportError:
        pass

    _READY = True


# ---- 颜色方案 ----
COLOR_PALETTE = ["#2c6fce", "#d9782b", "#4a9b3f", "#c44e52", "#8b5ea8", "#55a5b5"]
GOLD = "#c8960c"
DARK_BG = "#1a1a2e"

# ---- 工具函数 ----

def _safe_read_data(file_path: str | Path, nrows: int | None = None) -> pd.DataFrame | None:
    """安全读取数据文件（CSV/XLSX/XLS），列名统一转为字符串"""
    path = Path(file_path)
    if not path.exists():
        return None
    try:
        suffix = path.suffix.lower()
        df = None
        if suffix == ".csv":
            for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
                try:
                    df = pd.read_csv(path, encoding=enc, nrows=nrows)
                    break
                except Exception:
                    continue
        elif suffix in (".xlsx", ".xls"):
            for engine in ("openpyxl", "xlrd", None):
                try:
                    df = pd.read_excel(path, nrows=nrows, engine=engine)
                    break
                except Exception:
                    continue
        if df is not None and not df.empty:
            # 统一列名为字符串
            df.columns = [str(c).strip() for c in df.columns]
            return df
    except Exception:
        pass
    return None


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    """识别数值列"""
    nums = []
    for col in df.columns:
        try:
            s = pd.to_numeric(df[col], errors="coerce")
            if s.notna().sum() >= max(2, len(df) * 0.5):
                nums.append(str(col))
        except Exception:
            pass
    return nums


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    """识别分类列"""
    nums = set(_numeric_columns(df))
    return [str(c) for c in df.columns if str(c) not in nums]


# ============================================================
# 图表生成函数
# ============================================================

def generate_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    output_path: str | Path = "chart.png",
    figsize: tuple = (12, 7),
) -> str | None:
    """折线图 — 适用于时间序列、趋势"""
    _init_matplotlib()

    if x_col not in data.columns:
        return None

    valid_y = [c for c in y_cols if c in data.columns and c in _numeric_columns(data)]
    if not valid_y:
        return None

    fig, ax = plt.subplots(figsize=figsize)
    for i, yc in enumerate(valid_y):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        ax.plot(data[x_col], pd.to_numeric(data[yc], errors="coerce"),
                marker="o", markersize=4, linewidth=1.8, color=color, label=yc, alpha=0.85)

    ax.set_title(title or f"{' & '.join(valid_y)} 趋势图", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel or x_col, fontsize=11)
    ax.set_ylabel(ylabel or "数值", fontsize=11)
    ax.legend(loc="best", frameon=True, fontsize=9)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_bar_chart(
    data: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    output_path: str | Path = "chart.png",
    horizontal: bool = False,
    figsize: tuple = (10, 5),
) -> str | None:
    """柱状图 — 适用于对比、排名"""
    _init_matplotlib()

    if x_col not in data.columns:
        return None

    valid_y = [c for c in y_cols if c in data.columns and c in _numeric_columns(data)]
    if not valid_y:
        return None

    # 自动调整图形大小
    if len(data) > 10:
        figsize = (max(figsize[0], len(data) * 0.5), figsize[1])

    fig, ax = plt.subplots(figsize=figsize)
    x = range(len(data))
    width = 0.8 / max(len(valid_y), 1)

    for i, yc in enumerate(valid_y):
        vals = pd.to_numeric(data[yc], errors="coerce").fillna(0)
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        if horizontal:
            ax.barh([v + i * width for v in x], vals, width, label=yc, color=color, alpha=0.85)
        else:
            ax.bar([v + i * width for v in x], vals, width, label=yc, color=color, alpha=0.85)

    if horizontal:
        ax.set_yticks([v + width * (len(valid_y) - 1) / 2 for v in x])
        ax.set_yticklabels(data[x_col].astype(str), fontsize=8)
    else:
        ax.set_xticks([v + width * (len(valid_y) - 1) / 2 for v in x])
        ax.set_xticklabels(data[x_col].astype(str), fontsize=8, rotation=30, ha="right")

    ax.set_title(title or f"{' & '.join(valid_y)} 对比图", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel or (x_col if not horizontal else "数值"), fontsize=11)
    ax.set_ylabel(ylabel or ("数值" if not horizontal else x_col), fontsize=11)
    if valid_y:
        ax.legend(loc="best", frameon=True, fontsize=9)
    ax.grid(True, alpha=0.3, axis="y" if not horizontal else "x")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    output_path: str | Path = "chart.png",
    color_by: str = "",
    figsize: tuple = (12, 8),
) -> str | None:
    """散点图 — 适用于相关性分析、聚类可视化"""
    _init_matplotlib()

    if x_col not in data.columns or y_col not in data.columns:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    x_vals = pd.to_numeric(data[x_col], errors="coerce")
    y_vals = pd.to_numeric(data[y_col], errors="coerce")
    mask = x_vals.notna() & y_vals.notna()

    if color_by and color_by in data.columns:
        categories = data[color_by].astype(str)
        for i, cat in enumerate(categories.unique()):
            idx = (categories == cat) & mask
            ax.scatter(x_vals[idx], y_vals[idx], label=cat, alpha=0.7, s=40,
                       color=COLOR_PALETTE[i % len(COLOR_PALETTE)])
        ax.legend(loc="best", fontsize=8)
    else:
        ax.scatter(x_vals[mask], y_vals[mask], alpha=0.7, s=40, color=COLOR_PALETTE[0])

    # 趋势线
    if mask.sum() >= 2:
        try:
            from numpy.polynomial.polynomial import polyfit
            coef = polyfit(x_vals[mask].to_numpy(dtype=float), y_vals[mask].to_numpy(dtype=float), 1)
            x_line = np.linspace(x_vals[mask].min(), x_vals[mask].max(), 100)
            ax.plot(x_line, coef[0] + coef[1] * x_line, "--", color=GOLD, linewidth=1.2, alpha=0.7, label="趋势线")
        except Exception:
            pass

    ax.set_title(title or f"{y_col} vs {x_col}", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel or x_col, fontsize=11)
    ax.set_ylabel(ylabel or y_col, fontsize=11)
    ax.grid(True, alpha=0.3)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_correlation_heatmap(
    data: pd.DataFrame,
    title: str = "特征相关性热力图",
    output_path: str | Path = "chart.png",
    figsize: tuple = (12, 10),
) -> str | None:
    """热力图 — 适用于变量相关性分析"""
    _init_matplotlib()

    num_cols = _numeric_columns(data)
    if len(num_cols) < 2:
        return None

    corr = data[num_cols].corr()
    if corr.empty:
        return None

    fig, ax = plt.subplots(figsize=figsize)
    try:
        import seaborn as sns
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                    center=0, square=True, linewidths=0.5,
                    cbar_kws={"shrink": 0.8}, ax=ax,
                    vmin=-1, vmax=1)
    except ImportError:
        im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        plt.colorbar(im, ax=ax, shrink=0.8)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(corr.columns, fontsize=9)
        for i in range(len(corr.columns)):
            for j in range(len(corr.columns)):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_distribution_plot(
    data: pd.DataFrame,
    column: str,
    title: str = "",
    xlabel: str = "",
    output_path: str | Path = "chart.png",
    bins: int = 30,
    figsize: tuple = (14, 6),
) -> str | None:
    """分布图（直方图 + KDE）— 适用于数据分布分析"""
    _init_matplotlib()

    if column not in data.columns:
        return None

    vals = pd.to_numeric(data[column], errors="coerce").dropna()
    if len(vals) < 3:
        return None

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # 直方图 + KDE
    ax = axes[0]
    ax.hist(vals, bins=min(bins, len(vals) // 2), color=COLOR_PALETTE[0], alpha=0.7, edgecolor="white", density=True)
    try:
        import seaborn as sns
        sns.kdeplot(vals, ax=ax, color=COLOR_PALETTE[1], linewidth=2)
    except ImportError:
        pass
    ax.axvline(vals.mean(), color=GOLD, linestyle="--", linewidth=1.5, label=f"均值={vals.mean():.3f}")
    ax.axvline(vals.median(), color=COLOR_PALETTE[2], linestyle=":", linewidth=1.5, label=f"中位数={vals.median():.3f}")
    ax.set_title(f"{column} 分布", fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel or column, fontsize=10)
    ax.set_ylabel("密度", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 箱线图
    ax2 = axes[1]
    bp = ax2.boxplot(vals, vert=True, patch_artist=True, widths=0.4)
    bp["boxes"][0].set_facecolor(COLOR_PALETTE[0])
    bp["boxes"][0].set_alpha(0.7)
    ax2.set_title(f"{column} 箱线图", fontsize=12, fontweight="bold")
    ax2.set_ylabel(xlabel or column, fontsize=10)
    ax2.set_xticklabels([column], fontsize=10)
    ax2.grid(True, alpha=0.3, axis="y")

    fig.suptitle(title or f"{column} 分布分析", fontsize=14, fontweight="bold")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_multi_distribution(
    data: pd.DataFrame,
    columns: list[str],
    title: str = "多变量分布对比",
    output_path: str | Path = "chart.png",
    figsize: tuple = (14, 10),
) -> str | None:
    """多变量分布子图 — 一目了然看所有数值变量分布"""
    _init_matplotlib()

    valid_cols = [c for c in columns if c in data.columns and c in _numeric_columns(data)]
    if not valid_cols:
        return None

    n = len(valid_cols)
    cols_layout = min(3, n)
    rows = (n + cols_layout - 1) // cols_layout

    fig, axes = plt.subplots(rows, cols_layout, figsize=figsize)
    if rows == 1 and cols_layout == 1:
        axes = np.array([[axes]])
    elif rows == 1:
        axes = axes.reshape(1, -1)
    elif cols_layout == 1:
        axes = axes.reshape(-1, 1)

    for idx, col in enumerate(valid_cols):
        r, c = idx // cols_layout, idx % cols_layout
        ax = axes[r, c]
        vals = pd.to_numeric(data[col], errors="coerce").dropna()
        ax.hist(vals, bins=min(25, len(vals) // 2), color=COLOR_PALETTE[idx % len(COLOR_PALETTE)],
                alpha=0.75, edgecolor="white")
        ax.axvline(vals.mean(), color=GOLD, linestyle="--", linewidth=1.2)
        ax.set_title(col, fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.3)

    # 隐藏多余子图
    for idx in range(n, rows * cols_layout):
        r, c = idx // cols_layout, idx % cols_layout
        axes[r, c].set_visible(False)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_pie_chart(
    data: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str = "",
    output_path: str | Path = "chart.png",
    figsize: tuple = (8, 8),
) -> str | None:
    """饼图 — 适用于比例展示"""
    _init_matplotlib()

    if label_col not in data.columns or value_col not in data.columns:
        return None

    labels = data[label_col].astype(str).tolist()
    values = pd.to_numeric(data[value_col], errors="coerce").fillna(0).tolist()
    total = sum(values)
    if total <= 0:
        return None

    fig, ax = plt.subplots(figsize=figsize)
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct="%1.1f%%",
        colors=COLOR_PALETTE[:len(labels)],
        startangle=90, pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(10)

    ax.set_title(title or f"{value_col} 构成", fontsize=14, fontweight="bold", pad=15)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


# ============================================================
# 论文综合图表生成
# ============================================================

def generate_data_overview_dashboard(
    df: pd.DataFrame,
    output_dir: str | Path,
    prefix: str = "overview",
) -> list[str]:
    """生成数据概览仪表盘（多张图）"""
    _init_matplotlib()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []

    num_cols = _numeric_columns(df)
    cat_cols = _categorical_columns(df)

    # 1. 相关性热力图
    if len(num_cols) >= 2:
        p = generate_correlation_heatmap(df, output_path=output_dir / f"{prefix}_correlation_heatmap.png")
        if p:
            generated.append(p)

    # 2. 多变量分布
    if num_cols:
        p = generate_multi_distribution(df, num_cols[:9],
                                         output_path=output_dir / f"{prefix}_distributions.png")
        if p:
            generated.append(p)

    # 3. 缺失值热图
    if len(df.columns) >= 2:
        try:
            p = generate_missing_heatmap(df, output_path=output_dir / f"{prefix}_missing.png")
            if p:
                generated.append(p)
        except Exception:
            pass

    # 4. 数值变量描述统计
    if num_cols:
        stats = df[num_cols].describe()
        stats_path = output_dir / f"{prefix}_statistics.csv"
        stats.to_csv(stats_path, encoding="utf-8-sig")
        generated.append(str(stats_path))

    return generated


def generate_missing_heatmap(
    df: pd.DataFrame,
    output_path: str | Path = "chart.png",
    figsize: tuple = (10, 6),
) -> str | None:
    """缺失值热力图"""
    _init_matplotlib()

    missing = df.isnull()
    if not missing.any().any():
        return None  # 无缺失值，不生成

    fig, ax = plt.subplots(figsize=figsize)

    # 列级缺失率
    missing_pct = (missing.sum() / len(df) * 100).sort_values(ascending=False)
    missing_pct = missing_pct[missing_pct > 0]

    bars = ax.bar(range(len(missing_pct)), missing_pct.values, color=COLOR_PALETTE[0], alpha=0.8)
    ax.set_xticks(range(len(missing_pct)))
    ax.set_xticklabels(missing_pct.index, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("缺失率 (%)", fontsize=11)
    ax.set_title("数据缺失率分析", fontsize=14, fontweight="bold", pad=12)

    # 在柱上标值
    for bar, val in zip(bars, missing_pct.values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.grid(True, alpha=0.3, axis="y")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_prediction_comparison(
    true_values: list | np.ndarray,
    predicted_values: list | np.ndarray,
    title: str = "预测效果对比",
    output_path: str | Path = "chart.png",
    figsize: tuple = (12, 5),
) -> str | None:
    """预测对比图 — 真实值 vs 预测值 + 残差"""
    _init_matplotlib()

    true_vals = np.asarray(true_values, dtype=float)
    pred_vals = np.asarray(predicted_values, dtype=float)
    residual = true_vals - pred_vals

    if len(true_vals) < 2:
        return None

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # 左侧：真实 vs 预测
    ax = axes[0]
    ax.plot(true_vals, "o-", color=COLOR_PALETTE[0], markersize=5, linewidth=1.5, label="真实值", alpha=0.8)
    ax.plot(pred_vals, "s--", color=COLOR_PALETTE[1], markersize=5, linewidth=1.5, label="预测值", alpha=0.8)
    ax.set_title("真实值 vs 预测值", fontsize=12, fontweight="bold")
    ax.set_xlabel("样本序号", fontsize=10)
    ax.set_ylabel("值", fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 右侧：残差
    ax2 = axes[1]
    ax2.bar(range(len(residual)), residual, color=[COLOR_PALETTE[2] if r >= 0 else COLOR_PALETTE[3] for r in residual],
            alpha=0.7)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.axhline(np.mean(residual), color=GOLD, linestyle="--", linewidth=1.2, label=f"平均残差={np.mean(residual):.4f}")
    ax2.set_title("残差分布", fontsize=12, fontweight="bold")
    ax2.set_xlabel("样本序号", fontsize=10)
    ax2.set_ylabel("残差", fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=14, fontweight="bold")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_sensitivity_analysis(
    param_values: list,
    metric_values: list,
    param_name: str = "参数",
    metric_name: str = "指标",
    title: str = "敏感性分析",
    output_path: str | Path = "chart.png",
    figsize: tuple = (8, 5),
) -> str | None:
    """敏感性分析图"""
    _init_matplotlib()

    if len(param_values) < 2 or len(metric_values) < 2:
        return None

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(param_values, metric_values, "o-", color=COLOR_PALETTE[0],
            markersize=8, linewidth=2, markerfacecolor="white", markeredgewidth=2)
    ax.fill_between(param_values, metric_values,
                     np.array(metric_values) - np.std(metric_values) * 0.5,
                     np.array(metric_values) + np.std(metric_values) * 0.5,
                     alpha=0.2, color=COLOR_PALETTE[0])
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(param_name, fontsize=11)
    ax.set_ylabel(metric_name, fontsize=11)
    ax.grid(True, alpha=0.3)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_radar_chart(
    categories: list[str],
    values: list[float],
    title: str = "综合评价雷达图",
    output_path: str | Path = "chart.png",
    figsize: tuple = (8, 8),
) -> str | None:
    """雷达图 — 适用于多维度综合评价"""
    _init_matplotlib()

    n = len(categories)
    if n < 3:
        return None

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    values_plot = list(values) + [values[0]]
    angles_plot = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=figsize, subplot_kw={"projection": "polar"})
    ax.fill(angles_plot, values_plot, color=COLOR_PALETTE[0], alpha=0.25)
    ax.plot(angles_plot, values_plot, "o-", color=COLOR_PALETTE[0], linewidth=2, markersize=6)

    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.grid(True, alpha=0.3)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


# ============================================================
# 🆕 高级图表：拟合曲线、空间图、残差分析
# ============================================================

def generate_fitted_curve(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    output_path: str | Path = "chart.png",
    degree: int = 1,
    figsize: tuple = (10, 6),
) -> str | None:
    """
    拟合曲线图 — 散点 + 多项式/线性拟合线 + R² + 方程标注
    适用于数据规律发掘、趋势分析
    """
    _init_matplotlib()

    if x_col not in data.columns or y_col not in data.columns:
        return None

    x_vals = pd.to_numeric(data[x_col], errors="coerce")
    y_vals = pd.to_numeric(data[y_col], errors="coerce")
    mask = x_vals.notna() & y_vals.notna()

    if mask.sum() < 3:
        return None

    x = x_vals[mask].to_numpy(dtype=float)
    y = y_vals[mask].to_numpy(dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=figsize, gridspec_kw={"width_ratios": [3, 2]})

    # ---- 左图：散点 + 拟合线 ----
    ax = axes[0]
    ax.scatter(x, y, alpha=0.6, s=35, color=COLOR_PALETTE[0], edgecolors="white", linewidth=0.5, zorder=3)

    # 多项式拟合
    try:
        coeffs = np.polyfit(x, y, min(degree, len(x) - 1))
        poly = np.poly1d(coeffs)
        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = poly(x_line)
        ax.plot(x_line, y_line, "-", color=COLOR_PALETTE[1], linewidth=2.5, alpha=0.9, zorder=4, label="拟合曲线")

        # 计算 R²
        y_pred = poly(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # 标注方程
        eq_parts = []
        for i, c in enumerate(coeffs):
            p = len(coeffs) - 1 - i
            if abs(c) < 1e-10:
                continue
            if p == 0:
                eq_parts.append(f"{c:.4f}")
            elif p == 1:
                eq_parts.append(f"{c:.4f}x")
            else:
                eq_parts.append(f"{c:.4f}x^{p}")
        eq_str = " + ".join(eq_parts).replace("+ -", "- ")
        ax.text(0.05, 0.95, f"$y = {eq_str}$\n$R^2 = {r2:.4f}$",
                transform=ax.transAxes, fontsize=10, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85, edgecolor=COLOR_PALETTE[1]))
    except Exception:
        r2 = 0
        ax.plot(x, y, "-", color=COLOR_PALETTE[1], linewidth=1.5, alpha=0.5)

    ax.set_title(f"{y_col} vs {x_col} (拟合曲线)", fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel or x_col, fontsize=10)
    ax.set_ylabel(ylabel or y_col, fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)

    # ---- 右图：残差分析 ----
    ax2 = axes[1]
    try:
        residuals = y - y_pred
        ax2.scatter(x, residuals, alpha=0.6, s=25, color=COLOR_PALETTE[3], edgecolors="white", linewidth=0.3)
        ax2.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax2.axhline(np.mean(residuals), color=GOLD, linewidth=1.2, linestyle="-",
                    label=f"均值={np.mean(residuals):.4f}")
        ax2.fill_between([x.min(), x.max()],
                          -2 * np.std(residuals), 2 * np.std(residuals),
                          alpha=0.15, color=COLOR_PALETTE[4], label="±2σ")
        ax2.set_title("残差分布", fontsize=12, fontweight="bold")
        ax2.set_xlabel(xlabel or x_col, fontsize=10)
        ax2.set_ylabel("残差", fontsize=10)
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
    except Exception:
        ax2.text(0.5, 0.5, "无法计算残差", transform=ax2.transAxes, ha="center", va="center")

    fig.suptitle(title or f"{y_col} ~ {x_col} 拟合分析", fontsize=14, fontweight="bold")
    fig.tight_layout()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_spatial_route(
    coordinates: pd.DataFrame,
    x_col: str,
    y_col: str,
    label_col: str | None = None,
    route_edges: list[tuple[int, int]] | None = None,
    title: str = "",
    output_path: str | Path = "chart.png",
    figsize: tuple = (14, 12),
) -> str | None:
    """
    空间路径图 — 客户坐标散点 + 可选路径连线
    适用于 VRP 路径可视化、客户分布、配送网络
    """
    _init_matplotlib()

    if x_col not in coordinates.columns or y_col not in coordinates.columns:
        return None

    x = pd.to_numeric(coordinates[x_col], errors="coerce")
    y = pd.to_numeric(coordinates[y_col], errors="coerce")
    mask = x.notna() & y.notna()
    x_arr = x[mask].to_numpy(dtype=float)
    y_arr = y[mask].to_numpy(dtype=float)
    n = len(x_arr)

    if n < 2:
        return None

    # 计算坐标范围，合理设置图形比例
    x_range = x_arr.max() - x_arr.min() or 1
    y_range = y_arr.max() - y_arr.min() or 1
    aspect = x_range / y_range
    if aspect > 2:
        figsize = (max(figsize[0], 16), max(figsize[1], 6))
    elif aspect < 0.5:
        figsize = (max(figsize[0], 8), max(figsize[1], 14))
    else:
        figsize = (max(figsize[0], 12), max(figsize[1], 12))

    fig, ax = plt.subplots(figsize=figsize)

    # 路径连线（可选）
    if route_edges:
        for i, j in route_edges:
            if 0 <= i < n and 0 <= j < n:
                ax.plot([x_arr[i], x_arr[j]], [y_arr[i], y_arr[j]], "-",
                        color=COLOR_PALETTE[1], linewidth=0.6, alpha=0.35, zorder=1)

    # 按类型着色：配送中心 vs 普通客户
    has_types = label_col and label_col in coordinates.columns
    if has_types:
        labels = coordinates[label_col].astype(str)
        unique_labels = labels[mask].unique()
        color_map = {}
        for i, lab in enumerate(unique_labels):
            if "配送" in str(lab) or "中心" in str(lab) or "仓库" in str(lab):
                color_map[lab] = "#e74c3c"  # 红色配送中心
            else:
                color_map[lab] = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        for lab in unique_labels:
            idx = labels[mask] == lab
            is_depot = any(k in str(lab) for k in ("配送", "中心", "仓库"))
            ax.scatter(x_arr[idx], y_arr[idx], c=color_map[lab], label=str(lab),
                       s=120 if is_depot else 35, alpha=0.85,
                       edgecolors="white", linewidth=0.5,
                       zorder=3 if is_depot else 2,
                       marker="*" if is_depot else "o")
        ax.legend(loc="upper right", fontsize=9, title=label_col, framealpha=0.9)
    else:
        # 自动识别配送中心（第一个点通常是仓库）
        colors_arr = [COLOR_PALETTE[0]] * n
        if n > 0:
            colors_arr[0] = "#e74c3c"  # 仓库红色
        ax.scatter([x_arr[0]], [y_arr[0]], c="#e74c3c", s=200, marker="*",
                   edgecolors="darkred", linewidth=2, zorder=5, label="配送中心 (ID=0)")
        if n > 1:
            ax.scatter(x_arr[1:], y_arr[1:], c=COLOR_PALETTE[0], s=30, alpha=0.75,
                       edgecolors="white", linewidth=0.3, zorder=2, label=f"客户点 (n={n-1})")
        ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

    # 🆕 仅标注关键点（配送中心和前20个客户），避免标注过于密集
    if n > 0:
        # 配送中心大字标注
        ax.annotate("DC", (x_arr[0], y_arr[0]), textcoords="offset points",
                    xytext=(8, 8), fontsize=11, fontweight="bold", color="darkred",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        # 客户点：只标注前20个，且数量>50时只标注前10个
        max_label = 10 if n > 50 else (20 if n > 20 else n)
        for i in range(1, min(n, max_label + 1)):
            ax.annotate(str(i), (x_arr[i], y_arr[i]), textcoords="offset points",
                        xytext=(3, 3), fontsize=5, alpha=0.6)

    # 🆕 绘制绿色配送区域示意（如果标题包含"绿色配送区"）
    if any(k in (title or "") for k in ("绿色配送", "限行", "配送区")):
        # 估算配送区域：以配送中心为圆心绘制示意圆
        radius = x_range * 0.3
        circle = plt.Circle((x_arr[0], y_arr[0]), radius, fill=True,
                            color="green", alpha=0.08, zorder=0, label="绿色配送区")
        ax.add_patch(circle)
        ax.annotate("绿色配送区", (x_arr[0] + radius * 0.6, y_arr[0] + radius * 0.6),
                    fontsize=10, color="green", alpha=0.7,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7))

    ax.set_title(title or "空间分布与路径图", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2, linestyle="--")
    fig.tight_layout(pad=1.5)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return str(path)


def generate_comparison_spatial(
    coordinates: pd.DataFrame,
    x_col: str,
    y_col: str,
    label_col: str | None = None,
    title: str = "",
    output_path: str | Path = "chart.png",
    figsize: tuple = (18, 8),
) -> str | None:
    """
    对比空间图 — 左右双面板（如"调整前/调整后"、"有/无政策"）
    适用于路径调整前后对比、策略对比等需要并排展示的场景
    自动从数据中拆分两组（前半/后半 或 奇数/偶数行）来模拟对比
    """
    _init_matplotlib()

    if x_col not in coordinates.columns or y_col not in coordinates.columns:
        return None

    x_all = pd.to_numeric(coordinates[x_col], errors="coerce")
    y_all = pd.to_numeric(coordinates[y_col], errors="coerce")
    mask = x_all.notna() & y_all.notna()
    x_arr = x_all[mask].to_numpy(dtype=float)
    y_arr = y_all[mask].to_numpy(dtype=float)
    n = len(x_arr)

    if n < 4:
        return None

    # 智能拆分：如果有 label_col，按类型拆分；否则前半/后半
    has_split = label_col and label_col in coordinates.columns
    if has_split:
        labels = coordinates[label_col].astype(str)[mask]
        unique_labs = labels.unique()
        if len(unique_labs) >= 2:
            group_a = labels == unique_labs[0]
            group_b = labels == unique_labs[-1]
        else:
            mid = n // 2
            group_a = np.array([True] * mid + [False] * (n - mid))
            group_b = ~group_a
    else:
        mid = n // 2
        group_a = np.array([True] * mid + [False] * (n - mid))
        group_b = ~group_a

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, sharex=True, sharey=True)

    # 配色方案
    color_a = COLOR_PALETTE[0]  # 蓝色
    color_b = COLOR_PALETTE[1]  # 橙色
    color_depot = "#e74c3c"

    for ax, group, color_pt, panel_title in [
        (ax1, group_a, color_a, "调整前 / 基准方案"),
        (ax2, group_b, color_b, "调整后 / 对比方案"),
    ]:
        x_g = x_arr[group]
        y_g = y_arr[group]

        # 客户点
        if len(x_g) > 1:
            ax.scatter(x_g[1:], y_g[1:], c=color_pt, s=40, alpha=0.7,
                      edgecolors="white", linewidth=0.3, zorder=2, label=f"客户 (n={len(x_g)-1})")
        # 配送中心（始终显示，用于参考）
        if n > 0:
            ax.scatter([x_arr[0]], [y_arr[0]], c=color_depot, s=200, marker="*",
                      edgecolors="darkred", linewidth=2, zorder=5, label="配送中心")
            ax.annotate("DC", (x_arr[0], y_arr[0]), textcoords="offset points",
                       xytext=(8, 8), fontsize=11, fontweight="bold", color="darkred")

        # 连接线（模拟路径：按 X 或 Y 排序连接）
        if len(x_g) >= 2:
            sort_idx = np.argsort(x_g)
            ax.plot(x_g[sort_idx], y_g[sort_idx], "--", color=color_pt,
                   linewidth=0.8, alpha=0.4, zorder=1)

        ax.set_title(panel_title, fontsize=13, fontweight="bold", color=color_pt)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2, linestyle="--")
        ax.legend(loc="upper right", fontsize=8)

    # 分析标题中的关键词，提取对比维度
    t = (title or "")
    if "突发事件" in t or "调整" in t or "扰动" in t:
        fig.suptitle(title, fontsize=15, fontweight="bold", y=1.02)
        fig.text(0.5, 0.01, "注：左图为原始路径方案，右图为突发事件下调整后的路径方案",
                ha="center", fontsize=10, color="gray", fontstyle="italic")
    elif "有无" in t or "政策" in t or "对比" in t:
        fig.suptitle(title, fontsize=15, fontweight="bold", y=1.02)
        fig.text(0.5, 0.01, "注：左图为无政策约束方案，右图为有政策约束下的调整方案",
                ha="center", fontsize=10, color="gray", fontstyle="italic")
    else:
        fig.suptitle(title, fontsize=15, fontweight="bold", y=1.02)

    fig.tight_layout(pad=2.0)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return str(path)


def generate_box_plot(
    data: pd.DataFrame,
    columns: list[str],
    group_by: str | None = None,
    title: str = "",
    output_path: str | Path = "chart.png",
    figsize: tuple = (12, 6),
) -> str | None:
    """
    箱线图 — 多变量分布对比、异常值识别
    适用于数据探索、装载率分布、成本分布分析
    """
    _init_matplotlib()

    valid_cols = [c for c in columns if c in data.columns and c in _numeric_columns(data)]
    if not valid_cols:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    if group_by and group_by in data.columns:
        groups = data[group_by].astype(str).unique()
        positions = []
        labels = []
        all_data = []
        for gi, grp in enumerate(groups):
            grp_data = data[data[group_by].astype(str) == grp]
            for ci, col in enumerate(valid_cols):
                vals = pd.to_numeric(grp_data[col], errors="coerce").dropna()
                if len(vals) > 0:
                    all_data.append(vals.tolist())
                    positions.append(gi * (len(valid_cols) + 0.5) + ci)
                    labels.append(f"{grp}\n{col}")
        if all_data:
            bp = ax.boxplot(all_data, positions=positions, widths=0.6, patch_artist=True)
            for patch, i in zip(bp["boxes"], range(len(all_data))):
                patch.set_facecolor(COLOR_PALETTE[i % len(COLOR_PALETTE)])
                patch.set_alpha(0.7)
            ax.set_xticks(positions)
            ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
    else:
        plot_data = []
        for col in valid_cols:
            vals = pd.to_numeric(data[col], errors="coerce").dropna()
            if len(vals) > 0:
                plot_data.append(vals.tolist())
        if plot_data:
            bp = ax.boxplot(plot_data, labels=valid_cols, patch_artist=True)
            for patch, i in zip(bp["boxes"], range(len(plot_data))):
                patch.set_facecolor(COLOR_PALETTE[i % len(COLOR_PALETTE)])
                patch.set_alpha(0.7)

    ax.set_title(title or "数据分布箱线图", fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("数值", fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_time_series_decomposition(
    data: pd.DataFrame,
    time_col: str,
    value_cols: list[str],
    title: str = "",
    output_path: str | Path = "chart.png",
    figsize: tuple = (12, 10),
) -> str | None:
    """
    时间序列分解图 — 多指标随时间变化 + 双Y轴
    适用于碳排放、成本、GDP等多指标时间趋势对比
    """
    _init_matplotlib()

    if time_col not in data.columns:
        return None
    valid_y = [c for c in value_cols if c in data.columns and c in _numeric_columns(data)]
    if not valid_y:
        return None

    n_plots = len(valid_y)
    fig, axes = plt.subplots(n_plots, 1, figsize=figsize, sharex=True)
    if n_plots == 1:
        axes = [axes]

    x_vals = pd.to_numeric(data[time_col], errors="coerce")

    for idx, col in enumerate(valid_y):
        ax = axes[idx]
        y_vals = pd.to_numeric(data[col], errors="coerce")
        mask = x_vals.notna() & y_vals.notna()
        x = x_vals[mask].to_numpy(dtype=float)
        y = y_vals[mask].to_numpy(dtype=float)

        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        ax.plot(x, y, "o-", color=color, markersize=5, linewidth=2, alpha=0.85)
        ax.fill_between(x, y, alpha=0.1, color=color)

        # 标注趋势线
        if len(x) >= 2:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            ax.plot(x, p(x), "--", color=GOLD, linewidth=1.5, alpha=0.7, label=f"趋势 (斜率={z[0]:.4f})")

        ax.set_ylabel(col, fontsize=10, color=color)
        ax.tick_params(axis="y", labelcolor=color)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel(time_col, fontsize=10)
    fig.suptitle(title or "时间序列趋势分析", fontsize=14, fontweight="bold")
    fig.tight_layout()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def generate_route_comparison(
    scenarios: list[dict],
    title: str = "方案对比分析",
    output_path: str | Path = "chart.png",
    figsize: tuple = (14, 8),
) -> str | None:
    """
    多方案对比图 — 柱状图 + 折线 + 表格
    每个 dict: {"name": "方案名", "总成本": 98550, "碳排放": 1200, "车辆数": 6, ...}
    适用于有/无政策对比、策略效果展示
    """
    _init_matplotlib()

    if not scenarios or len(scenarios) < 1:
        return None

    # 收集公共指标
    all_keys = set()
    for s in scenarios:
        all_keys.update(k for k in s.keys() if k != "name" and isinstance(s[k], (int, float)))
    metrics = sorted(all_keys)

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(1, 2, width_ratios=[3, 1])

    # ---- 左侧：分组柱状图 ----
    ax = fig.add_subplot(gs[0])
    names = [s.get("name", f"方案{i}") for i, s in enumerate(scenarios)]
    x = np.arange(len(names))
    n_metrics = len(metrics)
    width = 0.7 / max(n_metrics, 1)

    for mi, metric in enumerate(metrics):
        vals = [s.get(metric, 0) for s in scenarios]
        ax.bar(x + mi * width, vals, width, label=metric, color=COLOR_PALETTE[mi % len(COLOR_PALETTE)], alpha=0.85)
        # 数值标注
        for xi, v in enumerate(vals):
            if abs(v) > 0:
                ax.text(xi + mi * width, v, f"{v:.1f}", ha="center", va="bottom", fontsize=7, rotation=90)

    ax.set_xticks(x + width * (n_metrics - 1) / 2)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_title("方案对比", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # ---- 右侧：变化率表格 ----
    ax2 = fig.add_subplot(gs[1])
    ax2.axis("off")
    if len(scenarios) >= 2:
        base = scenarios[0]
        table_data = [["指标", "变化率"]]
        for metric in metrics:
            base_val = base.get(metric, 0)
            comp_val = scenarios[-1].get(metric, 0)
            if base_val != 0:
                change = (comp_val - base_val) / abs(base_val) * 100
                table_data.append([metric, f"{change:+.1f}%"])
        tbl = ax2.table(cellText=table_data, loc="center", cellLoc="center")
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        ax2.set_title("相对变化", fontsize=12, fontweight="bold")

    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


# ============================================================
# 批量生成入口
# ============================================================

def generate_all_charts(
    data_paths: list[str | Path],
    output_dir: str | Path,
    visualization_plan: dict | None = None,
    question_id: str = "",
) -> dict[str, Any]:
    """
    根据可视化计划批量生成图表

    Returns:
        {"generated": [{"figure_id": str, "path": str, "type": str, "title": str}], "errors": [...]}
    """
    _init_matplotlib()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"generated": [], "errors": []}

    # 读取所有数据，优先选择有命名列的文件
    dfs: list[tuple[str, pd.DataFrame]] = []
    for dp in data_paths:
        df = _safe_read_data(dp)
        if df is not None and not df.empty and len(df.columns) >= 2:
            # 优先选列名不是纯数字的文件
            dfs.append((str(dp), df))

    if not dfs:
        result["errors"].append("没有可用的数据文件（需要至少2列）")
        return result

    # 按列名质量排序：有中文字段名的优先
    def _col_quality(item):
        _, df = item
        cn_cols = sum(1 for c in df.columns if any('一' <= ch <= '鿿' for ch in str(c)))
        return (cn_cols, len(df.columns))
    dfs.sort(key=_col_quality, reverse=True)

    # 使用最佳数据文件作为主数据
    main_name, main_df = dfs[0]

    # ---- 1. 数据概览仪表盘 ----
    try:
        overview_charts = generate_data_overview_dashboard(main_df, output_dir, prefix=f"{question_id}_overview")
        for p in overview_charts:
            if p.endswith(".png"):
                result["generated"].append({
                    "figure_id": Path(p).stem,
                    "path": p,
                    "type": "overview",
                    "title": "数据概览",
                })
    except Exception as e:
        result["errors"].append(f"数据概览生成失败: {e}")

    # ---- 2. 根据可视化计划生成特定图表 ----
    if visualization_plan:
        figures = visualization_plan.get("figures", [])
        for fig_spec in figures:
            try:
                fid = fig_spec.get("figure_id", f"fig_{len(result['generated'])+1}")
                chart_type = fig_spec.get("chart_type", "bar")
                title = fig_spec.get("title", "")
                x_col = fig_spec.get("candidate_x", "")
                y_cols = fig_spec.get("candidate_y", [])

                # 🔧 优先用计划中的 data_source 找对应文件，否则按列名匹配
                planned_source = fig_spec.get("data_source", "")
                match_df = None
                if planned_source:
                    # 用文件名匹配（处理 cleaned_output 路径如 paper_output/1/data_cleaned/test_cleaned.csv）
                    source_stem = Path(planned_source).stem.replace("_cleaned", "")
                    for fpath, df in dfs:
                        fstem = Path(fpath).stem.replace("_cleaned", "")
                        if fstem == source_stem or source_stem in fstem or fstem in source_stem:
                            match_df = df
                            break
                # 回退：检查列名匹配
                if match_df is None:
                    for _, df in dfs:
                        has_x = not x_col or x_col in df.columns
                        has_y = not y_cols or all(y in df.columns for y in y_cols)
                        if has_x and has_y:
                            match_df = df
                            break
                # 如果没找到完全匹配的，用 main_df
                if match_df is None:
                    match_df = main_df

                # 🔧 回退匹配：如果指定列在数据中不存在，根据标题关键词搜索合适列
                if x_col and x_col not in match_df.columns:
                    num_cols = _numeric_columns(match_df)
                    cat_cols = _categorical_columns(match_df)
                    t = (title or "").lower()
                    all_cols = [str(c) for c in match_df.columns]

                    # 按标题语义搜索合适的 X/Y 列
                    if any(k in t for k in ("成本", "费用", "价格", "构成", "占比", "比例", "cost", "price")):
                        fallback_y = [c for c in num_cols if any(k in c.lower() for k in ("成本", "费用", "价格", "cost", "金额", "收入"))]
                        x_col = cat_cols[0] if cat_cols else ""
                        y_cols = fallback_y[:2] if fallback_y else (num_cols[:2] if len(num_cols) >= 2 else [])
                    elif any(k in t for k in ("收敛", "迭代", "损失", "误差曲线")):
                        fallback_iter = [c for c in all_cols if any(k in c.lower() for k in ("iter", "epoch", "step", "迭代", "轮次", "序号", "index"))]
                        fallback_err = [c for c in num_cols if any(k in c.lower() for k in ("loss", "error", "损失", "误差", "rmse"))]
                        x_col = fallback_iter[0] if fallback_iter else (cat_cols[0] if cat_cols else "")
                        y_cols = fallback_err[:2] if fallback_err else (num_cols[:2] if num_cols else [])
                    elif any(k in t for k in ("对比", "比较", "方案", "vs")):
                        x_col = cat_cols[0] if cat_cols else (all_cols[0] if all_cols else "")
                        y_cols = num_cols[:3] if num_cols else []
                    elif any(k in t for k in ("碳", "排放", "限行", "绿色", "emission", "carbon", "环境")):
                        fallback = [c for c in num_cols if any(k in c.lower() for k in ("碳", "排放", "carbon", "能源", "energy", "油耗"))]
                        x_col = cat_cols[0] if cat_cols else ""
                        y_cols = fallback[:3] if fallback else (num_cols[:3] if num_cols else [])
                    elif any(k in t for k in ("箱线", "装载", "利用率", "boxplot", "load")):
                        fallback = [c for c in num_cols if any(k in c.lower() for k in ("装载", "load", "利用率", "容量", "重量", "体积"))]
                        x_col = cat_cols[0] if cat_cols else ""
                        y_cols = fallback[:3] if fallback else (num_cols[:3] if num_cols else [])
                    elif any(k in t for k in ("路径", "轨迹", "路线", "坐标", "route", "path")):
                        x_cand = [c for c in all_cols if any(k in c.lower() for k in ("x", "lon", "lng", "经度", "横"))]
                        y_cand = [c for c in all_cols if any(k in c.lower() for k in ("y", "lat", "纬度", "纵"))]
                        x_col = x_cand[0] if x_cand else (num_cols[0] if num_cols else "")
                        y_cols = y_cand[:2] if y_cand else (num_cols[1:3] if len(num_cols) >= 2 else [])
                    else:
                        x_col = cat_cols[0] if cat_cols else (all_cols[0] if all_cols else "")
                        y_cols = num_cols[:3] if num_cols else []

                output_path = output_dir / f"{fid}.png"
                gen_path = None
                t = (title or "").lower()

                # 🆕 空间/路径图 — 根据标题含义做差异化渲染
                if any(k in t for k in ("路径", "空间", "坐标", "轨迹", "route", "spatial", "map")):
                    if x_col in match_df.columns and y_cols:
                        # 突发事件/调整前后 → 双面板对比图
                        if any(k in t for k in ("突发事件", "调整前后", "前后对比", "扰动", "变更")):
                            gen_path = generate_comparison_spatial(
                                match_df, x_col, y_cols[0],
                                label_col=y_cols[1] if len(y_cols) > 1 else None,
                                title=title, output_path=output_path)
                        else:
                            gen_path = generate_spatial_route(
                                match_df, x_col, y_cols[0],
                                label_col=y_cols[1] if len(y_cols) > 1 else None,
                                title=title, output_path=output_path)
                # 对比/有无政策 → 双面板或方案对比
                elif any(k in t for k in ("有无", "政策对比", "策略对比")):
                    if x_col in match_df.columns and y_cols:
                        # 如果有坐标列，用对比空间图；否则用方案对比图
                        has_coords = any(any(k in c.lower() for k in ("x", "y", "坐标", "lon", "lat", "经度", "纬度")) for c in match_df.columns)
                        if has_coords:
                            gen_path = generate_comparison_spatial(
                                match_df, x_col, y_cols[0],
                                title=title, output_path=output_path)
                        else:
                            num_cols = _numeric_columns(match_df)
                            scenarios = []
                            for ri in range(min(len(match_df), 6)):
                                row_data = {"name": str(match_df.iloc[ri, 0])[:15] if len(match_df.columns) > 0 else f"组{ri+1}"}
                                for nc in num_cols[:4]:
                                    val = pd.to_numeric(match_df.iloc[ri][nc], errors="coerce")
                                    if not pd.isna(val):
                                        row_data[nc] = val
                                scenarios.append(row_data)
                            if len(scenarios) >= 2:
                                gen_path = generate_route_comparison(scenarios, title=title, output_path=output_path)
                # 拟合曲线
                elif any(k in t for k in ("拟合", "回归", "fitted", "regression")):
                    if x_col in match_df.columns and y_cols:
                        gen_path = generate_fitted_curve(
                            match_df, x_col, y_cols[0],
                            title=title, output_path=output_path)
                # 箱线图
                elif any(k in t for k in ("箱线", "boxplot", "box")):
                    valid_for_box = [c for c in (y_cols or _numeric_columns(match_df))
                                    if c in match_df.columns][:6]
                    if valid_for_box:
                        gen_path = generate_box_plot(match_df, valid_for_box, title=title, output_path=output_path)
                # 时间序列分解
                elif any(k in t for k in ("时间", "趋势分解", "time series", "多指标")):
                    if x_col in match_df.columns and y_cols:
                        gen_path = generate_time_series_decomposition(
                            match_df, x_col, y_cols,
                            title=title, output_path=output_path)
                # 方案对比
                elif any(k in t for k in ("方案对比", "策略对比", "有无", "对比柱状")):
                    num_cols = _numeric_columns(match_df)
                    # 用数据行作为"方案"
                    scenarios = []
                    for ri in range(min(len(match_df), 8)):
                        row_data = {"name": str(match_df.iloc[ri, 0]) if len(match_df.columns) > 0 else f"方案{ri+1}"}
                        for nc in num_cols[:5]:
                            val = pd.to_numeric(match_df.iloc[ri][nc], errors="coerce")
                            if not pd.isna(val):
                                row_data[nc] = val
                        scenarios.append(row_data)
                    if len(scenarios) >= 2:
                        gen_path = generate_route_comparison(scenarios, title=title, output_path=output_path)

                # ---- 回退到基础图表类型 ----
                if gen_path is None:
                    if chart_type in ("spatial",) and x_col in match_df.columns and y_cols:
                        gen_path = generate_spatial_route(
                            match_df, x_col, y_cols[0],
                            label_col=y_cols[1] if len(y_cols) > 1 else None,
                            title=title, output_path=output_path)
                    elif chart_type in ("comparison_spatial",) and x_col in match_df.columns and y_cols:
                        gen_path = generate_comparison_spatial(
                            match_df, x_col, y_cols[0],
                            label_col=y_cols[1] if len(y_cols) > 1 else None,
                            title=title, output_path=output_path)
                    elif chart_type in ("pie",) and x_col in match_df.columns and y_cols:
                        gen_path = generate_pie_chart(match_df, x_col, y_cols[0],
                                                       title=title, output_path=output_path)
                    elif chart_type in ("box",) and y_cols:
                        valid_for_box = [c for c in y_cols if c in match_df.columns][:6]
                        if valid_for_box:
                            gen_path = generate_box_plot(match_df, valid_for_box, title=title, output_path=output_path)
                    elif chart_type in ("line", "prediction_comparison", "sensitivity_curve") and x_col and x_col in match_df.columns:
                        gen_path = generate_line_chart(match_df, x_col, y_cols or [match_df.columns[-1]],
                                                        title=title, output_path=output_path)
                    elif chart_type in ("bar", "model_comparison", "weight_bar", "score_ranking") and x_col and x_col in match_df.columns:
                        gen_path = generate_bar_chart(match_df, x_col, y_cols or [match_df.columns[-1]],
                                                       title=title, output_path=output_path)
                    elif chart_type in ("scatter",) and x_col and x_col in match_df.columns:
                        # 🆕 散点图自动加拟合线
                        gen_path = generate_fitted_curve(match_df, x_col, y_cols[0] if y_cols else match_df.columns[-1],
                                                          title=title, output_path=output_path)
                    elif chart_type in ("heatmap",):
                        gen_path = generate_correlation_heatmap(match_df, title=title, output_path=output_path)
                    elif chart_type in ("residual_distribution",) and y_cols:
                        col = y_cols[0] if isinstance(y_cols, list) else y_cols
                        if col in match_df.columns:
                            gen_path = generate_distribution_plot(match_df, col, title=title, output_path=output_path)
                    else:
                        # 默认：用匹配到的数据文件的数值列
                        num_cols = _numeric_columns(match_df)
                        if num_cols:
                            if x_col and x_col in match_df.columns and y_cols:
                                gen_path = generate_fitted_curve(match_df, x_col, y_cols[0],
                                                                  title=title, output_path=output_path)
                            elif x_col and x_col in match_df.columns:
                                gen_path = generate_bar_chart(match_df, x_col, num_cols[:3],
                                                               title=title, output_path=output_path)
                            else:
                                gen_path = generate_multi_distribution(match_df, num_cols[:6],
                                                                        title=title, output_path=output_path)

                if gen_path:
                    result["generated"].append({
                        "figure_id": fid,
                        "path": gen_path,
                        "type": chart_type,
                        "title": title,
                    })
            except Exception as e:
                result["errors"].append(f"图表 {fig_spec.get('figure_id', '?')} 生成失败: {e}")

    # ---- 3. 如果没有计划，生成默认图表集 ----
    if not visualization_plan or not visualization_plan.get("figures"):
        num_cols = _numeric_columns(main_df)
        cat_cols = _categorical_columns(main_df)

        # 每个数值列生成分布图
        for col in num_cols[:6]:
            try:
                fid = f"fig_{question_id}_dist_{col}" if question_id else f"fig_dist_{col}"
                p = generate_distribution_plot(main_df, col, output_path=output_dir / f"{fid}.png",
                                                title=f"{col} 分布分析")
                if p:
                    result["generated"].append({
                        "figure_id": fid, "path": p, "type": "distribution", "title": f"{col} 分布分析",
                    })
            except Exception as e:
                result["errors"].append(f"{col} 分布图失败: {e}")

        # 如果有时间和数值列，生成趋势图
        time_cols = [c for c in cat_cols if any(k in str(c).lower() for k in ("year", "date", "time", "month", "年", "月", "日"))]
        if time_cols and num_cols:
            try:
                fid = f"fig_{question_id}_trend" if question_id else "fig_trend"
                p = generate_line_chart(main_df, time_cols[0], num_cols[:3],
                                         output_path=output_dir / f"{fid}.png",
                                         title="数据趋势分析")
                if p:
                    result["generated"].append({
                        "figure_id": fid, "path": p, "type": "line", "title": "数据趋势分析",
                    })
            except Exception as e:
                result["errors"].append(f"趋势图失败: {e}")

        # 如果有分类列，生成柱状图对比
        if cat_cols and num_cols:
            try:
                fid = f"fig_{question_id}_compare" if question_id else "fig_compare"
                p = generate_bar_chart(main_df.head(20), cat_cols[0], num_cols[:2],
                                        output_path=output_dir / f"{fid}.png",
                                        title="分类对比分析")
                if p:
                    result["generated"].append({
                        "figure_id": fid, "path": p, "type": "bar", "title": "分类对比分析",
                    })
            except Exception as e:
                result["errors"].append(f"对比图失败: {e}")

    return result
