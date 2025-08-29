/* Bulk insert template for dbo.yellow_tripdata (PSV, UTF-8) */
/* Change the variables below then execute in SSMS */

DECLARE @DataDir NVARCHAR(4000) = N'D:\appdev\nyctaxi\data_out';
DECLARE @File NVARCHAR(4000) = N'yellow_tripdata_2024-01.psv';
DECLARE @FullPath NVARCHAR(4000) = @DataDir + CASE WHEN RIGHT(@DataDir,1) IN ('/','\') THEN '' ELSE '\\' END + @File;
DECLARE @SqlStatement NVARCHAR(MAX);

SET @SqlStatement = N'BULK INSERT [dbo].[yellow_tripdata]
FROM ''' + @FullPath + '''
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ''|'',
    ROWTERMINATOR = ''0x0A'',
    CODEPAGE = ''65001'',
    DATAFILETYPE = ''char'',
    TABLOCK,
    MAXERRORS = 100,
    BATCHSIZE = 100000,
    ERRORFILE = N''D:\AppDev\nyctaxi\data_in\errors\yellow_tripdata.bulk_errors''
);';

PRINT CONCAT('Loading: ', @FullPath);
EXEC sp_executesql @SqlStatement;