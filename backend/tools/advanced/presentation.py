"""
📊 RobovAI Nova — Presentation Engine (Manus-Level)
═══════════════════════════════════════════════════
• 6 professional themes   (modern · dark · minimal · corporate · creative · nature)
• Multi-source images     (Unsplash · Pexels · Pollinations AI · none)
• Print-ready HTML + PDF  (Playwright or browser Save-as-PDF)
• Alternating layouts     (image-left / image-right / text-only)
• Keyboard / Touch / Fullscreen navigation
"""

from backend.tools.base import BaseTool
from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, Field, field_validator
import os, json, ast, logging
from datetime import datetime

logger = logging.getLogger("robovai.tools.presentation")

# ─── lazy import of sibling module to avoid circular deps ───────
def _get_image_provider():
    from backend.tools.advanced.image_provider import image_provider
    return image_provider


# ═══════════════════════════════════════════════════════════════════
# 🎨  THEMES
# ═══════════════════════════════════════════════════════════════════
THEMES: Dict[str, Dict[str, str]] = {
    "modern": {
        "primary": "#667eea", "secondary": "#764ba2", "accent": "#f093fb",
        "bg": "#f0f2f5", "slide-bg": "#ffffff",
        "text": "#2d3436", "text-light": "#636e72",
        "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "font": "'Cairo', 'Segoe UI', sans-serif",
    },
    "dark": {
        "primary": "#00d2ff", "secondary": "#6c5ce7", "accent": "#fd79a8",
        "bg": "#0c0c1d", "slide-bg": "#16162a",
        "text": "#dfe6e9", "text-light": "#b2bec3",
        "gradient": "linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 100%)",
        "font": "'Cairo', 'Segoe UI', sans-serif",
    },
    "minimal": {
        "primary": "#2d3436", "secondary": "#636e72", "accent": "#e17055",
        "bg": "#ffffff", "slide-bg": "#ffffff",
        "text": "#2d3436", "text-light": "#969faa",
        "gradient": "linear-gradient(135deg, #2d3436 0%, #636e72 100%)",
        "font": "'Cairo', Georgia, serif",
    },
    "corporate": {
        "primary": "#0c2461", "secondary": "#1e3799", "accent": "#e55039",
        "bg": "#f1f2f6", "slide-bg": "#ffffff",
        "text": "#2f3542", "text-light": "#57606f",
        "gradient": "linear-gradient(135deg, #0c2461 0%, #1e3799 100%)",
        "font": "'Cairo', 'Segoe UI', sans-serif",
    },
    "creative": {
        "primary": "#e84393", "secondary": "#a29bfe", "accent": "#00cec9",
        "bg": "#fff0f3", "slide-bg": "#ffffff",
        "text": "#2d3436", "text-light": "#636e72",
        "gradient": "linear-gradient(135deg, #e84393 0%, #a29bfe 100%)",
        "font": "'Cairo', 'Segoe UI', sans-serif",
    },
    "nature": {
        "primary": "#00b894", "secondary": "#00cec9", "accent": "#fdcb6e",
        "bg": "#f0fff4", "slide-bg": "#ffffff",
        "text": "#2d3436", "text-light": "#636e72",
        "gradient": "linear-gradient(135deg, #00b894 0%, #00cec9 100%)",
        "font": "'Cairo', 'Segoe UI', sans-serif",
    },
}

THEME_NAMES = list(THEMES.keys())


# ═══════════════════════════════════════════════════════════════════
# 📐  SCHEMA
# ═══════════════════════════════════════════════════════════════════
class PresentationSchema(BaseModel):
    title: str = Field(..., description="Presentation title")
    slides: Union[List[str], str] = Field(
        ..., description="List of slide contents: ['Title: Content', ...]"
    )
    theme: str = Field(
        "modern",
        description=f"Visual theme. Options: {', '.join(THEME_NAMES)}",
    )
    image_source: str = Field(
        "auto",
        description="Image source: auto | unsplash | pexels | ai | none",
    )

    @field_validator("slides", mode="before")
    @classmethod
    def parse_slides(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    try:
                        return ast.literal_eval(v)
                    except Exception:
                        pass
            return [v]
        return [str(v)]


# ═══════════════════════════════════════════════════════════════════
# 🛠️  CSS TEMPLATE  (uses CSS custom-properties set per theme)
# ═══════════════════════════════════════════════════════════════════
CSS_TEMPLATE = r"""
/* === Reset === */
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden;font-family:var(--font);background:var(--bg);color:var(--text)}

/* === Slides wrapper === */
.sw{width:100%;height:100vh;position:relative}
.slide{position:absolute;inset:0;opacity:0;pointer-events:none;display:flex;flex-direction:column;transition:opacity .45s ease}
.slide.active{opacity:1;pointer-events:all}

/* === TITLE SLIDE === */
.ts{background:var(--gradient);justify-content:center;align-items:center;text-align:center;color:#fff;overflow:hidden}
.ts .bgi{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.15}
.ts .ov{position:absolute;inset:0;background:var(--gradient);opacity:.82}
.ts .inner{position:relative;z-index:2;padding:40px;max-width:860px}
.ts h1{font-size:3.4em;font-weight:900;line-height:1.25;margin-bottom:18px;text-shadow:2px 4px 18px rgba(0,0,0,.25)}
.ts .tag{font-size:1.35em;opacity:.92;font-weight:300}
.ts .meta{font-size:.92em;opacity:.6;margin-top:12px}

/* === CONTENT SLIDE === */
.cs{background:var(--slide-bg);padding:44px 54px 48px}
.cs .stop{display:flex;justify-content:space-between;margin-bottom:18px}
.cs .snum{color:var(--text-light);font-size:.82em;font-weight:600}
.cs .sbody{flex:1;display:grid;gap:36px;align-items:center}
.cs.hi .sbody{grid-template-columns:55% 1fr}
.cs.ni .sbody{grid-template-columns:1fr;max-width:860px}
.cs.if .tc{order:2}
.cs.if .ic{order:1}

/* text column */
.tc h2{font-size:1.85em;font-weight:700;color:var(--text);margin-bottom:18px;padding-inline-start:18px;border-inline-start:4px solid var(--primary)}
.tc .txt{font-size:1.12em;line-height:1.95;color:var(--text)}
.tc .txt p{margin-bottom:10px}
.tc .txt ul{list-style:none;padding:0}
.tc .txt li{padding:7px 0;padding-inline-start:26px;position:relative;border-bottom:1px solid rgba(128,128,128,.1)}
.tc .txt li::before{content:'';position:absolute;inset-inline-start:0;top:15px;width:9px;height:9px;background:var(--primary);border-radius:50%}

/* image column */
.ic{text-align:center}
.ic img{width:100%;max-height:56vh;object-fit:cover;border-radius:14px;box-shadow:0 8px 28px rgba(0,0,0,.12)}
.ic .cr{display:block;margin-top:6px;font-size:.72em;color:var(--text-light)}

/* === END SLIDE === */
.es{background:var(--gradient);justify-content:center;align-items:center;text-align:center;color:#fff;gap:14px}
.es h2{font-size:3em;font-weight:900}
.es p{font-size:1.15em;opacity:.85}

/* === NAV BAR === */
.nb{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.9);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);padding:9px 22px;border-radius:40px;box-shadow:0 4px 22px rgba(0,0,0,.1);z-index:100}
.nb button{border:none;background:var(--primary);color:#fff;padding:7px 16px;border-radius:18px;cursor:pointer;font-family:inherit;font-size:.85em;font-weight:600;transition:all .25s}
.nb button:hover{background:var(--secondary);transform:scale(1.06)}
.nb button:disabled{background:#ccc;cursor:default;transform:none}
.dots{display:flex;gap:5px}
.dot{width:9px;height:9px;border-radius:50%;background:#d0d0d0;cursor:pointer;transition:all .3s}
.dot.a{background:var(--primary);transform:scale(1.35)}

/* === PROGRESS === */
.pb{position:fixed;top:0;left:0;right:0;height:4px;background:rgba(0,0,0,.06);z-index:200}
.pf{height:100%;background:var(--primary);width:0;transition:width .4s}

/* === PDF BUTTON === */
.xpdf{position:fixed;top:12px;left:12px;z-index:200;background:var(--primary);color:#fff;border:none;padding:7px 18px;border-radius:18px;cursor:pointer;font-family:inherit;font-size:.82em;font-weight:600;box-shadow:0 2px 10px rgba(0,0,0,.15);transition:all .3s}
.xpdf:hover{background:var(--secondary);transform:scale(1.06)}

/* === PRINT / PDF === */
@media print{
  html,body{overflow:visible;height:auto}
  .sw{height:auto;position:static}
  .slide{position:static!important;opacity:1!important;pointer-events:all!important;page-break-after:always;height:100vh;min-height:100vh}
  .nb,.pb,.xpdf{display:none!important}
  .ts,.es,.cs{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}

/* === RESPONSIVE === */
@media(max-width:768px){
  .cs{padding:22px}
  .cs.hi .sbody{grid-template-columns:1fr}
  .ts h1{font-size:2.2em}
  .tc h2{font-size:1.4em}
}
"""

# ═══════════════════════════════════════════════════════════════════
# 🔧  JS TEMPLATE
# ═══════════════════════════════════════════════════════════════════
JS_TEMPLATE = r"""
let cur=0;const ss=document.querySelectorAll('.slide'),tot=ss.length;
function init(){const d=document.getElementById('dots');for(let i=0;i<tot;i++){const s=document.createElement('span');s.className='dot';s.onclick=()=>go(i);d.appendChild(s)}go(0)}
function go(n){cur=Math.max(0,Math.min(n,tot-1));ss.forEach((s,i)=>s.classList.toggle('active',i===cur));document.querySelectorAll('.dot').forEach((d,i)=>d.classList.toggle('a',i===cur));document.getElementById('pf').style.width=((cur+1)/tot*100)+'%';document.getElementById('prv').disabled=cur===0;document.getElementById('nxt').disabled=cur===tot-1}
function nav(d){go(cur+d)}
document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowDown'||e.key===' ')nav(1);if(e.key==='ArrowRight'||e.key==='ArrowUp')nav(-1);if(e.key==='Home')go(0);if(e.key==='End')go(tot-1);if(e.key==='f'||e.key==='F'){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()}});
let tx=0;document.addEventListener('touchstart',e=>{tx=e.touches[0].clientX});document.addEventListener('touchend',e=>{const d=tx-e.changedTouches[0].clientX;if(Math.abs(d)>50)nav(d>0?1:-1)});
init();
"""


# ═══════════════════════════════════════════════════════════════════
# 🚀  TOOL
# ═══════════════════════════════════════════════════════════════════
class PresentationTool(BaseTool):
    """Create stunning interactive HTML presentations with images & PDF export."""

    @property
    def args_schema(self) -> Type[BaseModel]:
        return PresentationSchema

    @property
    def name(self) -> str:
        return "/presentation"

    @property
    def description(self) -> str:
        themes = ", ".join(THEME_NAMES)
        return (
            "إنشاء عرض تقديمي HTML احترافي مع صور وتصدير PDF.\n"
            f"الثيمات المتاحة: {themes}\n"
            "مصادر الصور: auto (تلقائي) | unsplash | pexels | ai (مولدة بالذكاء الاصطناعي) | none\n"
            "يمكنك تمرير الثيم ومصدر الصور كمعاملات."
        )

    @property
    def cost(self) -> int:
        return 2

    # ───────── execute_kwargs (structured) ──────────────────────
    async def execute_kwargs(
        self,
        user_id: str,
        title: str,
        slides: List[str],
        theme: str = "modern",
        image_source: str = "auto",
    ) -> Dict[str, Any]:
        parsed = []
        for s in slides:
            if ":" in s:
                t, c = s.split(":", 1)
                parsed.append({"title": t.strip(), "content": c.strip()})
            else:
                parsed.append({"title": s, "content": ""})
        return await self._create_presentation(title, parsed, theme, image_source, user_id)

    # ───────── execute (string) ─────────────────────────────────
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        try:
            text = user_input.strip()

            # --- extract flags --theme / --images ---------------
            theme = "modern"
            image_source = "auto"
            for flag, choices, attr in [
                ("--theme", THEME_NAMES, "theme"),
                ("--images", ["auto", "unsplash", "pexels", "ai", "none"], "image_source"),
            ]:
                if flag in text:
                    parts = text.split(flag, 1)
                    rest = parts[1].strip().split()[0] if parts[1].strip() else ""
                    if rest.lower() in choices:
                        if attr == "theme":
                            theme = rest.lower()
                        else:
                            image_source = rest.lower()
                    text = parts[0].strip() + " " + " ".join(parts[1].strip().split()[1:])
                    text = text.strip()

            # --- JSON input ------------------------------------
            if text.startswith("{") and "title" in text:
                try:
                    data = json.loads(text)
                    data.setdefault("theme", theme)
                    data.setdefault("image_source", image_source)
                    return await self.execute_kwargs(user_id, **data)
                except Exception:
                    pass

            # --- pipe-separated structured input ----------------
            if "|" in text and ":" in text:
                parts = text.split("|")
                topic = parts[0].strip()
                slides = []
                for p in parts[1:]:
                    if ":" in p:
                        t, c = p.split(":", 1)
                        slides.append({"title": t.strip(), "content": c.strip()})
                return await self._create_presentation(topic, slides, theme, image_source, user_id)

            # --- plain topic -----------------------------------
            topic = text
            for prefix in [
                "اعمل برزنتيشن عن ",
                "اعمل عرض تقديمي عن ",
                "برزنتيشن عن ",
                "عرض تقديمي عن ",
                "presentation about ",
                "create presentation about ",
            ]:
                if topic.lower().startswith(prefix.lower()):
                    topic = topic[len(prefix):].strip()
                    break

            if not topic:
                return {"status": "error", "output": "❌ يرجى تحديد موضوع العرض", "tokens_deducted": 0}

            slides = self._auto_slides(topic)
            return await self._create_presentation(topic, slides, theme, image_source, user_id)

        except Exception as e:
            import traceback
            logger.error(f"Presentation error: {traceback.format_exc()}")
            return {"status": "error", "output": f"❌ خطأ: {str(e)}", "tokens_deducted": 0}

    # ═══════════════════════════════════════════════════════════════
    #  CORE — build presentation
    # ═══════════════════════════════════════════════════════════════
    async def _create_presentation(
        self,
        topic: str,
        slides: List[Dict[str, str]],
        theme: str,
        image_source: str,
        user_id: str,
    ) -> Dict[str, Any]:
        if not slides:
            return {"status": "error", "output": "❌ No slides provided.", "tokens_deducted": 0}

        theme = theme if theme in THEMES else "modern"

        # ── fetch images ──
        try:
            provider = _get_image_provider()
            images = await provider.get_images(topic, count=len(slides) + 1, source=image_source)
        except Exception as e:
            logger.warning(f"Image fetch failed: {e}")
            images = []

        # ── generate HTML ──
        html = self._build_html(topic, slides, theme, images)

        # ── save file ──
        os.makedirs("uploads/presentations", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_name = f"presentation_{ts}.html"
        html_path = os.path.join("uploads", "presentations", html_name)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        html_url = f"/uploads/presentations/{html_name}"

        # ── try PDF ──
        pdf_url = None
        pdf_path = await self._to_pdf(html_path)
        if pdf_path:
            pdf_url = f"/uploads/presentations/{os.path.basename(pdf_path)}"

        # ── response ──
        theme_info = THEMES[theme]
        out_lines = [
            f"✅ تم إنشاء العرض التقديمي بنجاح!",
            f"",
            f"📊 الموضوع: **{topic}**",
            f"📄 عدد الشرائح: {len(slides)}",
            f"🎨 الثيم: {theme}",
            f"🖼️ مصدر الصور: {image_source}",
            f"🔗 رابط HTML: {html_url}",
        ]
        if pdf_url:
            out_lines.append(f"📑 رابط PDF: {pdf_url}")
        else:
            out_lines.append("💡 للتحويل إلى PDF: افتح العرض ← اضغط زر 📄 PDF في الأعلى")

        return {
            "status": "success",
            "output": "\n".join(out_lines),
            "tokens_deducted": self.cost,
            "filepath": html_path,
            "url": html_url,
            "pdf_url": pdf_url,
            "slides_count": len(slides),
        }

    # ═══════════════════════════════════════════════════════════════
    #  HTML BUILDER
    # ═══════════════════════════════════════════════════════════════
    def _build_html(
        self,
        topic: str,
        slides: List[Dict[str, str]],
        theme_name: str,
        images: List[Dict[str, str]],
    ) -> str:
        theme = THEMES.get(theme_name, THEMES["modern"])

        # CSS custom-properties from theme
        root_lines = []
        for k, v in theme.items():
            root_lines.append(f"    --{k}: {v};")
        root_css = ":root {\n" + "\n".join(root_lines) + "\n}"

        total = len(slides) + 2  # title + content + end

        # title slide
        title_img = images[0]["url"] if images else ""
        slides_html = self._html_title(topic, title_img, total)

        # content slides
        for i, slide in enumerate(slides):
            img = images[i + 1] if (i + 1) < len(images) else None
            slides_html += self._html_content(slide, i + 2, total, img, i % 2 == 0)

        # end slide
        slides_html += self._html_end(total)

        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{topic} — RobovAI Presentation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
{root_css}
{CSS_TEMPLATE}
</style>
</head>
<body>
<div class="pb"><div class="pf" id="pf"></div></div>
<button class="xpdf" onclick="window.print()">📄 Save PDF</button>
<div class="sw" id="sw">{slides_html}</div>
<div class="nb">
  <button id="nxt" onclick="nav(1)">التالي ◀</button>
  <div class="dots" id="dots"></div>
  <button id="prv" onclick="nav(-1)">▶ السابق</button>
</div>
<script>
{JS_TEMPLATE}
</script>
</body>
</html>"""

    # ─── slide builders ─────────────────────────────────────────
    def _html_title(self, topic: str, img_url: str, total: int) -> str:
        img_tag = f'<img class="bgi" src="{img_url}" alt="" />' if img_url else ""
        now = datetime.now().strftime("%B %Y")
        return f"""
<section class="slide ts active">
  {img_tag}
  <div class="ov"></div>
  <div class="inner">
    <h1>{topic}</h1>
    <p class="tag">Powered by RobovAI Nova 🤖</p>
    <p class="meta">{now}</p>
  </div>
</section>"""

    def _html_content(
        self,
        slide: Dict[str, str],
        idx: int,
        total: int,
        image: Optional[Dict[str, str]],
        img_right: bool,
    ) -> str:
        title = slide.get("title", f"Slide {idx}")
        raw = slide.get("content", "")
        content_html = self._fmt(raw)
        has_img = image is not None

        cls = "hi" if has_img else "ni"
        if has_img and not img_right:
            cls += " if"

        img_block = ""
        if has_img:
            img_block = f"""
      <div class="ic">
        <img src="{image['url']}" alt="{title}" loading="lazy"/>
        <span class="cr">{image.get('credit','')}</span>
      </div>"""

        return f"""
<section class="slide cs {cls}">
  <div class="stop"><span class="snum">{idx} / {total}</span></div>
  <div class="sbody">
    <div class="tc">
      <h2>{title}</h2>
      <div class="txt">{content_html}</div>
    </div>{img_block}
  </div>
</section>"""

    def _html_end(self, total: int) -> str:
        return f"""
<section class="slide es">
  <h2>شكراً لكم! 🙏</h2>
  <p>تم الإنشاء بواسطة RobovAI Nova</p>
  <p style="font-size:.8em;opacity:.6">{total} / {total}</p>
</section>"""

    # ─── content formatter ──────────────────────────────────────
    @staticmethod
    def _fmt(text: str) -> str:
        """Convert plain text to styled HTML."""
        if not text:
            return ""
        lines = text.split("\n")
        parts: list[str] = []
        in_list = False
        for raw in lines:
            line = raw.strip()
            if not line:
                if in_list:
                    parts.append("</ul>")
                    in_list = False
                continue
            is_bullet = line.startswith(("• ", "- ", "* ", "✅ ", "🔹 ", "✓ "))
            is_num = len(line) > 2 and line[0].isdigit() and line[1] in ".)-"
            if is_bullet or is_num:
                if not in_list:
                    parts.append("<ul>")
                    in_list = True
                content = line.lstrip("•-*✅🔹✓0123456789.)- ")
                parts.append(f"<li>{content}</li>")
            else:
                if in_list:
                    parts.append("</ul>")
                    in_list = False
                # keep inline HTML (like <img>) as-is
                parts.append(f"<p>{line}</p>")
        if in_list:
            parts.append("</ul>")
        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════
    #  PDF CONVERSION  (Playwright, optional)
    # ═══════════════════════════════════════════════════════════════
    async def _to_pdf(self, html_path: str) -> Optional[str]:
        """Try converting HTML → PDF via Playwright. Returns PDF path or None."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.info("Playwright not installed — skipping PDF generation")
            return None

        pdf_path = html_path.replace(".html", ".pdf")
        try:
            abs_html = os.path.abspath(html_path).replace("\\", "/")
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                page = await browser.new_page()
                await page.goto(f"file:///{abs_html}", wait_until="networkidle")
                await page.pdf(
                    path=pdf_path,
                    format="A4",
                    landscape=True,
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                )
                await browser.close()
            logger.info(f"✅ PDF generated: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.warning(f"PDF conversion failed: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════
    #  AUTO SLIDE GENERATION  (fallback when agent sends no content)
    # ═══════════════════════════════════════════════════════════════
    def _auto_slides(self, topic: str) -> List[Dict[str, str]]:
        """Generate 6 generic slides for any topic."""
        return [
            {
                "title": f"📌 مقدمة عن {topic}",
                "content": (
                    f"نظرة عامة شاملة على {topic} وأهميته.\n\n"
                    f"• ما هو {topic}؟\n"
                    f"• لماذا يعتبر مهماً؟\n"
                    f"• كيف يؤثر في حياتنا اليومية؟"
                ),
            },
            {
                "title": "📊 حقائق وأرقام مهمة",
                "content": (
                    f"أهم الحقائق والإحصائيات المتعلقة بـ {topic}:\n\n"
                    "• حقيقة أولى بارزة\n"
                    "• إحصائية مهمة ثانية\n"
                    "• رقم لافت ثالث\n"
                    "• معلومة رابعة مفيدة"
                ),
            },
            {
                "title": "🎯 الأنواع والتصنيفات",
                "content": (
                    f"التصنيفات الرئيسية لـ {topic}:\n\n"
                    "• النوع / التصنيف الأول\n"
                    "• النوع / التصنيف الثاني\n"
                    "• النوع / التصنيف الثالث\n"
                    "• النوع / التصنيف الرابع"
                ),
            },
            {
                "title": "💡 الفوائد والمميزات",
                "content": (
                    f"أهم فوائد {topic}:\n\n"
                    "• تحسين الصحة والرفاهية\n"
                    "• تطوير المهارات الشخصية\n"
                    "• تعزيز الإنتاجية والإبداع\n"
                    "• بناء العلاقات والتواصل"
                ),
            },
            {
                "title": "⚠️ التحديات والنصائح",
                "content": (
                    f"تحديات شائعة ونصائح عملية حول {topic}:\n\n"
                    "• التحدي الأول — والحل المقترح\n"
                    "• التحدي الثاني — والحل المقترح\n"
                    "• التحدي الثالث — والحل المقترح"
                ),
            },
            {
                "title": "🔮 المستقبل والخلاصة",
                "content": (
                    f"التوقعات المستقبلية لـ {topic}:\n\n"
                    "• الاتجاهات الحديثة والتطورات\n"
                    "• الفرص الجديدة والابتكارات\n"
                    "• خلاصة: أهم ما يجب تذكره"
                ),
            },
        ]
