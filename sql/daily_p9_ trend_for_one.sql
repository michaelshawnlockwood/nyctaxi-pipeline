/* 3) Daily p95 trend for one procedure (swap name) */

DECLARE @since DATETIME2 = DATEADD(DAY, -14, SYSDATETIME());

WITH s AS (
    SELECT
        [runDate]  = CONVERT(date, [startTime]),
        [durationMs]
    FROM [dbo].[procTelemetry]
    WHERE [startTime] >= @since
      AND [procName] = N'dbo.uspGetCustomer'  -- <- change
      AND ([errorNumber] IS NULL OR [errorNumber] = 0)
),
p AS (
    SELECT
        [runDate],
        [p95_ms] = PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY [durationMs]) OVER (PARTITION BY [runDate])
    FROM s
)
SELECT [runDate], [p95_ms] = CAST([p95_ms] AS DECIMAL(18,1))
FROM p
GROUP BY [runDate], [p95_ms]
ORDER BY [runDate];
