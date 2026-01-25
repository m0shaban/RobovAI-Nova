"""
GitHub User Info Tool - معلومات مستخدم GitHub
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class GitHubUserTool(BaseTool):
    """
    أداة معلومات مستخدم GitHub
    """
    @property
    def name(self) -> str:
        return "/github"
    
    @property
    def description(self) -> str:
        return "🐙 GitHub User - معلومات أي مستخدم GitHub"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على معلومات مستخدم GitHub
        """
        
        if not user_input or not user_input.strip():
            return {
                "status": "success",
                "output": """🐙 **GitHub User Info**

**الاستخدام:**
`/github [username]`

**أمثلة:**
• `/github torvalds` - Linus Torvalds
• `/github gvanrossum` - Guido van Rossum
• `/github octocat` - GitHub Mascot

**المعلومات المتاحة:**
✅ الاسم والسيرة
✅ عدد المتابعين
✅ عدد المشاريع
✅ الموقع والشركة

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            username = user_input.strip()
            url = f"https://api.github.com/users/{username}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            name = data.get("name") or username
            bio = data.get("bio") or "No bio available"
            avatar = data.get("avatar_url", "")
            followers = data.get("followers", 0)
            following = data.get("following", 0)
            public_repos = data.get("public_repos", 0)
            public_gists = data.get("public_gists", 0)
            company = data.get("company") or "N/A"
            location = data.get("location") or "N/A"
            blog = data.get("blog") or ""
            twitter = data.get("twitter_username") or ""
            created_at = data.get("created_at", "")[:10]
            profile_url = data.get("html_url", "")
            
            output = f"""🐙 **GitHub Profile: {username}**

![Avatar]({avatar})

**{name}**
{bio}

**Stats:**
👥 **Followers:** {followers:,} | **Following:** {following:,}
📦 **Public Repos:** {public_repos:,}
📝 **Gists:** {public_gists:,}

**Info:**
🏢 **Company:** {company}
📍 **Location:** {location}
📅 **Joined:** {created_at}"""
            
            if blog:
                output += f"\n🌐 **Website:** {blog}"
            if twitter:
                output += f"\n🐦 **Twitter:** @{twitter}"
            
            output += f"""

**Profile:**
{profile_url}

---
🐙 Powered by GitHub API"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "status": "error",
                    "output": f"❌ المستخدم **{user_input}** غير موجود على GitHub",
                    "tokens_deducted": 0
                }
            return {
                "status": "error",
                "output": f"❌ خطأ: {e.response.status_code}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
