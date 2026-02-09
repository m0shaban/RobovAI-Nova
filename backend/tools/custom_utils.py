"""
🛠️ أدوات مخصصة - مكتوبة من الصفر بدون APIs خارجية
Custom Utility Tools - Pure Python Implementation
"""

from typing import Dict, Any, List
from .base import BaseTool
import re
import math
import hashlib
import random
import string
import json
from datetime import datetime, timedelta
import unicodedata


# ═══════════════════════════════════════════════════════════════════════════
# 📊 QUICKCHART - Charts Generation via QuickChart.io
# ═══════════════════════════════════════════════════════════════════════════

class QuickChartTool(BaseTool):
    """توليد رسوم بيانية احترافية"""
    
    @property
    def name(self): return "/chart"
    @property
    def description(self): return "إنشاء رسوم بيانية (bar, line, pie, doughnut)"
    @property
    def cost(self): return 2
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        Format: /chart bar Sales:100,200,300 Marketing:50,75,100
        Or: /chart pie Egypt:40 Saudi:30 UAE:20 Kuwait:10
        """
        import urllib.parse
        
        if not user_input.strip():
            return {
                "status": "success",
                "output": """📊 **كيفية استخدام أداة الرسوم البيانية:**

`/chart bar Sales:100,200,300 Cost:50,60,70`
`/chart line Revenue:1000,1500,2000,2500`
`/chart pie Egypt:40 Saudi:30 UAE:20`
`/chart doughnut Category1:25 Category2:35 Category3:40`

**الأنواع المتاحة:** bar, line, pie, doughnut, radar""",
                "tokens_deducted": 0
            }
        
        parts = user_input.strip().split()
        chart_type = parts[0].lower() if parts else "bar"
        
        if chart_type not in ["bar", "line", "pie", "doughnut", "radar", "polarArea"]:
            chart_type = "bar"
        
        # Parse data
        labels = []
        datasets = []
        
        colors = [
            'rgba(0, 240, 255, 0.8)',   # Cyan
            'rgba(139, 92, 246, 0.8)',  # Purple
            'rgba(255, 0, 170, 0.8)',   # Magenta
            'rgba(255, 215, 0, 0.8)',   # Gold
            'rgba(0, 255, 127, 0.8)',   # Spring Green
        ]
        
        for i, part in enumerate(parts[1:]):
            if ':' in part:
                name, values = part.split(':', 1)
                data_values = [float(v) for v in values.split(',') if v]
                
                if chart_type in ['pie', 'doughnut', 'polarArea']:
                    # For pie charts, each part is a slice
                    labels.append(name)
                    if not datasets:
                        datasets.append({
                            'data': [],
                            'backgroundColor': colors
                        })
                    datasets[0]['data'].append(data_values[0] if data_values else 0)
                else:
                    # For bar/line, each part is a dataset
                    if not labels:
                        labels = [f"Item {j+1}" for j in range(len(data_values))]
                    
                    datasets.append({
                        'label': name,
                        'data': data_values,
                        'backgroundColor': colors[i % len(colors)],
                        'borderColor': colors[i % len(colors)].replace('0.8', '1'),
                        'borderWidth': 2,
                        'fill': False if chart_type == 'line' else True
                    })
        
        # Build chart config
        chart_config = {
            'type': chart_type,
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'options': {
                'plugins': {
                    'legend': {'display': True},
                    'title': {'display': False}
                },
                'scales': {
                    'y': {'beginAtZero': True}
                } if chart_type in ['bar', 'line'] else {}
            }
        }
        
        # Generate QuickChart URL
        chart_json = json.dumps(chart_config)
        encoded = urllib.parse.quote(chart_json)
        chart_url = f"https://quickchart.io/chart?c={encoded}&backgroundColor=rgb(20,20,25)"
        
        return {
            "status": "success",
            "output": f"📊 **تم إنشاء الرسم البياني!**\n\n![Chart]({chart_url})\n\n🔗 [فتح في نافذة جديدة]({chart_url})",
            "tokens_deducted": self.cost,
            "media": [{"type": "image", "url": chart_url}]
        }


# ═══════════════════════════════════════════════════════════════════════════
# 🧮 MATH SOLVER - حل المعادلات الرياضية
# ═══════════════════════════════════════════════════════════════════════════

class MathSolverTool(BaseTool):
    """حل معادلات رياضية متقدمة - Pure Python"""
    
    @property
    def name(self): return "/math"
    @property
    def description(self): return "Solve math expressions. Pass the expression in 'query', e.g. query='5+5' or query='sqrt(144)'"
    @property
    def cost(self): return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not user_input.strip():
            return {
                "status": "success",
                "output": """🧮 **حاسبة رياضية متقدمة**

أمثلة:
- `2 + 3 * 4`
- `sqrt(144)`
- `sin(30)` (بالدرجات)
- `log(100)`
- `2^10`
- `factorial(5)`
- `pi * r^2` (استبدل r)""",
                "tokens_deducted": 0
            }
        
        expr = user_input.strip()
        
        # Safe math functions
        safe_dict = {
            'sqrt': math.sqrt,
            'sin': lambda x: math.sin(math.radians(x)),
            'cos': lambda x: math.cos(math.radians(x)),
            'tan': lambda x: math.tan(math.radians(x)),
            'log': math.log10,
            'ln': math.log,
            'exp': math.exp,
            'abs': abs,
            'factorial': math.factorial,
            'pow': pow,
            'pi': math.pi,
            'e': math.e,
        }
        
        # Replace ^ with **
        expr = expr.replace('^', '**')
        
        try:
            # Evaluate safely
            result = eval(expr, {"__builtins__": {}}, safe_dict)
            
            # Format result
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 8)
            
            return {
                "status": "success",
                "output": f"🧮 **النتيجة:**\n\n`{user_input}` = **{result}**",
                "tokens_deducted": self.cost
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في المعادلة: {str(e)}",
                "tokens_deducted": 0
            }


# ═══════════════════════════════════════════════════════════════════════════
# 🔤 TEXT TOOLS - أدوات النصوص
# ═══════════════════════════════════════════════════════════════════════════

class TextAnalyzerTool(BaseTool):
    """تحليل النصوص - Pure Python"""
    
    @property
    def name(self): return "/analyze_text"
    @property
    def description(self): return "تحليل نص (كلمات، أحرف، جمل، قراءة)"
    @property
    def cost(self): return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not user_input.strip():
            return {"status": "error", "output": "❌ أدخل نصاً للتحليل"}
        
        text = user_input.strip()
        
        # Analysis
        char_count = len(text)
        char_no_spaces = len(text.replace(" ", ""))
        word_count = len(text.split())
        sentence_count = len(re.findall(r'[.!?]+', text)) or 1
        paragraph_count = len(text.split('\n\n')) or 1
        
        # Word frequency
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Reading time (200 words/min average)
        reading_time = max(1, round(word_count / 200))
        speaking_time = max(1, round(word_count / 130))
        
        # Unique words
        unique_words = len(set(words))
        
        output = f"""📊 **تحليل النص:**

📝 **الإحصائيات:**
- الأحرف: {char_count:,} (بدون مسافات: {char_no_spaces:,})
- الكلمات: {word_count:,}
- الجمل: {sentence_count:,}
- الفقرات: {paragraph_count:,}
- كلمات فريدة: {unique_words:,}

⏱️ **الوقت:**
- وقت القراءة: ~{reading_time} دقيقة
- وقت التحدث: ~{speaking_time} دقيقة

🔝 **أكثر الكلمات تكراراً:**
{chr(10).join([f"  • {w}: {c} مرة" for w, c in top_words])}"""
        
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class TextCaseTool(BaseTool):
    """تحويل حالة النص"""
    
    @property
    def name(self): return "/case"
    @property
    def description(self): return "تحويل حالة النص (upper, lower, title, reverse)"
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not user_input.strip():
            return {
                "status": "success",
                "output": """🔤 **تحويل حالة النص:**
                
`/case upper Hello World` → HELLO WORLD
`/case lower HELLO WORLD` → hello world  
`/case title hello world` → Hello World
`/case reverse Hello` → olleH
`/case snake Hello World` → hello_world""",
                "tokens_deducted": 0
            }
        
        parts = user_input.strip().split(maxsplit=1)
        mode = parts[0].lower()
        text = parts[1] if len(parts) > 1 else ""
        
        conversions = {
            'upper': text.upper(),
            'lower': text.lower(),
            'title': text.title(),
            'capitalize': text.capitalize(),
            'reverse': text[::-1],
            'snake': re.sub(r'\s+', '_', text.lower()),
            'kebab': re.sub(r'\s+', '-', text.lower()),
            'camel': ''.join(word.capitalize() if i > 0 else word.lower() 
                           for i, word in enumerate(text.split())),
        }
        
        result = conversions.get(mode, text)
        
        return {
            "status": "success",
            "output": f"🔤 **النتيجة:**\n\n`{result}`",
            "tokens_deducted": self.cost
        }


# ═══════════════════════════════════════════════════════════════════════════
# 🔐 SECURITY TOOLS - أدوات الأمان
# ═══════════════════════════════════════════════════════════════════════════

class PasswordStrengthTool(BaseTool):
    """فحص قوة كلمة المرور"""
    
    @property
    def name(self): return "/check_password"
    @property
    def description(self): return "تحليل قوة كلمة المرور وتقديم نصائح"
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not user_input.strip():
            return {"status": "error", "output": "❌ أدخل كلمة مرور لفحصها"}
        
        password = user_input.strip()
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("⚠️ أقل من 8 أحرف")
        
        if len(password) >= 12:
            score += 1
        
        if len(password) >= 16:
            score += 1
        
        # Character types
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("⚠️ لا توجد أحرف صغيرة")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("⚠️ لا توجد أحرف كبيرة")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("⚠️ لا توجد أرقام")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 2
        else:
            feedback.append("⚠️ لا توجد رموز خاصة")
        
        # Common patterns
        common_patterns = ['123', 'abc', 'qwerty', 'password', 'admin']
        for pattern in common_patterns:
            if pattern in password.lower():
                score -= 2
                feedback.append(f"❌ نمط شائع: {pattern}")
        
        # Rating
        if score >= 8:
            rating = "🟢 قوية جداً"
            stars = "⭐⭐⭐⭐⭐"
        elif score >= 6:
            rating = "🟡 قوية"
            stars = "⭐⭐⭐⭐"
        elif score >= 4:
            rating = "🟠 متوسطة"
            stars = "⭐⭐⭐"
        elif score >= 2:
            rating = "🔴 ضعيفة"
            stars = "⭐⭐"
        else:
            rating = "⛔ ضعيفة جداً"
            stars = "⭐"
        
        # Entropy estimate
        charset_size = 0
        if re.search(r'[a-z]', password): charset_size += 26
        if re.search(r'[A-Z]', password): charset_size += 26
        if re.search(r'\d', password): charset_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): charset_size += 32
        
        entropy = len(password) * math.log2(charset_size) if charset_size > 0 else 0
        
        output = f"""🔐 **تحليل كلمة المرور:**

{stars}
**التقييم:** {rating}

📏 **الطول:** {len(password)} حرف
🔢 **درجة القوة:** {max(0, score)}/10
🔐 **الإنتروبي:** {entropy:.1f} بت

"""
        
        if feedback:
            output += "**نقاط الضعف:**\n" + "\n".join(feedback)
        else:
            output += "✅ لا توجد نقاط ضعف واضحة!"
        
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


# ═══════════════════════════════════════════════════════════════════════════
# 📅 DATE/TIME TOOLS - أدوات التاريخ والوقت
# ═══════════════════════════════════════════════════════════════════════════

class DateCalculatorTool(BaseTool):
    """حسابات التاريخ"""
    
    @property
    def name(self): return "/date_calc"
    @property
    def description(self): return "حساب الفرق بين تاريخين أو إضافة أيام"
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not user_input.strip():
            return {
                "status": "success",
                "output": """📅 **حاسبة التواريخ:**

**الفرق بين تاريخين:**
`/date_calc diff 2025-01-01 2025-12-31`

**إضافة أيام:**
`/date_calc add 2025-01-25 30`

**العمر:**
`/date_calc age 1990-05-15`""",
                "tokens_deducted": 0
            }
        
        parts = user_input.strip().split()
        mode = parts[0].lower()
        
        try:
            if mode == 'diff' and len(parts) >= 3:
                date1 = datetime.strptime(parts[1], '%Y-%m-%d')
                date2 = datetime.strptime(parts[2], '%Y-%m-%d')
                diff = abs((date2 - date1).days)
                
                years = diff // 365
                months = (diff % 365) // 30
                days = (diff % 365) % 30
                
                return {
                    "status": "success",
                    "output": f"""📅 **الفرق بين التاريخين:**

من: {parts[1]}
إلى: {parts[2]}

⏱️ **الفرق:**
- **{diff}** يوم
- أو **{years}** سنة، **{months}** شهر، **{days}** يوم
- أو **{diff * 24}** ساعة""",
                    "tokens_deducted": self.cost
                }
            
            elif mode == 'add' and len(parts) >= 3:
                date = datetime.strptime(parts[1], '%Y-%m-%d')
                days_to_add = int(parts[2])
                new_date = date + timedelta(days=days_to_add)
                
                return {
                    "status": "success",
                    "output": f"""📅 **إضافة أيام:**

التاريخ: {parts[1]}
+ {days_to_add} يوم
= **{new_date.strftime('%Y-%m-%d')}**
({new_date.strftime('%A, %d %B %Y')})""",
                    "tokens_deducted": self.cost
                }
            
            elif mode == 'age' and len(parts) >= 2:
                birthdate = datetime.strptime(parts[1], '%Y-%m-%d')
                today = datetime.now()
                age_days = (today - birthdate).days
                
                years = age_days // 365
                months = (age_days % 365) // 30
                days = (age_days % 365) % 30
                
                next_birthday = birthdate.replace(year=today.year)
                if next_birthday < today:
                    next_birthday = birthdate.replace(year=today.year + 1)
                days_to_birthday = (next_birthday - today).days
                
                return {
                    "status": "success",
                    "output": f"""🎂 **حساب العمر:**

تاريخ الميلاد: {parts[1]}

**العمر:** {years} سنة، {months} شهر، {days} يوم
**إجمالي الأيام:** {age_days:,} يوم
**عدد الساعات:** {age_days * 24:,} ساعة

🎉 **أيام حتى عيد ميلادك القادم:** {days_to_birthday} يوم""",
                    "tokens_deducted": self.cost
                }
            
        except Exception as e:
            return {"status": "error", "output": f"❌ خطأ: {str(e)}", "tokens_deducted": 0}
        
        return {"status": "error", "output": "❌ صيغة غير صحيحة", "tokens_deducted": 0}


# ═══════════════════════════════════════════════════════════════════════════
# 🎲 RANDOM TOOLS - أدوات عشوائية
# ═══════════════════════════════════════════════════════════════════════════

class RandomPickerTool(BaseTool):
    """اختيار عشوائي"""
    
    @property
    def name(self): return "/pick"
    @property
    def description(self): return "اختيار عشوائي من قائمة أو رقم عشوائي"
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not user_input.strip():
            return {
                "status": "success",
                "output": """🎲 **أداة الاختيار العشوائي:**

**اختيار من قائمة:**
`/pick item1, item2, item3, item4`

**رقم عشوائي:**
`/pick 1-100`

**نرد:**
`/pick dice 6` (نرد 6 أوجه)

**عملة:**
`/pick coin`""",
                "tokens_deducted": 0
            }
        
        text = user_input.strip()
        
        # Coin flip
        if text.lower() == 'coin':
            result = random.choice(['🪙 صورة (Heads)', '🪙 كتابة (Tails)'])
            return {"status": "success", "output": f"🎲 **النتيجة:**\n\n{result}", "tokens_deducted": self.cost}
        
        # Dice roll
        if text.lower().startswith('dice'):
            parts = text.split()
            sides = int(parts[1]) if len(parts) > 1 else 6
            result = random.randint(1, sides)
            dice_emoji = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}.get(result, "🎲")
            return {"status": "success", "output": f"🎲 **نرد {sides} أوجه:**\n\n{dice_emoji} **{result}**", "tokens_deducted": self.cost}
        
        # Number range
        if '-' in text and text.replace('-', '').isdigit():
            try:
                start, end = map(int, text.split('-'))
                result = random.randint(start, end)
                return {"status": "success", "output": f"🎲 **رقم عشوائي ({start}-{end}):**\n\n**{result}**", "tokens_deducted": self.cost}
            except:
                pass
        
        # Pick from list
        items = [item.strip() for item in text.split(',') if item.strip()]
        if items:
            result = random.choice(items)
            return {"status": "success", "output": f"🎲 **الاختيار من {len(items)} عناصر:**\n\n✨ **{result}**", "tokens_deducted": self.cost}
        
        return {"status": "error", "output": "❌ صيغة غير صحيحة", "tokens_deducted": 0}


# ═══════════════════════════════════════════════════════════════════════════
# 💱 UNIT CONVERTER - محول الوحدات (Pure Python)
# ═══════════════════════════════════════════════════════════════════════════

class UnitConverterTool(BaseTool):
    """محول الوحدات - Pure Python"""
    
    @property
    def name(self): return "/convert"
    @property
    def description(self): return "تحويل الوحدات (طول، وزن، حرارة، مساحة)"
    @property
    def cost(self): return 0
    
    CONVERSIONS = {
        # Length (to meters)
        'km': 1000, 'm': 1, 'cm': 0.01, 'mm': 0.001,
        'mi': 1609.344, 'yd': 0.9144, 'ft': 0.3048, 'in': 0.0254,
        # Weight (to grams)
        'kg': 1000, 'g': 1, 'mg': 0.001,
        'lb': 453.592, 'oz': 28.3495,
        # Area (to sq meters)
        'km2': 1000000, 'm2': 1, 'ha': 10000, 'acre': 4046.86,
        # Volume (to liters)
        'l': 1, 'ml': 0.001, 'gal': 3.78541, 'qt': 0.946353,
    }
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not user_input.strip():
            return {
                "status": "success",
                "output": """💱 **محول الوحدات:**

`/convert 100 km to mi`
`/convert 50 kg to lb`
`/convert 30 C to F`
`/convert 100 m2 to ft2`

**الوحدات المتاحة:**
- **طول:** km, m, cm, mm, mi, yd, ft, in
- **وزن:** kg, g, mg, lb, oz
- **مساحة:** km2, m2, ha, acre
- **حرارة:** C, F, K""",
                "tokens_deducted": 0
            }
        
        # Parse: "100 km to mi"
        match = re.match(r'([\d.]+)\s*(\w+)\s*(?:to|إلى)\s*(\w+)', user_input.strip(), re.IGNORECASE)
        if not match:
            return {"status": "error", "output": "❌ صيغة غير صحيحة. مثال: `/convert 100 km to mi`", "tokens_deducted": 0}
        
        value = float(match.group(1))
        from_unit = match.group(2).lower()
        to_unit = match.group(3).lower()
        
        # Temperature special case
        if from_unit in ['c', 'f', 'k'] and to_unit in ['c', 'f', 'k']:
            # Convert to Celsius first
            if from_unit == 'f':
                celsius = (value - 32) * 5/9
            elif from_unit == 'k':
                celsius = value - 273.15
            else:
                celsius = value
            
            # Convert from Celsius to target
            if to_unit == 'f':
                result = celsius * 9/5 + 32
            elif to_unit == 'k':
                result = celsius + 273.15
            else:
                result = celsius
            
            return {
                "status": "success",
                "output": f"🌡️ **تحويل الحرارة:**\n\n{value}°{from_unit.upper()} = **{result:.2f}°{to_unit.upper()}**",
                "tokens_deducted": self.cost
            }
        
        # Standard conversion
        if from_unit in self.CONVERSIONS and to_unit in self.CONVERSIONS:
            # Convert to base unit then to target
            base_value = value * self.CONVERSIONS[from_unit]
            result = base_value / self.CONVERSIONS[to_unit]
            
            return {
                "status": "success",
                "output": f"💱 **تحويل الوحدات:**\n\n{value} {from_unit} = **{result:,.4f} {to_unit}**",
                "tokens_deducted": self.cost
            }
        
        return {"status": "error", "output": f"❌ وحدة غير معروفة: {from_unit} أو {to_unit}", "tokens_deducted": 0}


# ═══════════════════════════════════════════════════════════════════════════
# 📊 DIAGRAM TOOL - مخططات Mermaid
# ═══════════════════════════════════════════════════════════════════════════

class DiagramTool(BaseTool):
    """إنشاء مخططات عبر Mermaid"""
    
    @property
    def name(self): return "/diagram"
    @property
    def description(self): return "إنشاء مخططات (flowchart, sequence, class, pie)"
    @property
    def cost(self): return 2
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        import urllib.parse
        
        if not user_input.strip():
            return {
                "status": "success",
                "output": """📊 **أداة المخططات (Mermaid):**

**Flowchart:**
`/diagram flow Start --> Process --> End`

**Sequence:**
`/diagram sequence User->Server: Request | Server->User: Response`

**Pie Chart:**
`/diagram pie Work:45 Sleep:30 Fun:25`""",
                "tokens_deducted": 0
            }
        
        parts = user_input.strip().split(maxsplit=1)
        diagram_type = parts[0].lower()
        content = parts[1] if len(parts) > 1 else ""
        
        if diagram_type == 'flow':
            mermaid = f"flowchart LR\n    {content.replace('->', ' --> ')}"
        elif diagram_type == 'sequence':
            lines = [f"    {item.strip()}" for item in content.split('|')]
            mermaid = "sequenceDiagram\n" + "\n".join(lines)
        elif diagram_type == 'pie':
            items = content.split()
            slices = []
            for item in items:
                if ':' in item:
                    name, val = item.split(':')
                    slices.append(f'    "{name}" : {val}')
            mermaid = "pie title Chart\n" + "\n".join(slices)
        else:
            mermaid = content
        
        # Encode for mermaid.ink
        import base64
        encoded = base64.urlsafe_b64encode(mermaid.encode()).decode()
        diagram_url = f"https://mermaid.ink/img/{encoded}?bgColor=141418"
        
        return {
            "status": "success",
            "output": f"📊 **تم إنشاء المخطط!**\n\n![Diagram]({diagram_url})\n\n```mermaid\n{mermaid}\n```",
            "tokens_deducted": self.cost,
            "media": [{"type": "image", "url": diagram_url}]
        }
