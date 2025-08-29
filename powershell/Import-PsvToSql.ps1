<# 
.SYNOPSIS
  Import all *.psv files from a folder into SQL Server using BULK INSERT.

.EXAMPLE
  .\Import-PsvToSql.ps1 `
    -ServerInstance "MSL-LAPTOP\MSSQLSERVER_2019" `
    -Database "nyctaxi" `
    -DataDir "D:\appdev\nyctaxi\nyctaxi-pipeline\data_out" `
    -LogDir  "D:\appdev\nyctaxi\nyctaxi-pipeline\logs"
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)] [string] $ServerInstance,
  [Parameter(Mandatory=$true)] [string] $Database,
  [Parameter(Mandatory=$true)] [string] $DataDir,
  [Parameter(Mandatory=$true)] [string] $LogDir,

  # Optional toggles
  [switch] $TrustServerCertificate,     # adds -C when using newer sqlcmd w/ Encrypt=Yes default
  [switch] $KeepNulls = $true,          # KEEPNULLS in BULK INSERT
  [switch] $Tablock  = $true,           # TABLOCK in BULK INSERT
  [string] $TableName = 'dbo.yellow_tripdata',
  [int]    $FirstRow = 2,               # header row skip
  [string] $FieldTerminator = '|',
  [string] $RowTerminator   = '0x0a',   # LF
  [string] $CodePage        = '65001'   # UTF-8
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Paths & setup ---
$ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$TmpDir = Join-Path $env:TEMP 'nyctaxi-bulk-tmp'
New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# --- Validate inputs ---
if (-not (Test-Path -LiteralPath $DataDir)) { throw "-DataDir not found: $DataDir" }
$psvFiles = Get-ChildItem -Path $DataDir -Filter *.psv -File | Sort-Object Name
if (-not $psvFiles) { Write-Warning "No .psv files found in $DataDir"; return $true }

# --- Helper: run sqlcmd with nice errors ---
function Invoke-SqlCmdSafe {
  param(
    [Parameter(Mandatory=$true)][string] $InputFile,
    [Parameter(Mandatory=$true)][string] $OutLog
  )

  $args = @('-S', $ServerInstance, '-d', $Database, '-b', '-e', '-i', $InputFile, '-o', $OutLog)
  if ($TrustServerCertificate) { $args = @('-C') + $args }  # trust server cert (local dev)

  # Call sqlcmd (capturing stderr -> pipeline for console visibility)
  $null = & sqlcmd @args 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    Write-Warning "sqlcmd exit code $code. See log: $OutLog"
    # Show last 40 lines to the console for fast triage
    if (Test-Path -LiteralPath $OutLog) {
      "`n--- tail of log ($OutLog) ---" | Write-Host -ForegroundColor DarkYellow
      Get-Content -LiteralPath $OutLog -Tail 40 | Write-Host
      "--------------------------------`n" | Write-Host -ForegroundColor DarkYellow
    }
    exit $code
  }
}

# --- Preflight: verify connectivity ---
Write-Host "Preflight: testing connectivity to [$ServerInstance] / DB [$Database]..." -ForegroundColor Cyan
$probeSql = Join-Path $TmpDir 'probe.sql'
@"
SET NOCOUNT ON;
SELECT 1 AS ok, @@VERSION AS version_info;
"@ | Set-Content -LiteralPath $probeSql -Encoding UTF8

$probeLog = Join-Path $LogDir 'probe.log'
Invoke-SqlCmdSafe -InputFile $probeSql -OutLog $probeLog
Write-Host "Connectivity OK.`n" -ForegroundColor Green

# --- Import loop ---
$importCount = 0
foreach ($file in $psvFiles) {
  $psvPath = $file.FullName

  # Create a per-file BULK INSERT script
  $bulkSqlPath = Join-Path $TmpDir ("bulk_" + [IO.Path]::GetFileNameWithoutExtension($file.Name) + ".sql")
  $bulkLogPath = Join-Path $LogDir ("bulk_" + [IO.Path]::GetFileNameWithoutExtension($file.Name) + ".log")

  # Option toggles
  $opts = @()
  if ($KeepNulls) { $opts += 'KEEPNULLS' }
  if ($Tablock)  { $opts += 'TABLOCK'  }
  $optList = if ($opts.Count) { ', ' + ($opts -join ', ') } else { '' }

  # Compose T-SQL
  @"
SET NOCOUNT ON;
PRINT 'Starting BULK INSERT: $($psvPath.Replace("'","''"))';
BULK INSERT $TableName
FROM '$($psvPath.Replace("'","''"))'
WITH (
  FIRSTROW = $FirstRow,
  FIELDTERMINATOR = '$FieldTerminator',
  ROWTERMINATOR   = '$RowTerminator',
  CODEPAGE        = '$CodePage'
  $optList
);
PRINT 'Finished BULK INSERT: $($psvPath.Replace("'","''"))';
"@ | Set-Content -LiteralPath $bulkSqlPath -Encoding UTF8

  Write-Host ("Importing {0} -> {1}" -f $file.Name, $TableName) -ForegroundColor Yellow
  Invoke-SqlCmdSafe -InputFile $bulkSqlPath -OutLog $bulkLogPath
  $importCount++
}

Write-Host "`nImported $importCount file(s) successfully." -ForegroundColor Green
return $true
