"""
MCP Tools Skill
Wraps MCP server functionality as an agent skill
"""
import logging
from typing import Dict, Any
from pathlib import Path

from skills.framework import Skill

logger = logging.getLogger(__name__)


class MCPToolsSkill(Skill):
    """Skill for executing MCP tools (external actions)"""

    def __init__(self, vault_path: str, mcp_server):
        """
        Initialize MCP tools skill

        Args:
            vault_path: Path to vault directory
            mcp_server: MCPServer instance
        """
        super().__init__(
            skill_id='mcp_tools',
            name='External Actions (MCP)',
            description='Executes external actions via MCP tools (email, WhatsApp, etc.)',
            category='communication'
        )

        self.vault_path = Path(vault_path)
        self.mcp_server = mcp_server

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate execution context

        Args:
            context: Must contain 'tool_name' and 'parameters'

        Returns:
            True if valid, False otherwise
        """
        if 'tool_name' not in context:
            logger.error("MCP skill requires 'tool_name' in context")
            return False

        if 'parameters' not in context:
            logger.error("MCP skill requires 'parameters' in context")
            return False

        return True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MCP tools skill

        Args:
            context: Execution context with tool_name and parameters

        Returns:
            Result with success status and tool output
        """
        tool_name = context['tool_name']
        parameters = context['parameters']

        # Execute tool via MCP server (handle async)
        try:
            import asyncio

            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run async execute_tool
            result = loop.run_until_complete(
                self.mcp_server.execute_tool(tool_name, parameters)
            )

            return {
                'success': result.get('success', False),
                'tool_name': tool_name,
                'result': result
            }

        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {e}")
            return {
                'success': False,
                'tool_name': tool_name,
                'error': str(e)
            }
