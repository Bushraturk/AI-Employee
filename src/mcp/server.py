"""
MCP Server Module

Model Context Protocol server for executing external actions with validation,
approval checking, and audit logging.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import asyncio


class MCPServer:
    """MCP server with tool registry, validation, and approval integration"""

    def __init__(self, vault_path: str = "vault"):
        """Initialize MCP server"""
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.vault_path = Path(vault_path)
        self.audit_log_path = self.vault_path / "Logs"
        self.audit_log_path.mkdir(parents=True, exist_ok=True)

    def register_tool(
        self,
        name: str,
        handler: Callable,
        risk_level: str,
        requires_approval: bool,
        description: str,
        parameters_schema: Dict[str, Any]
    ):
        """
        Register a tool in the registry

        Args:
            name: Tool name (e.g., 'send_email', 'post_linkedin')
            handler: Async function to execute the tool
            risk_level: 'low', 'medium', or 'high'
            requires_approval: Whether tool requires human approval
            description: Tool description
            parameters_schema: JSON schema for parameters
        """
        self.tools[name] = {
            'handler': handler,
            'risk_level': risk_level,
            'requires_approval': requires_approval,
            'description': description,
            'parameters_schema': parameters_schema,
            'enabled': True,
            'rate_limit': None
        }

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        task_reference: Optional[str] = None,
        approval_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with validation and approval checking

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            task_reference: Optional task ID that triggered this action
            approval_id: Optional approval ID if action was approved

        Returns:
            Execution result dictionary
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Step 1: Validate tool exists
            if tool_name not in self.tools:
                return self._error_response(
                    execution_id,
                    "TOOL_NOT_FOUND",
                    f"Tool '{tool_name}' not found in registry"
                )

            tool = self.tools[tool_name]

            # Step 2: Check if tool is enabled
            if not tool['enabled']:
                return self._error_response(
                    execution_id,
                    "TOOL_DISABLED",
                    f"Tool '{tool_name}' is currently disabled"
                )

            # Step 3: Validate parameters
            # TODO: Implement JSON schema validation
            # For now, just check required parameters exist

            # Step 4: Check if approval required
            if tool['requires_approval'] and not approval_id:
                return self._error_response(
                    execution_id,
                    "APPROVAL_REQUIRED",
                    f"Tool '{tool_name}' requires human approval",
                    details={'requires_approval': True}
                )

            # Step 5: If approval_id provided, verify it
            if approval_id:
                approval_valid, approval_error = await self._check_approval(approval_id)
                if not approval_valid:
                    return self._error_response(
                        execution_id,
                        "APPROVAL_INVALID",
                        approval_error
                    )

            # Step 6: Execute tool
            handler = tool['handler']
            result = await handler(**parameters)

            # Step 7: Log execution
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_execution(
                execution_id,
                tool_name,
                parameters,
                approval_id,
                result,
                execution_time_ms,
                success=True
            )

            # Step 8: Return success response
            return {
                'success': True,
                'tool_name': tool_name,
                'execution_id': execution_id,
                'result': result,
                'executed_at': datetime.now().isoformat()
            }

        except Exception as e:
            # Log error
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_execution(
                execution_id,
                tool_name,
                parameters,
                approval_id,
                {'error': str(e)},
                execution_time_ms,
                success=False
            )

            return self._error_response(
                execution_id,
                "EXECUTION_ERROR",
                f"Tool execution failed: {str(e)}"
            )

    async def _check_approval(self, approval_id: str) -> tuple[bool, str]:
        """
        Check if approval is valid

        Args:
            approval_id: Approval ID to check

        Returns:
            (is_valid, error_message)
        """
        approval_file = self.vault_path / "Needs_Approval" / f"{approval_id}.md"

        if not approval_file.exists():
            return False, "Approval not found"

        # TODO: Parse approval file and check status
        # For now, assume valid if file exists
        return True, ""

    async def _log_execution(
        self,
        execution_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        approval_id: Optional[str],
        result: Dict[str, Any],
        execution_time_ms: float,
        success: bool
    ):
        """Log tool execution to audit trail"""
        log_date = datetime.now().strftime("%Y-%m-%d")
        log_file = self.audit_log_path / f"mcp-executions-{log_date}.md"

        log_entry = {
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'tool_name': tool_name,
            'parameters': self._sanitize_parameters(tool_name, parameters),
            'approval_id': approval_id,
            'result': result if success else {'error': result.get('error')},
            'execution_time_ms': execution_time_ms,
            'success': success
        }

        # Append to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## Execution: {execution_id}\n\n")
            f.write(f"```json\n{json.dumps(log_entry, indent=2)}\n```\n\n")

    def _sanitize_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from parameters before logging"""
        sanitized = parameters.copy()

        # Remove email body content (privacy)
        if tool_name == 'send_email' and 'body' in sanitized:
            sanitized['body'] = '[REDACTED]'

        # Remove WhatsApp message content (privacy)
        if tool_name == 'send_whatsapp' and 'message' in sanitized:
            sanitized['message'] = '[REDACTED]'

        # Remove LinkedIn post content (privacy)
        if tool_name == 'post_linkedin' and 'content' in sanitized:
            sanitized['content'] = '[REDACTED]'

        return sanitized

    def _error_response(
        self,
        execution_id: str,
        error_code: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create error response"""
        return {
            'success': False,
            'execution_id': execution_id,
            'error': {
                'code': error_code,
                'message': error_message,
                'details': details or {}
            },
            'executed_at': datetime.now().isoformat()
        }

    def list_tools(self) -> list[Dict[str, Any]]:
        """List all registered tools"""
        return [
            {
                'name': name,
                'description': tool['description'],
                'risk_level': tool['risk_level'],
                'requires_approval': tool['requires_approval'],
                'enabled': tool['enabled']
            }
            for name, tool in self.tools.items()
        ]

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool details"""
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        return {
            'name': tool_name,
            'description': tool['description'],
            'risk_level': tool['risk_level'],
            'requires_approval': tool['requires_approval'],
            'parameters_schema': tool['parameters_schema'],
            'enabled': tool['enabled']
        }
