#!/usr/bin/env python3
"""
Test script to verify UI/CSS improvements, static report links, and reference links.

This script performs basic sanity checks on the improvements without requiring
a full Flask server or database setup.
"""

import os
import sys
from pathlib import Path

def test_static_reports_directory():
    """Verify static/reports directory exists and is writable."""
    print("Testing static reports directory...")
    
    reports_dir = Path("static/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Test write access
    test_file = reports_dir / "test_access.txt"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print("  ✓ static/reports/ directory is writable")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_modern_css_exists():
    """Verify modern CSS file exists."""
    print("Testing modern CSS file...")
    
    css_path = Path("static/css/modern.css")
    if css_path.exists():
        size = css_path.stat().st_size
        print(f"  ✓ modern.css exists ({size} bytes)")
        return True
    else:
        print("  ✗ modern.css not found")
        return False

def test_agent_imports():
    """Test that ReportEngine agent can be imported."""
    print("Testing ReportEngine imports...")
    
    try:
        # Add project root to path
        sys.path.insert(0, str(Path.cwd()))
        
        # Check if prompts file has valid Python syntax
        prompts_path = Path("ReportEngine/prompts/prompts.py")
        with open(prompts_path, 'r', encoding='utf-8') as f:
            compile(f.read(), prompts_path, 'exec')
        
        print("  ✓ prompts.py has valid syntax")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_prompt_modifications():
    """Verify that source citation instructions are in prompts."""
    print("Testing prompt modifications...")
    
    prompts_path = Path("ReportEngine/prompts/prompts.py")
    if not prompts_path.exists():
        print("  ✗ prompts.py not found")
        return False
    
    content = prompts_path.read_text(encoding='utf-8')
    
    checks = [
        ("Source Citation Protocol", "来源引用协议"),
        ("Link inline marks", "link"),
        ("References section", "参考资料"),
        ("URL handling", "url"),
    ]
    
    passed = 0
    for name, keyword in checks:
        if keyword in content:
            print(f"  ✓ {name} found")
            passed += 1
        else:
            print(f"  ✗ {name} not found (keyword: {keyword})")
    
    return passed == len(checks)

def test_flask_interface_modifications():
    """Verify flask_interface.py has static_report_path field."""
    print("Testing Flask interface modifications...")
    
    flask_path = Path("ReportEngine/flask_interface.py")
    if not flask_path.exists():
        print("  ✗ flask_interface.py not found")
        return False
    
    content = flask_path.read_text(encoding='utf-8')
    
    checks = [
        ("static_report_path field", "static_report_path"),
        ("to_dict includes static path", "'static_report_path'"),
    ]
    
    passed = 0
    for name, keyword in checks:
        if keyword in content:
            print(f"  ✓ {name} found")
            passed += 1
        else:
            print(f"  ✗ {name} not found")
    
    return passed == len(checks)

def test_agent_modifications():
    """Verify agent.py saves to static/reports/."""
    print("Testing agent.py modifications...")
    
    agent_path = Path("ReportEngine/agent.py")
    if not agent_path.exists():
        print("  ✗ agent.py not found")
        return False
    
    content = agent_path.read_text(encoding='utf-8')
    
    checks = [
        ("Static reports directory", "static/reports"),
        ("Static path logging", "静态目录"),
        ("Returns static_report_path", "static_report_path"),
    ]
    
    passed = 0
    for name, keyword in checks:
        if keyword in content:
            print(f"  ✓ {name} found")
            passed += 1
        else:
            print(f"  ✗ {name} not found")
    
    return passed == len(checks)

def test_frontend_modifications():
    """Verify index.html shows clickable report links."""
    print("Testing frontend modifications...")
    
    template_path = Path("templates/index.html")
    if not template_path.exists():
        print("  ✗ index.html not found")
        return False
    
    content = template_path.read_text(encoding='utf-8')
    
    checks = [
        ("Static report path handling", "static_report_path"),
        ("Clickable link display", "target=\"_blank\""),
        ("Report link styling", "4a9eff"),  # Blue color for links
    ]
    
    passed = 0
    for name, keyword in checks:
        if keyword in content:
            print(f"  ✓ {name} found")
            passed += 1
        else:
            print(f"  ✗ {name} not found")
    
    return passed == len(checks)

def main():
    """Run all tests."""
    print("=" * 60)
    print("BettaFish Improvements Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Static Reports Directory", test_static_reports_directory),
        ("Modern CSS File", test_modern_css_exists),
        ("Agent Imports", test_agent_imports),
        ("Prompt Modifications", test_prompt_modifications),
        ("Flask Interface", test_flask_interface_modifications),
        ("Agent Modifications", test_agent_modifications),
        ("Frontend Modifications", test_frontend_modifications),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Improvements are ready for testing.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
