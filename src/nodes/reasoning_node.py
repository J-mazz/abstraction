"""
Reasoning/reflection node for assessing outputs and planning.
"""
from typing import Dict, Any
from loguru import logger
from .state import AgentState
from ..agents.model_loader import ModelLoader


class ReasoningNode:
    """Node that performs reasoning and reflection on agent outputs."""

    def __init__(self, model_loader: ModelLoader, min_confidence: float = 0.7):
        """
        Initialize the reasoning node.

        Args:
            model_loader: Model loader instance
            min_confidence: Minimum confidence threshold
        """
        self.model = model_loader
        self.min_confidence = min_confidence

    def __call__(self, state: AgentState) -> AgentState:
        """
        Perform reasoning and reflection.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        logger.info("Reasoning node assessing current state")

        try:
            # Build reflection prompt
            prompt = self._build_reflection_prompt(state)

            # Generate reflection
            reflection = self.model.generate(prompt, temperature=0.3, max_new_tokens=256)

            # Extract confidence score
            confidence = self._extract_confidence(reflection)
            state['confidence_score'] = confidence

            # Add reflection to reasoning steps
            state['reasoning_steps'].append(f"Reflection: {reflection}")

            # Assess if we should continue or finish
            should_continue = self._should_continue(state, confidence)

            if should_continue:
                logger.info(f"Low confidence ({confidence:.2f}), continuing iteration")
            else:
                logger.info(f"High confidence ({confidence:.2f}), ready to finalize")

            # Add reflection message
            state['messages'].append({
                'role': 'system',
                'content': f"Reflection (confidence: {confidence:.2f}): {reflection}",
                'timestamp': state['timestamp']
            })

        except Exception as e:
            logger.error(f"Reasoning node error: {e}")
            state['errors'].append(str(e))
            state['confidence_score'] = 0.5  # Default medium confidence

        return state

    def _build_reflection_prompt(self, state: AgentState) -> str:
        """
        Build the reflection prompt.

        Args:
            state: Current agent state

        Returns:
            Formatted prompt
        """
        recent_reasoning = state['reasoning_steps'][-3:] if state['reasoning_steps'] else []
        recent_tools = state['tool_outputs'][-3:] if state['tool_outputs'] else []

        prompt = f"""Reflect on the current progress towards completing this task:

Task: {state['task']}

Recent Reasoning:
{chr(10).join(recent_reasoning) if recent_reasoning else 'No reasoning yet'}

Recent Tool Outputs:
{chr(10).join([f"- {t['tool']}: {'Success' if t['success'] else 'Failed'}" for t in recent_tools]) if recent_tools else 'No tools used yet'}

Iteration: {state['iteration_count']} / {state['max_iterations']}

Assess:
1. Are we making progress towards the goal?
2. Do we have enough information to answer?
3. Should we use additional tools or can we provide a final answer?

Provide your confidence level (0.0 to 1.0) and brief reasoning.

Format:
CONFIDENCE: <0.0-1.0>
REASONING: <your assessment>

Your reflection:"""

        return prompt

    def _extract_confidence(self, reflection: str) -> float:
        """
        Extract confidence score from reflection.

        Args:
            reflection: Reflection text

        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            for line in reflection.split('\n'):
                if line.strip().startswith('CONFIDENCE:'):
                    confidence_str = line.replace('CONFIDENCE:', '').strip()
                    confidence = float(confidence_str)
                    return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        except:
            pass

        # Default confidence if not found
        return 0.5

    def _should_continue(self, state: AgentState, confidence: float) -> bool:
        """
        Determine if we should continue iterating.

        Args:
            state: Current agent state
            confidence: Current confidence score

        Returns:
            True if should continue, False otherwise
        """
        # Stop if max iterations reached
        if state['iteration_count'] >= state['max_iterations']:
            return False

        # Stop if confidence is high enough
        if confidence >= self.min_confidence:
            return False

        # Stop if we have a final answer
        if state['final_answer']:
            return False

        # Continue otherwise
        return True
