import os
import json
import base64
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def load_config():
    config_path = Path("config/report_config.json")
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"설정 파일 읽기 실패: {e}")
        return None

def find_latest_images_folder():
    images_dir = Path("images")
    if not images_dir.exists():
        return None
    
    timestamp_folders = [d for d in images_dir.iterdir() if d.is_dir()]
    if not timestamp_folders:
        return None
    
    return max(timestamp_folders, key=lambda x: x.stat().st_mtime)

def categorize_chart(filename):
    """파일명으로 카테고리 자동 분류"""
    filename_lower = filename.lower()
    
    if 'total' in filename_lower:
        return '종합 현황'
    elif any(x in filename_lower for x in ['cpu', 'memory']):
        return '시스템 리소스'
    elif 'disk' in filename_lower:
        return '스토리지'
    elif 'network' in filename_lower:
        return '네트워크'
    else:
        return '기타'

def get_chart_name(filename):
    """파일명에서 차트 이름 추출"""
    name = filename.replace('.png', '').replace('_', ' ')
    # 파일명 끝의 숫자 제거 (예: "Cpu Usage 2" -> "Cpu Usage")
    parts = name.split()
    if parts and parts[-1].isdigit():
        parts = parts[:-1]
    return ' '.join(parts).title()

def collect_dashboard_data(images_folder):
    """대시보드별 데이터 수집"""
    dashboards_data = {}
    
    production_folder = images_folder / "Production-Server"
    if not production_folder.exists():
        return dashboards_data
    
    for dashboard_folder in production_folder.iterdir():
        if not dashboard_folder.is_dir():
            continue
        
        dashboard_name = dashboard_folder.name
        chart_files = list(dashboard_folder.glob("*.png"))
        
        # 카테고리별로 분류
        categorized_charts = defaultdict(list)
        
        for chart_file in chart_files:
            category = categorize_chart(chart_file.name)
            chart_name = get_chart_name(chart_file.name)
            
            categorized_charts[category].append({
                'name': chart_name,
                'file_path': chart_file,
                'filename': chart_file.name
            })
        
        # 카테고리별 정렬
        for category in categorized_charts:
            categorized_charts[category].sort(key=lambda x: x['name'])
        
        dashboards_data[dashboard_name] = {
            'charts': dict(categorized_charts),
            'total_charts': len(chart_files)
        }
    
    return dashboards_data

def image_to_base64(image_path):
    """이미지를 base64로 변환"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        logging.warning(f"이미지 변환 실패 {image_path}: {e}")
        return ""

def generate_chart_sections(charts_data):
    """차트 섹션 HTML 생성"""
    sections_html = ""
    
    # 카테고리 순서 정의
    category_order = ['시스템 리소스', '스토리지', '네트워크', '종합 현황', '기타']
    
    for category in category_order:
        if category not in charts_data or not charts_data[category]:
            continue
        
        charts = charts_data[category]
        charts_html = ""
        
        for chart in charts:
            img_base64 = image_to_base64(chart['file_path'])
            if img_base64:
                charts_html += f"""
                <div class="chart-card">
                    <div class="chart-header">
                        <div class="chart-title">{chart['name']}</div>
                        <div class="chart-description">시스템 성능 모니터링 지표</div>
                    </div>
                    <div class="chart-image-container">
                        <img src="data:image/png;base64,{img_base64}" 
                             alt="{chart['name']}" 
                             class="chart-image"
                             onclick="this.style.transform = this.style.transform ? '' : 'scale(1.5)'"
                             title="클릭하여 확대/축소">
                        <div class="zoom-indicator">+</div>
                    </div>
                </div>
                """
        
        if charts_html:
            sections_html += f"""
            <div class="category-section">
                <div class="category-header">
                    <div class="category-title">{category}</div>
                    <div class="category-description">{category} 관련 모니터링 지표</div>
                    <div class="category-badge">{len(charts)}개 항목</div>
                </div>
                <div class="charts-grid">
                    {charts_html}
                </div>
            </div>
            """
    
    return sections_html

def get_sample_metrics():
    """샘플 메트릭 값 (실제로는 차트에서 추출)"""
    return {
        'cpu_current': '2.4%',
        'memory_current': '7.75GB'
    }

def create_dashboard_html(dashboard_name, dashboard_data, config):
    """대시보드 HTML 생성"""
    
    # HTML 템플릿 로드
    template_path = Path("templates/dashboard.html")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except Exception as e:
        logging.error(f"템플릿 파일 읽기 실패: {e}")
        return None
    
    # 차트 섹션 생성
    chart_sections = generate_chart_sections(dashboard_data['charts'])
    
    # 메트릭 값 가져오기
    metrics = get_sample_metrics()
    
    # 템플릿 변수 치환
    html_content = template.replace('{{dashboard_name}}', dashboard_name)
    html_content = html_content.replace('{{report_month}}', config['report_month'])
    html_content = html_content.replace('{{period}}', config['period'])
    html_content = html_content.replace('{{generation_time}}', datetime.now().strftime('%Y-%m-%d %H:%M'))
    html_content = html_content.replace('{{total_charts}}', str(dashboard_data['total_charts']))
    html_content = html_content.replace('{{category_count}}', str(len(dashboard_data['charts'])))
    html_content = html_content.replace('{{cpu_current}}', metrics['cpu_current'])
    html_content = html_content.replace('{{memory_current}}', metrics['memory_current'])
    html_content = html_content.replace('{{chart_sections}}', chart_sections)
    html_content = html_content.replace('{{full_generation_time}}', datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S'))
    
    return html_content

def create_reports():
    """메인 리포트 생성 함수"""
    setup_logging()
    logging.info("=== 대시보드별 리포트 생성 시작 ===")
    
    # 설정 로드
    config = load_config()
    if not config:
        return False
    
    # 최신 이미지 폴더 찾기
    images_folder = find_latest_images_folder()
    if not images_folder:
        logging.error("이미지 폴더를 찾을 수 없습니다.")
        return False
    
    # 대시보드 데이터 수집
    dashboards_data = collect_dashboard_data(images_folder)
    if not dashboards_data:
        logging.error("대시보드 데이터를 찾을 수 없습니다.")
        return False
    
    # 출력 폴더 설정
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # CSS 파일 복사
    css_source = Path("templates/assets/style.css")
    css_dest = output_dir / "assets"
    css_dest.mkdir(exist_ok=True)
    
    if css_source.exists():
        import shutil
        shutil.copy2(css_source, css_dest / "style.css")
    
    # 각 대시보드별 HTML 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for dashboard_name, dashboard_data in dashboards_data.items():
        logging.info(f"리포트 생성 중: {dashboard_name}")
        
        # HTML 내용 생성
        html_content = create_dashboard_html(dashboard_name, dashboard_data, config)
        if not html_content:
            continue
        
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