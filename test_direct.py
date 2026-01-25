"""
🧪 Direct Tool Tester - Tests tools directly without HTTP
"""
import asyncio
import sys
sys.path.insert(0, '.')

# Try to import and register tools
print("=" * 60)
print("🔧 Testing Tool Registration...")
print("=" * 60)

try:
    from backend.tools.registry import ToolRegistry
    from backend.tools.loader import register_all_tools
    
    # Register tools
    print("\n📦 Registering tools...")
    register_all_tools()
    
    # List tools
    tools = ToolRegistry.list_tools()
    print(f"\n✅ Registered {len(tools)} tools:")
    for i, tool in enumerate(sorted(tools), 1):
        print(f"   {i:3}. {tool}")
        
except Exception as e:
    print(f"\n❌ Error during registration: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🧪 Testing Individual Tools...")
print("=" * 60)

async def test_tools():
    """Test key tools directly"""
    
    test_cases = [
        ("/math", "2+2"),
        ("/quote", ""),
        ("/fact", ""),
        ("/joke", ""),
        ("/qr_advanced", "بسم الله"),
        ("/currency", "100 USD EGP"),
        ("/quran", "1:1"),
        ("/password", "16"),
        ("/uuid", ""),
    ]
    
    results = []
    
    for tool_name, test_input in test_cases:
        try:
            tool_class = ToolRegistry.get_tool(tool_name)
            if not tool_class:
                results.append((tool_name, "❌ NOT FOUND", "Tool not registered"))
                continue
                
            tool = tool_class()
            result = await tool.execute(test_input, "tester")
            
            output = result.get("output", "")
            status = result.get("status", "unknown")
            
            if status == "success" and len(output) > 5:
                results.append((tool_name, "✅ PASS", output[:50] + "..."))
            else:
                results.append((tool_name, "⚠️ WARN", output[:50] if output else "Empty output"))
                
        except Exception as e:
            results.append((tool_name, "❌ ERROR", str(e)[:50]))
    
    # Print results
    print("\n📊 Results:")
    print("-" * 60)
    for name, status, preview in results:
        print(f"{status} {name}")
        print(f"      {preview}")
    
    passed = sum(1 for _, s, _ in results if "PASS" in s)
    print(f"\n✅ Passed: {passed}/{len(results)}")

# Run tests
asyncio.run(test_tools())
