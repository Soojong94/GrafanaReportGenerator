@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ==========================================
echo   그라파나 서버 모니터링 리포트 생성 v2.1
echo ==========================================
echo.

:: 환경변수 파일 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다!
    echo .env.example 파일을 .env로 복사하고 토큰을 설정하세요.
    pause
    exit /b 1
)

:: 0단계: 고급 설정 파일 검증 (새로 추가)
echo [0/3] 🔍 설정 파일 고급 검증 중...
echo.
python enhanced_config_validator.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 설정 파일에 오류가 있습니다!
    echo 💡 위의 상세한 해결책을 참고하여 문제를 수정하세요.
    echo    문제 해결 후 다시 runall.bat을 실행하세요.
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 설정 검증 완료! 리포트 생성을 시작합니다.
echo.

:: 기본 설정 파일 확인 (기존 코드 그대로)
if not exist "config\report_config.json" (
    echo ❌ 기본 설정 파일이 없습니다!
    echo 먼저 update_month.ps1을 실행하세요.
    echo 예: powershell -File update_month.ps1 -Year 2025 -Month 5
    pause
    exit /b 1
)

:: 시스템 그룹 설정 파일 확인
if not exist "config\system_groups.json" (
    echo ❌ 시스템 그룹 설정 파일이 없습니다!
    echo config\system_groups.json 파일을 생성하세요.
    pause
    exit /b 1
)

:: 필요한 폴더들 생성
if not exist "images" mkdir images
if not exist "output" mkdir output
if not exist "templates" (
    mkdir templates
    mkdir templates\assets
)

:: 템플릿 파일 존재 확인
set "missing_templates="
if not exist "templates\base.html" set "missing_templates=!missing_templates! base.html"
if not exist "templates\server_section.html" set "missing_templates=!missing_templates! server_section.html"
if not exist "templates\chart_category.html" set "missing_templates=!missing_templates! chart_category.html"
if not exist "templates\chart_card.html" set "missing_templates=!missing_templates! chart_card.html"
if not exist "templates\assets\style.css" set "missing_templates=!missing_templates! style.css"

if not "!missing_templates!"=="" (
    echo ❌ 템플릿 파일이 없습니다: !missing_templates!
    echo templates 폴더에 필요한 파일들을 생성하세요.
    pause
    exit /b 1
)

:: 1단계: 이미지 다운로드
echo [1/3] 그라파나 이미지 다운로드 중...
echo.
powershell -ExecutionPolicy Bypass -File "01_download_images.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 이미지 다운로드 실패!
    pause
    exit /b 1
)

:: 2단계: 템플릿 기반 리포트 생성
echo.
echo [2/3] 템플릿 기반 그룹별 리포트 생성 중...
echo.
python "02_generate_report.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 리포트 생성 실패!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 그룹별 리포트 생성 완료!
echo ==========================================
echo   - ✅ 설정 파일 사전 검증 완료
echo   - ✅ 실제 그라파나 이미지 사용
echo   - ✅ 템플릿 기반 HTML 생성
echo   - ✅ 그룹별 동적 헤더 적용
echo.

:: 결과 폴더 열기
set /p choice="결과 폴더를 여시겠습니까? (Y/N): "
if /i "%choice%"=="Y" (
    start explorer "output"
)

pause