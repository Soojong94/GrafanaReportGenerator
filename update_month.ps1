# update_month.ps1
param(
    [Parameter(Mandatory=$true)]
    [int]$Year,
    
    [Parameter(Mandatory=$true)]
    [int]$Month
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Report Settings Update ==="
Write-Host "Year: $Year, Month: $Month"

# Calculate dates
$startDate = Get-Date -Year $Year -Month $Month -Day 1
$endDate = $startDate.AddMonths(1).AddDays(-1)

# Create configuration
$config = @{
    "report_month" = "$Year. $($Month.ToString().PadLeft(2, '0'))"
    "period" = "$($startDate.ToString('yyyy-MM-dd')) ~ $($endDate.ToString('yyyy-MM-dd'))"
    "grafana_servers" = @(
        @{
            "name" = "Production-Server"
            "url" = "175.45.222.66:3000"
            "token" = ""
        }
    )
    "report_settings" = @{
        "include_storage_details" = $true
        "charts_per_page" = 4
        "time_range" = "30d"
        "grafana_time_from" = $startDate.ToString('yyyy-MM-dd')
        "grafana_time_to" = $endDate.ToString('yyyy-MM-dd')
    }
}

# Create config folder
New-Item -ItemType Directory -Path "config" -Force | Out-Null

# Save configuration file without BOM
try {
    $jsonContent = $config | ConvertTo-Json -Depth 10
    # UTF8NoBOM 인코딩으로 저장 (BOM 없이)
    [System.IO.File]::WriteAllText("config\report_config.json", $jsonContent, [System.Text.UTF8Encoding]::new($false))
    
    Write-Host "Settings updated successfully"
    Write-Host "  Report month: $($config.report_month)"
    Write-Host "  Period: $($config.period)"
    Write-Host ""
    Write-Host "Now run runall.bat"
} catch {
    Write-Host "ERROR: Failed to save config file: $($_.Exception.Message)"
    exit 1
}