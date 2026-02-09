"""
🧠 RobovAI Nova - Agent State Definition
═══════════════════════════════════════════════════════════════

Defines the state that flows through the Agent Graph.
This is the "memory" of the agent during execution.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentPhase(str, Enum):
    """Current phase of agent execution"""
    THINKING = "thinking"       # Analyzing the task
    PLANNING = "planning"       # Creating execution plan
    ACTING = "acting"           # Executing tools
    OBSERVING = "observing"     # Checking results
    REFLECTING = "reflecting"   # Deciding next step
    COMPLETED = "completed"     # Task finished
    FAILED = "failed"           # Task failed after retries


class ToolCall(TypedDict):
    """Structure for a tool call"""
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: str


class ToolResult(TypedDict):
    """Structure for tool execution result"""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str]
    execution_time_ms: float


class AgentState(TypedDict):
    """
    🚀 Nova Agent State - The Brain's Memory
    
    This state flows through every node in the graph.
    Each node can read and modify parts of this state.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # 💬 CONVERSATION
    # ═══════════════════════════════════════════════════════════════
    
    # Message history with LangGraph's add_messages reducer
    messages: Annotated[list, add_messages]
    
    # User context
    user_id: str
    platform: str  # "web", "telegram", "whatsapp"
    language: str  # "ar-EG", "en", etc.
    
    # ═══════════════════════════════════════════════════════════════
    # 🎯 TASK MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    # Original user request
    original_request: str
    
    # Task analysis
    task_understanding: str  # What the agent thinks the user wants
    task_complexity: str     # "simple", "medium", "complex"
    
    # Execution plan
    plan_steps: List[str]    # List of steps to execute
    current_step_index: int  # Which step we're on (0-indexed)
    
    # ═══════════════════════════════════════════════════════════════
    # 🔧 TOOL EXECUTION
    # ═══════════════════════════════════════════════════════════════
    
    # Tool calls made in current step
    pending_tool_calls: List[ToolCall]
    
    # Results from executed tools
    tool_results: List[ToolResult]
    
    # Accumulated outputs (images, texts, etc.)
    accumulated_outputs: List[Dict[str, Any]]
    
    # ═══════════════════════════════════════════════════════════════
    # 🔄 CONTROL FLOW
    # ═══════════════════════════════════════════════════════════════
    
    # Current phase
    phase: str  # AgentPhase value
    
    # Retry logic
    retry_count: int
    max_retries: int  # Default: 3
    
    # Error tracking
    errors: List[str]
    last_error: Optional[str]
    
    # ═══════════════════════════════════════════════════════════════
    # 📤 OUTPUT
    # ═══════════════════════════════════════════════════════════════
    
    # Final answer to user
    final_answer: Optional[str]
    
    # Should we end the loop?
    should_end: bool
    
    # Human intervention needed?
    needs_human_input: bool
    human_input_reason: Optional[str]


def create_initial_state(
    user_message: str,
    user_id: str = "anonymous",
    platform: str = "web",
    language: str = "ar-EG"
) -> AgentState:
    """
    Create initial state for a new agent run.
    
    Args:
        user_message: The user's request
        user_id: User identifier
        platform: Platform the request came from
        language: User's preferred language
    
    Returns:
        Initialized AgentState
    """
    return AgentState(
        # Conversation
        messages=[("user", user_message)],
        user_id=user_id,
        platform=platform,
        language=language,
        
        # Task
        original_request=user_message,
        task_understanding="",
        task_complexity="medium",
        
        # Plan
        plan_steps=[],
        current_step_index=0,
        
        # Tools
        pending_tool_calls=[],
        tool_results=[],
        accumulated_outputs=[],
        
        # Control
        phase=AgentPhase.THINKING.value,
        retry_count=0,
        max_retries=3,
        errors=[],
        last_error=None,
        
        # Output
        final_answer=None,
        should_end=False,
        needs_human_input=False,
        human_input_reason=None
    )


def state_summary(state: AgentState) -> str:
    """Get a human-readable summary of current state"""
    return f"""
╔══════════════════════════════════════════════════════════════╗
║  🤖 Nova Agent State Summary                                  ║
╠══════════════════════════════════════════════════════════════╣
║  Phase: {state.get('phase', 'unknown'):<15} Step: {state.get('current_step_index', 0)+1}/{len(state.get('plan_steps', []))}
║  User: {state.get('user_id', 'anonymous'):<20} Platform: {state.get('platform', 'web')}
║  Retries: {state.get('retry_count', 0)}/{state.get('max_retries', 3)}
║  Tools Executed: {len(state.get('tool_results', []))}
║  Errors: {len(state.get('errors', []))}
╚══════════════════════════════════════════════════════════════╝
"""
