@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ==========================================
echo   그라파나 서버 모니터링 리포트 생성 v2.0
echo   (통합 설정 기반)
echo ==========================================
echo.

:: 환경변수 파일 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다!
    echo .env.example 파일을 .env로 복사하고 토큰을 설정하세요.
    pause
    exit /b 1
)

:: 통합 설정 파일 확인 (기존 report_config.json 대신)
if not exist "config\unified_config.json" (
    echo ❌ 통합 설정 파일이 없습니다!
    echo 먼저 update_month.ps1을 실행하세요.
    echo 예: powershell -File update_month.ps1 -Year 2025 -Month 5
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
echo [1/2] 그라파나 이미지 다운로드 중...
echo.
powershell -ExecutionPolicy Bypass -File "01_download_images.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 이미지 다운로드 실패!
    pause
    exit /b 1
)

:: 2단계: 통합 설정 기반 리포트 생성
echo.
echo [2/2] 통합 설정 기반 리포트 생성 중...
echo.
python "02_generate_report_unified.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 리포트 생성 실패!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 통합 설정 기반 리포트 생성 완료!
echo ==========================================
echo   - 단일 통합 설정 파일 사용
echo   - 실제 그라파나 이미지 사용
echo   - 템플릿 기반 HTML 생성
echo   - 그룹별 동적 헤더 적용
echo.

:: 결과 폴더 열기
set /p choice="결과 폴더를 여시겠습니까? (Y/N): "
if /i "%choice%"=="Y" (
    start explorer "output"
)

pause