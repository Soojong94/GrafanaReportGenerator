import os
import json
import base64
import re
from pathlib import Path
from datetime import datetime
import logging
import shutil
from collections import defaultdict
import fnmatch

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def load_config():
    """기본 설정 로드 - 개선된 오류 처리"""
    config_path = Path("config/report_config.json")
    if not config_path.exists():
        logging.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        logging.error("먼저 update_month.ps1을 실행하여 설정을 생성하세요.")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
            logging.info("✅ 기본 설정 파일 로드 완료")
            return config
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON 문법 오류 in {config_path}: {e}")
        logging.error("💡 enhanced_config_validator.py를 실행하여 상세한 오류를 확인하세요.")
        return None
    except Exception as e:
        logging.error(f"❌ 설정 파일 읽기 실패: {e}")
        return None

def load_dashboard_config():
    """대시보드 설정 로드 - 개선된 오류 처리"""
    config_path = Path("config/dashboard_config.json")
    if not config_path.exists():
        logging.warning("⚠️  대시보드 설정 파일이 없습니다. 기본 설정을 사용합니다.")
        logging.info("💡 더 나은 차트 분류를 위해 dashboard_config.json을 생성하는 것을 권장합니다.")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info("✅ 대시보드 설정 파일 로드 완료")
            return config
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON 문법 오류 in {config_path}: {e}")
        logging.error("💡 enhanced_config_validator.py를 실행하여 상세한 오류를 확인하세요.")
        return None
    except Exception as e:
        logging.error(f"❌ 대시보드 설정 파일 읽기 실패: {e}")
        return None

def load_server_info():
    """서버 정보 설정 로드 - 개선된 오류 처리"""
    config_path = Path("config/server_info.json")
    if not config_path.exists():
        logging.warning("⚠️  서버 정보 설정 파일이 없습니다. 기본 정보를 사용합니다.")
        logging.info("💡 서버 상세 정보 표시를 위해 server_info.json을 생성하는 것을 권장합니다.")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info("✅ 서버 정보 설정 파일 로드 완료")
            return config
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON 문법 오류 in {config_path}: {e}")
        logging.error("💡 enhanced_config_validator.py를 실행하여 상세한 오류를 확인하세요.")
        return None
    except Exception as e:
        logging.error(f"❌ 서버 정보 설정 파일 읽기 실패: {e}")
        return None

def load_system_groups():
    """시스템 그룹 설정 로드 - 개선된 오류 처리"""
    config_path = Path("config/system_groups.json")
    if not config_path.exists():
        logging.error("❌ 시스템 그룹 설정 파일을 찾을 수 없습니다.")
        logging.error("💡 config/system_groups.json 파일을 생성해야 합니다.")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info("✅ 시스템 그룹 설정 파일 로드 완료")
            return config
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON 문법 오류 in {config_path}: {e}")
        logging.error("💡 enhanced_config_validator.py를 실행하여 상세한 오류를 확인하세요.")
        return None
    except Exception as e:
        logging.error(f"❌ 시스템 그룹 설정 파일 읽기 실패: {e}")
        return None

def find_latest_images_folder():
    """최신 이미지 폴더 찾기 - 개선된 안내 메시지"""
    images_dir = Path("images")
    if not images_dir.exists():
        logging.error("❌ images 폴더를 찾을 수 없습니다.")
        logging.error("💡 먼저 runall.bat을 실행하여 그라파나에서 이미지를 다운로드하세요.")
        return None
    
    timestamp_folders = [d for d in images_dir.iterdir() if d.is_dir()]
    if not timestamp_folders:
        logging.error("❌ 이미지 폴더에서 다운로드된 데이터를 찾을 수 없습니다.")
        logging.error("💡 다음 순서로 실행하세요:")
        logging.error("   1. powershell -File update_month.ps1 -Year 2025 -Month 5")
        logging.error("   2. runall.bat")
        return None
    
    latest_folder = max(timestamp_folders, key=lambda x: x.stat().st_mtime)
    
    # Production-Server 폴더 존재 확인
    production_folder = latest_folder / "Production-Server"
    if not production_folder.exists():
        logging.error(f"❌ Production-Server 폴더를 찾을 수 없습니다: {latest_folder}")
        logging.error("💡 그라파나 이미지 다운로드가 정상적으로 완료되었는지 확인하세요.")
        return None
        
    logging.info(f"✅ 실제 그라파나 이미지 폴더 사용: {latest_folder}")
    return latest_folder

def clean_chart_name(filename):
    """차트 이름에서 숫자 ID 제거 및 정리"""
    # 파일 확장자 제거
    name = filename.replace('.png', '')
    
    # 끝에 붙은 _숫자 패턴 제거 (예: _3, _6)
    name = re.sub(r'_\d+$', '', name)
    
    # 언더스코어를 공백으로 변경
    name = name.replace('_', ' ')
    
    # 각 단어의 첫 글자를 대문자로
    name = name.title()
    
    # 특수 케이스 처리
    name = name.replace('I O', 'I/O')
    name = name.replace('Cpu', 'CPU')
    name = name.replace('Ram', 'RAM')
    name = name.replace('Ssl', 'SSL')
    name = name.replace('Http', 'HTTP')
    name = name.replace('Tcp', 'TCP')
    name = name.replace('Udp', 'UDP')
    
    return name

def categorize_chart(filename, dashboard_config):
    """파일명을 기반으로 차트 카테고리 분류"""
    if not dashboard_config:
        return "기타", clean_chart_name(filename)
    
    filename_lower = filename.lower()
    
    # total과 system 관련 차트는 제외
    if 'total' in filename_lower or 'system' in filename_lower:
        return None, None
    
    for category_key, category_info in dashboard_config.get('chart_categories', {}).items():
        if category_key in filename_lower:
            return category_info['category'], clean_chart_name(filename)
    
    return "기타", clean_chart_name(filename)

def get_chart_description(filename, dashboard_config):
    """차트 파일명을 기반으로 적절한 설명 반환"""
    if not dashboard_config or 'chart_descriptions' not in dashboard_config:
        return "시스템 성능 및 리소스 사용량 추이"
    
    filename_lower = filename.lower()
    descriptions = dashboard_config['chart_descriptions']
    
    for key, description in descriptions.items():
        if key in filename_lower:
            return description
    
    return "시스템 성능 모니터링 지표"

def collect_dashboard_data(images_folder, dashboard_config):
    """대시보드별 데이터 수집"""
    dashboards_data = {}
    
    # Production-Server 폴더 찾기
    production_folder = images_folder / "Production-Server"
    if not production_folder.exists():
        logging.error("❌ Production-Server 폴더를 찾을 수 없습니다.")
        return dashboards_data
    
    # 각 대시보드 폴더 처리
    for dashboard_folder in production_folder.iterdir():
        if not dashboard_folder.is_dir():
            continue
        
        dashboard_name = dashboard_folder.name
        logging.info(f"📊 대시보드 처리 중: {dashboard_name}")
        
        # 대시보드 정보 가져오기
        dashboard_info = {}
        if dashboard_config and dashboard_name in dashboard_config.get('dashboards', {}):
            dashboard_info = dashboard_config['dashboards'][dashboard_name]
        
        # 차트 파일들 수집
        chart_files = list(dashboard_folder.glob("*.png"))
        logging.info(f"   📈 발견된 차트 파일: {len(chart_files)}개")
        
        # 카테고리별로 분류
        categorized_charts = defaultdict(list)
        
        for chart_file in chart_files:
            category, chart_name = categorize_chart(chart_file.name, dashboard_config)
            
            # total이나 system 관련 차트는 건너뛰기
            if category is None:
                continue
            
            chart_description = get_chart_description(chart_file.name, dashboard_config)
            
            chart_info = {
                'file_path': chart_file,
                'name': chart_name,
                'filename': chart_file.name,
                'description': chart_description
            }
            
            categorized_charts[category].append(chart_info)
        
        # 카테고리별 정렬
        for category in categorized_charts:
            categorized_charts[category].sort(key=lambda x: x['name'])
        
        dashboards_data[dashboard_name] = {
            'info': dashboard_info,
            'charts': dict(categorized_charts),
            'total_charts': len([f for f in chart_files if not any(x in f.name.lower() for x in ['total', 'system'])]),
            'folder_path': dashboard_folder
        }
        
        logging.info(f"   ✅ {dashboard_name} 처리 완료: {dashboards_data[dashboard_name]['total_charts']}개 차트")
    
    return dashboards_data

class TemplateEngine:
    """HTML 템플릿 엔진"""
    
    def __init__(self, templates_dir="templates"):
        self.templates_dir = Path(templates_dir)
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """모든 템플릿 파일 로드"""
        template_files = [
            'base.html',
            'server_section.html', 
            'chart_category.html',
            'chart_card.html'
        ]
        
        for template_file in template_files:
            template_path = self.templates_dir / template_file
            if template_path.exists():
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_name = template_file.replace('.html', '')
                        self.templates[template_name] = f.read()
                        logging.info(f"✅ 템플릿 로드: {template_file}")
                except Exception as e:
                    logging.error(f"❌ 템플릿 로드 실패 {template_file}: {e}")
            else:
                logging.error(f"❌ 템플릿 파일 없음: {template_file}")
                logging.error("💡 templates 폴더에 필요한 템플릿 파일들을 생성하세요.")
    
    def get_template(self, template_name):
        """템플릿 반환"""
        return self.templates.get(template_name, "")
    
    def load_css(self):
        """CSS 파일 로드"""
        css_path = self.templates_dir / "assets" / "style.css"
        if css_path.exists():
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    logging.info("✅ CSS 스타일 로드 완료")
                    return f.read()
            except Exception as e:
                logging.error(f"❌ CSS 로드 실패: {e}")
                return ""
        else:
            logging.error("❌ CSS 파일 없음: templates/assets/style.css")
            logging.error("💡 CSS 파일을 생성하여 스타일을 적용하세요.")
            return ""
    
    def render(self, template_name, data):
        """템플릿 렌더링"""
        template = self.templates.get(template_name, '')
        if not template:
            logging.error(f"❌ 템플릿을 찾을 수 없습니다: {template_name}")
            return ""
        
        result = template
        for key, value in data.items():
            placeholder = '{{' + key + '}}'
            result = result.replace(placeholder, str(value))
        
        return result

class ReportBuilder:
    """리포트 빌더 클래스"""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        
        # 설정 파일들 로드 (기존 방식 유지)
        self.config = load_config()
        self.server_info = load_server_info()
        self.dashboard_config = load_dashboard_config()
        self.system_groups = load_system_groups()
        
        # 카테고리 설명 매핑
        self.category_descriptions = {
            '시스템 리소스': 'CPU, 메모리 사용률 현황',
            '스토리지': '저장 공간 사용량 및 I/O 성능',
            '네트워크': '네트워크 트래픽 및 연결 상태',
            '모니터링': '모니터링 시스템 성능 지표',
            '애플리케이션': '애플리케이션 서비스 현황',
            '기타': '기타 모니터링 지표'
        }
    
    def image_to_base64(self, image_path):
        """이미지를 base64로 변환"""
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except Exception as e:
            logging.warning(f"⚠️  이미지 변환 실패 {image_path}: {e}")
            return ""
    
    def build_chart_card(self, chart_info):
        """차트 카드 HTML 생성"""
        img_base64 = self.image_to_base64(chart_info['file_path'])
        
        return self.template_engine.render('chart_card', {
            'CHART_TITLE': chart_info['name'],
            'CHART_DESC': chart_info['description'],
            'CHART_IMAGE': img_base64
        })
    
    def build_chart_category(self, category_name, charts):
        """차트 카테고리 섹션 생성"""
        if not charts:
            return ""
        
        # 모든 차트 카드 생성
        chart_cards_html = ""
        for chart in charts:
            chart_cards_html += self.build_chart_card(chart)
        
        category_desc = self.category_descriptions.get(category_name, f'{category_name} 관련 모니터링 지표')
        
        return self.template_engine.render('chart_category', {
            'CATEGORY_NAME': category_name,
            'CATEGORY_DESC': category_desc,
            'CHART_COUNT': len(charts),
            'CHART_CARDS': chart_cards_html
        })
    
    def get_server_info_with_mapping(self, server_name):
        """서버 정보 가져오기 (매핑 포함) - 개선된 버전"""
        server_details = {}
        
        if self.server_info:
            servers = self.server_info.get('servers', {})
            
            # 직접 매핑 확인
            if server_name in servers:
                server_details = servers[server_name]
                logging.info(f"✅ 서버 정보 직접 매핑: {server_name}")
            
            # 대시보드 설정에서 서버 매핑 확인
            elif self.dashboard_config and server_name in self.dashboard_config.get('dashboards', {}):
                mapped_servers = self.dashboard_config['dashboards'][server_name].get('servers', [])
                for mapped_server in mapped_servers:
                    if mapped_server in servers:
                        server_details = servers[mapped_server]
                        logging.info(f"✅ 서버 정보 매핑: {server_name} -> {mapped_server}")
                        break
        
        # 기본값 설정
        if not server_details:
            logging.warning(f"⚠️  서버 정보를 찾을 수 없어 기본값 사용: {server_name}")
            logging.info("💡 server_info.json에 서버 정보를 추가하면 더 자세한 정보를 표시할 수 있습니다.")
            server_details = {
                'display_name': f'{server_name} Server',
                'hostname': 'unknown',
                'os': 'unknown',
                'cpu_mem': 'unknown',
                'disk': 'unknown',
                'availability': 'unknown',
                'summary': {
                    'total_alerts': {'value': 0, 'label': '전체'},
                    'critical_alerts': {'value': 0, 'label': '긴급'},
                    'warning_alerts': {'value': 0, 'label': '경고'},
                    'top5_note': '정보 없음'
                }
            }
        
        return server_details
    
    def build_server_section(self, server_name, dashboard_data):
        """서버 섹션 HTML 생성"""
        # 서버 정보 가져오기 (개선된 매핑 로직)
        server_details = self.get_server_info_with_mapping(server_name)
        
        # 서버 정보 추출
        summary = server_details.get('summary', {})
        
        # 차트 카테고리들 생성
        categories_html = ""
        category_order = ['시스템 리소스', '스토리지', '네트워크', '모니터링', '애플리케이션', '기타']
        
        for category in category_order:
            if category in dashboard_data['charts'] and dashboard_data['charts'][category]:
                charts = dashboard_data['charts'][category]
                categories_html += self.build_chart_category(category, charts)
        
        # 서버 섹션 데이터 준비
        server_data = {
            'SERVER_NAME': server_details.get('display_name', server_name),
            'SERVER_DESC': f"{server_name} 시스템 모니터링",
            'SERVER_GROUP_NAME': server_details.get('display_name', server_name),
            'SERVER_HOSTNAME': server_details.get('hostname', 'unknown'),
            'SERVER_OS': server_details.get('os', 'unknown'),
            'SERVER_CPU_MEM': server_details.get('cpu_mem', 'unknown'),
            'SERVER_DISK': server_details.get('disk', 'unknown'),
            'SERVER_AVAILABILITY': server_details.get('availability', 'unknown'),
            'TOTAL_ALERTS': summary.get('total_alerts', {}).get('value', 0),
            'CRITICAL_ALERTS': summary.get('critical_alerts', {}).get('value', 0),
            'WARNING_ALERTS': summary.get('warning_alerts', {}).get('value', 0),
            'TOP5_NOTE': summary.get('top5_note', '정보 없음'),
            'CATEGORIES': categories_html
        }
        
        return self.template_engine.render('server_section', server_data)
    
    def build_report(self, group_name, group_info, dashboards_data):
        """전체 리포트 HTML 생성"""
        logging.info(f"📄 리포트 생성 중: {group_name}")
        
        if not self.config:
            logging.error("❌ 기본 설정이 없습니다.")
            return ""
        
        # 서버 섹션들 생성
        content = ""
        servers_in_group = group_info.get('servers', [])
        
        valid_servers = []
        for i, server_name in enumerate(servers_in_group):
            if server_name in dashboards_data:
                # 첫 번째가 아닌 서버는 구분선 추가
                if i > 0:
                    content += '<div class="server-separator"></div>'
                
                server_html = self.build_server_section(server_name, dashboards_data[server_name])
                content += server_html
                valid_servers.append(server_name)
                logging.info(f"   ✅ 서버 섹션 추가: {server_name}")
            else:
                logging.warning(f"   ⚠️  서버 데이터를 찾을 수 없습니다: {server_name}")
        
        if not valid_servers:
            logging.warning(f"⚠️  그룹 '{group_name}'에서 처리할 유효한 서버가 없습니다.")
            return ""
        
        # CSS 로드
        css_content = self.template_engine.load_css()
        
        # 기본 리포트 데이터 준비
        base_data = {
            'TITLE': f"{group_info['display_name']} - {self.config['report_month']}",
            'GROUP_NAME': group_info['display_name'],
            'GROUP_DESC': group_info['description'],
            'PERIOD': self.config['period'],
            'CSS': css_content,
            'CONTENT': content
        }
        
        # 최종 HTML 생성
        final_html = self.template_engine.render('base', base_data)
        
        logging.info(f"✅ 리포트 생성 완료: {group_name}")
        logging.info(f"   📋 헤더: {group_info['display_name']}")
        logging.info(f"   🖥️  포함 서버: {', '.join(valid_servers)}")
        
        return final_html

def get_next_version_filename(output_dir, base_filename):
    """중복되지 않는 버전 파일명 생성"""
    base_path = output_dir / base_filename
    
    # 파일이 존재하지 않으면 원본 파일명 반환
    if not base_path.exists():
        return base_filename
    
    # 파일명과 확장자 분리
    name_part = base_path.stem
    ext_part = base_path.suffix
   
   # 버전 번호 찾기
    version = 1
    while True:
       versioned_filename = f"{name_part}_v{version:03d}{ext_part}"
       versioned_path = output_dir / versioned_filename
       
       if not versioned_path.exists():
           return versioned_filename
       
       version += 1
       
       # 무한 루프 방지 (최대 999 버전까지)
       if version > 999:
           timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
           return f"{name_part}_{timestamp}{ext_part}"

def create_unified_report():
   """메인 리포트 생성 함수"""
   setup_logging()
   logging.info("🔍 === 템플릿 기반 통합 리포트 생성 시작 ===")
   
   # 기본 설정 확인
   config = load_config()
   if not config:
       logging.error("❌ 기본 설정을 로드할 수 없습니다.")
       logging.error("💡 먼저 다음을 확인하세요:")
       logging.error("   1. enhanced_config_validator.py 실행")
       logging.error("   2. update_month.ps1 실행")
       return False
   
   system_groups = load_system_groups()
   if not system_groups:
       logging.error("❌ 시스템 그룹 설정을 로드할 수 없습니다.")
       logging.error("💡 config/system_groups.json 파일을 생성하세요.")
       return False
   
   # 실제 이미지 폴더 확인
   images_folder = find_latest_images_folder()
   if not images_folder:
       logging.error("❌ 실제 그라파나 이미지 데이터가 필요합니다.")
       logging.error("💡 다음 명령어를 먼저 실행하세요:")
       logging.error("   1. powershell -File update_month.ps1 -Year 2025 -Month 5")
       logging.error("   2. runall.bat (또는 01_download_images.ps1)")
       return False
   
   # 대시보드 데이터 수집
   dashboard_config = load_dashboard_config()
   dashboards_data = collect_dashboard_data(images_folder, dashboard_config)
   
   if not dashboards_data:
       logging.error("❌ 대시보드 데이터를 수집할 수 없습니다.")
       logging.error("💡 그라파나 이미지가 정상적으로 다운로드되었는지 확인하세요.")
       return False
   
   logging.info(f"✅ 수집된 대시보드: {list(dashboards_data.keys())}")
   
   # 리포트 빌더 초기화
   try:
       builder = ReportBuilder()
   except Exception as e:
       logging.error(f"❌ 리포트 빌더 초기화 실패: {e}")
       logging.error("💡 템플릿 파일들이 모두 존재하는지 확인하세요.")
       return False
   
   # 출력 디렉토리 준비
   output_dir = Path("output")
   output_dir.mkdir(exist_ok=True)
   timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
   
   generated_reports = []
   
   # 각 그룹별 리포트 생성
   groups = system_groups.get('groups', {})
   active_groups = {name: info for name, info in groups.items() if info.get('active', True)}
   
   if not active_groups:
       logging.warning("⚠️  활성화된 그룹이 없습니다.")
       logging.info("💡 system_groups.json에서 최소 하나의 그룹을 활성화하세요.")
       return False
   
   logging.info(f"📊 처리할 활성 그룹: {list(active_groups.keys())}")
   
   for group_name, group_info in active_groups.items():
       logging.info(f"\n🔄 === 그룹 처리 시작: {group_name} ===")
       
       # HTML 생성
       html_content = builder.build_report(group_name, group_info, dashboards_data)
       
       if not html_content:
           logging.warning(f"⚠️  그룹 '{group_name}'의 HTML을 생성할 수 없습니다.")
           continue
       
       # 파일명 생성
       safe_group_name = group_name.replace(' ', '-').replace('/', '-')
       month_str = config['report_month'].replace('. ', '_')
       base_filename = f"{safe_group_name}_{month_str}_{timestamp}.html"
       
       # 중복되지 않는 파일명 생성
       final_filename = get_next_version_filename(output_dir, base_filename)
       output_path = output_dir / final_filename
       
       # 파일 저장
       try:
           with open(output_path, 'w', encoding='utf-8') as f:
               f.write(html_content)
           
           file_size = output_path.stat().st_size / (1024 * 1024)
           generated_reports.append(final_filename)
           
           if final_filename != base_filename:
               logging.info(f"✅ 리포트 생성 완료 (버전 생성): {final_filename} ({file_size:.1f} MB)")
           else:
               logging.info(f"✅ 리포트 생성 완료: {final_filename} ({file_size:.1f} MB)")
          
       except Exception as e:
           logging.error(f"❌ 리포트 생성 실패 ({group_name}): {e}")
   
   # 최종 결과 출력
   if generated_reports:
       logging.info(f"\n🎉 === 총 {len(generated_reports)}개 리포트 생성 완료 ===")
       for report in generated_reports:
           logging.info(f"   📄 {report}")
       
       logging.info(f"\n📂 결과 확인: output 폴더를 확인하세요.")
       logging.info(f"💡 브라우저에서 HTML 파일을 열어 리포트를 확인할 수 있습니다.")
       return True
   else:
       logging.error("❌ 생성된 리포트가 없습니다.")
       logging.error("💡 다음을 확인하세요:")
       logging.error("   1. 활성화된 그룹이 있는지")
       logging.error("   2. 그룹에 정의된 서버가 실제 이미지 폴더에 있는지")
       logging.error("   3. enhanced_config_validator.py로 설정 검증")
       return False

def main():
   """메인 실행 함수"""
   try:
       return create_unified_report()
   except KeyboardInterrupt:
       logging.info("\n⚠️  사용자에 의해 중단되었습니다.")
       return False
   except Exception as e:
       logging.error(f"❌ 예상치 못한 오류 발생: {e}")
       logging.error("💡 enhanced_config_validator.py를 실행하여 설정을 먼저 검증하세요.")
       return False

if __name__ == "__main__":
   import sys
   success = main()
   sys.exit(0 if success else 1)