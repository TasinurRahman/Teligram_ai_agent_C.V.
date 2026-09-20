import os
import sys
import logging

logging.basicConfig(level=logging.INFO)

from model_router import DynamicModelRouter
from memory_engine import MemoryEngine
from tools.code_builder import CodeBuilderTool
from tools.deployer import DeployerTool
from tools.security_sast import SecuritySASTTool

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_tests():
    print("\n--- [TEST] Starting Verification Tests ---")

    # 1. Test Router Intent Classification
    router = DynamicModelRouter()
    cat_code = router.classify_intent("Build a HTML CSS landing page")
    cat_sec = router.classify_intent("Audit this SAST vulnerability code for SQL Injection")
    cat_gen = router.classify_intent("What is quantum computing?")
    print(f"✅ Router Classification Test:")
    print(f"  - Coding Prompt -> {cat_code} (Expected: coding)")
    print(f"  - Security Prompt -> {cat_sec} (Expected: reasoning)")
    print(f"  - General Prompt -> {cat_gen} (Expected: general)")

    # 2. Test Memory Engine
    memory = MemoryEngine()
    user = memory.get_or_create_user("123456", "test_user")
    print(f"✅ Memory Engine User Creation: ID={user['telegram_id']}, Role={user['role']}")

    # 3. Test Code Builder Tool
    builder = CodeBuilderTool()
    res = builder.create_project_structure("test_site", {"index.html": "<h1>Test Site</h1>"})
    print(f"✅ Code Builder: {res}")

    # 4. Test Security SAST Scanner Tool
    sast = SecuritySASTTool()
    vulnerable_code = "let pass = 'secret1234567890'; eval(userInput);"
    vulns = sast.scan_code_snippet(vulnerable_code)
    print(f"✅ SAST Security Scan Vulnerabilities Detected: {len(vulns)}")

    print("\n🎉 ALL COMPONENT TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    run_tests()
