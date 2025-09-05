/* If you want one more handy pattern, here’s a compact regression detector: 
	p95 by proc for the last 7 days vs prior 7 days, side-by-side with a delta. */

DECLARE @now DATETIME2 = SYSDATETIME();
WITH s AS (
  SELECT
    [procName],
    [durationMs],
    [startTime],
    [errorNumber],
    [bucket] = CASE
                 WHEN [startTime] >= DATEADD(DAY,-7,@now) THEN 'last7'
                 WHEN [startTime] >= DATEADD(DAY,-14,@now) THEN 'prev7'
               END
  FROM [dbo].[procTelemetry]
  WHERE [startTime] >= DATEADD(DAY,-14,@now)
    AND ([errorNumber] IS NULL OR [errorNumber] = 0)
),
p AS (
  SELECT DISTINCT
    [procName],
    [bucket],
    [p95_ms] = CAST(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY [durationMs]) 
                    OVER (PARTITION BY [procName],[bucket]) AS DECIMAL(18,1)),
    [calls]  = COUNT(*) OVER (PARTITION BY [procName],[bucket])
  FROM s
)
SELECT 
  a.[procName],
  a.[calls]     AS [calls_last7],
  a.[p95_ms]    AS [p95_last7_ms],
  b.[calls]     AS [calls_prev7],
  b.[p95_ms]    AS [p95_prev7_ms],
  [delta_ms]    = a.[p95_ms] - b.[p95_ms]
FROM p a
LEFT JOIN p b 
  ON b.[procName] = a.[procName] AND b.[bucket] = 'prev7'
WHERE a.[bucket] = 'last7'
ORDER BY [delta_ms] DESC;
