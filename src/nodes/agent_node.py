"""
Main agent node that processes queries and decides on tool usage.
"""
from typing import Dict, Any, List
from loguru import logger
from .state import AgentState
from ..agents.model_loader import ModelLoader
from ..tools import tool_registry


class AgentNode:
    """Main agent that processes queries and uses tools."""

    def __init__(self, model_loader: ModelLoader):
        """
        Initialize the agent node.

        Args:
            model_loader: Model loader instance
        """
        self.model = model_loader

    def __call__(self, state: AgentState) -> AgentState:
        """
        Process the agent node.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        logger.info(f"Agent node processing task: {state['task']}")

        try:
            # Get available tools
            available_tools = tool_registry.list_tools()

            # Build prompt for the model
            prompt = self._build_prompt(state, available_tools)

            # Generate response
            response = self.model.generate(prompt)

            # Parse response to extract tool calls and reasoning
            tool_calls = self._parse_tool_calls(response)
            reasoning = self._extract_reasoning(response)

            # Update state
            state['messages'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': state['timestamp']
            })

            state['reasoning_steps'].append(reasoning)

            # If tool calls are needed, add to pending approvals
            if tool_calls:
                state['pending_approvals'].extend(tool_calls)
                logger.info(f"Agent requested {len(tool_calls)} tool calls")
            else:
                # No tools needed, extract final answer
                state['final_answer'] = response

            state['iteration_count'] += 1

        except Exception as e:
            logger.error(f"Agent node error: {e}")
            state['errors'].append(str(e))

        return state

    def _build_prompt(self, state: AgentState, available_tools: Dict[str, List[str]]) -> str:
        """
        Build the prompt for the model.

        Args:
            state: Current agent state
            available_tools: Available tools by category

        Returns:
            Formatted prompt
        """
        tools_str = "\n".join([
            f"- {category}: {', '.join(tools)}"
            for category, tools in available_tools.items()
        ])

        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in state['messages'][-5:]  # Last 5 messages
        ])

        prompt = f"""You are a helpful AI assistant with access to various tools.

Task: {state['task']}

Available Tools:
{tools_str}

Recent Conversation:
{conversation_history}

Based on the task, determine if you need to use any tools. If so, specify which tools and their parameters in the following format:

TOOL: <tool_name>
PARAMS: <param1=value1, param2=value2>
REASON: <why you need this tool>

If you can answer directly without tools, provide your answer clearly.

Your response:"""

        return prompt

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from model response.

        Args:
            response: Model response

        Returns:
            List of tool call dictionaries
        """
        tool_calls = []

        lines = response.split('\n')
        current_tool = None

        for line in lines:
            line = line.strip()
            if line.startswith('TOOL:'):
                if current_tool:
                    tool_calls.append(current_tool)
                tool_name = line.replace('TOOL:', '').strip()
                current_tool = {
                    'tool': tool_name,
                    'params': {},
                    'reason': ''
                }
            elif line.startswith('PARAMS:') and current_tool:
                params_str = line.replace('PARAMS:', '').strip()
                # Simple param parsing
                try:
                    params = {}
                    for param in params_str.split(','):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key.strip()] = value.strip()
                    current_tool['params'] = params
                except:
                    pass
            elif line.startswith('REASON:') and current_tool:
                current_tool['reason'] = line.replace('REASON:', '').strip()

        if current_tool:
            tool_calls.append(current_tool)

        return tool_calls

    def _extract_reasoning(self, response: str) -> str:
        """
        Extract reasoning from response.

        Args:
            response: Model response

        Returns:
            Extracted reasoning
        """
        # Simple extraction: remove tool calls
        lines = []
        for line in response.split('\n'):
            if not any(line.strip().startswith(prefix) for prefix in ['TOOL:', 'PARAMS:', 'REASON:']):
                lines.append(line)

        return '\n'.join(lines).strip()
