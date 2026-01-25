# F:/New folder (24)/backend/tools/test_voice.py
"""
اختبار سريع لأداة Voice Note
"""
import asyncio
from backend.tools.audio import VoiceNoteTool

async def test():
    tool = VoiceNoteTool()
    
    print("🧪 Testing Voice Note Tool...")
    print("=" * 50)
    
    # Test 1: No input
    result1 = await tool.execute("", "test_user")
    print("\n✅ Test 1 (No input):")
    print(result1['output'])
    
    # Test 2: Mock audio data
    result2 = await tool.execute("data:audio/wav;base64,GkXfo59ChoEBQ...", "test_user")
    print("\n✅ Test 2 (Mock audio):")
    print(result2['output'])
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test())
