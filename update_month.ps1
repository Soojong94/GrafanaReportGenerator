# update_month.ps1 (간단 버전)
param(
    [Parameter(Mandatory=$true)]
    [int]$Year,
    
    [Parameter(Mandatory=$true)]
    [int]$Month
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== 통합 설정 업데이트 ==="
Write-Host "Year: $Year, Month: $Month"

# 날짜 계산
$startDate = Get-Date -Year $Year -Month $Month -Day 1
$endDate = $startDate.AddMonths(1).AddDays(-1)

$configFile = "config\unified_config.json"

# config 폴더 생성
New-Item -ItemType Directory -Path "config" -Force | Out-Null

if (Test-Path $configFile) {
    Write-Host "기존 통합 설정 파일 업데이트 중..."
    try {
        $config = Get-Content -Path $configFile -Encoding UTF8 | ConvertFrom-Json
        
        # report_settings 섹션 업데이트만
        $config.report_settings.report_month = "$Year. $($Month.ToString().PadLeft(2, '0'))"
        $config.report_settings.period = "$($startDate.ToString('yyyy-MM-dd')) ~ $($endDate.ToString('yyyy-MM-dd'))"
        $config.report_settings.grafana_time_from = $startDate.ToString('yyyy-MM-dd')
        $config.report_settings.grafana_time_to = $endDate.ToString('yyyy-MM-dd')
        $config.report_settings.default_year = $Year
        $config.report_settings.default_month = $Month
        
        # 메타데이터 업데이트
        $config._metadata.last_updated = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        
        # 파일 저장
        $jsonContent = $config | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($configFile, $jsonContent, [System.Text.UTF8Encoding]::new($false))
        
        Write-Host "통합 설정 업데이트 완료"
        Write-Host "  리포트 월: $($config.report_settings.report_month)"
        Write-Host "  기간: $($config.report_settings.period)"
        
    } catch {
        Write-Host "ERROR: 설정 파일 업데이트 실패: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "ERROR: 통합 설정 파일이 없습니다: $configFile"
    Write-Host "먼저 config/unified_config.json 파일을 수동으로 생성하세요."
    Write-Host "또는 기존 설정 파일들이 있다면 다음을 실행하세요:"
    Write-Host "  mkdir config\legacy"
    Write-Host "  move config\*.json config\legacy\"
    Write-Host "그리고 unified_config.json을 수동으로 생성한 후 다시 실행하세요."
    exit 1
}

Write-Host ""
Write-Host "이제 runall.bat을 실행하세요"