import asyncio
from backend.tools.registry import ToolRegistry
from backend.tools.content import SocialTool, ScriptTool
from backend.tools.business import FeasibilityTool, CalcRoiTool
from backend.tools.dev import ArduinoTool, ExplainCodeTool
from backend.tools.image import ImagineTool
from backend.tools.utility import SummarizeTool, PdfProTool, VoiceToTextTool
from backend.core.database import db_client

async def run_verification():
    print("--- 1. Registering Tools ---")
    ToolRegistry.register(SocialTool)
    ToolRegistry.register(ScriptTool)
    ToolRegistry.register(FeasibilityTool)
    ToolRegistry.register(CalcRoiTool)
    ToolRegistry.register(ArduinoTool)
    ToolRegistry.register(ExplainCodeTool)
    ToolRegistry.register(ImagineTool)
    ToolRegistry.register(SummarizeTool)
    ToolRegistry.register(PdfProTool)
    ToolRegistry.register(VoiceToTextTool)
    
    tools = ToolRegistry.list_tools()
    print(f"Registered Tools: {tools}\n")
    
    print("--- 2. Simulating Tool Execution ---")
    user_id = "test_user_123"
    
    test_commands = [
        ("/social", "New AI Coffee Shop in Cairo"),
        ("/imagine", "Cyberpunk pyramid"),
        ("/arduino", "Blink LED"),
        ("/feasibility", "Mobile App for Laundry"),
    ]
    
    for cmd, inp in test_commands:
        print(f"\nTesting {cmd} with input: '{inp}'")
        tool_cls = ToolRegistry.get_tool(cmd)
        if tool_cls:
            tool = tool_cls()
            if tool.validate_balance(100):
                res = await tool.execute(inp, user_id)
                print(f"RESULT: {res['output'][:100]}...")
                print(f"COST: {res['tokens_deducted']} tokens")
            else:
                print("Insufficient balance!")
        else:
            print(f"Tool {cmd} not found!")

if __name__ == "__main__":
    asyncio.run(run_verification())
