<#
.SYNOPSIS
    Generate SQL Server CREATE TABLE scripts from data dictionary files (CSV/JSON).

.PARAMETER InputPath
    One or more files or folders. Folders are searched for *.dictionary.csv.

.PARAMETER OutPath
    Output folder for .sql files. Default: .\sql_out

.PARAMETER Schema
    Target schema name. Default: dbo

.PARAMETER CharMode
    String type to emit for generic string columns: VARCHAR or NVARCHAR. Default: VARCHAR

.EXAMPLE
    .\Generate-SqlFromDictionary.ps1 -InputPath .\phase2_dicts -OutPath .\sql_out -Schema dbo -CharMode VARCHAR
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0, ValueFromRemainingArguments=$true)]
    [string[]] $InputPath,

    [string] $OutPath = ".\sql_out",
    [string] $Schema = "dbo",
    [ValidateSet("VARCHAR","NVARCHAR")]
    [string] $CharMode = "VARCHAR"
)

function Try-Float($v) {
    try { return [double]$v } catch { return $null }
}

function Choose-IntWidth($min, $max) {
    if ($null -eq $min -or $null -eq $max) { return "INT" }
    $nonneg = ($min -ge 0)
    if ($nonneg -and 0 -le $max -and $max -le 255) { return "TINYINT" }
    if (-32768 -le $min -and $min -le 32767 -and -32768 -le $max -and $max -le 32767) { return "SMALLINT" }
    if (-2147483648 -le $min -and $min -le 2147483647 -and -2147483648 -le $max -and $max -le 2147483647) { return "INT" }
    return "BIGINT"
}

function Map-SqlType($row, $CharMode) {
    $t = ($row.type | Out-String).Trim().ToUpper()
    switch ($t) {
        "TIMESTAMP" { return "DATETIME2" }
        "BIGINT" {
            $mn = Try-Float $row.min
            $mx = Try-Float $row.max
            return (Choose-IntWidth $mn $mx)
        }
        "DOUBLE" { return "DECIMAL(18,4)" }
        "VARCHAR" { 
            $ex = $row.example
            $ln = 10
            if ($ex -is [string] -and $ex.Length -gt 0) { $ln = [Math]::Max(1, [Math]::Min($ex.Length, 100)) }
            return "$CharMode($ln)"
        }
        "STRING" {
            $ex = $row.example
            $ln = 10
            if ($ex -is [string] -and $ex.Length -gt 0) { $ln = [Math]::Max(1, [Math]::Min($ex.Length, 100)) }
            return "$CharMode($ln)"
        }
        default { return $t }
    }
}

function Is-Nullable($row) {
    try {
        $n = [double]$row.nulls
        return ($n -gt 0)
    } catch {
        return $true
    }
}

function Yes($v) {
    if ($null -eq $v) { return $false }
    $s = ($v | Out-String).Trim().ToLower()
    return @("y","yes","true","1","t") -contains $s
}

function Render-Table($schema, $table, $rows, $CharMode) {
    $lines = @()
    $pk = @()

    foreach ($r in $rows) {
        $colname = "[" + $r.column + "]"
        $sqlType = Map-SqlType $r $CharMode
        $nullness = if (Is-Nullable $r) { "NULL" } else { "NOT NULL" }

        $identityClause = ""
        if (Yes $r.identity) {
            $seed = 1
            $incr = 1
            if ($r.identity_seed -and ($r.identity_seed.ToString().Trim() -ne "")) {
                try { $seed = [int]$r.identity_seed } catch { $seed = 1 }
            }
            if ($r.identity_increment -and ($r.identity_increment.ToString().Trim() -ne "")) {
                try { $incr = [int]$r.identity_increment } catch { $incr = 1 }
            }
            $identityClause = " IDENTITY($seed,$incr)"
        }

        $defaultClause = ""
        if ($r.default -and ($r.default.ToString().Trim() -ne "")) {
            $defaultClause = " DEFAULT (" + $r.default + ")"
        }

        $lines += "    $colname $sqlType$identityClause$defaultClause $nullness"
        if (Yes $r.pk) { $pk += $colname }
    }

    $pkClause = ""
    if ($pk.Count -gt 0) {
        $pkList = [string]::Join(", ", $pk)
        $pkClause = ",`n    CONSTRAINT [PK_{0}_{1}] PRIMARY KEY CLUSTERED ({2})" -f $schema, $table, $pkList
    }

    $body = [string]::Join(",`n", $lines)
    $ddl = @"
IF OBJECT_ID(N'[$schema].[$table]', N'U') IS NOT NULL
    DROP TABLE [$schema].[$table];
GO

CREATE TABLE [$schema].[$table] (
$body$pkClause
);
GO
"@
    return $ddl
}

# Collect inputs
$targets = @()
foreach ($inp in $InputPath) {
    if (Test-Path $inp -PathType Container) {
        $targets += Get-ChildItem -Path $inp -Filter *.dictionary.csv -File
    } elseif (Test-Path $inp -PathType Leaf) {
        $targets += Get-Item $inp
    } else {
        Write-Warning "Skipping missing path: $inp"
    }
}

# Load rows per table
$tables = @{}
foreach ($t in $targets) {
    $path = $t.FullName
    $ext = [IO.Path]::GetExtension($path).ToLowerInvariant()
    $table = [IO.Path]::GetFileNameWithoutExtension($path) -replace '\.dictionary$',''
    $rows = @()

    if ($ext -eq ".csv") {
        $rows = Import-Csv -Path $path
    } elseif ($ext -eq ".json") {
        $json = Get-Content -Raw -Path $path | ConvertFrom-Json
        if ($json -is [array]) { $rows = $json } else { $rows = @($json) }
    } else {
        Write-Warning "Unsupported file type: $path"; continue
    }

    $tables["$Schema|$table"] = $rows
}

# Output
$OutDir = New-Item -ItemType Directory -Force -Path $OutPath
$aggregate = @()

foreach ($key in $tables.Keys) {
    $parts = $key.Split("|")
    $sch = $parts[0]; $tbl = $parts[1]
    $rows = $tables[$key]
    if ($rows.Count -eq 0) { continue }

    $ddl = Render-Table -schema $sch -table $tbl -rows $rows -CharMode $CharMode
    $file = Join-Path $OutDir.FullName "$sch.$tbl.sql"
    Set-Content -Path $file -Value $ddl -Encoding UTF8
    $aggregate += $ddl
}

# Write create_all.sql
$all = [string]::Join("", $aggregate)
Set-Content -Path (Join-Path $OutDir.FullName "create_all.sql") -Value $all -Encoding UTF8

Write-Host "Generated $($tables.Keys.Count) table script(s) in $($OutDir.FullName)"
Get-ChildItem $OutDir -Filter *.sql | ForEach-Object { Write-Host " - $($_.Name)" }
