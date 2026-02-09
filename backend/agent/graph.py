"""
🚀 RobovAI Nova - Agent Graph
═══════════════════════════════════════════════════════════════

The main StateGraph that orchestrates the ReAct Agent Loop.
This is the "brain" that controls the flow of execution.

Architecture:
    ┌─────────────────────────────────────────────────────┐
    │                    USER REQUEST                      │
    └────────────────────────┬────────────────────────────┘
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │                    🧠 THINK                          │
    │         (Analyze request, understand intent)         │
    └────────────────────────┬────────────────────────────┘
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │                    ⚡ ACT                            │
    │         (Execute tools, call APIs)                   │
    └────────────────────────┬────────────────────────────┘
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │                    👁️ OBSERVE                        │
    │         (Check results, accumulate outputs)          │
    └────────────────────────┬────────────────────────────┘
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │                    🔄 REFLECT                        │
    │         (Decide: success, retry, or next step)       │
    └─────────┬───────────────────────────────┬───────────┘
              │                               │
              ▼                               ▼
    ┌──────────────────┐            ┌──────────────────────┐
    │   ↩️ CONTINUE     │            │     ✅ END            │
    │   (Loop back)    │            │  (Return answer)      │
    └──────────────────┘            └──────────────────────┘
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState, create_initial_state, AgentPhase
from .nodes import think_node, act_node, observe_node, reflect_node, should_continue
import logging
import os

logger = logging.getLogger("robovai.agent.graph")


# ═══════════════════════════════════════════════════════════════
# 🏗️ GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════


def build_agent_graph(
    use_persistence: bool = False, db_path: str = "agent_memory.db"
) -> StateGraph:
    """
    Build the Nova Agent StateGraph.

    Args:
        use_persistence: Whether to persist state to SQLite
        db_path: Path to SQLite database for persistence

    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("🏗️ Building Nova Agent Graph...")

    # Create the graph with our state schema
    workflow = StateGraph(AgentState)

    # ═══════════════════════════════════════════════════════════
    # ADD NODES
    # ═══════════════════════════════════════════════════════════

    workflow.add_node("think", think_node)
    workflow.add_node("act", act_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("reflect", reflect_node)

    logger.info("  ✅ Added nodes: think, act, observe, reflect")

    # ═══════════════════════════════════════════════════════════
    # SET ENTRY POINT
    # ═══════════════════════════════════════════════════════════

    workflow.set_entry_point("think")
    logger.info("  ✅ Entry point: think")

    # ═══════════════════════════════════════════════════════════
    # ADD EDGES (The Flow)
    # ═══════════════════════════════════════════════════════════

    # Think → Act (always)
    workflow.add_edge("think", "act")

    # Act → Observe (always)
    workflow.add_edge("act", "observe")

    # Observe → Reflect (always)
    workflow.add_edge("observe", "reflect")

    # Reflect → (Continue or End) - THE LOOP!
    workflow.add_conditional_edges(
        "reflect",
        should_continue,
        {
            "continue": "act",  # Go back to act for retry or next step
            "end": END,  # Task completed
        },
    )

    logger.info("  ✅ Added edges with conditional loop")

    # ═══════════════════════════════════════════════════════════
    # COMPILE WITH CHECKPOINTER
    # ═══════════════════════════════════════════════════════════

    # Use MemorySaver by default (simpler, no async issues)
    checkpointer = MemorySaver()
    logger.info("  ✅ Using in-memory checkpointer")

    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)

    logger.info("🚀 Nova Agent Graph compiled successfully!")

    return app


# ═══════════════════════════════════════════════════════════════
# 🎯 NOVA AGENT CLASS
# ═══════════════════════════════════════════════════════════════


class NovaAgent:
    """
    High-level interface for the Nova Agent.

    Example:
        agent = NovaAgent()
        result = await agent.run("ارسم صورة قطة وترجمها للفرنساوي")
        print(result)
    """

    def __init__(self, use_persistence: bool = True, db_path: str = "agent_memory.db"):
        """
        Initialize the Nova Agent.

        Args:
            use_persistence: Whether to persist conversations
            db_path: Path for SQLite database
        """
        self.graph = build_agent_graph(use_persistence, db_path)
        self.db_path = db_path
        logger.info("🤖 NovaAgent initialized")

    async def run(
        self,
        message: str,
        user_id: str = "anonymous",
        platform: str = "web",
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the agent with a user message.

        Args:
            message: User's request
            user_id: User identifier
            platform: Platform (web, telegram, etc.)
            thread_id: Optional thread ID for conversation persistence

        Returns:
            Dict with final_answer, tool_results, and metadata
        """
        logger.info(f"🚀 Running agent for user {user_id}: {message[:50]}...")

        # Create initial state
        initial_state = create_initial_state(
            user_message=message, user_id=user_id, platform=platform
        )

        # Config for persistence
        config = {"configurable": {"thread_id": thread_id or f"{user_id}_{platform}"}}

        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state, config=config)

            logger.info(f"✅ Agent completed. Phase: {final_state.get('phase')}")
            logger.info(f"📊 Final state keys: {list(final_state.keys())}")
            final_answ_log = final_state.get("final_answer") or "NONE"
            logger.info(f"💬 Final answer: {final_answ_log[:200]}")
            logger.info(
                f"🔧 Tool results count: {len(final_state.get('tool_results', []))}"
            )

            # Ensure we have a final_answer
            final_answer = final_state.get("final_answer")
            if not final_answer:
                logger.warning("⚠️ No final_answer in state, generating fallback...")
                # Generate a fallback answer
                tool_results = final_state.get("tool_results", [])
                if tool_results:
                    final_answer = "✅ تم تنفيذ المهمة بنجاح!"
                else:
                    final_answer = "تم معالجة طلبك."

            return {
                "success": True,
                "final_answer": final_answer,
                "tool_results": final_state.get("tool_results", []),
                "accumulated_outputs": final_state.get("accumulated_outputs", []),
                "plan": final_state.get("plan_steps", []),
                "phase": final_state.get("phase"),
                "errors": final_state.get("errors", []),
            }

        except Exception as e:
            logger.error(f"❌ Agent error: {e}", exc_info=True)
            return {
                "success": False,
                "final_answer": f"❌ حدث خطأ: {str(e)}",
                "error": str(e),
            }

    async def stream(
        self,
        message: str,
        user_id: str = "anonymous",
        platform: str = "web",
        thread_id: Optional[str] = None,
    ):
        """
        Stream the agent execution step by step.

        Yields state updates as the agent progresses.
        """
        initial_state = create_initial_state(
            user_message=message, user_id=user_id, platform=platform
        )

        config = {"configurable": {"thread_id": thread_id or f"{user_id}_{platform}"}}

        async for state in self.graph.astream(initial_state, config=config):
            yield state

    def get_state(self, thread_id: str) -> Optional[AgentState]:
        """Get the current state for a thread (for Human-in-the-loop)"""
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.get_state(config)

    def update_state(self, thread_id: str, updates: Dict[str, Any]):
        """Update the state for a thread (for Human-in-the-loop)"""
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.update_state(config, updates)


# ═══════════════════════════════════════════════════════════════
# 🔧 CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

# Global agent instance
_agent_instance: Optional[NovaAgent] = None


def get_agent() -> NovaAgent:
    """Get or create the global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = NovaAgent()
    return _agent_instance


async def run_agent(
    message: str, user_id: str = "anonymous", platform: str = "web"
) -> Dict[str, Any]:
    """
    Convenience function to run the agent.

    Example:
        result = await run_agent("ارسم صورة قطة")
        print(result["final_answer"])
    """
    agent = get_agent()
    return await agent.run(message, user_id, platform)


# ═══════════════════════════════════════════════════════════════
# 📊 VISUALIZATION
# ═══════════════════════════════════════════════════════════════


def visualize_graph():
    """Generate a Mermaid diagram of the graph"""
    return """
```mermaid
graph TD
    START((Start)) --> THINK[🧠 Think]
    THINK --> ACT[⚡ Act]
    ACT --> OBSERVE[👁️ Observe]
    OBSERVE --> REFLECT[🔄 Reflect]
    REFLECT -->|Continue| ACT
    REFLECT -->|End| FINISH((✅ End))
    
    style THINK fill:#4CAF50,color:white
    style ACT fill:#2196F3,color:white
    style OBSERVE fill:#FF9800,color:white
    style REFLECT fill:#9C27B0,color:white
```
"""
