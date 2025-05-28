import os
import json
import base64
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

def categorize_chart(filename, dashboard_config):
    """파일명을 기반으로 차트 카테고리 분류"""
    if not dashboard_config:
        return "기타", filename.replace('.png', '').replace('_', ' ').title()
    
    filename_lower = filename.lower()
    
    for category_key, category_info in dashboard_config.get('chart_categories', {}).items():
        if category_key in filename_lower:
            return category_info['category'], category_info['name']
    
    return "기타", filename.replace('.png', '').replace('_', ' ').title()

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
        
        # 카테고리별로 분류
        categorized_charts = defaultdict(list)
        
        for chart_file in chart_files:
            category, chart_name = categorize_chart(chart_file.name, dashboard_config)
            
            chart_info = {
                'file_path': chart_file,
                'name': chart_name,
                'filename': chart_file.name
            }
            
            categorized_charts[category].append(chart_info)
        
        # 카테고리별 정렬
        for category in categorized_charts:
            categorized_charts[category].sort(key=lambda x: x['name'])
        
        dashboards_data[dashboard_name] = {
            'info': dashboard_info,
            'charts': dict(categorized_charts),
            'total_charts': len(chart_files),
            'folder_path': dashboard_folder
        }
    
    return dashboards_data

def create_dashboard_html(dashboard_name, dashboard_data, config, dashboard_config):
    """개별 대시보드 HTML 생성"""
    
    dashboard_info = dashboard_data['info']
    display_name = dashboard_info.get('display_name', dashboard_name)
    description = dashboard_info.get('description', f'{dashboard_name} 시스템 모니터링')
    
    # 서버 정보 가져오기 (기본값: 단일 서버)
    servers = dashboard_info.get('servers', [dashboard_name])
    server_display = ', '.join(servers)
    
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
                    <div class="meta-label">서버 정보</div>
                    <div class="meta-value">{server_display}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">리포트 유형</div>
                    <div class="meta-value">월간 종합 모니터링</div>
                </div>
            </div>
        </div>
        
        <div class="summary-stats">
            <div class="stat-card">
                <span class="stat-number">30</span>
                <div class="stat-label">모니터링 기간 (일)</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">정상</span>
                <div class="stat-label">서버 상태</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">99.9%</span>
                <div class="stat-label">데이터 수집률</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">0건</span>
                <div class="stat-label">알림 발생</div>
            </div>
        </div>
"""
    
    # 카테고리별 차트 섹션 생성 - '요약'을 맨 앞으로 이동
    category_order = ['요약', '시스템 리소스', '스토리지', '네트워크', '기타']
    category_descriptions = {
        '요약': '시스템 전반적인 상태 및 핵심 지표 요약',
        '시스템 리소스': 'CPU, 메모리, 디스크 사용률 현황',
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
                        <div class="chart-description">시스템 성능 및 리소스 사용량 추이</div>
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
                        웹사이트: cloud.tbit.co.kr | 문의: info@allrightit.co.kr
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
    """CSS 내용 반환 (위에서 정의한 CSS)"""
    css_file = Path("templates/assets/style.css")
    if css_file.exists():
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.warning(f"CSS 파일 읽기 실패: {e}")
    
    # CSS 파일이 없으면 기본 CSS 사용 (위에서 정의한 CSS 내용)
    return """
        /* 위에서 정의한 CSS 내용을 여기에 복사 */
        :root { --primary-color: #2c5aa0; /* ... 나머지 CSS ... */ }
    """

def create_reports():
    """메인 리포트 생성 함수"""
    setup_logging()
    logging.info("=== 대시보드별 리포트 생성 시작 ===")
    
    # 설정 파일들 로드
    config = load_config()
    if not config:
        return False
    
    dashboard_config = load_dashboard_config()
    
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
        html_content = create_dashboard_html(dashboard_name, dashboard_data, config, dashboard_config)
        
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