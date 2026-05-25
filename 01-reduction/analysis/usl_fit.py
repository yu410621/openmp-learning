"""
USL (Universal Scalability Law) fitting for OpenMP reduction benchmark.

模型：
    Speedup(n) = n / [1 + α(n-1) + β·n(n-1)]

    α (contention)  : 多线程争用资源的系数（线性影响）
    β (coherency)   : 线程间一致性维护的系数（n^2 影响，导致反向退化）

数据来源：
    在 i9-14900k 上对 1 亿元素数组求正数之和，
    扫描 OMP_NUM_THREADS = 1, 2, 4, 8, 16, 24, 32, 48。
    详见 ../data/thread-scan-results.txt 和 ../README.md。

参考文献：
    Neil J. Gunther, "Guerrilla Capacity Planning: A Tactical Approach to
    Planning for Highly Scalable Applications and Services", 2007.
"""

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


def usl(n, alpha, beta):
    """Universal Scalability Law: speedup as a function of thread count."""
    return n / (1.0 + alpha * (n - 1) + beta * n * (n - 1))


def fit_and_report():
    # 实测数据（三轮中位数）
    threads = np.array([1, 2, 4, 8, 16, 24, 32, 48])
    speedup = np.array([1.16, 1.95, 3.29, 4.17, 7.20, 9.47, 9.99, 5.75])

    # 非线性拟合
    popt, pcov = curve_fit(usl, threads, speedup, p0=[0.05, 0.001])
    alpha, beta = popt
    alpha_err, beta_err = np.sqrt(np.diag(pcov))

    # 理论峰值线程数：dS/dn = 0 解出 n* = sqrt((1-α)/β)
    n_peak = int(np.sqrt((1.0 - alpha) / beta))
    s_peak = usl(n_peak, alpha, beta)

    print("=" * 60)
    print("USL Fit Results")
    print("=" * 60)
    print(f"  α (contention) = {alpha:.5f} ± {alpha_err:.5f}")
    print(f"  β (coherency)  = {beta:.5f} ± {beta_err:.5f}")
    print(f"  理论峰值线程数 = {n_peak}")
    print(f"  理论峰值加速比 = {s_peak:.2f}x")
    print(f"  实测峰值线程数 = 32 (speedup=9.99x)")
    print("=" * 60)

    # 拟合质量评估
    predicted = usl(threads, alpha, beta)
    residuals = speedup - predicted
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((speedup - np.mean(speedup)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot)
    print(f"  R² = {r_squared:.4f}  (越接近 1 拟合越好)")
    print("=" * 60)

    return threads, speedup, alpha, beta


def plot_curve(threads, speedup, alpha, beta, output="usl_curve.png"):
    n_smooth = np.linspace(1, 64, 200)
    s_smooth = usl(n_smooth, alpha, beta)
    s_linear = n_smooth  # 理想线性

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(n_smooth, s_linear, '--', color='gray',
            label='Linear (ideal)', linewidth=1)
    ax.plot(n_smooth, s_smooth, '-', color='#185FA5',
            label=f'USL fit (α={alpha:.4f}, β={beta:.4f})', linewidth=2)
    ax.scatter(threads, speedup, color='#993556', s=80, zorder=5,
               label='Measured (median of 3 runs)')

    ax.set_xlabel('Threads (OMP_NUM_THREADS)', fontsize=12)
    ax.set_ylabel('Speedup (vs. serial)', fontsize=12)
    ax.set_title('OpenMP reduction scalability on i9-14900k\n'
                 'fitted with Universal Scalability Law',
                 fontsize=13)
    ax.set_xlim(0, 52)
    ax.set_ylim(0, 16)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=11)

    plt.tight_layout()
    plt.savefig(output, dpi=120)
    print(f"\n图已保存到 {output}")


if __name__ == "__main__":
    threads, speedup, alpha, beta = fit_and_report()
    plot_curve(threads, speedup, alpha, beta)