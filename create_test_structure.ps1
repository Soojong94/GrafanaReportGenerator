# create_test_structure.ps1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== 통합 리포트용 테스트 구조 생성 ==="

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$testImagesDir = "images\test_$timestamp\Production-Server"

# 테스트 폴더 구조 생성
$folders = @(
    "$testImagesDir\Mail-Server",
    "$testImagesDir\Main-Prometheus"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    Write-Host "폴더 생성: $folder"
}

# 테스트용 더미 이미지 파일 생성
$testFiles = @{
    "Mail-Server" = @(
        "CPU_Usage_3.png",
        "Memory_Usage_6.png", 
        "Disk_IO_9.png",
        "Network_Traffic_12.png",
        "Mail_Queue_15.png",
        "SMTP_Connections_18.png",
        "Mail_Processing_21.png",
        "Email_Volume_24.png"
    )
    "Main-Prometheus" = @(
        "CPU_Utilization_27.png",
        "Memory_Consumption_30.png",
        "Disk_Space_33.png", 
        "Network_IO_36.png",
        "Prometheus_Metrics_39.png",
        "Grafana_Dashboard_42.png",
        "Prometheus_Targets_45.png",
        "Grafana_Users_48.png"
    )
}

foreach ($dashboard in $testFiles.Keys) {
    $dashboardPath = "$testImagesDir\$dashboard"
    Write-Host ""
    Write-Host "대시보드: $dashboard"
    
    foreach ($filename in $testFiles[$dashboard]) {
        $filePath = "$dashboardPath\$filename"
        
        # 간단한 더미 PNG 헤더 생성 (실제 PNG 파일처럼 보이게)
        $pngHeader = [byte[]](137, 80, 78, 71, 13, 10, 26, 10) # PNG 시그니처
        $dummyData = [byte[]](1..100) # 더미 데이터
        $combinedData = $pngHeader + $dummyData
        
        [System.IO.File]::WriteAllBytes($filePath, $combinedData)
        Write-Host "  ✓ $filename"
    }
}

Write-Host ""
Write-Host "=========================================="
Write-Host "✅ 테스트 구조 생성 완료!"
Write-Host "=========================================="
Write-Host "생성된 경로: $testImagesDir"
Write-Host ""
Write-Host "📋 다음 단계:"
Write-Host "1. 설정 파일들이 모두 생성되었는지 확인"
Write-Host "   - config/system_groups.json"
Write-Host "   - config/server_info.json (업데이트됨)"
Write-Host "   - config/dashboard_config.json (업데이트됨)"
Write-Host ""
Write-Host "2. 통합 리포트 생성 실행:"
Write-Host "   python 02_generate_report.py"
Write-Host ""
Write-Host "3. output 폴더에서 생성된 통합 HTML 파일 확인"
Write-Host "   파일명 예시: 통합_시스템1_2025_05_*.html"
Write-Host ""
Write-Host "🔧 서버 추가 방법:"
Write-Host "1. system_groups.json의 servers 배열에 서버명 추가"
Write-Host "2. server_info.json에 서버 정보 추가"
Write-Host "3. dashboard_config.json에 대시보드 설정 추가"
Write-Host "4. 이미지 폴더에 해당 서버 폴더 생성"
Write-Host ""