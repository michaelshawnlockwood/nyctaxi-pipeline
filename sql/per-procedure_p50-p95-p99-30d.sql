/* 1) Per-procedure p50/p95/p99 (last 30 days), plus calls & avg */

USE [YourDb];
GO

DECLARE @since DATETIME2 = DATEADD(DAY, -30, SYSDATETIME());

WITH s AS (
    SELECT [procName],
        [durationMs],
        [startTime],
        [errorNumber]
    FROM [dbo].[procTelemetry] -- <- adjust to your table
    WHERE [startTime] >= @since
      AND ([errorNumber] IS NULL OR [errorNumber] = 0) -- exclude failed runs
),
w AS (
    SELECT [procName],
        [calls]    = COUNT(*) OVER (PARTITION BY [procName]),
        [avg_ms]   = AVG([durationMs]) OVER (PARTITION BY [procName]),
        [p50_ms]   = PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY [durationMs]) OVER (PARTITION BY [procName]),
        [p95_ms]   = PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY [durationMs]) OVER (PARTITION BY [procName]),
        [p99_ms]   = PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY [durationMs]) OVER (PARTITION BY [procName])
    FROM s
)
SELECT DISTINCT
    [procName],
    [calls],
    [p50_ms] = CAST([p50_ms] AS DECIMAL(18,1)),
    [p95_ms] = CAST([p95_ms] AS DECIMAL(18,1)),
    [p99_ms] = CAST([p99_ms] AS DECIMAL(18,1)),
    [avg_ms] = CAST([avg_ms] AS DECIMAL(18,1))
FROM w
ORDER BY [p95_ms] DESC;
