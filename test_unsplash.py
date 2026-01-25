"""
Test script for Unsplash API integration
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from tools.unsplash import UnsplashSearchTool

async def test_unsplash():
    """Test the Unsplash tool with different queries"""
    
    tool = UnsplashSearchTool()
    
    print("="*60)
    print("🧪 Testing Unsplash Search Tool")
    print("="*60)
    
    # Test 1: Arabic query (natural landscape)
    print("\n📝 Test 1: Arabic query - منظر طبيعي في الجبال")
    print("-"*60)
    result1 = await tool.execute("أريد صورة لمنظر طبيعي في الجبال", "test_user")
    print(f"Status: {result1['status']}")
    print(f"Output:\n{result1['output'][:500]}...")  # First 500 chars
    print(f"Tokens: {result1['tokens_deducted']}")
    
    # Test 2: English query
    print("\n\n📝 Test 2: English query - city skyline")
    print("-"*60)
    result2 = await tool.execute("city skyline at sunset", "test_user")
    print(f"Status: {result2['status']}")
    print(f"Output:\n{result2['output'][:500]}...")
    print(f"Tokens: {result2['tokens_deducted']}")
    
    # Test 3: Fantasy query (should work but may have limited results)
    print("\n\n📝 Test 3: Fantasy query - تنين ناري")
    print("-"*60)
    result3 = await tool.execute("تنين ناري في مدينة مستقبلية", "test_user")
    print(f"Status: {result3['status']}")
    print(f"Output:\n{result3['output'][:500]}...")
    print(f"Tokens: {result3['tokens_deducted']}")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_unsplash())
