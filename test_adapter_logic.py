import asyncio
from backend.agent.tools_adapter import ToolsAdapter
from backend.tools.base import BaseTool
from pydantic import BaseModel, Field


class MySchema(BaseModel):
    arg1: str
    arg2: int = 10


class MyTool(BaseTool):
    args_schema = MySchema

    @property
    def name(self) -> str:
        return "test_tool"

    @property
    def description(self) -> str:
        return "A test tool"

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, query: str, user_id: str) -> dict:
        return {"status": "success", "output": f"Legacy: {query}"}

    async def execute_kwargs(self, user_id: str, **kwargs) -> dict:
        return {
            "status": "success",
            "output": f"Structured: arg1={kwargs.get('arg1')}, arg2={kwargs.get('arg2')}",
        }


async def main():
    adapter = ToolsAdapter()

    # We need to manually wrap it as adapter does
    lc_tool = adapter._wrap_tool(MyTool, "user123")
    wrapped_coro = lc_tool.coroutine

    print("--- Test 1: Structured Call (LangChain style kwargs) ---")
    try:
        res = await wrapped_coro(arg1="hello", arg2=20)
        print(f"Result 1: {res}")
    except Exception as e:
        print(f"Error 1: {e}")

    print("\n--- Test 2: Legacy Call (String args) ---")
    try:
        res = await wrapped_coro("some_string_query")
        print(f"Result 2: {res}")
    except Exception as e:
        print(f"Error 2: {e}")

    print(
        "\n--- Test 3: Mixed/Confused Call (Simulate LLM putting JSON in first arg?) ---"
    )
    try:
        import json

        json_str = json.dumps({"arg1": "json_arg", "arg2": 99})
        res = await wrapped_coro(json_str)
        print(f"Result 3: {res}")
    except Exception as e:
        print(f"Error 3: {e}")


if __name__ == "__main__":
    asyncio.run(main())
