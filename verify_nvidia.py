import asyncio
from backend.tools.loader import register_all_tools
from backend.tools.registry import ToolRegistry
from backend.core.config import settings

async def main():
    print(f"Testing NVIDIA Model: {settings.NVIDIA_MODEL}")
    register_all_tools()
    
    cmd = "/code_fix"
    input_text = "def foo(: print('broken')"
    
    tool_cls = ToolRegistry.get_tool(cmd)
    if not tool_cls:
        print(f"FAIL: {cmd} not found")
        return

    tool = tool_cls()
    print(f"Testing {cmd}...")
    try:
        res = await tool.execute(input_text, "test_user")
        print(f"SUCCESS Result: {res}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
