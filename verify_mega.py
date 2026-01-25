import asyncio
from backend.tools.registry import ToolRegistry
# Import all tool modules to trigger registration (assuming decorators or manual registration)
# Since I used manual registration in the previous verify script, I need to register all classes here.

# Ideally, we should have a function in each module to register its tools.
# But for now, I will import classes and register them manually.

from backend.tools.fun import (RoastTool, RizzTool, DreamTool, HoroscopeTool, FightTool,
                               JokeTool, CatTool, DogTool, BoredTool, TriviaTool)
from backend.tools.utility import (IpTool, CryptoTool, ShortenTool, PasswordTool, UuidTool,
                                   QrTool, WebsiteStatusTool, CurrencyTool, ColorTool, UnitTool)
from backend.tools.dev import (CodeFixTool, SqlTool, RegexTool, ExplainCodeTool, ArduinoTool,
                               TimestampTool, HashTool, LoremTool, JsonTool, Base64Tool)
from backend.tools.life import (WeatherTool, WikiTool, DefinitionTool, NumberFactTool, HolidayTool,
                                TravelPlanTool, MealPlanTool, WorkoutTool, GiftTool, MovieRecTool)
from backend.tools.edu import (SocialTool, ScriptTool, EmailFormalTool, EmailAngryTool,
                               Eli5Tool, QuizTool, BookRecTool, TranslateEgyTool, GrammarTool, SynonymTool)

async def check_all_tools():
    # 1. Register Batch 1
    tools_classes = [
        RoastTool, RizzTool, DreamTool, HoroscopeTool, FightTool, JokeTool, CatTool, DogTool, BoredTool, TriviaTool,
        IpTool, CryptoTool, ShortenTool, PasswordTool, UuidTool, QrTool, WebsiteStatusTool, CurrencyTool, ColorTool, UnitTool,
        CodeFixTool, SqlTool, RegexTool, ExplainCodeTool, ArduinoTool, TimestampTool, HashTool, LoremTool, JsonTool, Base64Tool,
        WeatherTool, WikiTool, DefinitionTool, NumberFactTool, HolidayTool, TravelPlanTool, MealPlanTool, WorkoutTool, GiftTool, MovieRecTool,
        SocialTool, ScriptTool, EmailFormalTool, EmailAngryTool, Eli5Tool, QuizTool, BookRecTool, TranslateEgyTool, GrammarTool, SynonymTool
    ]
    
    print(f"--- Registering {len(tools_classes)} Tools ---")
    for cls in tools_classes:
        ToolRegistry.register(cls)
        
    print(f"Total Registered: {len(ToolRegistry.list_tools())}\n")
    
    # 2. Test Execution (Sample 1 from each category)
    test_cases = [
        ("/joke", ""),
        ("/password", "16"),
        ("/timestamp", ""),
        ("/weather", ""),
        ("/eli5", "Quantum Physics")
    ]
    
    print("--- Running Sample Tests ---")
    for cmd, inp in test_cases:
        print(f"Testing {cmd}...")
        tool_cls = ToolRegistry.get_tool(cmd)
        if tool_cls:
            tool = tool_cls()
            try:
                res = await tool.execute(inp, "test_user")
                print(f"SUCCESS: {res['output'][:50]}...")
            except Exception as e:
                print(f"ERROR: {e}")
        else:
            print(f"FAIL: Tool {cmd} not found")

if __name__ == "__main__":
    asyncio.run(check_all_tools())
