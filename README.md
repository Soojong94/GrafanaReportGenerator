# 그라파나 월간 리포트 자동 생성기 v2.0

그라파나 대시보드에서 자동으로 이미지를 수집하고 **통합 월간 서버 모니터링 리포트**를 PDF로 생성하는 도구입니다.

## 🆕 v2.0 주요 변경사항

- **통합 리포트**: 여러 서버를 하나의 HTML 파일에 통합
- **시스템 그룹**: 관련 서버들을 그룹별로 관리
- **버전 관리**: 기존 파일 덮어쓰기 방지
- **동적 설정**: JSON 설정 파일을 통한 유연한 서버 관리

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

# 4. 설정 파일 확인
# config/system_groups.json - 시스템 그룹 설정
# config/server_info.json - 서버 정보 설정
# config/dashboard_config.json - 대시보드 설정
2. 리포트 생성
bash# 월 설정
powershell -File update_month.ps1 -Year 2025 -Month 5

# 통합 리포트 생성
runall.bat
📁 폴더 구조
GrafanaReportGenerator/
├── config/
│   ├── system_groups.json      # 시스템 그룹 설정 (NEW)
│   ├── server_info.json        # 서버 정보 설정
│   ├── dashboard_config.json   # 대시보드 설정
│   └── report_config.json      # 리포트 기본 설정
├── images/                     # 다운로드된 이미지
├── output/                     # 생성된 리포트
├── templates/assets/           # CSS 스타일
├── 01_download_images.ps1      # 이미지 다운로드
├── 02_generate_report.py       # 통합 리포트 생성 (UPDATED)
├── update_month.ps1           # 월 설정 업데이트
└── runall.bat                 # 전체 실행
⚙️ 서버 추가 방법
1. 시스템 그룹에 서버 추가
config/system_groups.json:
json{
  "groups": {
    "시스템1": {
      "servers": [
        "Mail-Server",
        "Main-Prometheus",
        "NEW-SERVER"  // 새 서버 추가
      ]
    }
  }
}
2. 서버 정보 추가
config/server_info.json:
json{
  "servers": {
    "NEW-SERVER": {
      "display_name": "새 서버 이름",
      "hostname": "new-server-01",
      "os": "ubuntu-22.04",
      "cpu_mem": "8vCPU / 32GB Mem",
      "disk": "200 GB / 1TB",
      "availability": "99.9%",
      "summary": {
        "total_alerts": {"value": 0, "label": "전체"},
        "critical_alerts": {"value": 0, "label": "긴급"},
        "warning_alerts": {"value": 0, "label": "경고"},
        "top5_note": "알림 현황 메모"
      }
    }
  }
}
3. 대시보드 설정 추가
config/dashboard_config.json:
json{
  "dashboards": {
    "NEW-SERVER": {
      "display_name": "새 서버 모니터링",
      "description": "새 서버 시스템 모니터링",
      "color": "#17a2b8",
      "servers": ["NEW-SERVER"]
    }
  }
}
🧪 테스트
bash# 테스트 구조 생성
powershell -File create_test_structure.ps1

# 리포트 생성 테스트
python 02_generate_report.py
📊 생성되는 리포트

파일명: 통합_시스템1_2025_05_YYYYMMDD_HHMMSS.html
구조:

공통 헤더
서버별 섹션 (메일 서버, 프로메테우스)
각 서버의 현황 및 차트
공통 푸터



🔧 주요 기능

✅ 통합 리포트: 여러 서버를 하나의 파일에 통합
✅ 버전 관리: 기존 파일 덮어쓰기 방지 (_v001, _v002...)
✅ 동적 설정: JSON 파일로 서버 정보 관리
✅ 반응형 디자인: 모바일/데스크톱 지원
✅ 카테고리 분류: 자동 차트 분류 및 정렬

📝 설정 파일 가이드
각 JSON 설정 파일에는 주석과 사용법 가이드가 포함되어 있습니다:

system_groups.json: 서버 그룹 관리
server_info.json: 서버 상세 정보
dashboard_config.json: 대시보드 표시 설정

🆘 문제 해결

설정 파일 오류: JSON 문법 확인
이미지 없음: 그라파나 연결 및 폴더 구조 확인
서버 정보 없음: server_info.json에 서버 정보 추가
리포트 생성 실패: 로그 메시지 확인

📞 지원

이슈: GitHub Issues
문서: 각 설정 파일 내 주석 참조


이제 모든 파일이 준비되었습니다! 

## 💡 사용 방법 요약

1. **설정 파일 생성**: 위의 JSON 파일들을 `config/` 폴더에 생성
2. **테스트 실행**: `powershell -File create_test_structure.ps1`
3. **리포트 생성**: `python 02_generate_report.py`
4. **결과 확인**: `output/` 폴더에서 `통합_시스템1_*.html` 파일 확인

이제 하나의 HTML 파일에 메일 서버와 프로메테우스 서버가 모두 포함된 통합 리포트가 생성됩니다! 🎉