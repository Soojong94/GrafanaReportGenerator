@echo off
echo 테스트 환경 설정 중...

:: 필요한 폴더 생성
if not exist "config" mkdir config
if not exist "templates" mkdir templates
if not exist "templates\assets" mkdir templates\assets

echo ✅ 폴더 구조 생성 완료
echo.
echo 다음 단계:
echo 1. config\system_groups.json 파일 생성
echo 2. templates\ 폴더에 HTML 템플릿 파일들 생성
echo 3. templates\assets\style.css 파일 생성
echo 4. runall.bat 실행

pause