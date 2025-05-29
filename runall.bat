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

:: 통합 설정 파일 확인
if not exist "config\unified_config.json" (
    echo ❌ 통합 설정 파일이 없습니다!
    echo.
    echo 다음 중 하나를 실행하세요:
    echo   1. copy config\unified_config_example.json config\unified_config.json
    echo   2. powershell -File update_month.ps1 -Year 2025 -Month 5
    echo.
    pause
    exit /b 1
)

:: 0단계: 설정 파일 검증
echo [0/3] 통합 설정 파일 검증 중...
echo.
python enhanced_config_validator.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 설정 파일 검증 실패!
    echo 위의 오류를 수정한 후 다시 실행하세요.
    echo.
    echo 💡 도움말:
    echo   - config/unified_config_example.json 파일을 참고하세요
    echo   - 설정 수정 후 다시 runall.bat을 실행하세요
    pause
    exit /b 1
)

echo.
echo ✅ 설정 파일 검증 완료!
echo.

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
powershell -ExecutionPolicy RemoteSigned -File "01_download_images.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 이미지 다운로드 실패!
    echo.
    echo 💡 확인사항:
    echo   - .env 파일의 그라파나 토큰이 올바른지 확인
    echo   - 그라파나 서버 접속이 가능한지 확인
    echo   - 네트워크 연결 상태 확인
    pause
    exit /b 1
)

:: 2단계: 통합 설정 기반 리포트 생성
echo.
echo [2/3] 통합 설정 기반 리포트 생성 중...
echo.
python "02_generate_report_unified.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 리포트 생성 실패!
    echo.
    echo 💡 확인사항:
    echo   - 이미지가 정상적으로 다운로드되었는지 확인
    echo   - 템플릿 파일들이 존재하는지 확인
    echo   - Python 패키지가 설치되었는지 확인 (pip install -r requirements.txt)
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 통합 설정 기반 리포트 생성 완료!
echo ==========================================
echo   - 0단계: 설정 파일 검증 ✅
echo   - 1단계: 실제 그라파나 이미지 수집 ✅  
echo   - 2단계: 템플릿 기반 HTML 생성 ✅
echo   - 그룹별 동적 헤더 적용 ✅
echo.

:: 결과 폴더 열기
set /p choice="결과 폴더를 여시겠습니까? (Y/N): "
if /i "%choice%"=="Y" (
    start explorer "output"
)

pause