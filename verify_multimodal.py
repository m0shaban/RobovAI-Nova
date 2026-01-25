import asyncio
from backend.tools.loader import register_all_tools
from backend.tools.registry import ToolRegistry

async def main():
    print("=" * 60)
    print("🚀 RobovAI MEGA VERIFICATION - 66 Tools")
    print("=" * 60)
    
    register_all_tools()
    
    all_tools = ToolRegistry.list_tools()
    print(f"\n📊 Total Tools Registered: {len(all_tools)}")
    
    # Test samples from each new phase
    test_cases = [
        # Phase 7: Vision
        ("/scan_receipt", "https://example.com/receipt.jpg"),
        ("/meme_explain", "https://example.com/meme.jpg"),
        ("/ask_pdf", "https://example.com/doc.pdf | What is the main topic?"),
        
        # Phase 8: Audio
        ("/voice_note", "https://example.com/voice.mp3"),
        ("/meeting_notes", "https://example.com/meeting.mp3"),
        
        # Phase 9: Safety
        ("/check_content", "This is a test post about technology"),
        ("/dish_recipe", "https://example.com/dish.jpg"),
        ("/compare_offers", "offer1.jpg | offer2.jpg")
    ]
    
    print("\n" + "=" * 60)
    print("🧪 Testing New Multimodal Tools")
    print("=" * 60)
    
    for cmd, inp in test_cases:
        print(f"\n🔍 Testing {cmd}...")
        tool_cls = ToolRegistry.get_tool(cmd)
        if tool_cls:
            tool = tool_cls()
            try:
                res = await tool.execute(inp, "test_user")
                status = "✅ SUCCESS" if res['status'] == 'success' else "❌ FAILED"
                print(f"{status}: {cmd}")
                print(f"   Cost: {res.get('tokens_deducted', 0)} tokens")
                # Show first 100 chars of output
                output_preview = res.get('output', '')[:100]
                print(f"   Output: {output_preview}...")
            except Exception as e:
                print(f"❌ ERROR: {cmd} - {str(e)[:100]}")
        else:
            print(f"❌ FAIL: Tool {cmd} not found in registry")
    
    print("\n" + "=" * 60)
    print("🎉 Verification Complete!")
    print("=" * 60)
    print(f"\n📋 All Available Tools ({len(all_tools)}):")
    for i, tool_name in enumerate(sorted(all_tools), 1):
        print(f"{i:2d}. {tool_name}")

if __name__ == "__main__":
    asyncio.run(main())
