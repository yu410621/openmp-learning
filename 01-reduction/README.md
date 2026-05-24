# 01. Reduction 子句

> **Day 1** — OpenMP 入门第一个真正能跑出数据的实验

## 一句话定义

`reduction` 让多线程各自维护一份私有的累加器副本，在并行区域结束时把所有副本合并 — 这样既消除了竞态条件，又避免了显式加锁的开销。

## 关键语法

```c
#pragma omp parallel for reduction(运算符:变量)
for (...) {
    变量 += ...;
}
```

支持的运算符：`+`、`-`、`*`、`&`、`|`、`^`、`&&`、`||`、`min`、`max`。

## 实验目标

1. 验证 `reduction` 子句能正确并行化累加循环
2. 测量 i9-14900k 上不同线程数的加速曲线
3. 找出内存带宽瓶颈的位置

## 实验设计

对长度为 1 亿（`N = 100000000`）的 `long` 数组求所有正数之和，对比：

- **Serial 版本**：单线程基准
- **Parallel 版本**：`#pragma omp parallel for reduction(+:sum)`

代码：[task1.c](./task1.c)

## 实验环境

| 项目 | 配置 |
|------|------|
| CPU | i9-14900k（8 P-core × 2HT + 16 E-core = 32 线程） |
| 内存 | 48GB DDR5 |
| 系统 | Ubuntu 24.04 |
| 编译器 | gcc 14 |
| 编译命令 | `gcc -O2 -Wall -Werror -fopenmp task1.c -o task1` |

## 实验结果

### 单次基准测试

```
Serial:    sum=85714284, time=0.110 s
Parallel:  sum=85714284, time=0.011 s
OK: results match, speedup = 9.99x
```

### 线程数扫描（三轮中位数）

| 线程数 | 加速比 | 备注 |
|--------|--------|------|
| 1 | 1.16x | OpenMP 框架轻微优化（vs 纯串行）|
| 2 | 1.95x | 接近线性加速 |
| 4 | 3.29x | 接近线性加速 |
| 8 | 4.17x | P-core 用满，开始放缓 |
| 16 | 7.20x | E-core 开始贡献 |
| 24 | 9.47x | 接近性能平台 |
| **32** | **9.99x** | **峰值** |
| 48 | 5.75x | 超出物理线程数，性能崩塌 |

详细原始数据：[data/thread-scan-results.txt](./data/thread-scan-results.txt)

## 三个核心观察

### 1. 加速比远低于线程数

32 个线程只换来 10x 加速。理论极限是 32x，实际只达到 31%。

**原因**：这个循环每次迭代只做"一次内存读 + 一次比较 + 一次加法"，工作量极轻，**瓶颈在内存带宽而非 CPU 算力**。多线程不能让 DDR5 内存条变得更快。

### 2. 16 线程后存在明显拐点

从 16 线程开始，再增加线程的边际收益急剧下降：

```
1 → 16   线程：加速比从 1.16 → 7.20（6.2x 提升）
16 → 32  线程：加速比从 7.20 → 9.99（仅 1.4x 提升）
```

这就是**内存带宽墙**的位置。CPU 算力还有富余，但内存子系统已经被打满。

### 3. 超过物理线程数会反向退化

48 线程比 32 线程**慢一倍**。

**原因**：
- 48 个线程争抢 32 个物理执行单元，操作系统不断切换上下文
- 多线程共享同一核时，L1/L2 cache 被反复刷新（cache 污染）
- 调度开销超过并行收益

**金科玉律**：`OMP_NUM_THREADS` 永远不要超过物理线程数（`nproc`）。

## 我撞过的坑

### 坑 #1：把 reduction 写成独立的 pragma 行

**错误写法**：

```c
#pragma omp parallel for
#pragma omp reduction(+:sum)      // ← 编译器忽略
for (long i = 0; i < N; i++) {
    sum += arr[i];
}
```

**现象**：结果错误，4 核机器上得到正确答案的 1/4（race condition 的典型指纹）。

**根因**：`reduction` 是 `parallel for` 的子句（clause），不是独立的指令（directive）。第二行 `#pragma` 编译器不识别，直接忽略。结果是 4 个线程裸奔 `sum`，发生 race condition。

**正确写法**：

```c
#pragma omp parallel for reduction(+:sum)
for (long i = 0; i < N; i++) {
    sum += arr[i];
}
```

**预防措施**：编译时加 `-Werror`，立刻报错而不是 warning：

```
task1.c:34: error: ignoring '#pragma omp reduction' [-Werror=unknown-pragmas]
```

### 坑 #2：speedup 显示永远是 1.00x

最初模板里的占位符代码：

```c
printf("speedup = %.2fx\n", (double)(t2-t1 == 0 ? 1 : 1));
```

三目运算符两个分支都是 `1`，永远输出 1.00x。修复后才看到真实加速。

**教训**：写 benchmark 一定要保存每段计时，最后用串行时间除以并行时间得到 speedup。

### 坑 #3：单次测量不可信

同一段代码连续跑 5 次，加速比在 8.10x ~ 9.81x 之间波动。

**原因**：
- 操作系统调度噪声
- CPU 频率动态调整（Turbo Boost）
- Cache 冷热状态不同
- 后台进程干扰

**工程做法**：至少跑 5 次取最小值或中位数。Parallel 时间太短（11ms）时相对误差大，应该把 N 加大让运行时间到 1 秒以上。

## 编译与运行

### 编译

```bash
gcc -O2 -Wall -Werror -fopenmp task1.c -o task1
```

参数说明：

- `-O2`：基础优化（benchmark 必加，否则测的是没优化的代码）
- `-Wall`：打开所有 warning
- `-Werror`：warning 升级为 error（OpenMP 救命选项）
- `-fopenmp`：启用 OpenMP 支持

### 运行

```bash
# 默认线程数（= nproc）
./task1

# 指定线程数
OMP_NUM_THREADS=8 ./task1

# 线程数扫描（验证加速曲线）
for n in 1 2 4 8 16 24 32 48; do
    echo "=== Threads = $n ==="
    OMP_NUM_THREADS=$n ./task1
done
```

## 验证 race condition 的可视化

去掉 `reduction(+:sum)` 让代码裸奔：

```c
#pragma omp parallel for         // ← 故意不加 reduction
for (long i = 0; i < N; i++) {
    if (arr[i] > 0) sum += arr[i];
}
```

连续跑 5 次，每次 sum 都是不同的随机数。**这就是 race condition 的真面目**。

## 还没搞懂的（留给后续）

- [ ] `reduction` 内部的合并是怎么实现的？树形归约 vs 顺序累加？
- [ ] 自定义 `reduction` 操作（user-defined reduction）的写法
- [ ] 用 `perf stat -e cache-misses,cache-references` 验证内存带宽假设
- [ ] 在 NUMA 多 socket 系统上 `reduction` 的性能特征
- [ ] `reduction` vs 手动写私有变量 + critical 合并，性能差异有多大

## 关联知识

- **下一个实验**：[02-critical-atomic-reduction](../02-critical-atomic-reduction/) — 三种同步方式的性能对比（critical 会慢 100 倍）
- **理论补充**：
  - Bakhvalov《现代 CPU 性能分析与优化》第 8 章"优化内存访问" — 解释内存带宽墙
  - 同书第 3 章"CPU 微体系结构" — 解释 P-core/E-core 加速差异
  - 同书第 13 章"优化多线程应用" — false sharing、NUMA、多线程扩展性

## 文件清单

```
01-reduction/
├── README.md                        ← 本文件
├── task1.c                          ← 实验代码
└── data/
    └── thread-scan-results.txt      ← 原始扫描输出
```