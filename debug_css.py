# debug_css.py - CSS 파일 검증
def validate_css_file():
    """CSS 파일 구문 검증"""
    from pathlib import Path
    
    css_path = Path("templates/assets/style.css")
    
    if not css_path.exists():
        print("❌ CSS 파일이 없습니다.")
        return False
    
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 기본적인 구문 검증
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        print(f"CSS 파일 검증:")
        print(f"  파일 크기: {len(content)} 문자")
        print(f"  열린 괄호: {open_braces}")
        print(f"  닫힌 괄호: {close_braces}")
        
        if open_braces != close_braces:
            print("❌ 괄호 개수가 맞지 않습니다!")
            return False
        
        # 기본 CSS 선택자 확인
        selectors = ['.container', '.report-header', '.server-section', '.chart-card']
        missing_selectors = []
        
        for selector in selectors:
            if selector not in content:
                missing_selectors.append(selector)
        
        if missing_selectors:
            print(f"❌ 누락된 선택자: {missing_selectors}")
            return False
        
        print("✅ CSS 파일이 정상입니다.")
        return True
        
    except Exception as e:
        print(f"❌ CSS 파일 읽기 실패: {e}")
        return False

if __name__ == "__main__":
    validate_css_file()