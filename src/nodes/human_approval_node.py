"""
Human-in-the-loop node for approving tool executions.
"""
from typing import Dict, Any, Optional, Callable
from loguru import logger
from .state import AgentState
from ..tools import tool_registry


class HumanApprovalNode:
    """Node that requests human approval for tool executions."""

    def __init__(self, approval_callback: Optional[Callable] = None, auto_approve_read_only: bool = False):
        """
        Initialize the human approval node.

        Args:
            approval_callback: Function to call for approvals (GUI will provide this)
            auto_approve_read_only: Automatically approve read-only operations
        """
        self.approval_callback = approval_callback
        self.auto_approve_read_only = auto_approve_read_only

    def __call__(self, state: AgentState) -> AgentState:
        """
        Process approval requests.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        logger.info(f"Processing {len(state['pending_approvals'])} pending approvals")

        approved = []
        rejected = []

        for tool_call in state['pending_approvals']:
            tool_name = tool_call['tool']
            tool = tool_registry.get_tool(tool_name)

            if not tool:
                logger.warning(f"Unknown tool: {tool_name}")
                rejected.append(tool_call)
                continue

            # Auto-approve read-only operations if configured
            if self.auto_approve_read_only and not tool.requires_approval:
                logger.info(f"Auto-approved read-only tool: {tool_name}")
                approved.append(tool_call)
                state['approved_tools'].append(tool_name)
                continue

            # Request human approval
            if self.approval_callback:
                approval_result = self.approval_callback(tool_call)
                if approval_result:
                    logger.info(f"Human approved tool: {tool_name}")
                    approved.append(tool_call)
                    state['approved_tools'].append(tool_name)
                else:
                    logger.info(f"Human rejected tool: {tool_name}")
                    rejected.append(tool_call)
            else:
                # No callback provided, default to approval for testing
                logger.warning(f"No approval callback, defaulting to approval for: {tool_name}")
                approved.append(tool_call)
                state['approved_tools'].append(tool_name)

        # Execute approved tools
        for tool_call in approved:
            result = self._execute_tool(tool_call)
            state['tool_outputs'].append(result)
            state['tools_used'].append(tool_call['tool'])

        # Clear pending approvals
        state['pending_approvals'] = []

        # Add rejection messages for rejected tools
        if rejected:
            rejection_msg = f"The following tools were rejected: {', '.join([t['tool'] for t in rejected])}"
            state['messages'].append({
                'role': 'system',
                'content': rejection_msg,
                'timestamp': state['timestamp']
            })

        return state

    def _execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call.

        Args:
            tool_call: Tool call specification

        Returns:
            Tool execution result
        """
        tool_name = tool_call['tool']
        params = tool_call.get('params', {})

        logger.info(f"Executing tool: {tool_name} with params: {params}")

        try:
            output = tool_registry.execute_tool(tool_name, **params)
            return {
                'tool': tool_name,
                'params': params,
                'output': output.model_dump(),
                'success': output.success
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                'tool': tool_name,
                'params': params,
                'output': None,
                'success': False,
                'error': str(e)
            }
