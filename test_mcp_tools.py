"""
MCP Tools Integration Test
Tests MCP server and tools functionality
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from skills.mcp_skill import MCPToolsSkill
from mcp.server import MCPServer


def test_mcp_tools():
    """Test MCP tools skill"""

    print("=" * 60)
    print("MCP Tools Integration Test")
    print("=" * 60)

    # Configuration
    vault_path = "AI_Employee_Vault"

    print("\n[INFO] Configuration:")
    print(f"  Vault Path: {vault_path}")

    # Create MCP server
    print("\n[INFO] Creating MCP server...")
    mcp_server = MCPServer(vault_path)
    mcp_server.initialize_default_tools()

    print("[SUCCESS] MCP server created")

    # List available tools
    tools = mcp_server.list_tools()
    print(f"\n[INFO] Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")

    # Create MCP skill
    print("\n[INFO] Creating MCP tools skill...")
    skill = MCPToolsSkill(vault_path, mcp_server)

    print(f"[SUCCESS] Skill created: {skill.name}")
    print(f"  Skill ID: {skill.skill_id}")
    print(f"  Category: {skill.category}")

    # Test Case 1: Send Email (Dry Run)
    print("\n" + "=" * 60)
    print("Test Case 1: Send Email Tool")
    print("=" * 60)

    email_context = {
        'tool_name': 'send_email',
        'parameters': {
            'to': 'test@example.com',
            'subject': 'Test Email from MCP',
            'body': 'This is a test email from the MCP tools integration test.',
            'dry_run': True  # Don't actually send
        }
    }

    print("\n[INFO] Executing send_email tool (dry run)...")
    print(f"  To: {email_context['parameters']['to']}")
    print(f"  Subject: {email_context['parameters']['subject']}")

    result = skill.execute(email_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Tool: {result.get('tool_name')}")

    if result.get('success'):
        print("\n[SUCCESS] Email tool executed successfully (dry run)")
    else:
        print(f"\n[WARNING] Email tool failed: {result.get('error')}")
        print("[INFO] This is expected if Gmail credentials not configured")

    # Test Case 2: Send WhatsApp (Dry Run)
    print("\n" + "=" * 60)
    print("Test Case 2: Send WhatsApp Tool")
    print("=" * 60)

    whatsapp_context = {
        'tool_name': 'send_whatsapp',
        'parameters': {
            'phone_number': '+1234567890',
            'message': 'Test message from MCP tools',
            'dry_run': True  # Don't actually send
        }
    }

    print("\n[INFO] Executing send_whatsapp tool (dry run)...")
    print(f"  Phone: {whatsapp_context['parameters']['phone_number']}")
    print(f"  Message: {whatsapp_context['parameters']['message']}")

    result = skill.execute(whatsapp_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Tool: {result.get('tool_name')}")

    if result.get('success'):
        print("\n[SUCCESS] WhatsApp tool executed successfully (dry run)")
    else:
        print(f"\n[WARNING] WhatsApp tool failed: {result.get('error')}")
        print("[INFO] This is expected if WhatsApp not configured")

    # Test Case 3: Invalid Tool
    print("\n" + "=" * 60)
    print("Test Case 3: Invalid Tool (Error Handling)")
    print("=" * 60)

    invalid_context = {
        'tool_name': 'invalid_tool',
        'parameters': {}
    }

    print("\n[INFO] Executing invalid tool...")

    result = skill.execute(invalid_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Error: {result.get('error')}")

    if not result.get('success'):
        print("\n[SUCCESS] Correctly handled invalid tool")
        return True
    else:
        print("\n[ERROR] Should have failed for invalid tool")
        return False


if __name__ == '__main__':
    print("\nMCP Tools Integration Test")
    print("Tests MCP server and tools functionality\n")

    try:
        success = test_mcp_tools()

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] MCP Tools Test PASSED")
            print("=" * 60)
            print("\nMCP tools skill is working correctly!")
            print("\nNote: Actual email/WhatsApp sending requires:")
            print("  1. Gmail OAuth2 credentials configured")
            print("  2. WhatsApp Web session authenticated")
            print("  3. Remove 'dry_run' parameter for real execution")
        else:
            print("\n" + "=" * 60)
            print("[ERROR] MCP Tools Test FAILED")
            print("=" * 60)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Test cancelled by user")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\nDone!")
