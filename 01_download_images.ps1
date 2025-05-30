# 01_download_images.ps1 (Fixed Version)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Grafana Image Downloader Start (Unified Config Based) ==="

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$configFile = Join-Path $projectRoot "config\unified_config.json"
$imagesDir = Join-Path $projectRoot "images"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$downloadDir = Join-Path $imagesDir $timestamp

Write-Host "Project Root: $projectRoot"
Write-Host "Download Dir: $downloadDir"

# Load environment variables
$envFile = Join-Path $projectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "Environment variables loaded"
} else {
    Write-Host "ERROR: .env file not found"
    exit 1
}

# Load unified config file
if (-not (Test-Path $configFile)) {
    Write-Host "ERROR: Unified config file not found: $configFile"
    Write-Host "Please create config/unified_config.json file or run update_month.ps1"
    exit 1
}

try {
    $config = Get-Content -Path $configFile -Encoding UTF8 | ConvertFrom-Json
    $servers = $config.grafana_servers
    Write-Host "Unified config loaded: $($servers.Count) servers"
} catch {
    Write-Host "ERROR: Failed to read unified config file: $($_.Exception.Message)"
    exit 1
}

# Set tokens
foreach ($server in $servers) {
    $server.token = [Environment]::GetEnvironmentVariable("GRAFANA_PRODUCTION_TOKEN")
    if ([string]::IsNullOrWhiteSpace($server.token)) {
        Write-Host "ERROR: GRAFANA_PRODUCTION_TOKEN not set"
        Write-Host "Please set token in .env file"
        exit 1
    }
}

# Create directories
New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
Write-Host "Created download directory"

# Helper functions
function Test-GrafanaConnection {
    param([string]$ServerUrl, [string]$Token)
    $headers = @{"Authorization" = "Bearer $Token"}
    try {
        Invoke-RestMethod -Uri "http://$ServerUrl/api/org" -Headers $headers -TimeoutSec 10 | Out-Null
        return $true
    } catch {
        Write-Host "  Connection failed: $($_.Exception.Message)"
        return $false
    }
}

function Get-GrafanaDashboards {
    param([string]$ServerUrl, [string]$Token)
    $headers = @{"Authorization" = "Bearer $Token"}
    try {
        $response = Invoke-RestMethod -Uri "http://$ServerUrl/api/search?type=dash-db" -Headers $headers
        return $response
    } catch {
        Write-Host "  Failed to get dashboards: $($_.Exception.Message)"
        return $null
    }
}

function Get-GrafanaPanels {
    param([string]$ServerUrl, [string]$Token, [string]$DashboardUid)
    $headers = @{"Authorization" = "Bearer $Token"}
    try {
        $response = Invoke-RestMethod -Uri "http://$ServerUrl/api/dashboards/uid/$DashboardUid" -Headers $headers
        $panels = $response.dashboard.panels | Where-Object { 
            $_.id -ne $null -and $_.type -ne "row" -and -not $_.collapsed 
        }
        return $panels
    } catch {
        Write-Host "  Failed to get panels: $($_.Exception.Message)"
        return $null
    }
}

function Download-GrafanaPanel {
    param(
        [string]$ServerUrl,
        [string]$Token,
        [string]$DashboardUid,
        [int]$PanelId,
        [string]$OutputPath
    )
    
    $timeFrom = "now-30d"
    $timeTo = "now"
    
    # Use date range from unified config if available
    if ($config.report_settings -and $config.report_settings.grafana_time_from) {
        try {
            $fromDate = [DateTime]::Parse($config.report_settings.grafana_time_from)
            $toDate = [DateTime]::Parse($config.report_settings.grafana_time_to).AddDays(1)
            $timeFrom = [DateTimeOffset]::new($fromDate).ToUnixTimeMilliseconds()
            $timeTo = [DateTimeOffset]::new($toDate).ToUnixTimeMilliseconds()
        } catch {
            Write-Host "    Date parsing error, using default"
        }
    }
    
    # Fix: Properly escape URL parameters
    $baseUrl = "http://$ServerUrl/render/d-solo/$DashboardUid"
    $params = @(
        "orgId=1",
        "panelId=$PanelId",
        "width=1200",
        "height=800", 
        "scale=1",
        "from=$timeFrom",
        "to=$timeTo",
        "tz=Asia%2FSeoul"
    )
    $url = $baseUrl + "?" + ($params -join "&")
    
    $headers = @{"Authorization" = "Bearer $Token"}
    
    try {
        Invoke-WebRequest -Uri $url -Headers $headers -OutFile $OutputPath -TimeoutSec 30
        $size = (Get-Item $OutputPath).Length / 1KB
        Write-Host "    Panel $PanelId completed: $([math]::Round($size, 1)) KB"
        return $true
    } catch {
        Write-Host "    Panel $PanelId failed: $($_.Exception.Message)"
        return $false
    }
}

function Clean-SafeFileName {
    param([string]$Name)
    # Fix: Properly escape regex pattern
    $invalidChars = '[\\/:*?"<>|]'
    return $Name -replace $invalidChars, '_'
}

# Main execution
$totalImages = 0
$successImages = 0

foreach ($server in $servers) {
    Write-Host ""
    Write-Host "=== Processing Server: $($server.name) ==="
    Write-Host "URL: $($server.url)"
    
    # Test connection
    Write-Host "Testing connection..."
    if (-not (Test-GrafanaConnection -ServerUrl $server.url -Token $server.token)) {
        Write-Host "Connection failed, skipping server"
        continue
    }
    Write-Host "Connection successful"
    
    # Get dashboards
    Write-Host "Getting dashboards..."
    $dashboards = Get-GrafanaDashboards -ServerUrl $server.url -Token $server.token
    
    if ($dashboards -eq $null -or $dashboards.Count -eq 0) {
        Write-Host "No dashboards found"
        continue
    }
    
    Write-Host "Found $($dashboards.Count) dashboards"
    
    # Create server directory
    $serverDir = Join-Path $downloadDir $server.name
    New-Item -ItemType Directory -Path $serverDir -Force | Out-Null
    
    # Process each dashboard
    foreach ($dashboard in $dashboards) {
        $cleanDashName = Clean-SafeFileName -Name $dashboard.title
        Write-Host ""
        Write-Host "--- Processing Dashboard: $cleanDashName ---"
        
        # Get panels
        $panels = Get-GrafanaPanels -ServerUrl $server.url -Token $server.token -DashboardUid $dashboard.uid
        
        if ($panels -eq $null -or $panels.Count -eq 0) {
            Write-Host "  No panels found"
            continue
        }
        
        Write-Host "  Found $($panels.Count) panels"
        
        # Create dashboard directory
        $dashboardDir = Join-Path $serverDir $cleanDashName
        New-Item -ItemType Directory -Path $dashboardDir -Force | Out-Null
        
        # Download each panel
        foreach ($panel in $panels) {
            $totalImages++
            $cleanPanelTitle = if ($panel.title) { Clean-SafeFileName -Name $panel.title } else { "Panel" }
            $fileName = Join-Path $dashboardDir "$($cleanPanelTitle)_$($panel.id).png"
            
            Write-Host "  Panel: $($panel.title) (ID: $($panel.id))"
            
            if (Download-GrafanaPanel -ServerUrl $server.url -Token $server.token -DashboardUid $dashboard.uid -PanelId $panel.id -OutputPath $fileName) {
                $successImages++
            }
            
            Start-Sleep -Milliseconds 500
        }
    }
    
    Write-Host "Server $($server.name) completed"
}

# Save results - Update unified config file
try {
    # Read existing unified config and update
    $originalConfig = Get-Content -Path $configFile -Encoding UTF8 | ConvertFrom-Json
    
    # Add/update last_download info
    $lastDownloadInfo = @{
        "timestamp" = $timestamp
        "download_path" = $downloadDir
        "total_images" = $totalImages
        "success_images" = $successImages
        "download_time" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    # Add property to PowerShell object
    if ($originalConfig.last_download) {
        $originalConfig.last_download = $lastDownloadInfo
    } else {
        $originalConfig | Add-Member -Type NoteProperty -Name "last_download" -Value $lastDownloadInfo
    }
    
    # Update metadata
    if ($originalConfig._metadata) {
        $originalConfig._metadata.last_updated = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    # Save unified config file
    $jsonContent = $originalConfig | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($configFile, $jsonContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host "Unified config file updated successfully"
} catch {
    Write-Host "Warning: Failed to update unified config file: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "=== Download Complete ==="
Write-Host "Total images: $totalImages"
Write-Host "Success: $successImages"
Write-Host "Failed: $($totalImages - $successImages)"
Write-Host "Location: $downloadDir"
Write-Host ""
Write-Host "Image download completed successfully!"
Write-Host "Download completed based on unified configuration."