"""
🧪 Test Agent Execution - Debug Version (V2)
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.agent.graph import run_agent

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_presentation():
    """Test presentation creation"""
    print("\n" + "=" * 60)
    print("🧪 Testing: Presentation Tool with Schema")
    print("=" * 60 + "\n")

    result = await run_agent(
        message="Create a presentation about 'The Future of AI' with 3 slides: Intro, Benefits, Risks",
        user_id="test_user",
        platform="web",
    )

    print("\n" + "=" * 60)
    print("📊 RESULT:")
    print("=" * 60)
    print(f"Success: {result.get('success')}")
    print(f"Phase: {result.get('phase')}")
    print(f"Plan: {result.get('plan')}")
    print(f"Tool Results: {len(result.get('tool_results', []))} items")
    print(f"Errors: {result.get('errors')}")
    print(f"\nFinal Answer:\n{result.get('final_answer')}")
    print("=" * 60 + "\n")

    return result


if __name__ == "__main__":
    asyncio.run(test_presentation())
