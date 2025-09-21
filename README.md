# 📊 그라파나 월간 리포트 자동 생성기 v2.0

그라파나 대시보드에서 자동으로 이미지를 수집하고 **HTML 월간 모니터링 리포트**를 생성하는 도구입니다.

##  시스템 아키텍처

### 전체 워크플로우
```
[수집 대상 서버들]
    ↓ (WireGuard VPN 터널링)
[중앙 수집 서버]
  - Prometheus (메트릭 수집)
  - Grafana (시각화 + 이미지 생성) ⚠️
    ↓ (HTTP API 호출)
[사용자 서버]
  - 이 도구 실행
  - HTML 리포트 생성
```

### 컴포넌트 역할
- **수집 대상 서버**: 모니터링 대상 시스템 (Node Exporter 등)
- **중앙 수집 서버**: 메트릭 저장 및 대시보드 제공
- **사용자 서버**: 리포트 생성 요청 및 HTML 파일 생성

---

##  사전 요구사항 (중요!)

###  그라파나 서버 설정 (필수)

>  **중요**: 그라파나에서 **이미지 렌더링 기능**이 활성화되어 있어야 합니다.

**확인 방법:**
1. 그라파나 웹에서 아무 대시보드 열기
2. 패널에 마우스 올리기 → **Export** → **Share link** 클릭
3. **"Generate image"** 버튼이 보이는지 확인

**설정 방법:**
- 📖 **[상세 설정 가이드 보기](docs/GRAFANA_IMAGE_SETUP.md)**

### 🌐 네트워크 요구사항
- **사용자 서버 → 그라파나 서버**: HTTP 접근 가능
- **그라파나 API 포트** (기본 3000번) 접근 허용
- **방화벽 설정**: 해당 포트 허용 필요

### 💻 시스템 요구사항
- **Python 3.7+**
- **PowerShell** (Windows 기본 설치)
- **그라파나 API 토큰** (Viewer 권한 이상)

---

##  핵심 기능

- ** 통합 리포트**: 여러 서버를 하나의 HTML 파일로 통합
- ** 단일 설정**: JSON 파일 하나만 편집하면 끝
- ** 자동 분류**: 차트를 카테고리별로 자동 정리
- ** 반응형 디자인**: PC/모바일 모두 지원
- ** 버전 관리**: 기존 파일 덮어쓰기 방지

---

##  빠른 시작 (4단계)

### 0단계: 그라파나 서버 준비 ⚠️
**먼저 그라파나에서 이미지 생성이 가능한지 확인하세요:**
1. 그라파나 웹에서 대시보드 열기
2. 패널 → Export → Share link → **"Generate image"** 버튼 확인
3. 버튼이 없다면 → **[그라파나 이미지 설정 가이드](docs/GRAFANA_IMAGE_SETUP.md)** 참조

### 1단계: 기본 설정
```bash
# Python 패키지 설치
pip install -r requirements.txt

# 환경변수 파일 생성
copy .env.example .env
# .env 파일을 열어서 그라파나 토큰 입력
```

### 2단계: JSON 설정 파일 생성
```bash
# 예시 파일을 복사
copy config\unified_config_example.json config\unified_config.json
# unified_config.json 파일을 환경에 맞게 편집 (아래 가이드 참조)
```

### 3단계: 실행
```bash
# 리포트 월 설정 (JSON 파일의 날짜가 자동 업데이트됩니다)
powershell -File update_month.ps1 -Year 2025 -Month 5

# 리포트 생성 (이미지 다운로드 + HTML 생성)
runall.bat
```

**끝!** `output` 폴더에 HTML 리포트 파일이 생성됩니다.

---

## ⚙️ JSON 설정 파일 가이드

**핵심**: `config/unified_config.json` **파일 하나만 편집하면 됩니다.**

###  기본 구조
```json
{
  "report_settings": { /* 리포트 기간 - update_month.ps1이 자동 업데이트 */ },
  "grafana_servers": [ /* 그라파나 서버 정보 */ ],
  "servers": { /* 서버 상세 정보 */ },
  "groups": { /* 리포트에 표시할 서버 그룹 */ }
}
```

###  **중요: 날짜는 자동 업데이트!**

>  **주의**: `report_settings` 섹션의 날짜 정보는 **직접 편집하지 마세요**!
> 
> ```bash
> # 이 명령어가 JSON 파일의 날짜를 자동으로 업데이트합니다
> powershell -File update_month.ps1 -Year 2025 -Month 5
> ```

###  직접 편집해야 할 항목들

#### 1. 그라파나 서버 연결 정보
```json
"grafana_servers": [
  {
    "name": "Production-Server",
    "url": "192.168.1.100:3000",
    "description": "메인 그라파나 서버"
  }
]
```
- `url`: 그라파나 서버 IP:포트 (예: `192.168.1.100:3000`)

#### 2. 서버 상세 정보
```json
"servers": {
  "Mail-Server": {
    "display_name": "메일 서버 시스템",
    "hostname": "mail-server-01", 
    "os": "ubuntu-20.04",
    "cpu_mem": "4vCPU / 16GB Mem",
    "disk": "100 GB / 500 GB",
    "availability": "99.9%"
  }
}
```

#### 3. 리포트 그룹 정의
```json
"groups": {
  "전체시스템": {
    "display_name": "전체 시스템 통합 모니터링",
    "description": "모든 시스템의 통합 현황",
    "servers": ["Mail-Server", "Web-Server", "DB-Server"],
    "active": true
  }
}
```
- `servers`: 이 그룹에 포함할 서버 목록 (**그라파나 대시보드 이름과 정확히 일치해야 함**)
- `active`: `true`로 설정된 그룹만 리포트 생성

###  실제 설정 예시

**우리 회사에 Mail-Server, Web-Server가 있다면:**

```json
{
  "_metadata": {
    "version": "2.0",
    "description": "우리 회사 그라파나 리포트 설정"
  },
  "report_settings": {
    // ⚠️ 이 섹션은 update_month.ps1이 자동으로 업데이트하므로 건드리지 마세요!
    "report_month": "2025. 05",
    "period": "2025-05-01 ~ 2025-05-31",
    "default_year": 2025,
    "default_month": 5
  },
  "grafana_servers": [
    {
      "name": "Production-Server",
      "url": "192.168.1.100:3000"
    }
  ],
  "servers": {
    // ✅ 이 부분은 직접 편집하세요
    "Mail-Server": {
      "display_name": "메일 서버",
      "hostname": "mail-01",
      "os": "Ubuntu 20.04",
      "cpu_mem": "4vCPU / 16GB",
      "disk": "200GB / 1TB",
      "availability": "99.9%"
    },
    "Web-Server": {
      "display_name": "웹 서버",
      "hostname": "web-01", 
      "os": "Ubuntu 22.04",
      "cpu_mem": "8vCPU / 32GB",
      "disk": "500GB / 2TB",
      "availability": "99.99%"
    }
  },
  "groups": {
    // ✅ 이 부분도 직접 편집하세요
    "전체시스템": {
      "display_name": "전체 시스템 모니터링",
      "description": "메일서버와 웹서버 통합 현황",
      "servers": ["Mail-Server", "Web-Server"],
      "active": true
    },
    "메일시스템": {
      "display_name": "메일 시스템 전용",
      "description": "메일 서버 상세 분석",
      "servers": ["Mail-Server"],
      "active": true
    }
  }
}
```

###  중요한 주의사항

1. **서버 이름 일치**: `groups`의 `servers` 배열에 있는 이름이 **그라파나 대시보드 이름**과 정확히 일치해야 합니다.

2. **JSON 문법**: 마지막 항목에는 쉼표(`,`)를 붙이지 마세요.
   ```json
   // ❌ 잘못된 예
   "active": true,
   
   // ✅ 올바른 예  
   "active": true
   ```

3. **한글 사용 가능**: 모든 문자열에서 한글 사용 가능합니다.

---

## 🔧 환경변수 설정 (.env 파일)

```bash
# 그라파나 API 토큰 (필수)
GRAFANA_PRODUCTION_TOKEN=your_grafana_api_token_here
GRAFANA_PRODUCTION_URL=192.168.1.100:3000

# 기본 설정
DEFAULT_YEAR=2025
DEFAULT_MONTH=5
```

**그라파나 API 토큰 생성 방법:**
1. 그라파나 웹 → Configuration → API Keys
2. Add API key 클릭
3. Name: `ReportGenerator`, Role: `Viewer` 선택
4. 생성된 토큰을 `.env` 파일에 붙여넣기

---

##  프로젝트 구조

```
GrafanaReportGenerator/
├── README.md                       #  메인 가이드 (현재 파일)
├── docs/
│   └── GRAFANA_IMAGE_SETUP.md     #  그라파나 이미지 설정 가이드
├── config/
│   ├── unified_config.json         #  메인 설정 (여기만 편집!)
│   └── unified_config_example.json # 참고용 예시
├── templates/                      # HTML 템플릿 파일들
├── images/                         # 다운로드된 이미지 (자동 생성)
├── output/                         # 최종 HTML 리포트 (자동 생성)
├── .env                           # 환경변수 (토큰 정보)
├── runall.bat                     #  메인 실행 파일
├── update_month.ps1              # 월 설정 변경
└── enhanced_config_validator.py   # 설정 파일 검증
```

---

##  사용법 - 상황별 가이드

### ** 매월 리포트 생성**
```bash
# 1. 월 변경 (JSON 파일의 날짜 정보가 자동으로 업데이트됩니다)
powershell -File update_month.ps1 -Year 2025 -Month 6

# 2. 리포트 생성
runall.bat
```

### **⚙️ 새 서버 추가**

1. `config/unified_config.json` 열기
2. `servers` 섹션에 새 서버 정보 추가:
```json
"servers": {
  "기존서버들": { ... },
  "NEW-SERVER": {
    "display_name": "새로운 서버",
    "hostname": "new-server-01",
    "os": "ubuntu-22.04", 
    "cpu_mem": "8vCPU / 32GB",
    "disk": "500GB / 2TB",
    "availability": "99.9%"
  }
}
```
3. `groups` 섹션에서 원하는 그룹에 추가:
```json
"groups": {
  "전체시스템": {
    "servers": ["기존서버", "NEW-SERVER"]
  }
}
```
4. `runall.bat` 실행

---

##  문제 해결

### **설정 파일 검증:**
```bash
python enhanced_config_validator.py
```
오류가 있으면 구체적인 해결방법을 알려줍니다.

### **일반적인 문제들:**
- ❌ **"서버를 찾을 수 없습니다"** → 그라파나 대시보드 이름과 JSON의 서버 이름이 일치하는지 확인
- ❌ **"JSON 문법 오류"** → 마지막 항목의 쉼표 제거, 따옴표 확인
- ❌ **"토큰 오류"** → `.env` 파일의 토큰이 올바른지 확인

### **그라파나 관련 문제:**
- ❌ **"이미지 다운로드 실패"** → **[그라파나 이미지 렌더링 설정](docs/GRAFANA_IMAGE_SETUP.md)** 확인
- ❌ **"Empty image"** → 그라파나에서 해당 대시보드가 실제 데이터를 표시하는지 확인
- ❌ **"Connection timeout"** → 네트워크 접근 권한 및 방화벽 설정 확인
- ❌ **"Generate image 버튼 없음"** → 그라파나 이미지 렌더러 플러그인 미설치

---

## 📊 생성되는 리포트

**파일명 형식**: `그룹명_2025_05_20250529_143022.html`

**리포트 구성:**
-  **헤더**: 그룹명, 리포트 기간
-  **서버별 섹션**: 각 서버의 현황 정보 + 차트들
-  **자동 분류**: 시스템 리소스, 네트워크, 스토리지 등으로 분류
-  **반응형**: PC/모바일에서 모두 깔끔하게 표시

---

##  팁

1. **월말 실행 권장**: 해당 월의 전체 데이터 수집을 위해 월말에 실행
2. **설정 백업**: `unified_config.json` 파일을 정기적으로 백업
3. **그룹 활용**: 부서별, 시스템별로 다양한 그룹을 만들어 각각 리포트 생성 가능
4. **브라우저로 열기**: 생성된 HTML 파일을 브라우저에서 열어서 확인
5. **그라파나 확인**: 리포트 생성 전에 그라파나에서 대시보드가 정상 작동하는지 먼저 확인

---

## 📚 추가 문서

- 📖 **[그라파나 이미지 렌더링 설정 가이드](docs/GRAFANA_IMAGE_SETUP.md)** - 필수 설정 방법

---

