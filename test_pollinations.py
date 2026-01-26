"""
Test script for new Pollinations.ai + ImgBB image generation
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.tools.image_gen import ImageGenTool

async def test_image_gen():
    tool = ImageGenTool()
    
    print("🧪 Testing Image Generation with Pollinations.ai + ImgBB\n")
    print("="*60)
    
    # Test 1: Arabic prompt
    print("\n📝 Test 1: Arabic Prompt")
    print("-" * 60)
    result = await tool.execute("قطة لطيفة ترتدي نظارات", "test_user")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"✅ SUCCESS!")
        print(f"Output preview: {result['output'][:200]}...")
        if 'image_url' in result:
            print(f"🔗 Image URL: {result['image_url']}")
    else:
        print(f"❌ FAILED: {result['output']}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_image_gen())
