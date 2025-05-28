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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def load_config():
    """기본 설정 로드"""
    config_path = Path("config/report_config.json")
    if not config_path.exists():
        logging.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
            logging.info("기본 설정 파일 로드 완료")
            return config
    except Exception as e:
        logging.error(f"설정 파일 읽기 실패: {e}")
        return None

def load_dashboard_config():
    """대시보드 설정 로드"""
    config_path = Path("config/dashboard_config.json")
    if not config_path.exists():
        logging.warning("대시보드 설정 파일이 없습니다. 기본 설정을 사용합니다.")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info("대시보드 설정 파일 로드 완료")
            return config
    except Exception as e:
        logging.error(f"대시보드 설정 파일 읽기 실패: {e}")
        return None

def load_server_info():
    """서버 정보 설정 로드"""
    config_path = Path("config/server_info.json")
    if not config_path.exists():
        logging.warning("서버 정보 설정 파일이 없습니다. 기본 정보를 사용합니다.")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info("서버 정보 설정 파일 로드 완료")
            return config
    except Exception as e:
        logging.error(f"서버 정보 설정 파일 읽기 실패: {e}")
        return None

def find_latest_images_folder():
    """최신 이미지 폴더 찾기"""
    images_dir = Path("images")
    if not images_dir.exists():
        logging.error("images 폴더를 찾을 수 없습니다.")
        return None
    
    timestamp_folders = [d for d in images_dir.iterdir() if d.is_dir()]
    if not timestamp_folders:
        logging.error("이미지 폴더에서 다운로드된 데이터를 찾을 수 없습니다.")
        return None
    
    latest_folder = max(timestamp_folders, key=lambda x: x.stat().st_mtime)
    logging.info(f"사용할 이미지 폴더: {latest_folder}")
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
    """파일명을 기반으로 차트 카테고리 분류 (total과 system 제외)"""
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
        logging.error("Production-Server 폴더를 찾을 수 없습니다.")
        return dashboards_data
    
    # 각 대시보드 폴더 처리
    for dashboard_folder in production_folder.iterdir():
        if not dashboard_folder.is_dir():
            continue
        
        dashboard_name = dashboard_folder.name
        logging.info(f"대시보드 처리 중: {dashboard_name}")
        
        # 대시보드 정보 가져오기
        dashboard_info = {}
        if dashboard_config and dashboard_name in dashboard_config.get('dashboards', {}):
            dashboard_info = dashboard_config['dashboards'][dashboard_name]
        
        # 차트 파일들 수집
        chart_files = list(dashboard_folder.glob("*.png"))
        
        # 카테고리별로 분류 (total과 system 제외)
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
    
    return dashboards_data

def create_dashboard_html(dashboard_name, dashboard_data, config, dashboard_config, server_info):
    """개별 대시보드 HTML 생성"""
    
    dashboard_info = dashboard_data['info']
    display_name = dashboard_info.get('display_name', dashboard_name)
    description = dashboard_info.get('description', f'{dashboard_name} 시스템 모니터링')
    
    # 서버 정보 동적으로 가져오기
    server_details = {}
    if server_info and 'Production-Server' in server_info.get('servers', {}):
        server_details = server_info['servers']['Production-Server']
        logging.info("서버 정보를 JSON에서 동적으로 로드했습니다.")
    else:
        logging.warning("서버 정보 JSON을 찾을 수 없어 기본값을 사용합니다.")
    
    # 서버 정보 (JSON에서 동적으로 가져옴)
    server_display_name = server_details.get('display_name', 'Production Server')
    hostname = server_details.get('hostname', 'server-01')
    os_info = server_details.get('os', 'ubuntu-20.04')
    cpu_mem = server_details.get('cpu_mem', '4vCPU / 16GB Mem')
    disk_info = server_details.get('disk', '100 GB / 500 GB')
    availability = server_details.get('availability', '99.9%')
    
    # 알림 정보 (JSON에서 동적으로 가져옴)
    summary = server_details.get('summary', {})
    total_alerts = summary.get('total_alerts', {'value': 0, 'label': '전체'})
    critical_alerts = summary.get('critical_alerts', {'value': 0, 'label': '긴급'})
    warning_alerts = summary.get('warning_alerts', {'value': 0, 'label': '경고'})
    top5_note = summary.get('top5_note', '측정된 알림이 없습니다.')
    
    # 이미지를 base64로 변환
    def image_to_base64(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except Exception as e:
            logging.warning(f"이미지 변환 실패 {image_path}: {e}")
            return ""
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name} - {config['report_month']}</title>
    <style>
        {get_css_content()}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1>{display_name}</h1>
            <div class="report-subtitle">{description}</div>
            <div class="report-meta">
                <div class="meta-item">
                    <div class="meta-label">리포트 기간</div>
                    <div class="meta-value">{config['period']}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">리포트 유형</div>
                    <div class="meta-value">월간 종합 모니터링</div>
                </div>
            </div>
        </div>
        
        <!-- 서버 현황 섹션 -->
        <div class="summary-section">
            <div class="summary-header">
                <h2>📊 서버 현황</h2>
                <p>서버 상태 및 핵심 지표 요약</p>
            </div>
            
            <div class="server-info-grid">
                <div class="server-info-table">
                    <table>
                        <tr>
                            <th>그룹명</th>
                            <td>{server_display_name}</td>
                            <th>OS</th>
                            <td>{os_info}</td>
                        </tr>
                        <tr>
                            <th>장비명</th>
                            <td>{hostname}</td>
                            <th>DISK</th>
                            <td>{disk_info}</td>
                        </tr>
                        <tr>
                            <th>CPU/MEM</th>
                            <td>{cpu_mem}</td>
                            <th>가용률</th>
                            <td>{availability}</td>
                        </tr>
                        <tr>
                            <th>기간</th>
                            <td colspan="3">{config['period']}</td>
                        </tr>
                    </table>
                </div>
                
                <div class="alerts-section">
                    <div class="alerts-summary">
                        <h3>🚨 전체 이상현황</h3>
                        <div class="alert-counts">
                            <div class="alert-item">
                                <div class="alert-number">{total_alerts['value']}</div>
                                <div class="alert-label">{total_alerts['label']}</div>
                            </div>
                            <div class="alert-item">
                                <div class="alert-number">{critical_alerts['value']}</div>
                                <div class="alert-label">{critical_alerts['label']}</div>
                            </div>
                            <div class="alert-item">
                                <div class="alert-number">{warning_alerts['value']}</div>
                                <div class="alert-label">{warning_alerts['label']}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="top5-alerts">
                        <h4>주요 알림 Top5</h4>
                        <p>{top5_note}</p>
                    </div>
                </div>
            </div>
        </div>
"""
    
    # 차트 섹션들 생성 (system 카테고리 제외)
    category_order = ['시스템 리소스', '스토리지', '네트워크', '기타']
    category_descriptions = {
        '시스템 리소스': 'CPU, 메모리 사용률 현황',
        '스토리지': '저장 공간 사용량 및 I/O 성능',
        '네트워크': '네트워크 트래픽 및 연결 상태',
        '기타': '기타 모니터링 지표'
    }
    
    for category in category_order:
        if category not in dashboard_data['charts'] or not dashboard_data['charts'][category]:
            continue
        
        charts = dashboard_data['charts'][category]
        category_desc = category_descriptions.get(category, f'{category} 관련 모니터링 지표')
        
        html_content += f"""
        <div class="category-section">
            <div class="category-header">
                <div class="category-title">{category}</div>
                <div class="category-description">{category_desc}</div>
                <div class="category-badge">{len(charts)}개 항목</div>
            </div>
            <div class="charts-grid">
"""
        
        for chart in charts:
            img_base64 = image_to_base64(chart['file_path'])
            if img_base64:
                html_content += f"""
                <div class="chart-card">
                    <div class="chart-header">
                        <div class="chart-title">{chart['name']}</div>
                        <div class="chart-description">{chart['description']}</div>
                    </div>
                    <div class="chart-image-container">
                        <img src="data:image/png;base64,{img_base64}" 
                             alt="{chart['name']}" 
                             class="chart-image">
                    </div>
                </div>
"""
        
        html_content += """
            </div>
        </div>
"""
    
    # 푸터 추가
    html_content += f"""
        <div class="report-footer">
            <div class="footer-main">
                <div class="company-info">
                    <div class="company-name">으뜸정보기술</div>
                    <div class="company-details">
                        웹사이트: cloud.tbit.co.kr 
                    </div>
                </div>
                <div class="report-info">
                    <div class="report-version">Report Version 1.0</div>
                    <div class="security-level">보안등급: 내부용</div>
                </div>
            </div>
            <div class="copyright">
                © 2025 으뜸정보기술. All Rights Reserved.
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def get_css_content():
    """CSS 내용 반환"""
    css_file = Path("templates/assets/style.css")
    if css_file.exists():
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                base_css = f.read()
        except Exception as e:
            logging.warning(f"CSS 파일 읽기 실패: {e}")
            base_css = ""
    else:
        base_css = ""
    
    # 추가 CSS for 종합현황 섹션
    additional_css = """
    
    /* 종합현황 섹션 스타일 */
    .summary-section {
        background: var(--white);
        border-radius: 12px;
        margin-bottom: 3rem;
        overflow: hidden;
        box-shadow: var(--shadow-medium);
        border: 1px solid var(--border-color);
    }
    
    .summary-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, #1e3d72 100%);
        color: var(--white);
        padding: 2rem;
        text-align: center;
    }
    
    .summary-header h2 {
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
    }
    
    .server-info-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 2rem;
        padding: 2rem;
    }
    
    .server-info-table table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
    }
    
    .server-info-table th,
    .server-info-table td {
        padding: 0.75rem;
        border: 1px solid var(--border-color);
        text-align: left;
    }
    
    .server-info-table th {
        background: var(--light-bg);
        font-weight: 600;
        color: var(--text-primary);
        width: 100px;
    }
    
    .alerts-section {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    
    .alerts-summary h3 {
        color: var(--text-primary);
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
    
    .alert-counts {
        display: flex;
        gap: 1rem;
    }
    
    .alert-item {
        text-align: center;
        padding: 1rem;
        border-radius: 8px;
        background: var(--light-bg);
        flex: 1;
    }
    
    .alert-number {
        font-size: 2rem;
        font-weight: 700;
        color: var(--secondary-color);
        margin-bottom: 0.5rem;
    }
    
    .alert-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
    }
    
    .top5-alerts {
        padding: 1rem;
        background: var(--light-bg);
        border-radius: 8px;
    }
    
    .top5-alerts h4 {
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    .top5-alerts p {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin: 0;
    }
    
    @media (max-width: 768px) {
        .server-info-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .alert-counts {
            flex-direction: column;
        }
    }
    """
    
    return base_css + additional_css

def create_reports():
    """메인 리포트 생성 함수"""
    setup_logging()
    logging.info("=== 대시보드별 리포트 생성 시작 ===")
    
    # 설정 파일들 로드
    config = load_config()
    if not config:
        return False
    
    dashboard_config = load_dashboard_config()
    server_info = load_server_info()
    
    # 최신 이미지 폴더 찾기
    images_folder = find_latest_images_folder()
    if not images_folder:
        return False
    
    # 대시보드 데이터 수집
    dashboards_data = collect_dashboard_data(images_folder, dashboard_config)
    if not dashboards_data:
        logging.error("대시보드 데이터를 찾을 수 없습니다.")
        return False
    
    # 출력 폴더 설정
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 기존 파일들 정리
    for item in output_dir.iterdir():
        if item.is_file() and item.suffix == '.html':
            item.unlink()
    
    # 각 대시보드별 HTML 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for dashboard_name, dashboard_data in dashboards_data.items():
        logging.info(f"리포트 생성 중: {dashboard_name}")
        
        # HTML 내용 생성
        html_content = create_dashboard_html(dashboard_name, dashboard_data, config, dashboard_config, server_info)
        
        # 파일명 생성
        safe_name = dashboard_name.replace(' ', '-').replace('/', '-')
        filename = f"{safe_name}_{config['report_month'].replace('. ', '_')}_{timestamp}.html"
        output_path = output_dir / filename
        
        # HTML 파일 저장
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            file_size = output_path.stat().st_size / (1024 * 1024)
            logging.info(f"✅ {dashboard_name} 리포트 생성 완료: {output_path.name} ({file_size:.1f} MB)")
            
        except Exception as e:
            logging.error(f"❌ {dashboard_name} 리포트 생성 실패: {e}")
    
    logging.info("=== 모든 대시보드 리포트 생성 완료 ===")
    return True

def main():
    return create_reports()

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)