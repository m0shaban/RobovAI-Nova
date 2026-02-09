import asyncio
import logging
import sys

from backend.agent.graph import run_agent

logging.basicConfig(level=logging.INFO)

async def test():
    result = await run_agent(
        message="create presentation about egypt",
        user_id="test",
        platform="web"
    )
    
    print("\n=== RESULT ===")
    print(f"Success: {result.get('success')}")
    print(f"Tools: {len(result.get('tool_results', []))}")
    print(f"Answer: {result.get('final_answer')}")
    
if __name__ == "__main__":
    asyncio.run(test())
