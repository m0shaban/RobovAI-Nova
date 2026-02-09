"""
🧪 RobovAI Nova - Agent Test Script
═══════════════════════════════════════════════════════════════

Tests the LangGraph Agent with various scenarios.

Run: python scripts/test_agent.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_simple_task():
    """Test a simple single-step task"""
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Simple Task (Joke)")
    print("=" * 60)
    
    from backend.agent.graph import run_agent
    
    result = await run_agent(
        message="احكيلي نكتة",
        user_id="test_user",
        platform="test"
    )
    
    print(f"\n✅ Success: {result.get('success')}")
    print(f"📝 Answer: {result.get('final_answer', 'No answer')[:300]}")
    print(f"🔧 Tools Used: {len(result.get('tool_results', []))}")
    print(f"📊 Phase: {result.get('phase')}")
    
    return result.get('success', False)


async def test_tool_task():
    """Test a task that requires a tool"""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Tool Task (Weather)")
    print("=" * 60)
    
    from backend.agent.graph import run_agent
    
    result = await run_agent(
        message="ايه الطقس في القاهرة؟",
        user_id="test_user",
        platform="test"
    )
    
    print(f"\n✅ Success: {result.get('success')}")
    print(f"📝 Answer: {result.get('final_answer', 'No answer')[:300]}")
    print(f"🔧 Tools Used: {len(result.get('tool_results', []))}")
    print(f"📋 Plan: {result.get('plan', [])}")
    
    return result.get('success', False)


async def test_multi_step_task():
    """Test a complex multi-step task"""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Multi-Step Task")
    print("=" * 60)
    
    from backend.agent.graph import run_agent
    
    result = await run_agent(
        message="ابحث عن مصر في ويكيبيديا واحكيلي نكتة عنها",
        user_id="test_user",
        platform="test"
    )
    
    print(f"\n✅ Success: {result.get('success')}")
    print(f"📝 Answer: {result.get('final_answer', 'No answer')[:500]}")
    print(f"📋 Plan: {result.get('plan', [])}")
    print(f"🔧 Outputs: {len(result.get('accumulated_outputs', []))}")
    
    return result.get('success', False)


async def test_tools_adapter():
    """Test the tools adapter"""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Tools Adapter")
    print("=" * 60)
    
    from backend.agent.tools_adapter import get_langgraph_tools, get_tool_names
    
    tool_names = get_tool_names()
    print(f"\n📦 Registered Tools: {len(tool_names)}")
    print(f"   First 10: {tool_names[:10]}")
    
    tools = get_langgraph_tools("test_user")
    print(f"\n🔧 LangGraph Tools: {len(tools)}")
    
    if tools:
        print(f"   Example: {tools[0].name} - {tools[0].description[:50]}...")
    
    return len(tools) > 0


async def test_state_creation():
    """Test state creation"""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: State Creation")
    print("=" * 60)
    
    from backend.agent.state import create_initial_state, state_summary
    
    state = create_initial_state(
        user_message="ارسم صورة قطة",
        user_id="test_123",
        platform="telegram"
    )
    
    print(state_summary(state))
    
    return state is not None


async def test_memory():
    """Test memory persistence"""
    print("\n" + "=" * 60)
    print("🧪 TEST 6: Memory Persistence")
    print("=" * 60)
    
    from backend.agent.memory import get_memory
    
    memory = get_memory()
    
    # Save a message
    memory.save_message(
        user_id="test_user",
        thread_id="test_thread",
        role="user",
        content="Hello, this is a test message",
        platform="test"
    )
    
    # Get history
    history = memory.get_conversation_history("test_user", "test_thread")
    print(f"\n📚 Messages in history: {len(history)}")
    
    # Save preference
    memory.save_user_preference("test_user", "language", "ar-EG")
    
    # Get preferences
    prefs = memory.get_user_preferences("test_user")
    print(f"⚙️ User preferences: {prefs}")
    
    return len(history) > 0


async def test_streaming():
    """Test streaming execution"""
    print("\n" + "=" * 60)
    print("🧪 TEST 7: Streaming Execution")
    print("=" * 60)
    
    from backend.agent.graph import NovaAgent
    
    agent = NovaAgent(use_persistence=False)
    
    print("\n🔄 Streaming agent execution...")
    step_count = 0
    
    async for state in agent.stream("قولي نكتة", user_id="test"):
        step_count += 1
        # Get the node name from the state dict
        for node_name, node_state in state.items():
            phase = node_state.get('phase', 'unknown') if isinstance(node_state, dict) else 'unknown'
            print(f"   Step {step_count}: {node_name} → {phase}")
    
    print(f"\n✅ Total steps: {step_count}")
    
    return step_count > 0


async def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("   ROBOVAI NOVA AGENT - TEST SUITE")
    print("🚀" * 30)
    
    start_time = datetime.now()
    results = {}
    
    try:
        # Test 1: State creation (no API calls)
        results["state"] = await test_state_creation()
    except Exception as e:
        print(f"❌ State test failed: {e}")
        results["state"] = False
    
    try:
        # Test 2: Tools adapter
        results["tools"] = await test_tools_adapter()
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        results["tools"] = False
    
    try:
        # Test 3: Memory
        results["memory"] = await test_memory()
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        results["memory"] = False
    
    try:
        # Test 4: Simple task (API call)
        results["simple"] = await test_simple_task()
    except Exception as e:
        print(f"❌ Simple task test failed: {e}")
        results["simple"] = False
    
    try:
        # Test 5: Tool task
        results["tool"] = await test_tool_task()
    except Exception as e:
        print(f"❌ Tool task test failed: {e}")
        results["tool"] = False
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    print(f"⏱️ Time: {elapsed:.2f}s")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The Agent is ready!")
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")
    
    return passed == total


if __name__ == "__main__":
    print("\n🤖 Starting RobovAI Nova Agent Tests...\n")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Register all tools BEFORE running tests
    from backend.tools.loader import register_all_tools
    register_all_tools()
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    sys.exit(0 if success else 1)
