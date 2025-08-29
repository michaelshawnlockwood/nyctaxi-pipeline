SELECT CASE WHEN GROUPING(CAST(tpep_pickup_datetime AS date)) = 1
		THEN 'GRAND TOTAL'
		ELSE CONVERT(varchar(10), CAST(tpep_pickup_datetime AS date), 120)  -- yyyy-mm-dd
	END                                               AS trip_date,
	COUNT(*)                                          AS total_trips,
	SUM(total_amount)                                 AS total_revenue,
	AVG(trip_distance)                                AS average_trip_distance,
	HASHBYTES('SHA2_256',
		(CASE WHEN GROUPING(CAST(tpep_pickup_datetime AS date))=1
			THEN 'ALL-DAYS'
			ELSE CONVERT(varchar(10), CAST(tpep_pickup_datetime AS date), 120)
		END)
		+ '|' + CONVERT(varchar(20), COUNT(*))
		+ '|' + CONVERT(varchar(38), SUM(total_amount))
		+ '|' + CONVERT(varchar(20), AVG(trip_distance))
	)                                                 AS data_integrity_hash
FROM dbo.yellow_tripdata
GROUP BY ROLLUP (CAST(tpep_pickup_datetime AS date))
ORDER BY GROUPING(CAST(tpep_pickup_datetime AS date)),     -- 0 (days) first, 1 (total) last
  CAST(tpep_pickup_datetime AS date);
