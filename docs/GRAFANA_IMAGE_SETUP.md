# 그라파나 이미지 렌더링 기능 활성화 가이드

## 📋 개요
그라파나에서 **패널 → Export → Share link → Generate image** 기능을 활성화하여 대시보드 패널을 PNG 이미지로 내보낼 수 있도록 설정하는 방법입니다.

## 🔧 1단계: 이미지 렌더러 플러그인 설치

### 방법 1: 명령어로 설치 
```bash
# 이미지 렌더러 플러그인 설치
sudo grafana-cli plugins install grafana-image-renderer

# 플러그인 파일 소유자 변경 (중요!)
sudo chown -R grafana:grafana /var/lib/grafana/plugins/grafana-image-renderer/

# 그라파나 서비스 재시작
sudo systemctl restart grafana-server
```

### 방법 2: 웹 인터페이스에서 설치
1. 그라파나 웹 접속 → **Administration → Plugins and data → Plugins**
2. **grafana-image-renderer** 검색
3. **Install** 버튼 클릭
4. 설치 완료 후 그라파나 재시작

## 🛠️ 2단계: 시스템 의존성 설치

### Ubuntu/Debian 환경
```bash
# 패키지 목록 업데이트
sudo apt update

# Chrome 헤드리스 브라우저 실행에 필요한 라이브러리 설치
sudo apt install -y \
  libx11-6 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
  libxext6 libxfixes3 libxi6 libxrender1 libxtst6 libglib2.0-0 \
  libnss3 libcups2 libdbus-1-3 libxss1 libxrandr2 libgtk-3-0 \
  libasound2 libxcb-dri3-0 libgbm1 libxshmfence1
```

### CentOS/RHEL 환경
```bash
# 필요한 패키지 설치
sudo yum install -y \
  libXcomposite libXdamage libXtst cups libXScrnSaver pango atk \
  adwaita-cursor-theme adwaita-icon-theme at-spi2-atk at-spi2-core \
  cairo-gobject colord-libs dconf desktop-file-utils gdk-pixbuf2 \
  glib-networking gnutls gsettings-desktop-schemas gtk3 \
  hicolor-icon-theme json-glib libappindicator-gtk3 libdbusmenu \
  libdbusmenu-gtk3 libepoxy liberation-fonts alsa-lib
```


## ⚙️ 3단계: 그라파나 설정 수정

```bash
sudo nano /etc/grafana/grafana.ini
```

### 📋 네트워크 환경별 설정 가이드

#### 🏠 **로컬 환경 (같은 서버에서 실행)**
```ini
[server]
# 로컬 실행 시에는 기본 설정으로도 충분
domain = localhost
root_url = http://localhost:3000

[rendering]
# 로컬에서는 빈 값으로 두어도 됨
server_url =
callback_url = http://localhost:3000/
renderer_token = -
concurrent_render_request_limit = 30
```

#### 🌐 **원격 접속 - WireGuard 사용 (사설 IP)**
```ini
[server]
# WireGuard VPN 내부 IP 사용
domain = 10.0.0.100
root_url = http://10.0.0.100:3000

[rendering]
# callback_url은 반드시 WireGuard IP로 설정
server_url =
callback_url = http://10.0.0.100:3000/
renderer_token = -
concurrent_render_request_limit = 30
```

#### 🌍 **원격 접속 - 공인 IP/도메인 사용**
```ini
[server]
# 공인 IP 또는 도메인 사용
domain = 203.0.113.100
# 또는 domain = grafana.yourcompany.com
root_url = http://203.0.113.100:3000

[rendering]
# ⚠️ 중요: 외부에서 접근 가능한 주소로 설정
server_url =
callback_url = http://203.0.113.100:3000/
renderer_token = -
concurrent_render_request_limit = 30
```

### 🔑 설정 항목 상세 설명

#### **[server] 섹션**
- **`domain`**: 그라파나 서버의 주소
  - 로컬: `localhost`
  - WireGuard: `10.0.0.100` (VPN 내부 IP)
  - 공인망: `203.0.113.100` 또는 도메인명
- **`root_url`**: 완전한 URL 형태로 작성

#### **[rendering] 섹션**
- **`server_url`**: 보통 빈 값으로 둠 (플러그인이 자동 감지)
- **`callback_url`**: ⚠️ **가장 중요한 설정**
  - 그라파나가 이미지 렌더러와 통신할 때 사용
  - 반드시 **실제 접근 가능한 주소**로 설정
  - `localhost` 사용 금지 (외부 접속 시 렌더링 실패 원인)
- **`renderer_token`**: 기본값 `-`로 두면 됨
- **`concurrent_render_request_limit`**: 동시 렌더링 요청 수 제한

### 🔍 환경별 확인 방법

#### **어떤 IP를 사용해야 할지 모르겠다면:**

1. **그라파나 접속 주소 확인**
   ```bash
   # 현재 그라파나에 접속할 때 사용하는 주소가 바로 설정할 주소입니다
   # 예: http://192.168.1.100:3000 으로 접속한다면
   #     domain = 192.168.1.100
   #     callback_url = http://192.168.1.100:3000/
   ```

2. **네트워크 인터페이스 확인**
   ```bash
   # 서버의 IP 주소 확인
   ip addr show
   
   # 또는
   hostname -I
   ```

3. **WireGuard 사용 확인**
   ```bash
   # WireGuard 인터페이스 확인
   wg show
   
   # WireGuard IP 확인 (보통 10.x.x.x 대역)
   ip addr show wg0
   ```

### ⚠️ 중요한 주의사항

1. **localhost 금지**: 외부에서 접속하는 경우 `callback_url`에 `localhost` 사용 불가
   ```ini
   # ❌ 잘못된 예 (외부 접속 시 렌더링 실패)
   callback_url = http://localhost:3000/
   
   # ✅ 올바른 예
   callback_url = http://192.168.1.100:3000/
   ```

2. **방화벽 설정**: 3000번 포트가 열려있는지 확인
   ```bash
   # 포트 확인
   sudo netstat -tlnp | grep :3000
   
   # 방화벽 허용 (Ubuntu/Debian)
   sudo ufw allow 3000
   
   # 방화벽 허용 (CentOS/RHEL)
   sudo firewall-cmd --permanent --add-port=3000/tcp
   sudo firewall-cmd --reload
   ```

3. **설정 적용**: 수정 후 반드시 재시작
   ```bash
   sudo systemctl restart grafana-server
   ```

### 🧪 설정 테스트

설정 완료 후 다음 방법으로 테스트:

```bash
# 1. API로 직접 테스트
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
"http://YOUR_GRAFANA_IP:3000/render/d-solo/dashboard-uid?panelId=1&width=1000&height=500" \
-o test.png

# 2. 파일 생성 확인
ls -lh test.png
file test.png

# 3. 이미지 크기 확인 (50KB 이상이면 정상)
du -h test.png
```

### 💡 환경별 권장사항

- **개발/테스트**: 로컬 설정으로 충분
- **내부망**: WireGuard IP 사용 권장 (보안성 향상)
- **외부 공개**: 공인 IP + 방화벽 설정 필수
- **도메인 사용**: SSL 인증서 적용 권장


## 🔄 4단계: 서비스 재시작 및 확인

```bash
# 그라파나 재시작
sudo systemctl restart grafana-server

# 서비스 상태 확인
sudo systemctl status grafana-server

# 플러그인 프로세스 실행 확인
ps aux | grep plugin_start_linux_amd64
```

## ✅ 5단계: 기능 확인

### 웹 인터페이스에서 확인
1. 그라파나 대시보드 접속
2. 패널에 마우스를 올려 **패널 메뉴** 표시
3. **Export** → **Share link** 클릭
4. 오른쪽 창에서 **Image settings** 섹션 확인
5. **"Generate image"** 버튼 클릭하여 이미지 생성 테스트

### API로 직접 확인
```bash
# API 토큰 생성 후 테스트
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
"http://YOUR_SERVER:3000/render/d-solo/DASHBOARD_UID?panelId=PANEL_ID&width=1000&height=500" \
-o test.png

# 생성된 파일 확인
ls -lh test.png
file test.png
```

## 🎛️ 6단계: 추가 설정 (선택사항)

### 이미지 품질 설정
```ini
[rendering]
# 기본 이미지 크기 설정
default_image_width = 1000
default_image_height = 500
default_image_scale = 1

# 최대 크기 제한
viewport_max_width = 3000
viewport_max_height = 3000
```

### 메모리 사용량 최적화
```ini
[rendering]
# 렌더링 모드 설정 (기본값: default)
mode = clustered
clustering_mode = browser
clustering_max_concurrency = 5
clustering_timeout = 30
```

## 📊 PowerShell 자동 다운로드 스크립트

Windows에서 그라파나 이미지를 자동으로 다운로드하려면:

```powershell
# 기본 설정
$server = "YOUR_SERVER_IP:3000"
$token = "YOUR_API_TOKEN"
$headers = @{"Authorization" = "Bearer $token"}

# 이미지 다운로드
$url = "http://$server/render/d-solo/DASHBOARD_UID?panelId=PANEL_ID&width=1200&height=800&from=now-24h&to=now"
Invoke-WebRequest -Uri $url -Headers $headers -OutFile "panel.png"
```

## 🔧 문제 해결

### 일반적인 문제들

1. **Generate image 버튼이 보이지 않음**: 플러그인 미설치 또는 권한 문제
2. **"Failed to render panel image"**: callback_url 설정 오류
3. **ERR_CONNECTION_REFUSED**: 네트워크 설정 또는 방화벽 문제
4. **Chrome 실행 오류**: 시스템 의존성 미설치

### 로그 확인 방법
```bash
# 렌더링 관련 로그 확인
sudo grep -i "render\|plugin" /var/log/grafana/grafana.log | tail -20

# 실시간 로그 모니터링
sudo tail -f /var/log/grafana/grafana.log | grep -i render
```

## 🎯 완료 확인 사항

- ✅ 패널 → Export → Share link → Generate image 버튼 표시
- ✅ 이미지 생성 및 다운로드 성공
- ✅ PNG 파일 정상 생성 (크기 50KB 이상)
- ✅ 플러그인 프로세스 실행 중
