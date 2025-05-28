@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ==========================================
echo   그라파나 서버 모니터링 리포트 생성
echo ==========================================
echo.

:: 환경변수 파일 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다!
    echo .env.example 파일을 .env로 복사하고 토큰을 설정하세요.
    pause
    exit /b 1
)

:: 설정 파일 확인
if not exist "config\report_config.json" (
    echo ❌ 설정 파일이 없습니다!
    echo 먼저 update_month.ps1을 실행하세요.
    echo 예: powershell -File update_month.ps1 -Year 2025 -Month 4
    pause
    exit /b 1
)

:: 필요한 폴더들 생성
if not exist "images" mkdir images
if not exist "output" mkdir output

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

:: 2단계: PDF 생성
echo.
echo [2/2] PDF 리포트 생성 중...
echo.
python "02_generate_report.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ PDF 생성 실패!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 리포트 생성 완료!
echo ==========================================
echo.

:: 결과 폴더 열기
set /p choice="결과 폴더를 여시겠습니까? (Y/N): "
if /i "%choice%"=="Y" (
    start explorer "output"
)

pause