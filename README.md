# 그라파나 월간 리포트 자동 생성기 v2.0

그라파나 대시보드에서 자동으로 이미지를 수집하고 **통합 월간 서버 모니터링 리포트**를 HTML로 생성하는 도구입니다.

## 🆕 v2.0 주요 변경사항

- **통합 설정**: 하나의 JSON 파일로 모든 설정 관리
- **통합 리포트**: 여러 서버를 하나의 HTML 파일에 통합
- **시스템 그룹**: 관련 서버들을 그룹별로 관리
- **버전 관리**: 기존 파일 덮어쓰기 방지
- **동적 설정**: JSON을 통한 유연한 서버 관리

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

# 4. 설정 확인
# config/unified_config.json 파일만 편집하면 됩니다!
```

### 2. 리포트 생성
```bash
# 월 설정 (unified_config.json이 자동 업데이트됩니다)
powershell -File update_month.ps1 -Year 2025 -Month 4

# 통합 리포트 생성
runall.bat
```

## 📁 폴더 구조
```
GrafanaReportGenerator/
├── config/
│   └── unified_config.json         # 통합 설정 파일 (이것만 편집!)
├── templates/
│   ├── base.html                   # 메인 HTML 템플릿
│   ├── server_section.html         # 서버 섹션 템플릿
│   ├── chart_category.html         # 차트 카테고리 템플릿
│   ├── chart_card.html            # 개별 차트 템플릿
│   └── assets/
│       └── style.css              # CSS 스타일
├── images/                        # 다운로드된 이미지
├── output/                        # 생성된 리포트
├── 01_download_images.ps1         # 이미지 다운로더
├── 02_generate_report_unified.py  # 통합 리포트 생성기
├── update_month.ps1              # 월 설정 업데이터
└── runall.bat                    # 전체 실행 스크립트
```

## ⚙️ 설정 가이드

### 단일 설정 파일: `config/unified_config.json`

이제 **이 파일 하나만** 편집하면 됩니다. 모든 설정이 여기에 들어있습니다.

#### 구조 개요:
```json
{
  "_metadata": {
    "version": "2.0",
    "description": "그라파나 리포트 생성기 통합 설정"
  },
  "report_settings": {
    "report_month": "2025. 04",
    "period": "2025-04-01 ~ 2025-04-30"
  },
  "grafana_servers": [
    {
      "name": "Production-Server",
      "url": "175.45.222.66:3000"
    }
  ],
  "servers": { /* 서버 상세 정보 */ },
  "dashboards": { /* 대시보드 설정 */ },
  "chart_categories": { /* 차트 분류 */ },
  "groups": { /* 시스템 그룹 */ }
}
```

#### 주요 섹션 설명:

1. **report_settings**: 리포트 기간 및 설정
2. **grafana_servers**: 그라파나 서버 연결 정보
3. **servers**: 개별 서버 정보 및 알림 현황
4. **dashboards**: 대시보드 표시 설정 및 설명
5. **chart_categories**: 차트 분류 및 정렬 순서
6. **groups**: 함께 표시할 서버들을 정의하는 시스템 그룹

### 새 서버 추가 방법

`unified_config.json`에서 다음 섹션들을 편집하세요:

#### 1. servers 섹션에 추가:
```json
"servers": {
  "NEW-SERVER": {
    "display_name": "새 서버 시스템",
    "hostname": "new-server-01",
    "os": "ubuntu-22.04",
    "cpu_mem": "8vCPU / 32GB Mem",
    "disk": "200 GB / 1TB",
    "availability": "99.9%",
    "summary": {
      "total_alerts": {"value": 0, "label": "전체"},
      "critical_alerts": {"value": 0, "label": "긴급"},
      "warning_alerts": {"value": 0, "label": "경고"},
      "top5_note": "시스템 정상 운영 중"
    }
  }
}
```

#### 2. dashboards 섹션에 추가:
```json
"dashboards": {
  "NEW-SERVER": {
    "display_name": "새 서버 모니터링",
    "description": "새 서버 시스템 모니터링",
    "color": "#17a2b8",
    "servers": ["NEW-SERVER"]
  }
}
```

#### 3. groups 섹션에 추가:
```json
"groups": {
  "새그룹": {
    "display_name": "새 시스템 그룹",
    "description": "새 시스템 그룹 설명",
    "servers": ["NEW-SERVER", "Mail-Server"],
    "order": 4,
    "active": true
  }
}
```

## 🧪 테스트 및 검증

### 설정 검증:
```bash
# 설정 파일 검증
python enhanced_config_validator.py

### 테스트 리포트 생성:
```bash
# 테스트 월 설정
powershell -File update_month.ps1 -Year 2025 -Month 4

# 리포트 생성
python 02_generate_report_unified.py
```

## 📊 생성되는 리포트

**파일명 형식**: `그룹명_YYYY_MM_YYYYMMDD_HHMMSS.html`

**예시**: `IntegratedMonitoring_2025_04_20250529_143022.html`

### 리포트 구조:
1. **공통 헤더**: 그룹명과 리포트 기간
2. **서버별 섹션**: 각 서버의 현황과 차트들
3. **차트 카테고리**: 시스템 리소스, 스토리지, 네트워크 등으로 자동 분류
4. **공통 푸터**: 회사 정보 및 리포트 메타데이터

## 🔧 주요 기능

✅ **통합 리포트**: 여러 서버를 하나의 파일에 통합  
✅ **단일 설정**: config/unified_config.json 하나만 관리  
✅ **버전 관리**: 기존 파일 덮어쓰기 방지 (_v001, _v002...)  
✅ **자동 분류**: 차트를 카테고리별로 자동 분류 및 정렬  
✅ **반응형 디자인**: 모바일/데스크톱 모두 지원  
✅ **실시간 데이터**: 실제 그라파나에서 이미지 수집  

## 📝 사용법 단계별 가이드

### 첫 실행 시:
1. `.env` 파일에 그라파나 토큰 설정
2. `config/unified_config.json`에서 서버 정보 확인/수정
3. 월 설정: `powershell -File update_month.ps1 -Year 2025 -Month 4`
4. 실행: `runall.bat`

### 매월 리포트 생성 시:
1. 월만 변경: `powershell -File update_month.ps1 -Year 2025 -Month 5`
2. 실행: `runall.bat`

### 서버 추가 시:
1. `config/unified_config.json`에서 servers, dashboards, groups 섹션 편집
2. 실행: `runall.bat`

## 🆘 문제 해결

### 자주 발생하는 문제들:

**1. 설정 파일 오류**
```bash
# 검증 실행
python enhanced_config_validator.py
```

**2. 그라파나 연결 실패**
- `.env` 파일의 토큰 확인
- 그라파나 서버 URL 확인

**3. 이미지 다운로드 실패**
- 네트워크 연결 확인
- 그라파나 대시보드 존재 여부 확인

**4. 리포트 생성 실패**
- 템플릿 파일들 존재 확인
- Python 패키지 설치 확인


## 💡 팁 및 권장사항

1. **월말에 실행**: 해당 월의 전체 데이터를 위해 월말에 실행 권장
2. **정기 백업**: `config/unified_config.json` 파일 정기 백업
3. **템플릿 커스터마이징**: `templates/` 폴더의 HTML/CSS 파일 수정으로 디자인 변경 가능
4. **대용량 처리**: 차트가 많은 경우 `charts_per_page` 설정으로 페이지당 차트 수 조절

## 📞 지원 및 문의

- **이슈**: GitHub Issues 페이지 활용
- **문서**: 각 설정 파일 내 주석 참조
- **설정 도움**: `enhanced_config_validator.py` 실행으로 상세 오류 확인

---
