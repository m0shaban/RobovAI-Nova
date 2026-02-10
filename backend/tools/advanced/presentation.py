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
from typing import Dict, Any, List, Optional, Type, Union, Tuple
from pydantic import BaseModel, Field, field_validator
import os, json, ast, logging, re
from datetime import datetime

from backend.core.llm import llm_client

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
        default_factory=list,
        description="Optional list of slide contents: ['Title: Content', ...]. If empty, slides will be auto-generated.",
    )
    slides_count: int = Field(
        6,
        ge=3,
        le=20,
        description="Auto slide count when slides are not provided (3-20)",
    )
    language: str = Field(
        "ar",
        description="Presentation language: ar | en",
    )
    use_web: bool = Field(
        False,
        description="If true, do a lightweight web research summary first and use it to guide slide generation.",
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
        slides: Optional[List[str]] = None,
        slides_count: int = 6,
        language: str = "ar",
        use_web: bool = False,
        theme: str = "modern",
        image_source: str = "auto",
    ) -> Dict[str, Any]:
        slides = slides or []

        parsed: List[Dict[str, str]] = []
        for s in slides:
            s = str(s or "").strip()
            if not s:
                continue
            if ":" in s:
                t, c = s.split(":", 1)
                parsed.append({"title": t.strip(), "content": c.strip()})
            else:
                parsed.append({"title": s, "content": ""})

        research_text = ""
        extra_cost = 0
        if use_web:
            research_text = await self._web_research(title, user_id=user_id)
            extra_cost = 3

        # If no slides provided, auto-generate.
        if not parsed:
            parsed = await self._auto_slides(
                title,
                slides_count=slides_count,
                language=language,
                research_text=research_text,
            )

        # If slides exist but some contents are empty, fill them.
        parsed = await self._fill_missing_slide_content(
            title,
            parsed,
            language=language,
            research_text=research_text,
        )

        # Sanitize (remove emojis / noisy markers)
        parsed = [{"title": self._sanitize_text(s.get("title", "")), "content": self._sanitize_text(s.get("content", ""))} for s in parsed]
        result = await self._create_presentation(title, parsed, theme, image_source, user_id)
        if result.get("status") == "success" and extra_cost:
            result["tokens_deducted"] = int(result.get("tokens_deducted") or 0) + extra_cost
            result["web_research"] = True
        return result

    # ───────── execute (string) ─────────────────────────────────
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        try:
            text = user_input.strip()

            # --- extract flags --theme / --images / --web -------
            theme = "modern"
            image_source = "auto"
            use_web = False
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

            if "--web" in text:
                use_web = True
                text = text.replace("--web", " ").strip()

            # --- JSON input ------------------------------------
            if text.startswith("{") and "title" in text:
                try:
                    data = json.loads(text)
                    data.setdefault("theme", theme)
                    data.setdefault("image_source", image_source)
                    data.setdefault("use_web", use_web)
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

            research_text = ""
            if use_web:
                research_text = await self._web_research(topic, user_id=user_id)

            slides = await self._auto_slides(topic, slides_count=6, language="ar", research_text=research_text)
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

        # De-duplication: if an identical presentation was generated very recently,
        # return the existing file instead of creating another copy.
        existing = self._find_recent_duplicate(user_id, topic, slides, theme, image_source)
        if existing:
            html_path, html_url, pdf_url = existing
            out_lines = [
                "✅ تم إنشاء العرض التقديمي بنجاح!",
                "",
                f"📊 الموضوع: **{topic}**",
                f"📄 عدد الشرائح: {len(slides)}",
                f"🎨 الثيم: {theme}",
                f"🖼️ مصدر الصور: {image_source}",
                f"🔗 رابط HTML: {html_url}",
            ]
            if pdf_url:
                out_lines.append(f"📑 رابط PDF: {pdf_url}")
            else:
                out_lines.append("💡 للتحويل إلى PDF: افتح العرض ← اضغط زر PDF في الأعلى")
            return {
                "status": "success",
                "output": "\n".join(out_lines),
                "tokens_deducted": 0,
                "filepath": html_path,
                "url": html_url,
                "pdf_url": pdf_url,
                "slides_count": len(slides),
                "deduped": True,
            }

        theme = theme if theme in THEMES else "modern"

        # ── fetch images ──
        try:
            provider = _get_image_provider()
            images = await provider.get_images(topic, count=len(slides) + 1, source=image_source)
        except Exception as e:
            logger.warning(f"Image fetch failed: {e}")
            images = []

        effective_image_source = str(images[0].get("source") or "auto") if images else "none"
        images_count = len(images)

        # ── generate HTML ──
        html = self._build_html(
            topic,
            slides,
            theme,
            images,
            user_id=user_id,
            image_source=effective_image_source,
        )

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
        out_lines = [
            f"✅ تم إنشاء العرض التقديمي بنجاح!",
            f"",
            f"📊 الموضوع: **{topic}**",
            f"📄 عدد الشرائح: {len(slides)}",
            f"🎨 الثيم: {theme}",
            f"🖼️ مصدر الصور: {image_source} (فعليًا: {effective_image_source} · {images_count} صور)",
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
        user_id: str,
        image_source: str,
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

        meta = {
            "user_id": user_id,
            "topic": topic,
            "slides_count": len(slides),
            "theme": theme_name,
            "image_source": image_source,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

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
<!--ROBOVAI_META {json.dumps(meta, ensure_ascii=False)} -->
<div class="pb"><div class="pf" id="pf"></div></div>
<button class="xpdf" onclick="window.print()">PDF</button>
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
        <p class="tag">RobovAI Nova</p>
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
    <h2>شكراً لكم</h2>
    <p>RobovAI Nova</p>
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
            is_bullet = line.startswith(("• ", "- ", "* ", "✓ "))
            is_num = len(line) > 2 and line[0].isdigit() and line[1] in ".)-"
            if is_bullet or is_num:
                if not in_list:
                    parts.append("<ul>")
                    in_list = True
                content = line.lstrip("•-*✓0123456789.)- ")
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
    async def _auto_slides(
        self,
        topic: str,
        slides_count: int = 6,
        language: str = "ar",
        research_text: str = "",
    ) -> List[Dict[str, str]]:
        """Generate topic-related slides (LLM-first)."""
        slides_count = max(3, min(int(slides_count or 6), 20))

        try:
            slides = await self._llm_generate_slides(
                topic,
                slides_count=slides_count,
                language=language,
                research_text=research_text,
            )
            if slides:
                return slides[:slides_count]
        except Exception as e:
            logger.warning(f"LLM slide generation failed, falling back: {e}")

        # Fallback only if LLM isn't available.
        summary = await self._wiki_summary(topic, language=language)
        if language == "en":
            base = [
                {"title": f"Introduction to {topic}", "content": summary or f"A brief overview of {topic}."},
                {"title": "Key facts", "content": self._generic_facts_en(topic)},
                {"title": "Uses and applications", "content": self._generic_uses_en(topic)},
            ]
            while len(base) < slides_count:
                base.append({"title": "Tips", "content": self._generic_tips_en(topic)})
        else:
            base = [
                {"title": f"مقدمة عن {topic}", "content": summary or f"نظرة عامة موجزة عن {topic}."},
                {"title": "معلومات أساسية", "content": self._generic_facts_ar(topic)},
                {"title": "الاستخدامات", "content": self._generic_uses_ar(topic)},
            ]
            while len(base) < slides_count:
                base.append({"title": "نصائح عملية", "content": self._generic_tips_ar(topic)})
        return base[:slides_count]

    async def _fill_missing_slide_content(
        self,
        topic: str,
        slides: List[Dict[str, str]],
        language: str = "ar",
        research_text: str = "",
    ) -> List[Dict[str, str]]:
        """If the caller provided only titles (or empty content), fill with meaningful text (LLM-first)."""
        if not slides:
            return slides

        needs = sum(1 for s in slides if not (s.get("content") or "").strip())
        if needs:
            try:
                filled = await self._llm_fill_slides(
                    topic,
                    slides,
                    language=language,
                    research_text=research_text,
                )
                if filled:
                    return filled
            except Exception as e:
                logger.warning(f"LLM fill failed, falling back: {e}")

        # If many slides are empty, fetch a single summary to anchor (fallback only).
        summary = await self._wiki_summary(topic, language=language) if needs else ""

        filled: List[Dict[str, str]] = []
        for s in slides:
            title = (s.get("title") or "").strip() or topic
            content = (s.get("content") or "").strip()
            if not content:
                # Heuristic by title keywords.
                t = title.lower()
                if language == "en":
                    if "intro" in t or "overview" in t:
                        content = summary or f"A concise overview of {topic}."
                    elif "use" in t or "application" in t:
                        content = self._generic_uses_en(topic)
                    elif "tip" in t or "how" in t:
                        content = self._generic_tips_en(topic)
                    else:
                        content = self._generic_facts_en(topic)
                else:
                    if "مقدم" in title or "تعريف" in title:
                        content = summary or f"نظرة عامة موجزة عن {topic}."
                    elif "استخدام" in title:
                        content = self._generic_uses_ar(topic)
                    elif "نصيح" in title or "تخزين" in title or "اختيار" in title:
                        content = self._generic_tips_ar(topic)
                    else:
                        content = self._generic_facts_ar(topic)

            filled.append({"title": title, "content": content})
        return filled

    async def _web_research(self, topic: str, user_id: str) -> str:
        """Lightweight research summary to guide slide generation (best-effort)."""
        try:
            from backend.tools.advanced.deep_research import DeepResearchTool

            tool = DeepResearchTool()
            res = await tool.execute(topic, user_id)
            if res.get("status") == "success":
                out = (res.get("output") or "").strip()
                # keep it bounded so prompts stay stable
                return out[:6000]
            return ""
        except Exception as e:
            logger.info(f"Web research unavailable: {e}")
            return ""

    async def _llm_generate_slides(
        self,
        topic: str,
        slides_count: int,
        language: str = "ar",
        research_text: str = "",
    ) -> List[Dict[str, str]]:
        lang = "Arabic" if language != "en" else "English"
        research_block = ""
        if (research_text or "").strip():
            research_block = (
                "\n\nHere are research notes (may include noise; use only what is relevant):\n"
                + research_text.strip()
            )

        prompt = (
            f"Create a high-quality slide deck about: {topic}.\n"
            f"Language: {lang}.\n"
            f"Slides count: {slides_count}.\n"
            "Output MUST be valid JSON only (no markdown, no code fences) with this shape:\n"
            "{\"slides\":[{\"title\":...,\"content\":...}, ...]}\n"
            "Rules:\n"
            "- No emojis.\n"
            "- Each slide content is plain text with 4-6 bullet lines starting with '• '.\n"
            "- Avoid vague filler; be specific and practical.\n"
            "- Do not mention internal technologies/providers.\n"
            "- Keep titles short (2-6 words).\n"
            "- Cover: overview, key points, benefits/uses, how-to/tips, risks/limitations, conclusion.\n"
            + research_block
        )

        system_prompt = (
            "أنت نوفا، مساعد ذكي. اكتب محتوى عرض تقديمي واضح ومنظم، "
            "بدون رموز تعبيرية، وبنقاط مختصرة." if language != "en" else
            "You are Nova. Write clear, structured slide content with no emojis and concise bullets."
        )

        raw = await llm_client.generate(prompt, provider="auto", system_prompt=system_prompt)
        data = self._safe_json_load(raw)
        slides = data.get("slides") if isinstance(data, dict) else None
        if not isinstance(slides, list):
            return []

        out: List[Dict[str, str]] = []
        for item in slides:
            if not isinstance(item, dict):
                continue
            t = str(item.get("title") or "").strip()
            c = str(item.get("content") or "").strip()
            if not t or not c:
                continue
            out.append({"title": t, "content": c})
        return out

    async def _llm_fill_slides(
        self,
        topic: str,
        slides: List[Dict[str, str]],
        language: str = "ar",
        research_text: str = "",
    ) -> List[Dict[str, str]]:
        lang = "Arabic" if language != "en" else "English"
        skeleton = [{"title": (s.get("title") or "").strip(), "content": (s.get("content") or "").strip()} for s in slides]
        research_block = ""
        if (research_text or "").strip():
            research_block = (
                "\n\nResearch notes (optional):\n" + research_text.strip()
            )

        prompt = (
            f"Fill in missing/empty slide content for a deck about: {topic}.\n"
            f"Language: {lang}.\n"
            "Return JSON only: {\"slides\":[{\"title\":...,\"content\":...}, ...]}\n"
            "Rules:\n"
            "- Keep the same number of slides and the same titles as provided.\n"
            "- For any non-empty content, you may lightly polish, but keep meaning.\n"
            "- No emojis.\n"
            "- Each content is plain text with 4-6 bullet lines starting with '• '.\n"
            + research_block
            + "\n\nInput slides JSON:\n"
            + json.dumps({"slides": skeleton}, ensure_ascii=False)
        )

        system_prompt = (
            "أنت نوفا، اكتب نقاط واضحة ومنظمة للشرائح بدون رموز تعبيرية." if language != "en" else
            "You are Nova. Write clear bullet slide content with no emojis."
        )

        raw = await llm_client.generate(prompt, provider="auto", system_prompt=system_prompt)
        data = self._safe_json_load(raw)
        slides_out = data.get("slides") if isinstance(data, dict) else None
        if not isinstance(slides_out, list) or len(slides_out) != len(slides):
            return []

        out: List[Dict[str, str]] = []
        for i, item in enumerate(slides_out):
            if not isinstance(item, dict):
                return []
            title = str(item.get("title") or "").strip() or (slides[i].get("title") or topic)
            content = str(item.get("content") or "").strip() or (slides[i].get("content") or "")
            out.append({"title": title, "content": content})
        return out

    @staticmethod
    def _safe_json_load(text: str) -> Dict[str, Any]:
        if not text:
            return {}
        s = text.strip()

        # Strip common code-fence wrappers just in case.
        if s.startswith("```"):
            s = re.sub(r"^```[a-zA-Z0-9_+-]*\n", "", s)
            s = s.rstrip("`\n ")

        # Try direct json
        try:
            return json.loads(s)
        except Exception:
            pass

        # Try to extract the first JSON object
        try:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(s[start : end + 1])
        except Exception:
            return {}

        return {}

    @staticmethod
    def _sanitize_text(text: str) -> str:
        if not text:
            return ""
        # Remove common emoji ranges + extra markers in titles.
        cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", text)
        cleaned = cleaned.replace("🤖", "").replace("🙏", "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _find_recent_duplicate(
        self,
        user_id: str,
        topic: str,
        slides: List[Dict[str, str]],
        theme: str,
        image_source: str,
        window_seconds: int = 120,
    ) -> Optional[Tuple[str, str, Optional[str]]]:
        """Reuse the latest matching HTML generated recently to avoid double-creation."""
        try:
            folder = os.path.join("uploads", "presentations")
            if not os.path.isdir(folder):
                return None

            # Compare by a lightweight signature
            sig = {
                "user_id": str(user_id),
                "topic": topic,
                "slides_count": len(slides),
                "theme": theme,
                "image_source": image_source,
            }

            now = datetime.now().timestamp()
            candidates = [
                f
                for f in os.listdir(folder)
                if f.startswith("presentation_") and f.endswith(".html")
            ]
            candidates.sort(reverse=True)

            for name in candidates[:40]:
                path = os.path.join(folder, name)
                try:
                    mtime = os.path.getmtime(path)
                    if (now - mtime) > window_seconds:
                        continue
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        head = fh.read(4096)
                    m = re.search(r"<!--ROBOVAI_META (\{.*?\}) -->", head)
                    if not m:
                        continue
                    meta = json.loads(m.group(1))
                    same = all(str(meta.get(k)) == str(sig.get(k)) for k in sig.keys())
                    if same:
                        html_url = f"/uploads/presentations/{name}"
                        pdf_name = name.replace(".html", ".pdf")
                        pdf_path = os.path.join(folder, pdf_name)
                        pdf_url = f"/uploads/presentations/{pdf_name}" if os.path.exists(pdf_path) else None
                        return (path, html_url, pdf_url)
                except Exception:
                    continue
        except Exception:
            return None
        return None

    async def _wiki_summary(self, topic: str, language: str = "ar") -> str:
        """Fetch a short summary from Wikipedia REST API (best-effort)."""
        try:
            import httpx

            lang = "ar" if language != "en" else "en"
            # Wikipedia REST expects URL-encoded title.
            safe = httpx.URL("https://example.com/" + topic).path.lstrip("/")
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{safe}"
            async with httpx.AsyncClient(timeout=6) as client:
                r = await client.get(url, headers={"User-Agent": "RobovAI-Nova/1.0"})
                if r.status_code != 200:
                    return ""
                data = r.json()
                extract = (data.get("extract") or "").strip()
                # Keep it short for slides.
                if extract and len(extract) > 380:
                    extract = extract[:380].rsplit(" ", 1)[0] + "..."
                return extract
        except Exception:
            return ""

    @staticmethod
    def _generic_facts_ar(topic: str) -> str:
        return (
            f"أبرز النقاط حول {topic}:\n\n"
            "• التعريف: ما هو؟\n"
            "• الخصائص: الشكل والطعم والرائحة\n"
            "• القيمة الغذائية: عناصر مفيدة ومضادات أكسدة\n"
            "• موسم التوفر: يختلف حسب البلد\n"
            "• الاستخدام الشائع: طازج أو عصائر أو حلويات"
        )

    @staticmethod
    def _generic_uses_ar(topic: str) -> str:
        return (
            f"طرق استخدام {topic}:\n\n"
            "• تناوله طازجاً بعد الغسل والتجهيز\n"
            "• عصير أو سموذي\n"
            "• مربى أو صوص\n"
            "• إضافته للسلطات والحلويات\n"
            "• استخدامه في وصفات منزلية حسب الذوق"
        )

    @staticmethod
    def _generic_tips_ar(topic: str) -> str:
        return (
            f"نصائح سريعة عند التعامل مع {topic}:\n\n"
            "• اختر الثمرة ذات الرائحة الواضحة والملمس المناسب\n"
            "• خزّنها في درجة حرارة مناسبة حسب درجة النضج\n"
            "• قطّعها قبل التقديم مباشرة للحفاظ على القوام\n"
            "• إذا كانت للاستخدام في العصير، اختر الثمرة الناضجة\n"
            "• احفظ البقايا في وعاء محكم داخل الثلاجة"
        )

    @staticmethod
    def _generic_facts_en(topic: str) -> str:
        return (
            f"Key points about {topic}:\n\n"
            "• Definition and overview\n"
            "• Notable characteristics\n"
            "• Nutritional highlights\n"
            "• Availability/seasonality\n"
            "• Common uses"
        )

    @staticmethod
    def _generic_uses_en(topic: str) -> str:
        return (
            f"Common uses of {topic}:\n\n"
            "• Fresh consumption\n"
            "• Juices and smoothies\n"
            "• Jams and sauces\n"
            "• Desserts and salads\n"
            "• Home recipes"
        )

    @staticmethod
    def _generic_tips_en(topic: str) -> str:
        return (
            f"Practical tips for {topic}:\n\n"
            "• Choose based on aroma and firmness\n"
            "• Store according to ripeness\n"
            "• Prepare close to serving\n"
            "• Use ripe fruit for blending\n"
            "• Refrigerate leftovers in an airtight container"
        )
