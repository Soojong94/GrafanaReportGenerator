# 그라파나 월간 리포트 자동 생성기

그라파나 대시보드에서 자동으로 이미지를 수집하고 월간 서버 모니터링 리포트를 PDF로 생성하는 도구입니다.

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 1. 저장소 클론
git clone https://github.com/your-username/GrafanaReportGenerator.git
cd GrafanaReportGenerator

# 2. Python 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정
copy .env.example .env
# .env 파일을 편집하여 실제 그라파나 토큰 입력