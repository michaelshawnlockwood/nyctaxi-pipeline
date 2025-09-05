/* 2) Overall p95 for the workload (last 30 days) */

DECLARE @since DATETIME2 = DATEADD(DAY, -30, SYSDATETIME());

SELECT
    [calls]  = COUNT(*),
    [p50_ms] = CAST(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY [durationMs]) OVER () AS DECIMAL(18,1)),
    [p95_ms] = CAST(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY [durationMs]) OVER () AS DECIMAL(18,1)),
    [p99_ms] = CAST(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY [durationMs]) OVER () AS DECIMAL(18,1))
FROM [dbo].[procTelemetry]
WHERE [startTime] >= @since
  AND ([errorNumber] IS NULL OR [errorNumber] = 0);
