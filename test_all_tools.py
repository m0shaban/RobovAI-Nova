"""
🧪 RobovAI Nova - Comprehensive Tool Tester
Tests all registered tools and reports status
"""
import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

# Test cases for each tool
TOOL_TESTS = {
    # ═══════════════════════════════════════════════════════════════
    # 🛠️ UTILITY TOOLS
    # ═══════════════════════════════════════════════════════════════
    "/ip": {"input": "", "expect_key": "IP"},
    "/crypto": {"input": "bitcoin", "expect_key": "Bitcoin"},
    "/shorten": {"input": "https://google.com", "expect_key": "Short URL"},
    "/password": {"input": "16", "expect_key": "Password"},
    "/uuid": {"input": "", "expect_key": "UUID"},
    "/qr": {"input": "Hello", "expect_key": "QR Code"},
    "/website_status": {"input": "google.com", "expect_key": "UP"},
    "/currency": {"input": "100 USD EGP", "expect_key": "النتيجة"},
    "/color": {"input": "", "expect_key": "Color"},
    "/unit": {"input": "", "expect_key": "kg"},
    
    # ═══════════════════════════════════════════════════════════════
    # 🎨 CREATIVE TOOLS
    # ═══════════════════════════════════════════════════════════════
    "/joke": {"input": "", "expect_key": "😂"},
    "/quote": {"input": "", "expect_key": "اقتباس"},
    "/fact": {"input": "", "expect_key": "حقيقة"},
    "/qr_advanced": {"input": "بسم الله", "expect_key": "QR"},
    
    # ═══════════════════════════════════════════════════════════════
    # 📊 DATA TOOLS
    # ═══════════════════════════════════════════════════════════════
    "/chart": {"input": "bar Sales:100,200,300", "expect_key": "Chart"},
    "/diagram": {"input": "flow A --> B --> C", "expect_key": "mermaid"},
    "/math": {"input": "2+2", "expect_key": "4"},
    
    # ═══════════════════════════════════════════════════════════════
    # 🌐 SEARCH/INFO TOOLS
    # ═══════════════════════════════════════════════════════════════
    "/weather": {"input": "Cairo", "expect_key": "°"},
    "/quran": {"input": "1:1", "expect_key": "الفاتحة"},
    "/translate_egy": {"input": "Hello my friend", "expect_key": "صديق"},
    
    # ═══════════════════════════════════════════════════════════════
    # 💻 CODE TOOLS
    # ═══════════════════════════════════════════════════════════════
    "/code_fix": {"input": "def foo() print('hello')", "expect_key": "def"},
    "/explain_code": {"input": "for i in range(10): print(i)", "expect_key": "loop"},
    "/sql": {"input": "get all users where age > 18", "expect_key": "SELECT"},
    "/regex": {"input": "email validation", "expect_key": "@"},
    
    # ═══════════════════════════════════════════════════════════════
    # 🔧 SYSTEM TOOLS
    # ═══════════════════════════════════════════════════════════════
    "/check_password": {"input": "Password123!", "expect_key": "قوة"},
    "/hash": {"input": "hello world", "expect_key": "hash"},
    "/base64_encode": {"input": "Hello", "expect_key": "SGVs"},
    "/json_format": {"input": '{"a":1,"b":2}', "expect_key": '"a"'},
}

async def test_tool(tool_name: str, test_config: dict) -> dict:
    """Test a single tool"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build message
            message = f"{tool_name} {test_config['input']}".strip()
            
            response = await client.post(
                f"{API_BASE}/webhook",
                json={
                    "user_id": "tester",
                    "message": message,
                    "platform": "test"
                }
            )
            
            data = response.json()
            output = data.get("response", "") or data.get("output", "")
            
            # Check if expected content is in output
            expect = test_config.get("expect_key", "")
            passed = expect.lower() in output.lower() if expect else len(output) > 10
            
            return {
                "tool": tool_name,
                "status": "✅ PASS" if passed else "⚠️ WARN",
                "passed": passed,
                "output_preview": output[:100] + "..." if len(output) > 100 else output,
                "error": None
            }
            
    except Exception as e:
        return {
            "tool": tool_name,
            "status": "❌ FAIL",
            "passed": False,
            "output_preview": "",
            "error": str(e)
        }

async def get_all_tools() -> list:
    """Get list of all registered tools"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/tools")
            data = response.json()
            return list(data.get("tools", {}).keys())
    except:
        return []

async def main():
    print("=" * 60)
    print("🧪 RobovAI Nova - Tool Verification Report")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Get all registered tools
    all_tools = await get_all_tools()
    print(f"📦 إجمالي الأدوات المسجلة: {len(all_tools)}")
    print()
    
    # Test defined tools
    results = []
    tested_tools = set()
    
    print("🔍 جاري اختبار الأدوات...")
    print("-" * 60)
    
    for tool_name, config in TOOL_TESTS.items():
        result = await test_tool(tool_name, config)
        results.append(result)
        tested_tools.add(tool_name)
        
        status_icon = result["status"]
        print(f"{status_icon} {tool_name}")
        if result["error"]:
            print(f"   ⚠️ Error: {result['error']}")
    
    print()
    print("=" * 60)
    print("📊 ملخص النتائج:")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    print(f"✅ نجح: {passed}")
    print(f"❌ فشل: {failed}")
    print(f"📋 تم اختبار: {len(results)} من {len(all_tools)} أداة")
    print()
    
    # List untested tools
    untested = set(all_tools) - tested_tools
    if untested:
        print("⏳ أدوات لم يتم اختبارها:")
        for tool in sorted(untested):
            print(f"   • {tool}")
    
    # List failed tools
    failed_tools = [r for r in results if not r["passed"]]
    if failed_tools:
        print()
        print("❌ أدوات تحتاج إصلاح:")
        for r in failed_tools:
            print(f"   • {r['tool']}: {r.get('error') or 'لم يمر الاختبار'}")
    
    print()
    print("✨ اكتمل الفحص!")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
