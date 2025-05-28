# 02_generate_report.py
import os
import json
import base64
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

def setup_logging():
    """로깅 설정"""
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
    """설정 파일 로드"""
    config_path = Path("config/report_config.json")
    
    if not config_path.exists():
        logging.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info("설정 파일 로드 완료")
            return config
    except Exception as e:
        logging.error(f"설정 파일 읽기 실패: {e}")
        return None

def find_latest_images_folder():
    """가장 최근 이미지 폴더 찾기"""
    images_dir = Path("images")
    
    if not images_dir.exists():
        logging.error("images 폴더를 찾을 수 없습니다. 먼저 이미지 다운로드를 실행하세요.")
        return None
    
    timestamp_folders = [d for d in images_dir.iterdir() if d.is_dir()]
    
    if not timestamp_folders:
        logging.error("이미지 폴더에서 다운로드된 데이터를 찾을 수 없습니다.")
        return None
    
    latest_folder = max(timestamp_folders, key=lambda x: x.stat().st_mtime)
    logging.info(f"사용할 이미지 폴더: {latest_folder}")
    
    return latest_folder

def collect_server_info(images_folder):
    """서버 정보 수집"""
    servers_info = []
    
    for server_folder in images_folder.iterdir():
        if not server_folder.is_dir():
            continue
        
        total_images = len(list(server_folder.rglob("*.png")))
        dashboard_count = len([d for d in server_folder.iterdir() if d.is_dir()])
        
        server_info = {
            "name": server_folder.name,
            "os": "ubuntu-20.04",
            "cpu_mem": "[Standard] 4vCPU / 16GB Mem",
            "disk": "50 GB / 200 GB",
            "ip": "211.188.65.42",
            "availability": "100%",
            "alert_total": 0,
            "alert_warning": 0,
            "alert_critical": 0,
            "dashboard_count": dashboard_count,
            "image_count": total_images,
            "dashboards": []
        }
        
        for dashboard_folder in server_folder.iterdir():
            if not dashboard_folder.is_dir():
                continue
            
            dashboard_info = {
                "name": dashboard_folder.name,
                "panels": list(dashboard_folder.glob("*.png"))
            }
            server_info["dashboards"].append(dashboard_info)
        
        servers_info.append(server_info)
        logging.info(f"서버 정보 수집 완료: {server_info['name']} ({total_images}개 이미지)")
    
    return servers_info

def generate_company_logo():
    """회사 로고 HTML 생성"""
    return '''
    <div class="company-logo">
        <div style="background: #e74c3c; color: white; padding: 10px 20px; font-weight: bold; border-radius: 5px;">
            TnT<br>
            <span style="font-size: 10pt;">모종정보시스템</span>
        </div>
    </div>
    '''

def generate_overall_summary(servers_info):
    """전체 이용현황 섹션 생성"""
    total_windows = sum(1 for s in servers_info if "windows" in s["os"].lower())
    total_linux = sum(1 for s in servers_info if "linux" in s["os"].lower() or "ubuntu" in s["os"].lower())
    total_other = len(servers_info) - total_windows - total_linux
    
    return f'''
    <div class="metrics-section">
        <h4>📊 전체 이용현황</h4>
        <div class="summary-grid">
            <div class="summary-box">
                <h3>운영장비</h3>
                <div style="font-size: 36pt; font-weight: bold; color: #3498db; margin: 20px 0;">
                    {len(servers_info)}대
                </div>
                <table style="width: 100%; text-align: left; margin-top: 20px; font-size: 10pt;">
                    <tr><td>Windows</td><td style="text-align: right;">{total_windows}대</td></tr>
                    <tr><td>Linux</td><td style="text-align: right;">{total_linux}대</td></tr>
                    <tr><td>기타</td><td style="text-align: right;">{total_other}대</td></tr>
                </table>
            </div>
            
            <div class="summary-box">
                <h3>알람 건수</h3>
                <div class="alert-stats">
                    <div><div class="number">0</div><div class="label">전체</div></div>
                    <div><div class="number">0</div><div class="label">경고</div></div>
                    <div><div class="number">0</div><div class="label">치명</div></div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="metrics-section">
        <h4>🔍 중요 알람 Top5</h4>
        <div style="text-align: center; padding: 40px; color: #7f8c8d; border: 1px solid #eee;">
            <div style="font-size: 48pt; margin-bottom: 20px;">0</div>
            <p>* 중요 알람 Top 5는 Disk Read/ Write 알람은 집계하지 않습니다.</p>
        </div>
    </div>
    '''

def generate_host_summary_table(servers_info):
    """호스트별 이용현황 테이블 생성"""
    rows = ""
    for server in servers_info:
        rows += f'''
        <tr>
            <td>{server["name"]}</td>
            <td>{server["cpu_mem"]}</td>
            <td>{server["ip"]}</td>
            <td>{server["alert_total"]}건</td>
            <td>{server["alert_warning"]}건</td>
            <td>{server["alert_critical"]}건</td>
        </tr>
        '''
    
    return f'''
    <div class="metrics-section">
        <h4>🖥️ 호스트별 이용현황</h4>
        <table class="host-summary-table">
            <thead>
                <tr>
                    <th>호스트명</th>
                    <th>장비사양</th>
                   <th>IP</th>
                   <th colspan="3">알람 건수</th>
               </tr>
               <tr>
                   <th></th>
                   <th></th>
                   <th></th>
                   <th>전체</th>
                   <th>경고</th>
                   <th>치명</th>
               </tr>
           </thead>
           <tbody>
               {rows}
           </tbody>
       </table>
   </div>
   '''

def generate_server_detail_pages(images_folder, servers_info, config):
   """서버별 상세 페이지 생성"""
   pages_html = ""
   
   for server in servers_info:
       server_folder = images_folder / server["name"]
       
       pages_html += f'''
       <div class="server-detail-page">
           <table class="server-info-table">
               <tr>
                   <td class="label">그룹명</td>
                   <td>{config["organization"]}</td>
                   <td class="label">OS</td>
                   <td>{server["os"]}</td>
               </tr>
               <tr>
                   <td class="label">장비명</td>
                   <td>{server["name"]}</td>
                   <td class="label">DISK</td>
                   <td>{server["disk"]}</td>
               </tr>
               <tr>
                   <td class="label">CPU/MEM</td>
                   <td>{server["cpu_mem"]}</td>
                   <td class="label">가용률</td>
                   <td>{server["availability"]}</td>
               </tr>
               <tr>
                   <td class="label">기간</td>
                   <td>{config["period"]}</td>
                   <td class="label">알람 건수</td>
                   <td>전체 {server["alert_total"]} / 경고 {server["alert_warning"]} / 치명 {server["alert_critical"]}</td>
               </tr>
           </table>
           
           <div class="metrics-section">
               <h4>📊 전체 이용현황</h4>
               <div class="summary-grid">
                   <div class="summary-box">
                       <h3>알람 건수</h3>
                       <div class="alert-stats">
                           <div><div class="number">{server["alert_total"]}</div><div class="label">전체</div></div>
                           <div><div class="number">{server["alert_warning"]}</div><div class="label">경고</div></div>
                           <div><div class="number">{server["alert_critical"]}</div><div class="label">치명</div></div>
                       </div>
                   </div>
                   
                   <div class="summary-box">
                       <h3>주요 알람 Top5</h3>
                       <div style="padding: 20px 0; color: #7f8c8d;">
                           측정된 알람이 없습니다.
                       </div>
                       <p style="font-size: 9pt; color: #666;">
                           * 중요 알람 Top 5는 Disk Read/ Write 알람은 집계하지 않습니다.
                       </p>
                   </div>
               </div>
           </div>
           
           <div class="metrics-section">
               <h4>🚨 알람 상세 내역</h4>
               <table class="alert-detail-table">
                   <thead>
                       <tr>
                           <th>구분</th>
                           <th>알람 개수</th>
                           <th>구분</th>
                           <th>알람 개수</th>
                       </tr>
                   </thead>
                   <tbody>
                       <tr><td>CPU</td><td>0개</td><td>Process</td><td>0개</td></tr>
                       <tr><td>Memory</td><td>0개</td><td>Logfile</td><td>0개</td></tr>
                       <tr><td>SWAP</td><td>0개</td><td>Port</td><td>0개</td></tr>
                       <tr><td>Network</td><td>0개</td><td>Ping</td><td>0개</td></tr>
                       <tr><td>URL</td><td>0개</td><td>Agent</td><td>0개</td></tr>
                       <tr><td>DISK</td><td>0개</td><td></td><td></td></tr>
                   </tbody>
               </table>
           </div>
           
           <div class="metrics-section">
               <h4>📈 측정 결과</h4>
               <div class="charts-grid">
                   {generate_chart_panels(server_folder)}
               </div>
           </div>
       </div>
       '''
   
   return pages_html

def generate_chart_panels(server_folder):
   """차트 패널들 생성"""
   charts_html = ""
   chart_count = 0
   
   for dashboard_folder in server_folder.iterdir():
       if not dashboard_folder.is_dir():
           continue
           
       for img_file in dashboard_folder.glob("*.png"):
           if chart_count >= 4:  # 한 페이지에 4개까지
               break
               
           try:
               with open(img_file, "rb") as f:
                   img_data = base64.b64encode(f.read()).decode()
               
               panel_name = img_file.stem.replace('_', ' ').title()
               charts_html += f'''
               <div class="chart-container">
                   <h5>{panel_name}</h5>
                   <img src="data:image/png;base64,{img_data}" alt="{panel_name}">
               </div>
               '''
               chart_count += 1
           except Exception as e:
               logging.warning(f"이미지 처리 오류: {img_file.name} - {e}")
   
   return charts_html

def generate_storage_pages(servers_info):
   """스토리지 상세 페이지 생성"""
   pages_html = ""
   
   for server in servers_info:
       df_output = f"""ncloud@{server["name"]}:~$ df -h
Filesystem      Size  Used Avail Use% Mounted on
udev            7.8G     0  7.8G   0% /dev
tmpfs           1.6G  1.1M  1.6G   1% /run
/dev/xvda1       49G   24G   23G  51% /
tmpfs           7.9G     0  7.9G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           7.9G     0  7.9G   0% /sys/fs/cgroup
/dev/xvdb1       19G   21G   16G  11% /home
tmpfs           1.6G     0  1.6G   0% /run/user/11000
ncloud@{server["name"]}:~$ free -h
             total        used        free      shared  buff/cache   available
Mem:           15Gi        2.0Gi       194Mi       1.0Mi        13Gi        13Gi
Swap:            0B          0B          0B
ncloud@{server["name"]}:~$ """
       
       pages_html += f'''
       <div class="storage-section">
           <h4>🗄️ {server["name"]} 스토리지 이용 현황</h4>
           <div class="terminal-output">{df_output}</div>
       </div>
       '''
   
   return pages_html

def generate_html_content(config, servers_info, images_folder):
   """HTML 내용 생성"""
   html_content = f"""
   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="UTF-8">
       <title>서버 모니터링 월간보고서</title>
       <style>
           @page {{ margin: 2cm; size: A4; }}
           
           body {{ 
               font-family: 'Malgun Gothic', Arial, sans-serif; 
               font-size: 11pt; 
               line-height: 1.4;
               margin: 0;
               color: #333;
           }}
           
           .cover-page {{ 
               text-align: center; 
               padding: 120px 0;
               page-break-after: always;
               position: relative;
               height: 100vh;
           }}
           
           .cover-page h1 {{ 
               font-size: 28pt; 
               font-weight: bold;
               margin: 80px 0 30px 0;
               color: #2c3e50;
           }}
           
           .cover-page h2 {{ 
               font-size: 20pt; 
               margin: 30px 0;
               color: #34495e;
           }}
           
           .cover-page h3 {{ 
               font-size: 18pt; 
               margin: 20px 0;
               color: #7f8c8d;
           }}
           
           .company-logo {{ 
               position: absolute; 
               top: 30px; 
               right: 30px;
               width: 120px;
               height: auto;
           }}
           
           .summary-page {{ 
               page-break-before: always;
               padding: 20px 0;
           }}
           
           .summary-note {{ 
               font-size: 10pt;
               color: #666;
               margin-bottom: 20px;
           }}
           
           .summary-grid {{ 
               display: grid;
               grid-template-columns: 1fr 1fr;
               gap: 30px;
               margin: 30px 0;
           }}
           
           .summary-box {{ 
               border: 1px solid #ddd;
               padding: 20px;
               text-align: center;
           }}
           
           .summary-box h3 {{ 
               margin: 0 0 15px 0;
               font-size: 14pt;
               color: #2c3e50;
           }}
           
           .alert-stats {{ 
               display: flex;
               justify-content: space-around;
               margin: 15px 0;
           }}
           
           .alert-stats div {{ 
               text-align: center;
           }}
           
           .alert-stats .number {{ 
               font-size: 24pt;
               font-weight: bold;
               color: #e74c3c;
           }}
           
           .alert-stats .label {{ 
               font-size: 10pt;
               color: #666;
           }}
           
           .server-detail-page {{ 
               page-break-before: always;
               padding: 20px 0;
           }}
           
           .server-info-table {{ 
               width: 100%;
               border-collapse: collapse;
               margin: 20px 0;
               font-size: 10pt;
           }}
           
           .server-info-table td {{ 
               padding: 8px 12px;
               border: 1px solid #ddd;
           }}
           
           .server-info-table .label {{ 
               background: #f8f9fa;
               font-weight: bold;
               width: 120px;
           }}
           
           .metrics-section {{ 
               margin: 30px 0;
           }}
           
           .metrics-section h4 {{ 
               font-size: 14pt;
               margin: 20px 0 10px 0;
               color: #2c3e50;
               border-bottom: 2px solid #3498db;
               padding-bottom: 5px;
           }}
           
           .alert-detail-table {{ 
               width: 100%;
               border-collapse: collapse;
               margin: 15px 0;
               font-size: 10pt;
           }}
           
           .alert-detail-table th, .alert-detail-table td {{ 
               padding: 8px 12px;
               border: 1px solid #ddd;
               text-align: center;
           }}
           
           .alert-detail-table th {{ 
               background: #f8f9fa;
               font-weight: bold;
           }}
           
           .charts-grid {{ 
               display: grid;
               grid-template-columns: 1fr 1fr;
               gap: 20px;
               margin: 20px 0;
           }}
           
           .chart-container {{ 
               text-align: center;
               page-break-inside: avoid;
               border: 1px solid #eee;
               padding: 10px;
           }}
           
           .chart-container h5 {{ 
               margin: 0 0 10px 0;
               font-size: 11pt;
               color: #34495e;
           }}
           
           .chart-container img {{ 
               max-width: 100%;
               height: auto;
           }}
           
           .storage-section {{ 
               page-break-before: always;
               padding: 20px 0;
           }}
           
           .terminal-output {{ 
               background: #2c3e50;
               color: #ecf0f1;
               padding: 20px;
               font-family: 'Courier New', monospace;
               font-size: 9pt;
               white-space: pre-wrap;
               border-radius: 5px;
               overflow-x: auto;
           }}
           
           .host-summary-table {{ 
               width: 100%;
               border-collapse: collapse;
               margin: 20px 0;
               font-size: 10pt;
           }}
           
           .host-summary-table th, .host-summary-table td {{ 
               padding: 10px 12px;
               border: 1px solid #ddd;
               text-align: center;
           }}
           
           .host-summary-table th {{ 
               background: #f8f9fa;
               font-weight: bold;
           }}
       </style>
   </head>
   <body>
       <!-- 표지 페이지 -->
       <div class="cover-page">
           {generate_company_logo() if config.get("company_logo", True) else ""}
           <h1>서버 모니터링 월간보고서</h1>
           <h2>[ {config["organization"]} ]</h2>
           <h3>{config["report_month"]}</h3>
       </div>
       
       <!-- 요약 페이지 -->
       <div class="summary-page">
           <div class="summary-note">
               * 중요 알람 Top 5는 Disk Read/ Write 알람은 집계하지 않습니다.
           </div>
           
           <div class="summary-grid">
               <div class="summary-box">
                   <h3>운영장비 알람 건수</h3>
                   <div class="alert-stats">
                       <div><div class="number">0</div><div class="label">전체</div></div>
                       <div><div class="number">0</div><div class="label">경고</div></div>
                       <div><div class="number">0</div><div class="label">치명</div></div>
                   </div>
                   <div style="margin-top: 20px; font-size: 14pt; font-weight: bold;">
                       {len(servers_info)}대
                   </div>
               </div>
               
               <div class="summary-box">
                   <h3>중요 알람 Top5</h3>
                   <div style="padding: 40px 0; color: #7f8c8d;">
                       측정된 알람이 없습니다.
                   </div>
               </div>
           </div>
           
           <div style="margin-top: 40px;">
               <table class="server-info-table">
                   <tr>
                       <td class="label">그룹명</td>
                       <td>{config["organization"]}</td>
                       <td class="label">기간</td>
                       <td>{config["period"]}</td>
                   </tr>
               </table>
           </div>
           
           <!-- 전체 이용현황 -->
           {generate_overall_summary(servers_info)}
           
           <!-- 호스트별 이용현황 -->
           {generate_host_summary_table(servers_info)}
       </div>
       
       <!-- 서버별 상세 페이지 -->
       {generate_server_detail_pages(images_folder, servers_info, config)}
       
       <!-- 스토리지 상세 페이지 -->
       {generate_storage_pages(servers_info)}
   </body>
   </html>
   """
   
   return html_content

def create_grafana_report_pdf(config):
   """PDF 리포트 생성 메인 함수"""
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
   org_name = config['organization'].replace(' ', '').replace('/', '_')
   output_filename = f"서버모니터링월간보고서_{org_name}_{config['report_month'].replace('. ', '_')}_{timestamp}.pdf"
   output_path = output_dir / output_filename
   
   # HTML 생성
   html_content = generate_html_content(config, servers_info, images_folder)
   
   # PDF 생성
   try:
       from weasyprint import HTML, CSS
       
       logging.info("PDF 생성 중...")
       HTML(string=html_content).write_pdf(
           str(output_path),
           stylesheets=[CSS(string="""
               @page { 
                   margin: 2cm; 
                   size: A4;
               }
           """)]
       )
       
       file_size = output_path.stat().st_size / (1024 * 1024)  # MB
       logging.info(f"✅ PDF 생성 완료: {output_path} ({file_size:.1f} MB)")
       return True
       
   except ImportError:
       logging.error("❌ weasyprint가 설치되지 않았습니다.")
       logging.error("설치 명령어: pip install weasyprint")
       return False
   except Exception as e:
       logging.error(f"❌ PDF 생성 실패: {e}")
       return False

def main():
   """메인 실행 함수"""
   # 환경변수 로드
   load_dotenv()
   
   config = load_config()
   if not config:
       return False
   
   success = create_grafana_report_pdf(config)
   return success

if __name__ == "__main__":
   import sys
   success = main()
   sys.exit(0 if success else 1)