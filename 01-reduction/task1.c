#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define N 100000000

int main()
{
    // 任务：计算一个长度为 N 的数组里所有正数的和

    // === Step 1：分配并初始化数组 ===
    long *arr = malloc(N * sizeof(long));
    for (long i = 0; i < N; i++)
    {
        arr[i] = (i % 7) - 3;   // 数据里有正数也有负数
    }

    // === Step 2：单线程版本（基准） ===
    long sum_serial = 0;
    double t1 = omp_get_wtime();
    for (long i = 0; i < N; i++)
    {
        if(arr[i] > 0) sum_serial += arr[i];
    }
    double t2 = omp_get_wtime();
    double time_serial = t2 - t1;
    printf("Serial:       sum=%ld, time=%.3f s\n", sum_serial, time_serial);

    // === Step 3：OpenMP 并行循环 ===
    long sum_parallel = 0;
    t1 = omp_get_wtime();

    #pragma omp parallel for reduction(+:sum_parallel)
    for(long i = 0; i < N; i++)
    {
        if(arr[i] > 0) sum_parallel += arr[i];
    }

    t2 = omp_get_wtime();
    double time_parallel = t2 - t1;
    printf("Parallel:     sum=%ld, time=%.3f s\n", sum_parallel, time_parallel);

    // === Step 4: 验证结果 ===
    if(sum_serial == sum_parallel)
    {
        double speedup = time_serial / time_parallel;
        printf("OK: results match, speedup = %.2fx\n", speedup);
    }
    else
    {
        printf("ERROR: result differ\n");
    }

    free(arr);
    return 0;
}
