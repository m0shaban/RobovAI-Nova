"""
Quran Tool - القرآن الكريم
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class QuranTool(BaseTool):
    """
    أداة القرآن الكريم - البحث في الآيات والسور
    """
    @property
    def name(self) -> str:
        return "/quran"
    
    @property
    def description(self) -> str:
        return "📖 القرآن الكريم - ابحث عن آيات، سور، واستمع للتلاوات"
    
    @property
    def cost(self) -> int:
        return 0  # مجاني - خدمة دينية
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        البحث في القرآن الكريم
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """📖 **القرآن الكريم**

**الاستخدام:**
`/quran رقم السورة:رقم الآية`
أو
`/quran اسم السورة`
أو
`/quran كلمة للبحث`

**أمثلة:**
• `/quran 1:1` - الفاتحة الآية الأولى
• `/quran الفاتحة` - سورة الفاتحة كاملة
• `/quran الصبر` - البحث عن كلمة "الصبر"

**المميزات:**
✅ عرض الآيات بالرسم العثماني
✅ التفسير الميسر
✅ روابط التلاوة الصوتية
✅ مجاني بالكامل

🕌 المصدر: AlQuran Cloud API""",
                "tokens_deducted": 0
            }
        
        try:
            # تنظيف المدخل من الرموز الزائدة
            clean_input = user_input.strip()
            clean_input = clean_input.replace('•', '').replace('-', '').strip()
            
            # استخراج النمط surah:ayah
            import re
            surah_ayah_match = re.search(r'(\d+)\s*:\s*(\d+)', clean_input)
            
            if surah_ayah_match:
                # صيغة سورة:آية
                surah = surah_ayah_match.group(1)
                ayah = surah_ayah_match.group(2)
                return await self._get_ayah(surah, ayah)
            
            elif clean_input.isdigit():
                # رقم سورة فقط
                return await self._get_surah(clean_input)
            
            else:
                # بحث عن كلمة أو اسم سورة
                # تنظيف أسماء السور الشائعة
                surah_names = {
                    'الفاتحة': '1', 'البقرة': '2', 'آل عمران': '3', 'النساء': '4',
                    'المائدة': '5', 'الأنعام': '6', 'الأعراف': '7', 'الأنفال': '8',
                    'التوبة': '9', 'يونس': '10', 'هود': '11', 'يوسف': '12',
                    'الكهف': '18', 'مريم': '19', 'طه': '20', 'يس': '36',
                    'الرحمن': '55', 'الواقعة': '56', 'الملك': '67', 'الإخلاص': '112',
                    'الفلق': '113', 'الناس': '114'
                }
                
                for name, num in surah_names.items():
                    if name in clean_input:
                        return await self._get_surah(num)
                
                return await self._search_quran(clean_input)
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _get_ayah(self, surah: str, ayah: str) -> Dict[str, Any]:
        """الحصول على آية محددة"""
        try:
            url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.alafasy"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("code") != 200:
                return {
                    "status": "error",
                    "output": "❌ لم أجد هذه الآية. تأكد من رقم السورة والآية.",
                    "tokens_deducted": 0
                }
            
            ayah_data = data["data"]
            
            output = f"""📖 **{ayah_data['surah']['name']} - الآية {ayah_data['numberInSurah']}**

**النص:**
{ayah_data['text']}

**معلومات:**
• السورة: {ayah_data['surah']['englishName']} ({ayah_data['surah']['name']})
• رقم الآية في السورة: {ayah_data['numberInSurah']}
• رقم الآية في القرآن: {ayah_data['number']}
• الجزء: {ayah_data['juz']}

🎧 **استمع للتلاوة:**
[الشيخ مشاري العفاسي]({ayah_data.get('audio', '#')})

---
🕌 المصدر: AlQuran Cloud"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في جلب الآية: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _get_surah(self, surah_number: str) -> Dict[str, Any]:
        """الحصول على سورة كاملة"""
        try:
            url = f"https://api.alquran.cloud/v1/surah/{surah_number}/ar.alafasy"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("code") != 200:
                return {
                    "status": "error",
                    "output": "❌ لم أجد هذه السورة. تأكد من رقم السورة (1-114).",
                    "tokens_deducted": 0
                }
            
            surah_data = data["data"]
            
            # عرض أول 5 آيات فقط لتجنب الإطالة
            ayahs_text = []
            for i, ayah in enumerate(surah_data["ayahs"][:5], 1):
                ayahs_text.append(f"**{i}.** {ayah['text']}")
            
            more_ayahs = len(surah_data["ayahs"]) - 5
            
            output = f"""📖 **{surah_data['name']} ({surah_data['englishName']})**

**معلومات السورة:**
• الاسم بالإنجليزية: {surah_data['englishName']}
• الترجمة: {surah_data['englishNameTranslation']}
• عدد الآيات: {surah_data['numberOfAyahs']}
• نوع السورة: {surah_data['revelationType']}

**أول 5 آيات:**

{chr(10).join(ayahs_text)}

{"..." if more_ayahs > 0 else ""}
{f"*وهناك {more_ayahs} آية أخرى*" if more_ayahs > 0 else ""}

💡 **للحصول على آية محددة:** `/quran {surah_number}:رقم_الآية`

---
🕌 المصدر: AlQuran Cloud"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في جلب السورة: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _search_quran(self, query: str) -> Dict[str, Any]:
        """البحث في القرآن"""
        try:
            # البحث عن اسم السورة أولاً
            url = f"https://api.alquran.cloud/v1/search/{query}/ar.alafasy/ar"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("code") != 200 or not data.get("data", {}).get("matches"):
                return {
                    "status": "success",
                    "output": f"❌ لم أجد نتائج لـ: **{query}**\n\n💡 جرب البحث بكلمة أخرى أو استخدم رقم السورة.",
                    "tokens_deducted": self.cost
                }
            
            matches = data["data"]["matches"][:3]  # أول 3 نتائج
            
            results = []
            for match in matches:
                results.append(f"""**{match['surah']['name']} - الآية {match['numberInSurah']}**
{match['text']}
""")
            
            output = f"""🔍 **نتائج البحث عن: "{query}"**

وجدت {data['data']['count']} نتيجة، عرض أول 3:

{chr(10).join(results)}

💡 **للحصول على آية محددة:** `/quran رقم_السورة:رقم_الآية`

---
🕌 المصدر: AlQuran Cloud"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في البحث: {str(e)}",
                "tokens_deducted": 0
            }
