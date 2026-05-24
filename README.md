# OpenMP Learning

HPC 系统软件方向的 OpenMP 实战笔记和性能实验。

每个目录对应一个具体问题，包含代码、实验数据、踩坑记录和性能分析。所有 benchmark 在真实物理机上完成，数据可复现。

## 学习日志

| Day | 主题 | 链接 |
|-----|------|------|
| 1 | reduction 子句与线程扫描 benchmark | [01-reduction/](./01-reduction/) |
| 2 | critical vs atomic vs reduction 性能对比 | _coming soon_ |
| 3 | schedule 调度策略对比 | _planned_ |
| 4 | task 模型与并行斐波那契 | _planned_ |
| 5 | SIMD 向量化实验 | _planned_ |
| 6-7 | 矩阵乘法多版本优化（综合项目）| _planned_ |

## 实验环境

| 项目 | 配置 |
|------|------|
| CPU | i9-14900k（8 P-core × 2HT + 16 E-core = 32 线程） |
| 内存 | 48GB DDR5 |
| 系统 | Ubuntu 24.04 |
| 编译器 | gcc 14 |

## 编译惯例

所有代码统一使用以下参数编译：

```bash
gcc -O2 -Wall -Werror -fopenmp xxx.c -o xxx
```

参数说明：

- `-O2`：基础优化（benchmark 的最低要求）
- `-Wall`：打开所有 warning
- `-Werror`：warning 升级为 error（OpenMP 错误经常静默发生，这是早期信号）
- `-fopenmp`：启用 OpenMP

## 学习目标

完成 OpenMP 实战后进入 MPI → CUDA / HIP → LLVM 后端方向，最终目标是 HPC 编译器 / GPU 系统软件工程师。

## 学习方法

- **撞墙优先**：先写代码再翻书，让大脑在"饥饿"状态下吸收概念
- **数据驱动**：每个实验都要产出 benchmark 表格，不是"跑通就行"
- **完整踩坑**：每个坑都记录现象 / 根因 / 修复 / 预防四段论
