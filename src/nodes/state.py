"""
State definitions for the LangGraph agent.
"""
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from datetime import datetime


class AgentState(TypedDict):
    """State for the agent graph."""

    # Messages in the conversation
    messages: Annotated[List[Dict[str, Any]], add_messages]

    # Current task/query
    task: str

    # Tools to use
    tools_used: List[str]

    # Tool outputs
    tool_outputs: List[Dict[str, Any]]

    # Pending tool calls awaiting approval
    pending_approvals: List[Dict[str, Any]]

    # Approved tool calls
    approved_tools: List[str]

    # Reasoning/reflection outputs
    reasoning_steps: List[str]

    # Final answer
    final_answer: Optional[str]

    # Metadata
    session_id: str
    iteration_count: int
    max_iterations: int
    confidence_score: float
    timestamp: str

    # Error tracking
    errors: List[str]
