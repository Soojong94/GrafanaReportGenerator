# 02_generate_report.py
import os
import json
import base64
from pathlib import Path
from datetime import datetime
import logging

def setup_logging():
    log_dir = Path("output")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'report_generation.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_config():
    config_path = Path("config/report_config.json")
    if not config_path.exists():
        logging.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
            logging.info("설정 파일 로드 완료")
            return config
    except Exception as e:
        logging.error(f"설정 파일 읽기 실패: {e}")
        return None

def find_latest_images_folder():
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

def collect_server_info(images_folder):
    servers_info = []
    
    for server_folder in images_folder.iterdir():
        if not server_folder.is_dir():
            continue
        
        total_images = len(list(server_folder.rglob("*.png")))
        dashboard_count = len([d for d in server_folder.iterdir() if d.is_dir()])
        
        server_info = {
            "name": server_folder.name,
            "dashboard_count": dashboard_count,
            "image_count": total_images,
            "image_files": []
        }
        
        # 이미지 파일 수집
        for dashboard_folder in server_folder.iterdir():
            if not dashboard_folder.is_dir():
                continue
                
            for img_file in dashboard_folder.glob("*.png"):
                server_info["image_files"].append({
                    "path": img_file,
                    "dashboard": dashboard_folder.name,
                    "panel": img_file.stem.replace('_', ' ').title()
                })
        
        servers_info.append(server_info)
        logging.info(f"서버 정보 수집 완료: {server_info['name']} ({total_images}개 이미지)")
    
    return servers_info

def create_pdf_report(config):
    setup_logging()
    logging.info("=== PDF 리포트 생성 시작 ===")
    
    # 이미지 폴더 찾기
    images_folder = find_latest_images_folder()
    if not images_folder:
        return False
    
    # 서버 정보 수집
    servers_info = collect_server_info(images_folder)
    if not servers_info:
        logging.error("서버 정보를 찾을 수 없습니다.")
        return False
    
    # 출력 폴더 생성
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 출력 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"서버모니터링리포트_{config['report_month'].replace('. ', '_')}_{timestamp}.pdf"
    output_path = output_dir / output_filename
    
    # PDF 생성
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        logging.info("PDF 생성 중...")
        
        # PDF 문서 생성
        doc = SimpleDocTemplate(str(output_path), pagesize=A4, 
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkgreen
        )
        
        # PDF 컨텐츠 리스트
        story = []
        
        # 각 서버별 페이지 생성
        for idx, server in enumerate(servers_info):
            if idx > 0:
                story.append(PageBreak())
            
            # 서버 제목
            story.append(Paragraph(f"📊 {server['name']} 서버 모니터링 리포트", title_style))
            
            # 기본 정보
            info_data = [
                ['리포트 기간', config['period']],
                ['생성 일시', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ['대시보드 수', f"{server['dashboard_count']}개"],
                ['차트 수', f"{server['image_count']}개"]
            ]
            
            info_table = Table(info_data, colWidths=[4*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # 차트 이미지들
            story.append(Paragraph("📈 모니터링 차트", heading_style))
            
            chart_count = 0
            for img_info in server["image_files"]:
                try:
                    # 이미지 크기 조정 (A4 페이지에 맞게)
                    img = Image(str(img_info["path"]), width=16*cm, height=12*cm)
                    
                    # 차트 제목
                    chart_title = f"{img_info['dashboard']} - {img_info['panel']}"
                    story.append(Paragraph(chart_title, heading_style))
                    story.append(img)
                    story.append(Spacer(1, 20))
                    
                    chart_count += 1
                    
                    # 페이지당 2개 차트로 제한
                    if chart_count % 2 == 0 and chart_count < len(server["image_files"]):
                        story.append(PageBreak())
                        
                except Exception as e:
                    logging.warning(f"이미지 처리 오류: {img_info['path']} - {e}")
                    continue
        
        # PDF 생성
        doc.build(story)
        
        file_size = output_path.stat().st_size / (1024 * 1024)
        logging.info(f"✅ PDF 생성 완료: {output_path} ({file_size:.1f} MB)")
        return True
        
    except ImportError:
        logging.error("❌ reportlab이 설치되지 않았습니다.")
        logging.error("설치 명령어: pip install reportlab")
        return False
    except Exception as e:
        logging.error(f"❌ PDF 생성 실패: {e}")
        return False

def main():
    config = load_config()
    if not config:
        return False
    
    return create_pdf_report(config)

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)