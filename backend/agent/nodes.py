"""
🧠 RobovAI Nova - Agent Graph Nodes
═══════════════════════════════════════════════════════════════

The core logic nodes for the ReAct Agent Loop:
  Think → Plan → Act → Observe → Reflect → (Loop or End)

Each node receives the AgentState and returns updates to it.
"""

from typing import Dict, Any, List, Literal
from .state import AgentState, AgentPhase, ToolCall, ToolResult
from .tools_adapter import ToolsAdapter, get_langgraph_tools
from backend.core.config import settings
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
import json
import logging
from datetime import datetime
import random

logger = logging.getLogger("robovai.agent.nodes")


# ═══════════════════════════════════════════════════════════════
# 🤖 LLM SETUP - Smart Multi-Provider with Rotation & Fallback
# ═══════════════════════════════════════════════════════════════

# Track failed Groq keys at module level
_failed_groq_keys: set = set()
_groq_key_index: int = 0


def get_all_groq_keys() -> List[str]:
    """Get all valid Groq keys"""
    keys = [
        settings.GROQ_API_KEY,
        settings.GROQ_API_KEY_2,
        settings.GROQ_API_KEY_3,
        settings.GROQ_API_KEY_4,
    ]
    return [k for k in keys if k and k.startswith("gsk_")]


def get_groq_key() -> str | None:
    """Get next working Groq API key (round-robin, skip failed)"""
    global _groq_key_index
    valid_keys = get_all_groq_keys()

    if not valid_keys:
        return None

    # Try round-robin, skipping failed keys
    available = [k for k in valid_keys if k not in _failed_groq_keys]

    if not available:
        # All keys failed - reset and try again
        _failed_groq_keys.clear()
        available = valid_keys

    _groq_key_index = (_groq_key_index + 1) % len(available)
    selected = available[_groq_key_index]
    masked = f"{selected[:8]}...{selected[-4:]}"
    logger.info(f"🔑 Using Groq Key: {masked}")
    return selected


def mark_groq_key_failed(key: str):
    """Mark a Groq key as temporarily failed (rate limited)"""
    _failed_groq_keys.add(key)
    masked = f"{key[:8]}...{key[-4:]}"
    logger.warning(f"🚫 Marked Groq key as rate-limited: {masked}")


def get_nvidia_llm():
    """Get NVIDIA LLM instance"""
    if not settings.NVIDIA_API_KEY:
        return None
    try:
        return ChatOpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1",
            model=settings.NVIDIA_MODEL or "meta/llama-3.1-405b-instruct",
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to init NVIDIA LLM: {e}")
        return None


def get_openrouter_llm():
    """Get OpenRouter LLM instance as last resort"""
    if not settings.OPENROUTER_API_KEY:
        return None
    try:
        return ChatOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            model="meta-llama/llama-3.1-8b-instruct:free",
            temperature=0.3,
            max_tokens=4096,
            default_headers={"HTTP-Referer": "https://robovai.com"},
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to init OpenRouter LLM: {e}")
        return None


def get_llm(complexity: str = "medium"):
    """
    Get configured LLM with smart provider selection.
    Priority: Complex→NVIDIA, Normal→Groq→NVIDIA→OpenRouter
    """
    # For complex tasks, prefer NVIDIA (bigger model)
    if complexity == "complex":
        nvidia = get_nvidia_llm()
        if nvidia:
            logger.info("🧠 Complex task → NVIDIA Llama 3.1 405B")
            return nvidia

    # Try Groq with key rotation
    groq_key = get_groq_key()
    if groq_key:
        try:
            return ChatGroq(
                api_key=groq_key,
                model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=4096,
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to init Groq: {e}")
            mark_groq_key_failed(groq_key)

    # Fallback to NVIDIA
    nvidia = get_nvidia_llm()
    if nvidia:
        logger.info("🔄 Groq unavailable → NVIDIA fallback")
        return nvidia

    # Last resort: OpenRouter
    openrouter = get_openrouter_llm()
    if openrouter:
        logger.info("🔄 All providers failed → OpenRouter fallback")
        return openrouter

    # Absolute final fallback
    logger.error("❌ No LLM providers available!")
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=4096,
    )


# ═══════════════════════════════════════════════════════════════
# 📝 SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════

NOVA_PERSONA = """أنت "نوفا" (Nova) — مساعد ذكي متقدم ومتعدد القدرات من RobovAI Solutions 🇪🇬.
أنت مبرمج محترف، مصمم، منشئ محتوى، مستشار أعمال، ومساعد شخصي.

🎯 شخصيتك:
- ودود ومحترف، بتتكلم بلغة المستخدم (عربية مصرية بالزات أو إنجليزية)
- بتستخدم الإيموجي بذكاء ومن غير إفراط
- **بتنفذ مش بتشرح بس** — لو المستخدم طلب كود أو صفحة أو صورة، أنشئها فوراً
- أسلوبك مختصر وواضح ومنظم — مش بتطوّل بدون فايدة
- لو حد قالك "اهلا" أو كلام عادي، رد عليه بشكل طبيعي وبسيط. مش كل كلام محتاج أدوات!

🛠️ قدراتك المتقدمة (99+ أداة):
- كتابة أكواد HTML/CSS/JS/Python احترافية (صفحات هبوط، مواقع، بورتفوليو، تطبيقات)
- توليد صور بالذكاء الاصطناعي عبر أدواتك
- إنشاء عروض تقديمية كاملة
- بحث الويب، ترجمة، تحليل ملفات PDF/Excel
- استشارات أعمال وحساب ROI ودراسة جدوى
- تحويل صوت لنص والعكس
- إنشاء QR codes، charts، وأكتر من 99 أداة

📋 قواعد الردود (مهمة جداً):
1. **الروابط**: اعرض أي رابط كامل وواضح: [نص واضح](https://full-url)
   - لو الرابط طويل، اختار له اسم مختصر وواضح
   - ما تخليش الرابط مكسور أو ناقص أبداً
2. **الصور**: اعرض أي صورة كـ markdown: ![وصف الصورة](https://image-url)
   - تأكد إن الرابط كامل وصحيح (يبدأ بـ https://)
   - لو الصورة من أداة، استخدم الرابط المباشر من نتيجة الأداة
3. **الأكواد**: ضع أي كود في code blocks مع تحديد اللغة
4. **التنسيق**: استخدم Markdown بشكل احترافي:
   - عناوين واضحة (##) للأقسام
   - قوائم (- أو 1.) للنقاط
   - **Bold** للكلمات المهمة
   - > للاقتباسات
   - جداول لما يكون فيه مقارنات أو بيانات
5. **HTML/مواقع**: لما المستخدم يطلب صفحة HTML أو landing page:
   - أنشئ كود HTML+CSS+JS كامل واحترافي مع تصميم responsive
   - استخدم gradients وanimations وخطوط عربية حلوة
   - خلي التصميم عصري وجذاب
6. **المحادثة العادية**: لو الرسالة مجرد سلام أو سؤال بسيط أو دردشة:
   - رد بشكل طبيعي وبسيط بدون أدوات
   - كن ودود ومختصر
   - ما تعملش خطة ولا تستدعي أدوات لمجرد "ازيك" أو "من انت"

⚡ أسلوب العمل:
1. قيّم الطلب: هل محتاج أدوات ولا مجرد رد ذكي؟
2. لو محتاج أدوات: ضع خطة واضحة ونفذها
3. لو مجرد محادثة: رد مباشرة بذكاء وبساطة
4. اعرض النتائج بشكل منظم وجميل
5. اقترح خطوات تانية أو تحسينات

⚠️ قواعد صارمة:
- لا ترجع روابط localhost أبداً — استخدم الروابط الكاملة
- لو أداة رجعت URL، اعرضه كامل للمستخدم
- لو في صورة، اعرضها كـ ![وصف](url) — مش مجرد رابط
- لو في ملف تم إنشاؤه، اعرض رابط التحميل الكامل
- ردودك لازم تكون منسقة ومنظمة — مش فوضوية
"""

THINKING_PROMPT = """حلل طلب المستخدم التالي وأجب بـ JSON:

الطلب: {request}

أجب بـ JSON فقط بهذا الشكل:
{{
    "understanding": "فهمك للمطلوب بكلماتك",
    "complexity": "simple|medium|complex",
    "needs_tools": true/false,
    "suggested_tools": ["tool1", "tool2"],
    "plan": ["خطوة 1", "خطوة 2", "خطوة 3"]
}}
"""

REFLECTION_PROMPT = """راجع نتائج التنفيذ:

المهمة الأصلية: {original_request}
الخطة: {plan}
النتائج: {results}
الأخطاء: {errors}

قرر:
1. هل المهمة اكتملت بنجاح؟
2. هل تحتاج إعادة محاولة؟
3. ما الرد النهائي للمستخدم؟

أجب بـ JSON:
{{
    "task_completed": true/false,
    "needs_retry": true/false,
    "retry_reason": "السبب إن وجد",
    "final_answer": "الرد النهائي للمستخدم"
}}
"""


# ═══════════════════════════════════════════════════════════════
# 🧠 NODE 1: THINK
# ═══════════════════════════════════════════════════════════════


async def think_node(state: AgentState) -> Dict[str, Any]:
    """
    عقدة التفكير - تحلل المهمة وتفهم المطلوب

    Input: User request
    Output: Task understanding + complexity assessment
    """
    logger.info("🧠 THINK NODE: Analyzing request...")

    llm = get_llm()

    # Get available tools descriptions
    tools_desc = ToolsAdapter.get_tools_descriptions()

    # Build analysis prompt
    prompt = f"""
{NOVA_PERSONA}

{THINKING_PROMPT.format(request=state['original_request'])}

الأدوات المتاحة:
{tools_desc}
"""

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content="أنت محلل مهام. أجب بـ JSON فقط."),
                HumanMessage(content=prompt),
            ]
        )

        # Parse JSON response
        content = response.content
        # Clean up if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        analysis = json.loads(content.strip())

        logger.info(f"📊 Analysis: {analysis}")

        return {
            "task_understanding": analysis.get("understanding", ""),
            "task_complexity": analysis.get("complexity", "medium"),
            "plan_steps": analysis.get("plan", []),
            "phase": AgentPhase.PLANNING.value,
            "messages": [
                AIMessage(content=f"فهمت! {analysis.get('understanding', '')}")
            ],
        }

    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ JSON parse error: {e}")
        # Fallback: simple task
        return {
            "task_understanding": state["original_request"],
            "task_complexity": "simple",
            "plan_steps": [state["original_request"]],
            "phase": AgentPhase.PLANNING.value,
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Think node error: {e}")

        # Check if rate limit - try fallback providers
        if (
            "429" in error_msg
            or "rate_limit" in error_msg.lower()
            or "rate limit" in error_msg.lower()
        ):
            # Mark current key as failed
            current_key = get_groq_key()
            if current_key:
                mark_groq_key_failed(current_key)

            # Build fallback chain
            fallback_llms = []
            next_key = get_groq_key()
            if next_key:
                try:
                    fallback_llms.append(
                        (
                            "Groq (next)",
                            ChatGroq(
                                api_key=next_key,
                                model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                                temperature=0.3,
                                max_tokens=4096,
                            ),
                        )
                    )
                except:
                    pass
            nvidia = get_nvidia_llm()
            if nvidia:
                fallback_llms.append(("NVIDIA", nvidia))
            openrouter = get_openrouter_llm()
            if openrouter:
                fallback_llms.append(("OpenRouter", openrouter))

            for provider_name, fallback_llm in fallback_llms:
                logger.info(f"🔄 Think fallback: {provider_name}...")
                try:
                    response = await fallback_llm.ainvoke(
                        [
                            SystemMessage(content=NOVA_PERSONA),
                            HumanMessage(content=prompt),
                        ]
                    )
                    content = response.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    analysis = json.loads(content.strip())
                    logger.info(f"📊 [{provider_name}] Analysis: {analysis}")
                    return {
                        "task_understanding": analysis.get("understanding", ""),
                        "task_complexity": analysis.get("complexity", "medium"),
                        "plan_steps": analysis.get("plan", []),
                        "phase": AgentPhase.PLANNING.value,
                        "messages": [
                            AIMessage(
                                content=f"فهمت! {analysis.get('understanding', '')}"
                            )
                        ],
                    }
                except Exception as fb_e:
                    logger.warning(f"⚠️ {provider_name} Think fallback failed: {fb_e}")
                    continue

        # If all failed, treat as simple task (graceful degradation)
        logger.warning("⚠️ All providers failed in Think, treating as simple task")
        return {
            "task_understanding": state["original_request"],
            "task_complexity": "simple",
            "plan_steps": [state["original_request"]],
            "phase": AgentPhase.PLANNING.value,
        }


# ═══════════════════════════════════════════════════════════════
# 📋 NODE 2: PLAN (Optional Enhancement)
# ═══════════════════════════════════════════════════════════════


async def plan_node(state: AgentState) -> Dict[str, Any]:
    """
    عقدة التخطيط - تحضر الأدوات المطلوبة للخطوة الحالية

    This node prepares tool calls for the current step.
    """
    logger.info(f"📋 PLAN NODE: Preparing step {state['current_step_index'] + 1}")

    if not state.get("plan_steps"):
        return {"phase": AgentPhase.ACTING.value, "pending_tool_calls": []}

    current_step = state["plan_steps"][state["current_step_index"]]

    return {
        "phase": AgentPhase.ACTING.value,
        "messages": [AIMessage(content=f"🔄 جاري تنفيذ: {current_step}")],
    }


# ═══════════════════════════════════════════════════════════════
# ⚡ NODE 3: ACT
# ═══════════════════════════════════════════════════════════════


async def act_node(state: AgentState) -> Dict[str, Any]:
    """
    عقدة التنفيذ - تشغل الأدوات المطلوبة

    Uses LLM with tool binding to execute the plan.
    """
    logger.info("⚡ ACT NODE: Executing tools...")

    # Use complexity from state to decide LLM
    complexity = state.get("task_complexity", "medium")
    llm = get_llm(complexity)

    all_tools = get_langgraph_tools(state.get("user_id", "agent"))

    if not all_tools:
        logger.warning("⚠️ No tools available")
        return {
            "phase": AgentPhase.OBSERVING.value,
            "tool_results": [],
        }

    # ── Smart tool selection: send only relevant tools to avoid token overflow ──
    current_step = ""
    if state.get("plan_steps") and state["current_step_index"] < len(
        state["plan_steps"]
    ):
        current_step = state["plan_steps"][state["current_step_index"]]
    else:
        current_step = state["original_request"]

    request_lower = (current_step + " " + state.get("original_request", "")).lower()

    # Priority tools always included
    ALWAYS_INCLUDE = {"create_file", "generate_image", "math", "weather", "translate_egy",
                      "wiki", "wikipedia", "chart", "presentation", "run_code", "scrape_url"}

    # Score tools by keyword relevance
    def tool_relevance(t):
        name = t.name.lower()
        desc = (t.description or "").lower()
        score = 0
        if name in ALWAYS_INCLUDE:
            score += 100
        # Check if tool name or keywords appear in the request
        for word in name.replace("_", " ").split():
            if word in request_lower:
                score += 50
        for word in request_lower.split():
            if len(word) > 3 and word in desc:
                score += 10
        return score

    scored = sorted(all_tools, key=tool_relevance, reverse=True)
    MAX_TOOLS = 25  # Keep under Groq's 12K TPM limit
    tools = scored[:MAX_TOOLS]
    logger.info(f"🔧 Selected {len(tools)}/{len(all_tools)} relevant tools for: {current_step[:50]}")

    # Bind tools to LLM
    try:
        llm_with_tools = llm.bind_tools(tools)
    except (NotImplementedError, AttributeError):
        try:
            from langchain_core.utils.function_calling import convert_to_openai_tool

            formatted_tools = [convert_to_openai_tool(t) for t in tools]
            llm_with_tools = llm.bind(tools=formatted_tools)
        except Exception as e:
            logger.error(f"❌ Failed to bind tools manually: {e}")
            llm_with_tools = llm

    # Build execution prompt
    original_request = state.get("original_request", "")
    system_msg = f"""
{NOVA_PERSONA}

## Original User Request
{original_request}

## Current Step
{current_step}

## Instructions
- Use the available tools to execute this step.
- When creating files, use the EXACT content requested by the user. Do NOT use placeholder or example content.
- If the user requested specific text, HTML, or code, include ALL of it in the tool call.
- If you don't need tools, answer directly.
"""

    try:
        response = await llm_with_tools.ainvoke(
            [SystemMessage(content=system_msg), HumanMessage(content=current_step)]
        )

        # Check if tools were called
        tool_results = []

        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"🔧 Tool calls: {len(response.tool_calls)}")

            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})

                logger.info(f"  → Calling {tool_name} with {tool_args}")

                # Find and execute the tool
                start_time = datetime.now()
                try:
                    tool = ToolsAdapter.get_tool_by_name(
                        tool_name, state.get("user_id", "agent")
                    )
                    if tool:
                        # Execute async
                        if isinstance(tool, StructuredTool):
                            input_val = tool_args
                        else:
                            input_val = tool_args.get("query", str(tool_args))

                        result = await tool.ainvoke(input_val)

                        tool_results.append(
                            ToolResult(
                                tool_name=tool_name,
                                success=True,
                                output=result,
                                error=None,
                                execution_time_ms=(
                                    datetime.now() - start_time
                                ).total_seconds()
                                * 1000,
                            )
                        )
                    else:
                        tool_results.append(
                            ToolResult(
                                tool_name=tool_name,
                                success=False,
                                output=None,
                                error=f"Tool '{tool_name}' not found",
                                execution_time_ms=0,
                            )
                        )
                except Exception as e:
                    tool_results.append(
                        ToolResult(
                            tool_name=tool_name,
                            success=False,
                            output=None,
                            error=str(e),
                            execution_time_ms=(
                                datetime.now() - start_time
                            ).total_seconds()
                            * 1000,
                        )
                    )

            return {
                "phase": AgentPhase.OBSERVING.value,
                "tool_results": state.get("tool_results", []) + tool_results,
                "messages": [response],
            }
        else:
            # No tools needed, direct response
            logger.info("💬 Direct response (no tools needed)")
            return {
                "phase": AgentPhase.OBSERVING.value,
                "tool_results": [],
                "accumulated_outputs": state.get("accumulated_outputs", [])
                + [{"type": "text", "content": response.content}],
                "messages": [response],
            }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Act node error: {e}")

        # Check if it's a rate limit error - try fallback providers
        if (
            "429" in error_msg
            or "rate_limit" in error_msg.lower()
            or "rate limit" in error_msg.lower()
        ):
            # Mark the current Groq key as failed
            current_key = get_groq_key()
            if current_key:
                mark_groq_key_failed(current_key)

            # Build fallback chain
            fallback_llms = []

            # Try another Groq key first
            next_key = get_groq_key()
            if next_key:
                try:
                    fallback_llms.append(
                        (
                            "Groq (next key)",
                            ChatGroq(
                                api_key=next_key,
                                model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                                temperature=0.3,
                                max_tokens=4096,
                            ),
                        )
                    )
                except:
                    pass

            # Then NVIDIA
            nvidia = get_nvidia_llm()
            if nvidia:
                fallback_llms.append(("NVIDIA", nvidia))

            # Then OpenRouter
            openrouter = get_openrouter_llm()
            if openrouter:
                fallback_llms.append(("OpenRouter", openrouter))

            for provider_name, fallback_llm in fallback_llms:
                logger.info(f"🔄 Trying fallback: {provider_name}...")
                try:
                    from langchain_core.utils.function_calling import (
                        convert_to_openai_tool,
                    )

                    formatted_tools = [convert_to_openai_tool(t) for t in tools]

                    try:
                        fallback_with_tools = fallback_llm.bind_tools(tools)
                    except:
                        fallback_with_tools = fallback_llm.bind(tools=formatted_tools)

                    response = await fallback_with_tools.ainvoke(
                        [
                            SystemMessage(content=system_msg),
                            HumanMessage(content=current_step),
                        ]
                    )

                    # Process response
                    tool_results = []
                    if hasattr(response, "tool_calls") and response.tool_calls:
                        for tool_call in response.tool_calls:
                            tool_name = tool_call.get("name", "")
                            tool_args = tool_call.get("args", {})
                            logger.info(f"  → [{provider_name}] Calling {tool_name}")
                            start_time = datetime.now()
                            try:
                                tool = ToolsAdapter.get_tool_by_name(
                                    tool_name, state.get("user_id", "agent")
                                )
                                if tool:
                                    input_val = (
                                        tool_args
                                        if isinstance(tool, StructuredTool)
                                        else tool_args.get("query", str(tool_args))
                                    )
                                    result = await tool.ainvoke(input_val)
                                    tool_results.append(
                                        ToolResult(
                                            tool_name=tool_name,
                                            success=True,
                                            output=result,
                                            error=None,
                                            execution_time_ms=(
                                                datetime.now() - start_time
                                            ).total_seconds()
                                            * 1000,
                                        )
                                    )
                            except Exception as te:
                                tool_results.append(
                                    ToolResult(
                                        tool_name=tool_name,
                                        success=False,
                                        output=None,
                                        error=str(te),
                                        execution_time_ms=0,
                                    )
                                )
                        return {
                            "phase": AgentPhase.OBSERVING.value,
                            "tool_results": state.get("tool_results", [])
                            + tool_results,
                            "messages": [response],
                        }
                    else:
                        return {
                            "phase": AgentPhase.OBSERVING.value,
                            "tool_results": [],
                            "accumulated_outputs": state.get("accumulated_outputs", [])
                            + [{"type": "text", "content": response.content}],
                            "messages": [response],
                        }
                except Exception as fb_e:
                    logger.warning(f"⚠️ {provider_name} fallback failed: {fb_e}")
                    continue

        return {
            "phase": AgentPhase.REFLECTING.value,
            "errors": state.get("errors", []) + [str(e)],
            "last_error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# 👁️ NODE 4: OBSERVE
# ═══════════════════════════════════════════════════════════════


async def observe_node(state: AgentState) -> Dict[str, Any]:
    """
    عقدة الملاحظة - تفحص نتائج التنفيذ

    Checks tool results and accumulates outputs.
    """
    logger.info("👁️ OBSERVE NODE: Checking results...")

    tool_results = state.get("tool_results", [])
    accumulated = state.get("accumulated_outputs", [])

    # Process new results
    new_outputs = []
    has_errors = False

    for result in tool_results:
        if isinstance(result, dict):
            if result.get("success"):
                new_outputs.append(
                    {
                        "type": "tool_output",
                        "tool": result.get("tool_name"),
                        "content": result.get("output"),
                    }
                )
            else:
                has_errors = True
                logger.warning(f"⚠️ Tool error: {result.get('error')}")

    # Move to next step if we have more
    next_step = state["current_step_index"] + 1
    has_more_steps = next_step < len(state.get("plan_steps", []))

    return {
        "phase": AgentPhase.REFLECTING.value,
        "accumulated_outputs": accumulated + new_outputs,
        "current_step_index": (
            next_step if has_more_steps else state["current_step_index"]
        ),
    }


# ═══════════════════════════════════════════════════════════════
# 🔄 NODE 5: REFLECT
# ═══════════════════════════════════════════════════════════════


async def reflect_node(state: AgentState) -> Dict[str, Any]:
    """
    عقدة التأمل - تقرر: نجاح أم إعادة المحاولة؟

    This is the decision point in the loop.
    """
    logger.info("🔄 REFLECT NODE: Evaluating results...")

    llm = get_llm()

    # Gather results
    results_summary = []
    for output in state.get("accumulated_outputs", []):
        if isinstance(output, dict):
            results_summary.append(
                f"- {output.get('type')}: {str(output.get('content', ''))[:200]}"
            )

    # Check if we need to continue
    current_step = state["current_step_index"]
    total_steps = len(state.get("plan_steps", []))
    has_more_steps = current_step < total_steps - 1

    errors = state.get("errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # If we have errors and exhausted retries → give up gracefully
    if errors and retry_count >= max_retries:
        logger.warning(f"❌ Max retries ({max_retries}) exhausted. Generating fallback answer...")
        error_summary = "; ".join(str(e)[:100] for e in errors[-2:])
        # Check if we have any accumulated outputs regardless
        if results_summary:
            fallback = "⚠️ واجهت بعض المشاكل لكن هذه النتائج المتاحة:\n\n" + "\n".join(results_summary[:5])
        else:
            fallback = f"❌ لم أتمكن من تنفيذ الطلب بالكامل. السبب: {error_summary}\n\nجرب مرة تانية أو غيّر صياغة الطلب."
        return {
            "phase": AgentPhase.COMPLETED.value,
            "final_answer": fallback,
            "should_end": True,
        }

    # Simple decision logic — retry if errors and retries remain
    if errors and retry_count < max_retries:
        logger.info(f"🔄 Retrying... ({retry_count + 1}/{max_retries})")
        return {
            "phase": AgentPhase.ACTING.value,
            "retry_count": retry_count + 1,
            "errors": [],  # Clear errors for retry
            "should_end": False,
        }

    if has_more_steps:
        logger.info(f"➡️ Moving to next step ({current_step + 2}/{total_steps})")
        return {
            "phase": AgentPhase.ACTING.value,
            "current_step_index": current_step + 1,
            "should_end": False,
        }

    # All done - generate final answer
    logger.info("✅ Task completed, generating final answer...")

    # First, check if we have successful tool results - if so, build answer from them
    all_tool_results = state.get("tool_results", [])
    successful_tools = [r for r in all_tool_results if isinstance(r, dict) and r.get("success")]
    
    if successful_tools:
        # We have actual successful tool results - build answer directly
        final = "✅ تم تنفيذ المهمة بنجاح!\n\n"
        links = []
        tool_summaries = []
        
        for result in successful_tools:
            output = result.get("output", "")
            tool_name = result.get("tool_name", "")
            
            # Try to parse JSON output from the adapter
            try:
                import json as _json_mod
                parsed = _json_mod.loads(output) if isinstance(output, str) and output.startswith("{") else None
                if parsed:
                    if "url" in parsed:
                        links.append(f"[📁 تحميل الملف]({parsed['url']})")
                    if "text" in parsed:
                        tool_summaries.append(f"- **{tool_name}**: {parsed['text'][:300]}")
                else:
                    tool_summaries.append(f"- **{tool_name}**: {str(output)[:300]}")
            except:
                tool_summaries.append(f"- **{tool_name}**: {str(output)[:300]}")
        
        if links:
            final += "### 📎 الملفات والروابط:\n" + "\n".join(links) + "\n\n"
        if tool_summaries:
            final += "### 📋 النتائج:\n" + "\n".join(tool_summaries[:10])
        
        return {
            "phase": AgentPhase.COMPLETED.value,
            "final_answer": final,
            "should_end": True,
        }

    # No successful tool results — ask LLM to summarize

    prompt = REFLECTION_PROMPT.format(
        original_request=state["original_request"],
        plan=state.get("plan_steps", []),
        results="\n".join(results_summary) if results_summary else "No results",
        errors=errors if errors else "No errors",
    )

    try:
        response = await llm.ainvoke(
            [SystemMessage(content=NOVA_PERSONA), HumanMessage(content=prompt)]
        )

        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        reflection = json.loads(content.strip())

        return {
            "phase": AgentPhase.COMPLETED.value,
            "final_answer": reflection.get("final_answer", "تم تنفيذ المهمة!"),
            "should_end": True,
            "messages": [AIMessage(content=reflection.get("final_answer", "تم!"))],
        }

    except Exception as e:
        logger.warning(f"⚠️ Reflection parse error: {e}")
        # Fallback final answer with tool results
        final = "✅ تم تنفيذ المهمة!\n\n"

        # Extract links and files from tool results
        links = []
        tool_outputs = []

        for result in state.get("tool_results", []):
            # Handle both dict and ToolResult objects
            if hasattr(result, "__dict__"):
                # It's a ToolResult object
                if result.success:
                    output = result.output
                    tool_name = getattr(result, "tool_name", "unknown")

                    # Try to parse output if it's a string
                    if isinstance(output, str):
                        # Check if it contains URL patterns
                        if "/uploads/" in output:
                            import re
                            urls = re.findall(r"/uploads/[^\s\n\"']+", output)
                            for url in urls:
                                links.append(f"[📁 تحميل الملف]({url})")
                        # Check for external URLs
                        if "http" in output:
                            import re
                            ext_urls = re.findall(r"https?://[^\s\n\"']+", output)
                            for url in ext_urls:
                                if "localhost" not in url:
                                    links.append(f"[🔗 رابط]({url})")
                        tool_outputs.append(f"- **{tool_name}**: {output[:200]}")
                    elif isinstance(output, dict):
                        if "url" in output:
                            url = output["url"]
                            links.append(f"[📁 تحميل الملف]({url})")
                        if "filepath" in output:
                            links.append(f"📁 `{output['filepath']}`")
                        if "image_url" in output:
                            links.append(f"![صورة]({output['image_url']})")
                        if "output" in output:
                            tool_outputs.append(
                                f"- **{tool_name}**: {str(output['output'])[:200]}"
                            )
            elif isinstance(result, dict):
                # It's already a dict
                if result.get("success"):
                    output = result.get("output", {})
                    if isinstance(output, dict):
                        if "url" in output:
                            links.append(f"[📁 تحميل الملف]({output['url']})")
                        if "filepath" in output:
                            links.append(f"📁 `{output['filepath']}`")
                        if "image_url" in output:
                            links.append(f"![صورة]({output['image_url']})")

        if links:
            final += "### 📎 الملفات والروابط:\n" + "\n".join(links) + "\n\n"

        if tool_outputs:
            final += "### 📋 ملخص العمليات:\n" + "\n".join(tool_outputs[:5]) + "\n\n"

        if not links and not tool_outputs and results_summary:
            final += "### 📋 النتائج:\n" + "\n".join(results_summary[:5])

        # Ensure we always have some content
        if final == "✅ تم تنفيذ المهمة!\n\n":
            final += "تم إكمال جميع الخطوات بنجاح! ✨"

        logger.info(f"Final answer: {final[:200]}...")

        return {
            "phase": AgentPhase.COMPLETED.value,
            "final_answer": final,
            "should_end": True,
        }


# ═══════════════════════════════════════════════════════════════
# 🔀 CONDITIONAL EDGES
# ═══════════════════════════════════════════════════════════════


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """
    Decide whether to continue the loop or end.
    """
    if state.get("should_end", False):
        return "end"

    if state.get("phase") == AgentPhase.COMPLETED.value:
        return "end"

    if state.get("phase") == AgentPhase.FAILED.value:
        return "end"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    if retry_count >= max_retries:
        return "end"

    return "continue"


def route_after_think(state: AgentState) -> Literal["act", "end"]:
    """Route after thinking - go to action or end if simple response"""
    if state.get("task_complexity") == "simple" and not state.get("plan_steps"):
        return "end"
    return "act"
