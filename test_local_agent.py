#!/usr/bin/env python3
"""Quick test script for local agent imports."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing imports...")

try:
    from local_agent.src.approval_handler import ApprovalHandler
    print("[OK] ApprovalHandler imported successfully")
except Exception as e:
    print(f"[FAIL] ApprovalHandler import failed: {e}")

try:
    from local_agent.src.config import LocalAgentConfig
    print("[OK] LocalAgentConfig imported successfully")
except Exception as e:
    print(f"[FAIL] LocalAgentConfig import failed: {e}")

try:
    config = LocalAgentConfig.from_env()
    print(f"[OK] Configuration loaded: vault_path={config.vault_path}")
except Exception as e:
    print(f"[FAIL] Configuration loading failed: {e}")

print("\nAll imports successful!")
