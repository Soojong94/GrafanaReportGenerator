# update_month.ps1 - 월 변경 도우미 스크립트 (수정버전)
param(
    [Parameter(Mandatory=$true)]
    [int]$Year,
    
    [Parameter(Mandatory=$true)]
    [int]$Month
)

$configPath = "config\report_config.json"

if (-not (Test-Path $configPath)) {
    Write-Host "❌ 설정 파일을 찾을 수 없습니다: $configPath"
    exit 1
}

try {
    # 설정 파일 읽기
    $config = Get-Content -Path $configPath -Encoding UTF8 | ConvertFrom-Json
    
    # 날짜 계산
    $startDate = Get-Date -Year $Year -Month $Month -Day 1
    $endDate = $startDate.AddMonths(1).AddDays(-1)
    
    # 기본 설정 업데이트
    $config.report_month = "$Year. $($Month.ToString().PadLeft(2, '0'))"
    $config.period = "$($startDate.ToString('yyyy-MM-dd')) ~ $($endDate.ToString('yyyy-MM-dd'))"
    
    # report_settings가 없으면 생성
    if (-not $config.report_settings) {
        $config | Add-Member -Name "report_settings" -Value @{} -MemberType NoteProperty
    }
    
    # report_settings 내 속성들 추가/업데이트
    if (-not $config.report_settings.PSObject.Properties["include_storage_details"]) {
        $config.report_settings | Add-Member -Name "include_storage_details" -Value $true -MemberType NoteProperty
    }
    
    if (-not $config.report_settings.PSObject.Properties["charts_per_page"]) {
        $config.report_settings | Add-Member -Name "charts_per_page" -Value 4 -MemberType NoteProperty
    }
    
    if (-not $config.report_settings.PSObject.Properties["exclude_disk_rw_alerts"]) {
        $config.report_settings | Add-Member -Name "exclude_disk_rw_alerts" -Value $true -MemberType NoteProperty
    }
    
    if (-not $config.report_settings.PSObject.Properties["time_range"]) {
        $config.report_settings | Add-Member -Name "time_range" -Value "30d" -MemberType NoteProperty
    }
    
    # 날짜 관련 속성 추가/업데이트
    if ($config.report_settings.PSObject.Properties["grafana_time_from"]) {
        $config.report_settings.grafana_time_from = $startDate.ToString('yyyy-MM-dd')
    } else {
        $config.report_settings | Add-Member -Name "grafana_time_from" -Value $startDate.ToString('yyyy-MM-dd') -MemberType NoteProperty
    }
    
    if ($config.report_settings.PSObject.Properties["grafana_time_to"]) {
        $config.report_settings.grafana_time_to = $endDate.ToString('yyyy-MM-dd')
    } else {
        $config.report_settings | Add-Member -Name "grafana_time_to" -Value $endDate.ToString('yyyy-MM-dd') -MemberType NoteProperty
    }
    
    # 파일 저장
    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath -Encoding UTF8
    
    Write-Host "✅ 설정이 업데이트되었습니다:"
    Write-Host "   리포트 월: $($config.report_month)"
    Write-Host "   기간: $($config.period)"
    Write-Host "   그라파나 데이터 범위: $($startDate.ToString('yyyy-MM-dd')) ~ $($endDate.ToString('yyyy-MM-dd'))"
    Write-Host ""
    Write-Host "이제 03_run_all.bat을 실행하세요."
    
} catch {
    Write-Host "❌ 설정 파일 업데이트 실패: $($_.Exception.Message)"
    Write-Host "오류 상세: $($_.Exception.ToString())"
    exit 1
}