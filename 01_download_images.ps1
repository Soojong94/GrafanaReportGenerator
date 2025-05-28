# 01_download_images.ps1
param(
    [string]$ConfigPath = "config\report_config.json"
)

# ===== 자동 그라파나 이미지 다운로더 (환경변수 버전) =====

Add-Type -AssemblyName System.Web

Write-Host "=== 그라파나 이미지 다운로더 시작 ==="
Write-Host "시간: $(Get-Date)"

# 현재 스크립트 경로 기준으로 프로젝트 폴더 설정
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = $scriptPath
$configFile = Join-Path $projectRoot $ConfigPath
$imagesDir = Join-Path $projectRoot "images"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$downloadDir = Join-Path $imagesDir $timestamp

Write-Host "프로젝트 폴더: $projectRoot"
Write-Host "이미지 저장 경로: $downloadDir"
Write-Host ""

# 환경변수 파일 로드
$envFile = Join-Path $projectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            # 따옴표 제거
            $value = $value -replace '^"(.*)"$', '$1'
            $value = $value -replace "^'(.*)'$", '$1'
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "✓ 환경변수 로드 완료"
} else {
    Write-Host "❌ .env 파일을 찾을 수 없습니다."
    exit 1
}

# 설정 파일 읽기
if (Test-Path $configFile) {
    try {
        $config = Get-Content -Path $configFile -Encoding UTF8 | ConvertFrom-Json
        $servers = $config.grafana_servers
        Write-Host "✓ 설정 파일 로드 완료: $($servers.Count)개 서버"
    } catch {
        Write-Host "❌ 설정 파일 읽기 실패: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "❌ 설정 파일을 찾을 수 없습니다: $configFile"
    exit 1
}

# 토큰 확인
$missingTokens = @()
foreach ($server in $servers) {
    if ([string]::IsNullOrWhiteSpace($server.token)) {
        $missingTokens += $server.name
    }
}

if ($missingTokens.Count -gt 0) {
    Write-Host "❌ 다음 서버들의 토큰이 설정되지 않았습니다:"
    foreach ($serverName in $missingTokens) {
        Write-Host "  - $serverName"
    }
    Write-Host ".env 파일에서 토큰을 설정하세요."
    exit 1
}

# 기본 디렉터리 생성
New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null

# 함수 정의
function Get-Dashboards {
    param([string]$ServerUrl, [string]$Token)
    
    $headers = @{"Authorization" = "Bearer $Token"}
    
    try {
        $response = Invoke-RestMethod -Uri "http://$ServerUrl/api/search?type=dash-db" -Headers $headers
        return $response
    } catch {
        Write-Host "    ✗ 대시보드 목록 조회 실패: $($_.Exception.Message)"
        return $null
    }
}

function Get-DashboardPanels {
    param([string]$ServerUrl, [string]$Token, [string]$DashboardUid)
    
    $headers = @{"Authorization" = "Bearer $Token"}
    
    try {
        $response = Invoke-RestMethod -Uri "http://$ServerUrl/api/dashboards/uid/$DashboardUid" -Headers $headers
        $panels = $response.dashboard.panels | Where-Object { 
            $_.id -ne $null -and $_.type -ne "row" -and -not $_.collapsed 
        }
        return $panels
    } catch {
        Write-Host "    ✗ 패널 정보 조회 실패: $($_.Exception.Message)"
        return $null
    }
}

function Download-PanelImage {
    param(
        [string]$ServerUrl,
        [string]$Token,
        [string]$DashboardUid,
        [int]$PanelId,
        [string]$OutputPath
    )
    
    # 설정에서 시간 범위 사용
    $timeFrom = "now-30d"
    $timeTo = "now"
    
    if ($config.report_settings -and $config.report_settings.grafana_time_from) {
        $fromDate = [DateTime]::Parse($config.report_settings.grafana_time_from)
        $toDate = [DateTime]::Parse($config.report_settings.grafana_time_to).AddDays(1)
        
        $timeFrom = [DateTimeOffset]::new($fromDate).ToUnixTimeMilliseconds()
        $timeTo = [DateTimeOffset]::new($toDate).ToUnixTimeMilliseconds()
    }
    
    $url = "http://$ServerUrl/render/d-solo/$DashboardUid" + 
           "?orgId=1&panelId=$PanelId&width=1200&height=800&scale=1" +
           "&from=$timeFrom&to=$timeTo&tz=Asia%2FSeoul"
    
    $headers = @{"Authorization" = "Bearer $Token"}
    
    try {
        Invoke-WebRequest -Uri $url -Headers $headers -OutFile $OutputPath -TimeoutSec 30
        $size = (Get-Item $OutputPath).Length / 1KB
        Write-Host "      ✓ 패널 $PanelId 완료: $([math]::Round($size, 1)) KB"
        return $true
    } catch {
        Write-Host "      ✗ 패널 $PanelId 실패: $($_.Exception.Message)"
        return $false
    }
}

function Test-ServerConnection {
    param([string]$ServerUrl, [string]$Token)
    
    $headers = @{"Authorization" = "Bearer $Token"}
    
    try {
        Invoke-RestMethod -Uri "http://$ServerUrl/api/org" -Headers $headers -TimeoutSec 10 | Out-Null
        return $true
    } catch {
        Write-Host "    ✗ 서버 연결 실패: $($_.Exception.Message)"
        return $false
    }
}

function Clean-FileName {
    param([string]$Name)
    return $Name -replace '[\\/:*?"<>|]', '_'
}

# 메인 실행
$totalImages = 0
$successImages = 0

foreach ($server in $servers) {
    Write-Host "=== [$($server.name)] 서버 처리 중 ==="
    Write-Host "URL: $($server.url)"
    
    # 서버 연결 테스트
    Write-Host "  연결 테스트 중..."
    if (-not (Test-ServerConnection -ServerUrl $server.url -Token $server.token)) {
        Write-Host "  서버 연결 실패, 다음 서버로 이동..."
        Write-Host ""
        continue
    }
    Write-Host "  ✓ 연결 성공"
    
    # 대시보드 목록 조회
    Write-Host "  대시보드 목록 조회 중..."
    $dashboards = Get-Dashboards -ServerUrl $server.url -Token $server.token
    
    if ($dashboards -eq $null -or $dashboards.Count -eq 0) {
        Write-Host "  대시보드를 찾을 수 없습니다."
        Write-Host ""
        continue
    }
    
    Write-Host "  발견된 대시보드: $($dashboards.Count)개"
    
    # 서버별 디렉터리 생성
    $serverDir = Join-Path $downloadDir $server.name
    New-Item -ItemType Directory -Path $serverDir -Force | Out-Null
    
    # 각 대시보드 처리
    foreach ($dashboard in $dashboards) {
        $cleanDashName = Clean-FileName -Name $dashboard.title
        Write-Host ""
        Write-Host "  --- [$cleanDashName] 대시보드 처리 중 ---"
        
        # 패널 정보 조회
        $panels = Get-DashboardPanels -ServerUrl $server.url -Token $server.token -DashboardUid $dashboard.uid
        
        if ($panels -eq $null -or $panels.Count -eq 0) {
            Write-Host "    패널을 찾을 수 없습니다."
            continue
        }
        
        Write-Host "    발견된 패널: $($panels.Count)개"
        
        # 대시보드별 디렉터리 생성
        $dashboardDir = Join-Path $serverDir $cleanDashName
        New-Item -ItemType Directory -Path $dashboardDir -Force | Out-Null
        
        # 각 패널 이미지 다운로드
        foreach ($panel in $panels) {
            $totalImages++
            $cleanPanelTitle = if ($panel.title) { Clean-FileName -Name $panel.title } else { "Panel" }
            $fileName = Join-Path $dashboardDir "$($cleanPanelTitle)_$($panel.id).png"
            
            Write-Host "    패널: $($panel.title) (ID: $($panel.id))"
            
            if (Download-PanelImage -ServerUrl $server.url -Token $server.token -DashboardUid $dashboard.uid -PanelId $panel.id -OutputPath $fileName) {
                $successImages++
            }
            
            Start-Sleep -Milliseconds 500
        }
    }
    
    Write-Host ""
    Write-Host "[$($server.name)] 완료"
}

# 결과 요약
Write-Host ""
Write-Host "=== 다운로드 완료 ==="
Write-Host "총 이미지: $totalImages개"
Write-Host "성공: $successImages개"
Write-Host "실패: $($totalImages - $successImages)개"
Write-Host "저장 위치: $downloadDir"

# 설정 파일에 마지막 다운로드 정보 저장
$config | Add-Member -Name "last_download" -Value @{
    "timestamp" = $timestamp
    "download_path" = $downloadDir
    "total_images" = $totalImages
    "success_images" = $successImages
    "download_time" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
} -Force

$config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFile -Encoding UTF8

Write-Host ""
Write-Host "✅ 이미지 다운로드가 완료되었습니다!"