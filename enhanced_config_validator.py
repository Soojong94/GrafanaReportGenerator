# enhanced_config_validator.py - 완전한 버전
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

class EnhancedConfigValidator:
    def __init__(self):
        self.errors: List[ConfigError] = []
        self.warnings: List[ConfigError] = []
        self.configs = {}
        
    def validate_all(self) -> bool:
        """전체 검증 실행"""
        print("🔍 === 고급 설정 파일 검증 시작 ===")
        print(f"검증 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1단계: JSON 문법 및 구조 검증
        self._validate_json_syntax()
        
        # 2단계: 스키마 검증  
        self._validate_schema()
        
        # 3단계: 데이터 일관성 검증
        self._validate_consistency()
        
        # 4단계: 비즈니스 로직 검증
        self._validate_business_logic()
        
        # 결과 리포트 출력
        self._print_detailed_report()
        
        return len(self.errors) == 0
    
    def _validate_json_syntax(self):
        """JSON 문법 검증 - 상세한 오류 위치 및 해결책 제시"""
        print("📋 1단계: JSON 문법 검증")
        
        required_files = {
            'system_groups': 'config/system_groups.json',
            'server_info': 'config/server_info.json',
            'dashboard_config': 'config/dashboard_config.json', 
            'report_config': 'config/report_config.json'
        }
        
        for config_name, file_path in required_files.items():
            path = Path(file_path)
            
            if not path.exists():
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="FILE_MISSING",
                    message=f"필수 설정 파일이 없습니다",
                    solution="파일을 생성하거나 경로를 확인하세요",
                    example=f"touch {file_path} 또는 빈 JSON 객체 {{}} 로 생성"
                ))
                continue
            
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    
                # 빈 파일 체크
                if not content.strip():
                    self._add_error(ConfigError(
                        file_path=file_path,
                        error_type="EMPTY_FILE",
                        message="파일이 비어있습니다",
                        solution="최소한 빈 JSON 객체를 추가하세요",
                        example='{\n  "_comment": "설정 파일"\n}'
                    ))
                    continue
                
                # JSON 파싱 시도
                try:
                    config_data = json.loads(content)
                    self.configs[config_name] = config_data
                    print(f"  ✅ {path.name} - 문법 정상")
                    
                except json.JSONDecodeError as e:
                    # 상세한 JSON 오류 분석
                    self._analyze_json_error(file_path, content, e)
                    
            except UnicodeDecodeError as e:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="ENCODING_ERROR", 
                    message=f"파일 인코딩 오류: {e}",
                    solution="파일을 UTF-8로 저장하세요",
                    example="메모장 → 다른 이름으로 저장 → 인코딩: UTF-8"
                ))
            except Exception as e:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="FILE_READ_ERROR",
                    message=f"파일 읽기 오류: {e}",
                    solution="파일 권한 및 접근성을 확인하세요"
                ))
    
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
                    example=f'잘못된 예: {problematic_line.strip()}\n올바른 예: {self._suggest_comma_fix(problematic_line)}'
                ))
                
            elif "Expecting ':' delimiter" in error.msg:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="MISSING_COLON",
                    message=f"라인 {error_line}: 콜론(:) 누락",
                    line_number=error_line,
                    solution="키와 값 사이에 콜론을 추가하세요",
                    example=f'잘못된 예: {problematic_line.strip()}\n올바른 예: {self._suggest_colon_fix(problematic_line)}'
                ))
                
            elif "Expecting property name" in error.msg:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="INVALID_KEY",
                    message=f"라인 {error_line}: 잘못된 키 이름",
                    line_number=error_line,
                    solution="키 이름을 쌍따옴표로 감싸세요",
                    example=f'잘못된 예: {problematic_line.strip()}\n올바른 예: {self._suggest_key_fix(problematic_line)}'
                ))
                
            elif "Expecting value" in error.msg:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="MISSING_VALUE",
                    message=f"라인 {error_line}: 값 누락",
                    line_number=error_line,
                    solution="키에 해당하는 값을 추가하세요",
                    example='예: "key": "value" 또는 "key": null'
                ))
                
            elif "Extra data" in error.msg:
                self._add_error(ConfigError(
                    file_path=file_path,
                    error_type="EXTRA_CHARACTERS",
                    message=f"라인 {error_line}: 불필요한 문자",
                    line_number=error_line,
                    solution="JSON 종료 후 추가 문자를 제거하세요",
                    example="JSON 객체 닫기 } 이후의 모든 문자 삭제"
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
        """스키마 검증 - 필수 키 및 데이터 타입 확인"""
        print("\n📐 2단계: 스키마 구조 검증")
        
        # system_groups.json 스키마 검증
        if 'system_groups' in self.configs:
            self._validate_system_groups_schema()
        
        # server_info.json 스키마 검증  
        if 'server_info' in self.configs:
            self._validate_server_info_schema()
            
        # dashboard_config.json 스키마 검증
        if 'dashboard_config' in self.configs:
            self._validate_dashboard_config_schema()
    
    def _validate_system_groups_schema(self):
        """system_groups.json 스키마 검증"""
        config = self.configs['system_groups']
        
        if 'groups' not in config:
            self._add_error(ConfigError(
                file_path="config/system_groups.json",
                error_type="MISSING_REQUIRED_KEY",
                message="'groups' 키가 없습니다",
                solution="최상위에 'groups' 객체를 추가하세요",
                example='{\n  "groups": {\n    "시스템1": {\n      "display_name": "시스템명",\n      "servers": ["서버1"]\n    }\n  }\n}'
            ))
            return
        
        groups = config['groups']
        if not isinstance(groups, dict):
            self._add_error(ConfigError(
                file_path="config/system_groups.json",
                error_type="INVALID_DATA_TYPE",
                message="'groups'는 객체여야 합니다",
                solution="'groups' 값을 객체 형태로 변경하세요",
                example='"groups": { ... }'
            ))
            return
            
        if not groups:
            self._add_warning(ConfigError(
                file_path="config/system_groups.json",
                error_type="EMPTY_GROUPS",
                message="그룹이 정의되지 않았습니다",
                solution="최소 하나의 그룹을 추가하세요"
            ))
            
        # 각 그룹 검증
        for group_name, group_info in groups.items():
            self._validate_group_structure(group_name, group_info)
    
    def _validate_group_structure(self, group_name: str, group_info: Any):
        """개별 그룹 구조 검증"""
        if not isinstance(group_info, dict):
            self._add_error(ConfigError(
                file_path="config/system_groups.json",
                error_type="INVALID_GROUP_TYPE",
                message=f"그룹 '{group_name}'은 객체여야 합니다",
                solution="그룹 정보를 객체 형태로 정의하세요",
                example=f'"{group_name}": {{\n  "display_name": "표시명",\n  "servers": ["서버1"]\n}}'
            ))
            return
        
        # 필수 키 확인
        required_keys = ['display_name', 'servers']
        for key in required_keys:
            if key not in group_info:
                self._add_error(ConfigError(
                    file_path="config/system_groups.json",
                    error_type="MISSING_GROUP_KEY",
                    message=f"그룹 '{group_name}'에 '{key}' 키가 없습니다",
                    solution=f"'{key}' 키를 추가하세요",
                    example=f'"{key}": {"표시명" if key == "display_name" else "[]"}'
                ))
        
        # servers 배열 검증
        if 'servers' in group_info:
            servers = group_info['servers']
            if not isinstance(servers, list):
                self._add_error(ConfigError(
                    file_path="config/system_groups.json",
                    error_type="INVALID_SERVERS_TYPE",
                    message=f"그룹 '{group_name}'의 'servers'는 배열이어야 합니다",
                    solution="servers 값을 배열로 변경하세요",
                    example='"servers": ["Mail-Server", "Web-Server"]'
                ))
            elif not servers:
                self._add_warning(ConfigError(
                    file_path="config/system_groups.json", 
                    error_type="EMPTY_SERVERS",
                    message=f"그룹 '{group_name}'에 서버가 없습니다",
                    solution="최소 하나의 서버를 추가하세요"
                ))

    def _validate_server_info_schema(self):
        """server_info.json 스키마 검증"""
        config = self.configs['server_info']
        
        if 'servers' not in config:
            self._add_error(ConfigError(
                file_path="config/server_info.json",
                error_type="MISSING_REQUIRED_KEY",
                message="'servers' 키가 없습니다",
                solution="최상위에 'servers' 객체를 추가하세요",
                example='{\n  "servers": {\n    "Mail-Server": {\n      "display_name": "메일 서버",\n      "hostname": "mail-01"\n    }\n  }\n}'
            ))
            return
        
        servers = config['servers']
        if not isinstance(servers, dict):
            self._add_error(ConfigError(
                file_path="config/server_info.json",
                error_type="INVALID_DATA_TYPE",
                message="'servers'는 객체여야 합니다",
                solution="'servers' 값을 객체 형태로 변경하세요",
                example='"servers": { ... }'
            ))
            return
        
        if not servers:
            self._add_warning(ConfigError(
                file_path="config/server_info.json",
                error_type="EMPTY_SERVERS",
                message="서버 정보가 정의되지 않았습니다",
                solution="최소 하나의 서버 정보를 추가하세요"
            ))
        
        # 각 서버 정보 검증
        for server_name, server_info in servers.items():
            self._validate_server_structure(server_name, server_info)

    def _validate_server_structure(self, server_name: str, server_info: Any):
        """개별 서버 구조 검증"""
        if not isinstance(server_info, dict):
            self._add_error(ConfigError(
                file_path="config/server_info.json",
                error_type="INVALID_SERVER_TYPE",
                message=f"서버 '{server_name}'은 객체여야 합니다",
                solution="서버 정보를 객체 형태로 정의하세요",
                example=f'"{server_name}": {{\n  "display_name": "서버 표시명",\n  "hostname": "server-01"\n}}'
            ))
            return
        
        # 필수 키 확인
        required_keys = ['display_name', 'hostname', 'os']
        for key in required_keys:
            if key not in server_info:
                self._add_warning(ConfigError(
                    file_path="config/server_info.json",
                    error_type="MISSING_SERVER_KEY",
                    message=f"서버 '{server_name}'에 권장 키 '{key}'가 없습니다",
                    solution=f"'{key}' 키를 추가하는 것을 권장합니다",
                    example=f'"{key}": "적절한 값"'
                ))

    def _validate_dashboard_config_schema(self):
        """dashboard_config.json 스키마 검증"""
        config = self.configs['dashboard_config']
        
        # dashboards 키 확인
        if 'dashboards' in config:
            dashboards = config['dashboards']
            if not isinstance(dashboards, dict):
                self._add_error(ConfigError(
                    file_path="config/dashboard_config.json",
                    error_type="INVALID_DATA_TYPE",
                    message="'dashboards'는 객체여야 합니다",
                    solution="'dashboards' 값을 객체 형태로 변경하세요"
                ))
            else:
                # 각 대시보드 검증
                for dashboard_name, dashboard_info in dashboards.items():
                    self._validate_dashboard_structure(dashboard_name, dashboard_info)
        
        # chart_categories 키 확인
        if 'chart_categories' in config:
            categories = config['chart_categories']
            if not isinstance(categories, dict):
                self._add_error(ConfigError(
                    file_path="config/dashboard_config.json",
                    error_type="INVALID_DATA_TYPE",
                    message="'chart_categories'는 객체여야 합니다",
                    solution="'chart_categories' 값을 객체 형태로 변경하세요"
                ))

    def _validate_dashboard_structure(self, dashboard_name: str, dashboard_info: Any):
        """개별 대시보드 구조 검증"""
        if not isinstance(dashboard_info, dict):
            self._add_error(ConfigError(
                file_path="config/dashboard_config.json",
                error_type="INVALID_DASHBOARD_TYPE",
                message=f"대시보드 '{dashboard_name}'은 객체여야 합니다",
                solution="대시보드 정보를 객체 형태로 정의하세요"
            ))
            return
        
        # 권장 키 확인
        recommended_keys = ['display_name', 'description']
        for key in recommended_keys:
            if key not in dashboard_info:
                self._add_warning(ConfigError(
                    file_path="config/dashboard_config.json",
                    error_type="MISSING_DASHBOARD_KEY",
                    message=f"대시보드 '{dashboard_name}'에 권장 키 '{key}'가 없습니다",
                    solution=f"'{key}' 키를 추가하는 것을 권장합니다"
                ))
    
    def _validate_consistency(self):
        """데이터 일관성 검증"""
        print("\n🔗 3단계: 데이터 일관성 검증")
        
        if 'system_groups' not in self.configs or 'server_info' not in self.configs:
            return
            
        # 그룹-서버 매핑 검증
        system_groups = self.configs['system_groups'].get('groups', {})
        server_info = self.configs['server_info'].get('servers', {})
        dashboard_config = self.configs.get('dashboard_config', {}).get('dashboards', {})
        
        for group_name, group_info in system_groups.items():
            if not group_info.get('active', True):
                continue
                
            for server_name in group_info.get('servers', []):
                # 직접 서버 정보 확인
                if server_name not in server_info:
                    # 대시보드 매핑 확인
                    if server_name in dashboard_config:
                        mapped_servers = dashboard_config[server_name].get('servers', [])
                        if not any(ms in server_info for ms in mapped_servers):
                            self._add_error(ConfigError(
                                file_path="config/server_info.json",
                                error_type="MISSING_SERVER_INFO",
                                message=f"서버 '{server_name}' 정보가 없습니다",
                                solution="server_info.json에 서버 정보를 추가하세요",
                                example=self._generate_server_info_example(server_name)
                            ))
                    else:
                        self._add_error(ConfigError(
                            file_path="config/server_info.json",
                            error_type="MISSING_SERVER_INFO", 
                            message=f"서버 '{server_name}' 정보가 없습니다",
                            solution="server_info.json에 서버 정보를 추가하세요",
                            example=self._generate_server_info_example(server_name)
                        ))
    
    def _validate_business_logic(self):
        """비즈니스 로직 검증"""
        print("\n⚙️ 4단계: 비즈니스 로직 검증")
        
        # 활성화된 그룹이 있는지 확인
        if 'system_groups' in self.configs:
            groups = self.configs['system_groups'].get('groups', {})
            active_groups = [name for name, info in groups.items() if info.get('active', True)]
            
            if not active_groups:
                self._add_warning(ConfigError(
                    file_path="config/system_groups.json",
                    error_type="NO_ACTIVE_GROUPS",
                    message="활성화된 그룹이 없습니다",
                    solution="최소 하나의 그룹을 활성화하세요",
                    example='"active": true'
                ))
    
    def _print_detailed_report(self):
        """상세 검증 결과 리포트 출력"""
        print("\n" + "="*60)
        print("📊 === 상세 검증 결과 ===")
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
        print(f"📄 검사한 파일: {len(self.configs)}개")
        print(f"❌ 오류: {len(self.errors)}개")
        print(f"⚠️  경고: {len(self.warnings)}개")
        
        if len(self.errors) == 0:
            print(f"\n 모든 설정이 올바릅니다!")
            print(f"   runall.bat을 실행하여 리포트를 생성하세요.")
        else:
            print(f"\n🔧 위의 오류들을 수정한 후 다시 검증하세요.")
            print(f"   수정 완료 후: python enhanced_config_validator.py")
   
    def _add_error(self, error: ConfigError):
       """오류 추가"""
       self.errors.append(error)
       
    def _add_warning(self, warning: ConfigError):
       """경고 추가"""
       self.warnings.append(warning)
   
   # 유틸리티 메서드들
    def _suggest_comma_fix(self, line: str) -> str:
       """쉼표 수정 제안"""
       if line.strip().endswith('"'):
           return line.rstrip() + ','
       return line + ','
   
    def _suggest_colon_fix(self, line: str) -> str: 
       """콜론 수정 제안"""
       if '"' in line and ':' not in line:
           parts = line.split('"')
           if len(parts) >= 2:
               return f'"{parts[1]}": "value"'
       return line + ': "value"'
   
    def _suggest_key_fix(self, line: str) -> str:
       """키 이름 수정 제안"""
       # 따옴표 없는 키를 찾아서 수정
       if ':' in line:
           key_part = line.split(':')[0].strip()
           if not key_part.startswith('"'):
               return line.replace(key_part, f'"{key_part.strip()}"')
       return f'"{line.strip()}": "value"'
   
    def _generate_server_info_example(self, server_name: str) -> str:
       """서버 정보 예시 생성"""
       return f'''"{server_name}": {{
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
}}'''

# 메인 실행 함수
def main():
   validator = EnhancedConfigValidator()
   success = validator.validate_all()
   
   if not success:
       print(f"\n🚨 설정 오류가 발견되었습니다!")
       print(f"   위의 해결책을 참고하여 문제를 수정하세요.")
       return False
   
   return True

if __name__ == "__main__":
   import sys
   success = main()
   sys.exit(0 if success else 1)