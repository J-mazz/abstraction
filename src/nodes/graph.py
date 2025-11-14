"""
LangGraph workflow definition.
"""
from typing import Callable, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from loguru import logger

from .state import AgentState
from .agent_node import AgentNode
from .human_approval_node import HumanApprovalNode
from .reasoning_node import ReasoningNode
from ..agents.model_loader import ModelLoader


class AgentGraph:
    """Main agent workflow graph."""

    def __init__(
        self,
        model_loader: ModelLoader,
        approval_callback: Optional[Callable] = None,
        auto_approve_read_only: bool = False,
        min_confidence: float = 0.7,
        max_iterations: int = 5
    ):
        """
        Initialize the agent graph.

        Args:
            model_loader: Model loader instance
            approval_callback: Callback for human approvals
            auto_approve_read_only: Auto-approve read-only tools
            min_confidence: Minimum confidence threshold
            max_iterations: Maximum iterations
        """
        self.model_loader = model_loader
        self.max_iterations = max_iterations

        # Initialize nodes
        self.agent_node = AgentNode(model_loader)
        self.approval_node = HumanApprovalNode(
            approval_callback=approval_callback,
            auto_approve_read_only=auto_approve_read_only
        )
        self.reasoning_node = ReasoningNode(
            model_loader=model_loader,
            min_confidence=min_confidence
        )

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Compiled graph
        """
        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("human_approval", self.approval_node)
        workflow.add_node("reasoning", self.reasoning_node)

        # Define the flow
        workflow.set_entry_point("agent")

        # After agent: go to human approval if there are pending approvals
        workflow.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {
                "human_approval": "human_approval",
                "reasoning": "reasoning",
                "end": END
            }
        )

        # After human approval: go to reasoning
        workflow.add_edge("human_approval", "reasoning")

        # After reasoning: decide whether to continue or end
        workflow.add_conditional_edges(
            "reasoning",
            self._route_after_reasoning,
            {
                "agent": "agent",
                "end": END
            }
        )

        # Compile
        compiled = workflow.compile()
        logger.info("Agent graph compiled successfully")

        return compiled

    def _route_after_agent(self, state: AgentState) -> str:
        """
        Route after agent node.

        Args:
            state: Current state

        Returns:
            Next node name
        """
        # If there are pending approvals, go to human approval
        if state['pending_approvals']:
            return "human_approval"

        # If we have a final answer, go to reasoning for validation
        if state['final_answer']:
            return "reasoning"

        # If we hit max iterations, end
        if state['iteration_count'] >= self.max_iterations:
            return "end"

        # Otherwise go to reasoning
        return "reasoning"

    def _route_after_reasoning(self, state: AgentState) -> str:
        """
        Route after reasoning node.

        Args:
            state: Current state

        Returns:
            Next node name
        """
        # If we have a final answer with high confidence, end
        if state['final_answer'] and state['confidence_score'] >= 0.7:
            return "end"

        # If we hit max iterations, end
        if state['iteration_count'] >= self.max_iterations:
            return "end"

        # If there are errors, end
        if state['errors']:
            return "end"

        # Otherwise continue to agent
        return "agent"

    def run(self, task: str, session_id: str) -> AgentState:
        """
        Run the agent on a task.

        Args:
            task: Task to complete
            session_id: Session ID for memory

        Returns:
            Final state
        """
        # Initialize state
        initial_state: AgentState = {
            'messages': [{
                'role': 'user',
                'content': task,
                'timestamp': datetime.now().isoformat()
            }],
            'task': task,
            'tools_used': [],
            'tool_outputs': [],
            'pending_approvals': [],
            'approved_tools': [],
            'reasoning_steps': [],
            'final_answer': None,
            'session_id': session_id,
            'iteration_count': 0,
            'max_iterations': self.max_iterations,
            'confidence_score': 0.0,
            'timestamp': datetime.now().isoformat(),
            'errors': []
        }

        logger.info(f"Starting agent workflow for task: {task}")

        # Run graph
        final_state = self.graph.invoke(initial_state)

        logger.info(f"Agent workflow completed in {final_state['iteration_count']} iterations")

        return final_state
