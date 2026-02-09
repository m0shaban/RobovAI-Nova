"""
🔧 RobovAI Nova - Tools Adapter
═══════════════════════════════════════════════════════════════

Converts existing RobovAI tools to LangGraph-compatible format.
This bridges the 60+ existing tools with the new Agent system.
"""

from typing import List, Dict, Any, Callable
from langchain_core.tools import StructuredTool, tool
from backend.tools.registry import ToolRegistry
from backend.tools.base import BaseTool
from pydantic import BaseModel, Field
import asyncio
import logging

logger = logging.getLogger("robovai.agent.tools")


class GenericToolInput(BaseModel):
    """Generic input schema that accepts any arguments from the LLM.

    The 'query' field provides backward compatibility with tools expecting a string.
    'model_config extra=allow' lets LLMs pass structured kwargs (filename, content, etc.)
    """

    query: str = Field(default="", description="Input query or command")

    model_config = {"extra": "allow"}


class ToolsAdapter:
    """
    Adapts existing RobovAI tools to LangGraph format.

    The existing tools follow this pattern:
        class MyTool(BaseTool):
            async def execute(user_input: str, user_id: str) -> Dict

    LangGraph expects:
        @tool
        async def my_tool(query: str) -> str
    """

    _cached_tools: List[StructuredTool] = []
    _initialized: bool = False

    @classmethod
    def get_all_tools(cls, user_id: str = "agent") -> List[StructuredTool]:
        """
        Get all registered tools as LangGraph StructuredTools.

        Args:
            user_id: User ID to pass to tool execution

        Returns:
            List of StructuredTool objects
        """
        if cls._initialized and cls._cached_tools:
            logger.info(f"📦 Using cached tools: {len(cls._cached_tools)} tools")
            return cls._cached_tools

        # Force registration if not done
        registered_tools = ToolRegistry.list_tools()

        if not registered_tools:
            logger.warning("⚠️ No tools registered! Attempting to register...")
            try:
                from backend.tools.loader import register_all_tools

                register_all_tools()
                registered_tools = ToolRegistry.list_tools()
                logger.info(f"✅ Registered {len(registered_tools)} tools")
            except Exception as e:
                logger.error(f"❌ Failed to register tools: {e}")
                return []

        tools = []
        logger.info(
            f"🔧 Converting {len(registered_tools)} tools to LangGraph format..."
        )

        for tool_name in registered_tools:
            try:
                tool_cls = ToolRegistry.get_tool(tool_name)
                if tool_cls:
                    wrapped = cls._wrap_tool(tool_cls, user_id)
                    if wrapped:
                        tools.append(wrapped)
                        logger.debug(f"  ✓ Wrapped: {tool_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to wrap tool {tool_name}: {e}")

        cls._cached_tools = tools
        cls._initialized = True

        logger.info(f"✅ Successfully converted {len(tools)} tools")
        return tools

    @classmethod
    def _wrap_tool(cls, tool_cls: type, user_id: str) -> StructuredTool:
        """
        Wrap a single RobovAI tool as a LangGraph StructuredTool.
        """
        try:
            # Instantiate to get metadata
            instance = tool_cls()

            # Get properties
            name = instance.name.replace("/", "")  # Remove slash prefix
            description = instance.description
            cost = instance.cost

            # Create async wrapper
            async def tool_executor(
                *args, tool_instance=instance, uid=user_id, **kwargs
            ) -> str:
                """Execute the wrapped tool"""
                import json as _json

                query = args[0] if args else kwargs.get("query")
                # Separate structured kwargs from "query"
                other_kwargs = {
                    k: v for k, v in kwargs.items() if k not in ("query", "kwargs")
                }
                # Some LLMs nest args inside a "kwargs" key
                if "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
                    other_kwargs.update(kwargs["kwargs"])

                tool_name = tool_instance.name.replace("/", "")

                try:
                    # --- Smart input reconstruction ---
                    # Priority: execute_kwargs > structured kwargs > query string > empty

                    if hasattr(tool_instance, "execute_kwargs"):
                        logger.debug(f"  ROUTE: execute_kwargs")
                        result = await tool_instance.execute_kwargs(
                            uid,
                            **{**other_kwargs, **({"query": query} if query else {})},
                        )

                    elif tool_name == "create_file" and (
                        "filename" in other_kwargs or "content" in other_kwargs
                    ):
                        # create_file expects "filename | content"
                        fn = other_kwargs.get("filename", "output.html")
                        ct = other_kwargs.get("content", query or "")
                        # Detect file extension from content if filename has no extension
                        if "." not in fn:
                            if "<html" in ct.lower() or "<!doctype" in ct.lower():
                                fn += ".html"
                            elif ct.strip().startswith("{") or ct.strip().startswith(
                                "["
                            ):
                                fn += ".json"
                            else:
                                fn += ".html"
                        input_data = f"{fn} | {ct}"
                        result = await tool_instance.execute(input_data, uid)

                    elif other_kwargs and not query:
                        # Only structured kwargs, no query string
                        input_data = _json.dumps({**other_kwargs}, ensure_ascii=False)
                        result = await tool_instance.execute(input_data, uid)

                    elif query is not None:
                        result = await tool_instance.execute(str(query), uid)

                    else:
                        result = await tool_instance.execute("", uid)

                    # --- Check result success (support both "success" and "status" keys) ---
                    is_success = (
                        result.get("success", False)
                        or result.get("status") == "success"
                    )
                    if is_success:
                        # Return rich output as JSON so downstream nodes can extract URLs/paths
                        output = result.get("output", "")
                        # Include metadata if available
                        rich = {"text": str(output)}
                        for key in (
                            "url",
                            "filepath",
                            "filename",
                            "image_url",
                            "download_url",
                        ):
                            if key in result:
                                rich[key] = result[key]

                        if len(rich) > 1:
                            ret = _json.dumps(rich, ensure_ascii=False)
                        else:
                            ret = str(output)
                        return ret
                    else:
                        return f"Tool error: {result.get('output', 'Unknown error')}"

                except Exception as e:
                    return f"Execution failed: {str(e)}"

            # Create sync wrapper for compatibility
            def sync_executor(
                query: str = None, tool_instance=instance, uid=user_id, **kwargs
            ) -> str:
                """Sync wrapper that runs the async executor"""
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            tool_executor(query, tool_instance, uid, **kwargs),
                        )
                        return future.result()
                else:
                    return asyncio.run(
                        tool_executor(query, tool_instance, uid, **kwargs)
                    )

            # Build StructuredTool
            # Use tool's own schema if defined, otherwise GenericToolInput (accepts any kwargs)
            schema = getattr(instance, "args_schema", None) or GenericToolInput
            return StructuredTool.from_function(
                func=sync_executor,
                coroutine=tool_executor,
                name=name,
                description=f"{description} (Cost: {cost} tokens)",
                args_schema=schema,
            )

        except Exception as e:
            logger.error(f"❌ Error wrapping tool: {e}")
            return None

    @classmethod
    def get_tool_by_name(cls, name: str, user_id: str = "agent") -> StructuredTool:
        """Get a specific tool by name"""
        tools = cls.get_all_tools(user_id)
        for t in tools:
            if t.name == name or t.name == name.replace("/", ""):
                return t
        return None

    @classmethod
    def get_tools_descriptions(cls) -> str:
        """Get formatted descriptions of all tools for prompts"""
        tools_info = ToolRegistry.get_all_tools_info()

        lines = ["Available Tools:"]
        for info in tools_info:
            lines.append(f"- {info['name']}: {info['description']}")

        return "\n".join(lines)

    @classmethod
    def reset_cache(cls):
        """Reset the tools cache (useful for testing)"""
        cls._cached_tools = []
        cls._initialized = False


def get_langgraph_tools(user_id: str = "agent") -> List[StructuredTool]:
    """
    Convenience function to get all LangGraph tools.

    Example:
        tools = get_langgraph_tools("user123")
        agent = create_react_agent(llm, tools)
    """
    return ToolsAdapter.get_all_tools(user_id)


def get_tool_names() -> List[str]:
    """Get list of all available tool names"""
    return [t.replace("/", "") for t in ToolRegistry.list_tools()]


# ═══════════════════════════════════════════════════════════════
# 🎯 HIGH-PRIORITY TOOLS (for complex tasks)
# ═══════════════════════════════════════════════════════════════

PRIORITY_TOOLS = [
    "generate_image",
    "weather",
    "translate_egy",
    "wikipedia",
    "chart",
    "math",
    "joke",
    "quran",
    "vision",
    "code_fix",
]


def get_priority_tools(user_id: str = "agent") -> List[StructuredTool]:
    """Get only the high-priority tools for faster execution"""
    all_tools = get_langgraph_tools(user_id)
    return [t for t in all_tools if t.name in PRIORITY_TOOLS]
