@echo off
:: runall.bat - 통합 실행 파일
setlocal EnableDelayedExpansion
chcp 65001 > nul
cd /d "%~dp0"

:: 파라미터 파싱
set "YEAR="
set "MONTH="
set "HELP="

:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="-Year" (
    set "YEAR=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-Month" (
    set "MONTH=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="-h" set "HELP=1"
if "%~1"=="--help" set "HELP=1"
if "%~1"=="/?" set "HELP=1"
shift
goto :parse_args

:args_done

:: 도움말 표시
if defined HELP (
    echo.
    echo ==========================================
    echo   그라파나 월간 리포트 자동 생성기
    echo ==========================================
    echo.
    echo 사용법:
    echo   runall.bat -Year YYYY -Month M
    echo.
    echo 예시:
    echo   runall.bat -Year 2025 -Month 4
    echo   runall.bat -Year 2025 -Month 12
    echo.
    echo 옵션:
    echo   -Year    리포트 연도 (예: 2025)
    echo   -Month   리포트 월 (예: 4)
    echo   -h, --help, /?   이 도움말 표시
    echo.
    pause
    exit /b 0
)

echo.
echo ==========================================
echo   그라파나 월간 리포트 자동 생성기
echo ==========================================
echo 프로젝트 폴더: %CD%
echo.

:: 환경변수 파일 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다!
    echo .env.example 파일을 .env로 복사하고 토큰을 설정하세요.
    echo.
    echo 명령어: copy .env.example .env
    echo 그 다음 .env 파일을 편집하여 실제 토큰을 입력하세요.
    pause
    exit /b 1
)

:: 필요한 폴더들 생성
if not exist "images" mkdir images
if not exist "output" mkdir output
if not exist "config" mkdir config

:: Python 및 필수 패키지 확인
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python이 설치되지 않았습니다!
    echo Python 3.7 이상을 설치하세요.
    pause
    exit /b 1
)

:: 연도/월 파라미터 처리
if "%YEAR%"=="" (
    set /p YEAR="리포트 연도를 입력하세요 (예: 2025): "
)
if "%MONTH%"=="" (
    set /p MONTH="리포트 월을 입력하세요 (예: 4): "
)

:: 입력값 검증
if "%YEAR%"=="" (
    echo ❌ 연도가 입력되지 않았습니다.
    pause
    exit /b 1
)
if "%MONTH%"=="" (
    echo ❌ 월이 입력되지 않았습니다.
    pause
    exit /b 1
)

echo 설정된 리포트 기간: %YEAR%년 %MONTH%월
echo.

:: 1단계: 설정 업데이트
echo [1/3] 리포트 설정 업데이트 중...
python -c "
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

# 날짜 계산
year, month = int('%YEAR%'), int('%MONTH%')
start_date = datetime(year, month, 1)
if month == 12:
    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
else:
    end_date = datetime(year, month + 1, 1) - timedelta(days=1)

# 설정 생성
config = {
    'organization': os.getenv('ORGANIZATION_NAME', '보령시농업기술센터'),
    'report_month': f'{year}. {month:02d}',
    'period': f'{start_date.strftime(\"%%Y-%%m-%%d\")} ~ {end_date.strftime(\"%%Y-%%m-%%d\")}',
    'company_logo': True,
    'grafana_servers': [
        {
            'name': 'Production-Server',
            'url': os.getenv('GRAFANA_PRODUCTION_URL', '175.45.222.66:3000'),
            'token': os.getenv('GRAFANA_PRODUCTION_TOKEN', '')
        }
    ],
    'report_settings': {
        'include_storage_details': True,
        'charts_per_page': 4,
        'exclude_disk_rw_alerts': True,
        'time_range': '30d',
        'grafana_time_from': start_date.strftime('%%Y-%%m-%%d'),
        'grafana_time_to': end_date.strftime('%%Y-%%m-%%d')
    }
}

# 설정 파일 저장
Path('config').mkdir(exist_ok=True)
with open('config/report_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print(f'✅ 설정 업데이트 완료: {year}년 {month}월')
"

if %ERRORLEVEL% neq 0 (
    echo ❌ 설정 업데이트 실패!
    pause
    exit /b 1
)

:: 2단계: 이미지 다운로드
echo.
echo [2/3] 그라파나 이미지 다운로드 중...
echo.
powershell -ExecutionPolicy Bypass -File "01_download_images.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 이미지 다운로드 실패!
    echo 토큰 설정이나 서버 연결을 확인하세요.
    pause
    exit /b 1
)

:: 3단계: PDF 생성
echo.
echo [3/3] PDF 리포트 생성 중...
echo.
python "02_generate_report.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ PDF 생성 실패!
    echo Python 패키지 설치를 확인하세요: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 모든 작업이 완료되었습니다!
echo ==========================================
echo.

:: 결과 확인
echo 📁 생성된 파일들:
echo.
for /f %%i in ('dir images\*\*.png /s /b 2^>nul ^| find /c /v ""') do echo   📸 총 이미지: %%i개
for /f %%i in ('dir output\*.pdf /b 2^>nul ^| find /c /v ""') do echo   📄 PDF 파일: %%i개

echo.
echo 📋 최신 PDF 파일:
for /f "tokens=*" %%i in ('dir output\*.pdf /b /od 2^>nul') do set "LATEST_PDF=%%i"
if defined LATEST_PDF echo   %LATEST_PDF%

echo.
set /p choice="결과 폴더를 여시겠습니까? (Y/N): "
if /i "%choice%"=="Y" (
    start explorer "output"
)

echo.
echo 💡 다음에 실행할 때:
echo    runall.bat -Year %YEAR% -Month [다른월]
echo.
pause