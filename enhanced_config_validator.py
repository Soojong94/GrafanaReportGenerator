# enhanced_config_validator.py - 통합 설정 기반 버전
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

class ConfigError:
    def __init__(self, file_path: str, error_type: str, message: str, 
                 line_number: int = None, solution: str = None, example: str = None):
        self.file_path = file_path
        self.error_type = error_type
        self.message = message
        self.line_number = line_number
        self.solution = solution
        self.example = example
        self.timestamp = datetime.now()

class UnifiedConfigValidator:
    def __init__(self):
        self.errors: List[ConfigError] = []
        self.warnings: List[ConfigError] = []
        self.config = None
        
    def validate_all(self) -> bool:
        """전체 검증 실행"""
        print("🔍 === 통합 설정 파일 검증 시작 ===")
        print(f"검증 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1단계: 통합 설정 파일 존재 및 문법 검증
        if not self._load_unified_config():
            self._print_detailed_report()
            return False
        
        # 2단계: 스키마 검증  
        self._validate_schema()
        
        # 3단계: 데이터 일관성 검증
        self._validate_consistency()
        
        # 4단계: 비즈니스 로직 검증
        self._validate_business_logic()
        
        # 결과 리포트 출력
        self._print_detailed_report()
        
        return len(self.errors) == 0
    
    def _load_unified_config(self) -> bool:
        """통합 설정 파일 로드 및 기본 검증"""
        print("📋 1단계: 통합 설정 파일 검증")
        
        config_path = Path("config/unified_config.json")
        
        if not config_path.exists():
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="FILE_MISSING",
                message="통합 설정 파일이 없습니다",
                solution="config/unified_config_example.json을 복사하여 unified_config.json로 이름을 변경하세요",
                example="copy config\\unified_config_example.json config\\unified_config.json"
            ))
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                
            # 빈 파일 체크
            if not content.strip():
                self._add_error(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="EMPTY_FILE",
                    message="파일이 비어있습니다",
                    solution="unified_config_example.json을 참고하여 설정을 작성하세요",
                    example='예시 파일을 복사: copy config\\unified_config_example.json config\\unified_config.json'
                ))
                return False
            
            # JSON 파싱 시도
            try:
                self.config = json.loads(content)
                print(f"  ✅ unified_config.json - 문법 정상")
                return True
                
            except json.JSONDecodeError as e:
                # 상세한 JSON 오류 분석
                self._analyze_json_error("config/unified_config.json", content, e)
                return False
                
        except UnicodeDecodeError as e:
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="ENCODING_ERROR", 
                message=f"파일 인코딩 오류: {e}",
                solution="파일을 UTF-8로 저장하세요",
                example="메모장 → 다른 이름으로 저장 → 인코딩: UTF-8"
            ))
            return False
        except Exception as e:
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="FILE_READ_ERROR",
                message=f"파일 읽기 오류: {e}",
                solution="파일 권한 및 접근성을 확인하세요"
            ))
            return False
    
    def _analyze_json_error(self, file_path: str, content: str, error: json.JSONDecodeError):
        """JSON 오류 상세 분석 및 해결책 제시"""
        lines = content.split('\n')
        error_line = error.lineno
        error_col = error.colno
        
        # 오류 라인 추출
        if error_line <= len(lines):
            problematic_line = lines[error_line - 1]
            
            # 일반적인 JSON 오류 패턴들 분석
            if "Expecting ',' delimiter" in error.msg:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="MISSING_COMMA",
                    message=f"라인 {error_line}: 쉼표(,) 누락",
                    line_number=error_line,
                    solution="객체나 배열 요소 사이에 쉼표를 추가하세요",
                    example=f'문제 라인: {problematic_line.strip()}\n해결: 마지막에 쉼표(,) 추가'
                ))
                
            elif "Expecting ':' delimiter" in error.msg:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="MISSING_COLON",
                    message=f"라인 {error_line}: 콜론(:) 누락",
                    line_number=error_line,
                    solution="키와 값 사이에 콜론을 추가하세요",
                    example=f'문제 라인: {problematic_line.strip()}\n해결: "키": "값" 형태로 수정'
                ))
                
            elif "Expecting property name" in error.msg:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="INVALID_KEY",
                    message=f"라인 {error_line}: 잘못된 키 이름",
                    line_number=error_line,
                    solution="키 이름을 쌍따옴표로 감싸세요",
                    example=f'문제 라인: {problematic_line.strip()}\n해결: 키를 "키이름" 형태로 감싸기'
                ))
                
            else:
                # 일반적인 JSON 오류
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="JSON_SYNTAX_ERROR",
                    message=f"라인 {error_line}, 컬럼 {error_col}: {error.msg}",
                    line_number=error_line,
                    solution="JSON 문법을 확인하세요",
                    example=f"문제 라인: {problematic_line.strip()}"
                ))
    
    def _validate_schema(self):
        """통합 설정 스키마 검증"""
        print("\n📐 2단계: 통합 설정 구조 검증")
        
        if not self.config:
            return
        
        # 필수 최상위 키들 확인
        required_sections = {
            '_metadata': '메타데이터 정보',
            'report_settings': '리포트 기본 설정',
            'grafana_servers': '그라파나 서버 정보',
            'servers': '서버 상세 정보',
            'groups': '시스템 그룹 설정'
        }
        
        for section_key, section_desc in required_sections.items():
            if section_key not in self.config:
                self._add_error(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="MISSING_REQUIRED_SECTION",
                    message=f"필수 섹션 '{section_key}'가 없습니다 ({section_desc})",
                    solution=f"'{section_key}' 섹션을 추가하세요",
                    example=f'""{section_key}"": {{ }}'
                ))
        
        # 각 섹션별 상세 검증
        self._validate_metadata_section()
        self._validate_report_settings_section()
        self._validate_grafana_servers_section()
        self._validate_servers_section()
        self._validate_groups_section()
        
        # 선택적 섹션들 검증
        if 'dashboards' in self.config:
            self._validate_dashboards_section()
        if 'chart_categories' in self.config:
            self._validate_chart_categories_section()
    
    def _validate_metadata_section(self):
        """메타데이터 섹션 검증"""
        if '_metadata' not in self.config:
            return
            
        metadata = self.config['_metadata']
        if not isinstance(metadata, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SECTION_TYPE",
                message="'_metadata' 섹션은 객체여야 합니다",
                solution="메타데이터를 객체 형태로 정의하세요"
            ))
            return
        
        # 권장 키들 확인
        recommended_keys = ['version', 'description', 'created', 'last_updated']
        for key in recommended_keys:
            if key not in metadata:
                self._add_warning(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="MISSING_METADATA_KEY",
                    message=f"메타데이터에 권장 키 '{key}'가 없습니다",
                    solution=f"'{key}' 키를 추가하는 것을 권장합니다"
                ))
    
    def _validate_report_settings_section(self):
        """리포트 설정 섹션 검증"""
        if 'report_settings' not in self.config:
            return
            
        settings = self.config['report_settings']
        if not isinstance(settings, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SECTION_TYPE",
                message="'report_settings' 섹션은 객체여야 합니다",
                solution="리포트 설정을 객체 형태로 정의하세요"
            ))
            return
        
        # 필수 키들 확인
        required_keys = ['report_month', 'period', 'default_year', 'default_month']
        for key in required_keys:
            if key not in settings:
                self._add_error(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="MISSING_REPORT_SETTING",
                    message=f"리포트 설정에 필수 키 '{key}'가 없습니다",
                    solution=f"'{key}' 키를 추가하세요",
                    example=self._get_report_setting_example(key)
                ))
    
    def _validate_grafana_servers_section(self):
        """그라파나 서버 섹션 검증"""
        if 'grafana_servers' not in self.config:
            return
            
        servers = self.config['grafana_servers']
        if not isinstance(servers, list):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SECTION_TYPE",
                message="'grafana_servers' 섹션은 배열이어야 합니다",
                solution="그라파나 서버 정보를 배열 형태로 정의하세요",
                example='[{"name": "Production-Server", "url": "ip:port"}]'
            ))
            return
        
        if not servers:
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="EMPTY_GRAFANA_SERVERS",
                message="그라파나 서버가 정의되지 않았습니다",
                solution="최소 하나의 그라파나 서버를 추가하세요"
            ))
            return
        
        # 각 서버 검증
        for i, server in enumerate(servers):
            if not isinstance(server, dict):
                self._add_error(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="INVALID_SERVER_TYPE",
                    message=f"그라파나 서버 {i+1}번은 객체여야 합니다",
                    solution="서버 정보를 객체 형태로 정의하세요"
                ))
                continue
            
            # 필수 키 확인
            required_keys = ['name', 'url']
            for key in required_keys:
                if key not in server:
                    self._add_error(ConfigError(
                        file_path="config/unified_config.json",
                        error_type="MISSING_SERVER_KEY",
                        message=f"그라파나 서버 {i+1}번에 '{key}' 키가 없습니다",
                        solution=f"'{key}' 키를 추가하세요"
                    ))
    
    def _validate_servers_section(self):
        """서버 정보 섹션 검증"""
        if 'servers' not in self.config:
            return
            
        servers = self.config['servers']
        if not isinstance(servers, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SECTION_TYPE",
                message="'servers' 섹션은 객체여야 합니다",
                solution="서버 정보를 객체 형태로 정의하세요"
            ))
            return
        
        if not servers:
            self._add_warning(ConfigError(
                file_path="config/unified_config.json",
                error_type="EMPTY_SERVERS",
                message="서버 정보가 정의되지 않았습니다",
                solution="서버 정보를 추가하는 것을 권장합니다"
            ))
            return
        
        # 각 서버 정보 검증
        for server_name, server_info in servers.items():
            self._validate_server_info(server_name, server_info)
    
    def _validate_server_info(self, server_name: str, server_info: Any):
        """개별 서버 정보 구조 검증"""
        if not isinstance(server_info, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SERVER_INFO_TYPE",
                message=f"서버 '{server_name}' 정보는 객체여야 합니다",
                solution="서버 정보를 객체 형태로 정의하세요"
            ))
            return
        
        # 권장 키 확인
        recommended_keys = ['display_name', 'hostname', 'os', 'cpu_mem', 'disk', 'availability']
        for key in recommended_keys:
            if key not in server_info:
                self._add_warning(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="MISSING_SERVER_INFO_KEY",
                    message=f"서버 '{server_name}'에 권장 키 '{key}'가 없습니다",
                    solution=f"'{key}' 키를 추가하는 것을 권장합니다"
                ))
        
        # summary 섹션 검증
        if 'summary' in server_info:
            summary = server_info['summary']
            if not isinstance(summary, dict):
                self._add_error(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="INVALID_SUMMARY_TYPE",
                    message=f"서버 '{server_name}'의 summary는 객체여야 합니다",
                    solution="summary를 객체 형태로 정의하세요"
                ))
    
    def _validate_groups_section(self):
        """그룹 섹션 검증"""
        if 'groups' not in self.config:
            return
            
        groups = self.config['groups']
        if not isinstance(groups, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SECTION_TYPE",
                message="'groups' 섹션은 객체여야 합니다",
                solution="그룹 정보를 객체 형태로 정의하세요"
            ))
            return
        
        if not groups:
            self._add_warning(ConfigError(
                file_path="config/unified_config.json",
                error_type="EMPTY_GROUPS",
                message="그룹이 정의되지 않았습니다",
                solution="최소 하나의 그룹을 추가하세요"
            ))
            return
        
        # 각 그룹 검증
        for group_name, group_info in groups.items():
            self._validate_group_info(group_name, group_info)
    
    def _validate_group_info(self, group_name: str, group_info: Any):
        """개별 그룹 정보 검증"""
        if not isinstance(group_info, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_GROUP_TYPE",
                message=f"그룹 '{group_name}'은 객체여야 합니다",
                solution="그룹 정보를 객체 형태로 정의하세요"
            ))
            return
        
        # 필수 키 확인
        required_keys = ['display_name', 'servers']
        for key in required_keys:
            if key not in group_info:
                self._add_error(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="MISSING_GROUP_KEY",
                    message=f"그룹 '{group_name}'에 필수 키 '{key}'가 없습니다",
                    solution=f"'{key}' 키를 추가하세요"
                ))
        
        # servers 배열 검증
        if 'servers' in group_info:
            servers = group_info['servers']
            if not isinstance(servers, list):
                self._add_error(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="INVALID_SERVERS_TYPE",
                    message=f"그룹 '{group_name}'의 'servers'는 배열이어야 합니다",
                    solution="servers 값을 배열로 변경하세요",
                    example='"servers": ["Server1", "Server2"]'
                ))
            elif not servers:
                self._add_warning(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="EMPTY_GROUP_SERVERS",
                    message=f"그룹 '{group_name}'에 서버가 없습니다",
                    solution="최소 하나의 서버를 추가하세요"
                ))
    
    def _validate_dashboards_section(self):
        """대시보드 섹션 검증 (선택적)"""
        dashboards = self.config.get('dashboards', {})
        if not isinstance(dashboards, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SECTION_TYPE",
                message="'dashboards' 섹션은 객체여야 합니다",
                solution="대시보드 정보를 객체 형태로 정의하세요"
            ))
    
    def _validate_chart_categories_section(self):
        """차트 카테고리 섹션 검증 (선택적)"""
        categories = self.config.get('chart_categories', {})
        if not isinstance(categories, dict):
            self._add_error(ConfigError(
                file_path="config/unified_config.json",
                error_type="INVALID_SECTION_TYPE",
                message="'chart_categories' 섹션은 객체여야 합니다",
                solution="차트 카테고리를 객체 형태로 정의하세요"
            ))
    
    def _validate_consistency(self):
        """데이터 일관성 검증"""
        print("\n🔗 3단계: 데이터 일관성 검증")
        
        if not self.config:
            return
        
        # 그룹-서버 매핑 검증
        groups = self.config.get('groups', {})
        servers = self.config.get('servers', {})
        dashboards = self.config.get('dashboards', {})
        
        for group_name, group_info in groups.items():
            if not group_info.get('active', True):
                continue
                
            group_servers = group_info.get('servers', [])
            for server_name in group_servers:
                # 서버 정보 존재 확인
                if server_name not in servers:
                    # 대시보드 매핑 확인
                    if server_name in dashboards:
                        mapped_servers = dashboards[server_name].get('servers', [])
                        if not any(ms in servers for ms in mapped_servers):
                            self._add_error(ConfigError(
                                file_path="config/unified_config.json",
                                error_type="MISSING_SERVER_INFO",
                                message=f"그룹 '{group_name}'에 정의된 서버 '{server_name}' 정보가 없습니다",
                                solution="servers 섹션에 서버 정보를 추가하세요",
                                example=self._generate_server_info_example(server_name)
                            ))
                    else:
                        self._add_error(ConfigError(
                            file_path="config/unified_config.json",
                            error_type="MISSING_SERVER_INFO",
                            message=f"그룹 '{group_name}'에 정의된 서버 '{server_name}' 정보가 없습니다",
                            solution="servers 섹션에 서버 정보를 추가하세요",
                            example=self._generate_server_info_example(server_name)
                        ))
        
        # 대시보드-서버 매핑 검증
        for dashboard_name, dashboard_info in dashboards.items():
            if 'servers' in dashboard_info:
                for server_name in dashboard_info['servers']:
                    if server_name not in servers:
                        self._add_warning(ConfigError(
                            file_path="config/unified_config.json",
                            error_type="MISSING_DASHBOARD_SERVER",
                            message=f"대시보드 '{dashboard_name}'에 정의된 서버 '{server_name}' 정보가 없습니다",
                            solution="servers 섹션에 서버 정보를 추가하거나 대시보드에서 제거하세요"
                        ))
    
    def _validate_business_logic(self):
        """비즈니스 로직 검증"""
        print("\n⚙️ 4단계: 비즈니스 로직 검증")
        
        if not self.config:
            return
        
        # 활성화된 그룹이 있는지 확인
        groups = self.config.get('groups', {})
        active_groups = [name for name, info in groups.items() if info.get('active', True)]
        
        if not active_groups:
            self._add_warning(ConfigError(
                file_path="config/unified_config.json",
                error_type="NO_ACTIVE_GROUPS",
                message="활성화된 그룹이 없습니다",
                solution="최소 하나의 그룹을 활성화하세요",
                example='"active": true'
            ))
        
        # 그라파나 서버 URL 형식 검증
        grafana_servers = self.config.get('grafana_servers', [])
        for i, server in enumerate(grafana_servers):
            if isinstance(server, dict) and 'url' in server:
                url = server['url']
                if not self._is_valid_url_format(url):
                    self._add_warning(ConfigError(
                        file_path="config/unified_config.json",
                        error_type="INVALID_URL_FORMAT",
                        message=f"그라파나 서버 {i+1}번의 URL 형식이 잘못되었습니다: {url}",
                        solution="IP:PORT 또는 domain:PORT 형식으로 수정하세요",
                        example="예: 192.168.1.100:3000 또는 grafana.company.com:3000"
                    ))
        
        # 리포트 날짜 형식 검증
        report_settings = self.config.get('report_settings', {})
        if 'default_year' in report_settings and 'default_month' in report_settings:
            year = report_settings['default_year']
            month = report_settings['default_month']
            
            if not isinstance(year, int) or year < 2020 or year > 2030:
                self._add_warning(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="INVALID_YEAR",
                    message=f"잘못된 연도 값: {year}",
                    solution="2020-2030 사이의 연도를 입력하세요"
                ))
            
            if not isinstance(month, int) or month < 1 or month > 12:
                self._add_warning(ConfigError(
                    file_path="config/unified_config.json",
                    error_type="INVALID_MONTH",
                    message=f"잘못된 월 값: {month}",
                    solution="1-12 사이의 월을 입력하세요"
                ))
    
    def _is_valid_url_format(self, url: str) -> bool:
        """URL 형식 검증"""
        # 기본적인 IP:PORT 또는 domain:PORT 형식 확인
        pattern = r'^[\w\.-]+:\d+$'
        return bool(re.match(pattern, url))
    
    def _print_detailed_report(self):
        """상세 검증 결과 리포트 출력"""
        print("\n" + "="*60)
        print("📊 === 통합 설정 검증 결과 ===")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ 오류 발견: {len(self.errors)}개")
            print("-" * 40)
            
            for i, error in enumerate(self.errors, 1):
                print(f"\n[오류 {i}] {error.error_type}")
                print(f"📁 파일: {error.file_path}")
                if error.line_number:
                    print(f"📍 위치: 라인 {error.line_number}")
                print(f"❌ 문제: {error.message}")
                if error.solution:
                    print(f"💡 해결책: {error.solution}")
                if error.example:
                    print(f"📝 예시:")
                    print(f"   {error.example}")
        
        if self.warnings:
            print(f"\n⚠️  경고 발견: {len(self.warnings)}개")
            print("-" * 40)
            
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n[경고 {i}] {warning.error_type}")
                print(f"📁 파일: {warning.file_path}")
                print(f"⚠️  내용: {warning.message}")
                if warning.solution:
                    print(f"💡 권장사항: {warning.solution}")
        
        # 요약
        print(f"\n{'='*60}")
        print("📋 검증 요약")
        print(f"{'='*60}")
        print(f"✅ 검증 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📄 검사한 파일: config/unified_config.json")
        print(f"❌ 오류: {len(self.errors)}개")
        print(f"⚠️  경고: {len(self.warnings)}개")
        
        if len(self.errors) == 0:
            print(f"\n   모든 설정이 올바릅니다!")
            print(f"   리포트를 생성합니다.")
        else:
            print(f"\n🔧 위의 오류들을 수정한 후 다시 검증하세요.")
            print(f"   수정 완료 후: python enhanced_config_validator.py")
        
        # 설정 파일 가이드
        if len(self.errors) == 0 and len(self.warnings) > 0:
            print(f"\n📋 추가 개선 가능한 사항:")
            print(f"   - 경고 사항들을 해결하면 더 완성도 높은 설정이 됩니다")
            print(f"   - config/unified_config_example.json을 참고하세요")
   
    def _add_error(self, error: ConfigError):
        """오류 추가"""
        self.errors.append(error)
        
    def _add_warning(self, warning: ConfigError):
        """경고 추가"""
        self.warnings.append(warning)
   
    # 유틸리티 메서드들
    def _get_report_setting_example(self, key: str) -> str:
        """리포트 설정 예시 생성"""
        examples = {
            'report_month': '"report_month": "2025. 05"',
            'period': '"period": "2025-05-01 ~ 2025-05-31"',
            'default_year': '"default_year": 2025',
            'default_month': '"default_month": 5'
        }
        return examples.get(key, f'"{key}": "적절한 값"')
   
    def _generate_server_info_example(self, server_name: str) -> str:
        """서버 정보 예시 생성"""
        return f'''"servers": {{
    "{server_name}": {{
        "display_name": "{server_name} 시스템",
        "hostname": "{server_name.lower()}-01",
        "os": "ubuntu-20.04",
        "cpu_mem": "4vCPU / 16GB Mem",
        "disk": "100 GB / 500 GB",
        "availability": "99.9%",
        "summary": {{
            "total_alerts": {{"value": 0, "label": "전체"}},
            "critical_alerts": {{"value": 0, "label": "긴급"}},
            "warning_alerts": {{"value": 0, "label": "경고"}},
            "top5_note": "정상 운영 중"
        }}
    }}
}}'''

# 메인 실행 함수
def main():
    """메인 검증 실행"""
    validator = UnifiedConfigValidator()
    success = validator.validate_all()
    
    if not success:
        print(f"\n 통합 설정 파일에 오류가 발견되었습니다!")
        print(f"   위의 해결책을 참고하여 문제를 수정하세요.")
        print(f"   예시 파일: config/unified_config_example.json")
        return False
    
    return True

def check_example_file():
    """예시 파일 존재 확인 및 안내"""
    example_path = Path("config/unified_config_example.json")
    config_path = Path("config/unified_config.json")
    
    if not example_path.exists():
        print("  예시 파일이 없습니다: config/unified_config_example.json")
        print("   GitHub에서 최신 예시 파일을 다운로드하세요.")
    
    if not config_path.exists() and example_path.exists():
        print("💡 통합 설정 파일이 없습니다.")
        print("   다음 명령어로 예시 파일을 복사하세요:")
        print("   copy config\\unified_config_example.json config\\unified_config.json")

if __name__ == "__main__":
    import sys
    
    # 예시 파일 확인
    check_example_file()
    
    # 검증 실행
    success = main()
    sys.exit(0 if success else 1)