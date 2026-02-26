#!/usr/bin/env python3
"""Quick test script for cloud agent configuration."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cloud_agent.src.config import CloudAgentConfig

# Test configuration loading
config = CloudAgentConfig.from_env()

print("Configuration loaded successfully!")
print(f"Vault path: {config.vault_path}")
print(f"Sync method: {config.sync_method}")
print(f"Gmail enabled: {config.gmail_enabled}")
print(f"Dev mode: {config.dev_mode}")
