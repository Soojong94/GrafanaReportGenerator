# update_month.ps1 (Fixed Version)
param(
    [Parameter(Mandatory=$true)]
    [int]$Year,
    
    [Parameter(Mandatory=$true)]
    [int]$Month
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Grafana Report Config Update ==="
Write-Host "Year: $Year, Month: $Month"

# Calculate date ranges
$startDate = Get-Date -Year $Year -Month $Month -Day 1
$currentDate = Get-Date
$endDate = if ($currentDate.Year -eq $Year -and $currentDate.Month -eq $Month) {
    $currentDate
} else {
    $startDate.AddMonths(1).AddDays(-1)
}

$configFile = "config\unified_config.json"

# Create config folder
New-Item -ItemType Directory -Path "config" -Force | Out-Null

if (Test-Path $configFile) {
    Write-Host "Updating existing unified config..."
    try {
        $config = Get-Content -Path $configFile -Encoding UTF8 | ConvertFrom-Json
        
        # Update report_settings section only
        $config.report_settings.report_month = "$Year. $($Month.ToString().PadLeft(2, '0'))"
        $config.report_settings.period = "$($startDate.ToString('yyyy-MM-dd')) ~ $($endDate.ToString('yyyy-MM-dd'))"
        $config.report_settings.grafana_time_from = $startDate.ToString('yyyy-MM-dd')
        $config.report_settings.grafana_time_to = $endDate.ToString('yyyy-MM-dd')
        $config.report_settings.default_year = $Year
        $config.report_settings.default_month = $Month
        
        # Update metadata
        $config._metadata.last_updated = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        
        # Save file
        $jsonContent = $config | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($configFile, $jsonContent, [System.Text.UTF8Encoding]::new($false))
        
        Write-Host "Unified config updated successfully"
        Write-Host "  Report Period: $($config.report_settings.report_month)"
        Write-Host "  Date Range: $($config.report_settings.period)"
        
    } catch {
        Write-Host "ERROR: Failed to update config file: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "ERROR: Unified config file not found: $configFile"
    Write-Host "Please create config/unified_config.json file manually first."
    Write-Host "Or if you have existing config files, run:"
    Write-Host "  mkdir config\legacy"
    Write-Host "  move config\*.json config\legacy\"
    Write-Host "Then create unified_config.json manually and run this script again."
    exit 1
}

Write-Host ""
Write-Host "Now you can run runall.bat"