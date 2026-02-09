"""
🧠 Nova Agent - Multi-Agent Orchestration System
=================================================

نظام متقدم يدير عدة agents متخصصة لتنفيذ المهام المعقدة.

Agents:
- ResearchAgent: للبحث والتحليل
- CreativeAgent: للمحتوى الإبداعي  
- ToolAgent: لتنفيذ الأدوات
- ReflectionAgent: للمراجعة والتحقق
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """أدوار الـ Agents المتخصصة"""
    RESEARCHER = "researcher"      # بحث وتحليل
    CREATIVE = "creative"          # محتوى إبداعي
    TOOL_EXECUTOR = "tool_executor" # تنفيذ الأدوات
    REFLECTOR = "reflector"        # مراجعة وتحقق
    PLANNER = "planner"            # تخطيط
    COORDINATOR = "coordinator"    # تنسيق


@dataclass
class AgentCapability:
    """قدرة معينة للـ Agent"""
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    priority: int = 1


@dataclass
class AgentTask:
    """مهمة لـ Agent"""
    id: str
    description: str
    role: AgentRole
    input_data: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """قاعدة للـ Agents المتخصصة"""
    
    def __init__(self, role: AgentRole, llm=None):
        self.role = role
        self.llm = llm
        self.capabilities: List[AgentCapability] = []
        self._setup_capabilities()
    
    @abstractmethod
    def _setup_capabilities(self):
        """تعريف قدرات الـ Agent"""
        pass
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """تنفيذ مهمة"""
        pass
    
    def can_handle(self, task_description: str) -> float:
        """تقييم قدرة الـ Agent على معالجة المهمة (0-1)"""
        score = 0.0
        task_lower = task_description.lower()
        
        for cap in self.capabilities:
            for keyword in cap.keywords:
                if keyword.lower() in task_lower:
                    score += 0.1 * cap.priority
        
        return min(score, 1.0)


class ResearchAgent(BaseAgent):
    """Agent للبحث والتحليل"""
    
    def __init__(self, llm=None):
        super().__init__(AgentRole.RESEARCHER, llm)
    
    def _setup_capabilities(self):
        self.capabilities = [
            AgentCapability(
                name="web_search",
                description="البحث في الإنترنت",
                keywords=["بحث", "search", "ابحث", "find", "معلومات", "information"],
                priority=3
            ),
            AgentCapability(
                name="analysis",
                description="تحليل البيانات",
                keywords=["تحليل", "analyze", "حلل", "study", "examine"],
                priority=2
            ),
            AgentCapability(
                name="summarize",
                description="تلخيص المحتوى",
                keywords=["تلخيص", "summary", "لخص", "اختصر"],
                priority=2
            )
        ]
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """تنفيذ مهمة بحث"""
        logger.info(f"🔍 ResearchAgent executing: {task.description[:50]}...")
        
        # هنا نستخدم أدوات البحث
        from backend.tools.registry import ToolRegistry
        
        results = {
            "success": True,
            "agent": self.role.value,
            "findings": [],
            "sources": []
        }
        
        # محاولة استخدام أدوات البحث
        search_tools = ["web_search", "google_search", "duckduckgo_search"]
        for tool_name in search_tools:
            try:
                tool_cls = ToolRegistry.get_tool(tool_name)
                if tool_cls:
                    tool = tool_cls()
                    result = await tool.execute(task.description, "system")
                    if result.get("success"):
                        results["findings"].append(result)
                        break
            except Exception as e:
                logger.warning(f"Search tool {tool_name} failed: {e}")
        
        return results


class CreativeAgent(BaseAgent):
    """Agent للمحتوى الإبداعي"""
    
    def __init__(self, llm=None):
        super().__init__(AgentRole.CREATIVE, llm)
    
    def _setup_capabilities(self):
        self.capabilities = [
            AgentCapability(
                name="content_creation",
                description="إنشاء محتوى",
                keywords=["اكتب", "write", "أنشئ", "create", "محتوى", "content"],
                priority=3
            ),
            AgentCapability(
                name="presentation",
                description="إنشاء عروض",
                keywords=["برزنتيشن", "presentation", "عرض", "slides"],
                priority=3
            ),
            AgentCapability(
                name="image_generation",
                description="توليد صور",
                keywords=["صورة", "image", "رسم", "draw", "تصميم", "design"],
                priority=2
            ),
            AgentCapability(
                name="audio_video",
                description="محتوى صوتي ومرئي",
                keywords=["صوت", "audio", "فيديو", "video", "موسيقى", "music"],
                priority=2
            )
        ]
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """تنفيذ مهمة إبداعية"""
        logger.info(f"🎨 CreativeAgent executing: {task.description[:50]}...")
        
        results = {
            "success": True,
            "agent": self.role.value,
            "output": None,
            "files": []
        }
        
        # تحديد نوع المحتوى المطلوب
        task_lower = task.description.lower()
        
        from backend.tools.registry import ToolRegistry
        
        if any(kw in task_lower for kw in ["برزنتيشن", "presentation", "عرض"]):
            tool_cls = ToolRegistry.get_tool("presentation")
            if tool_cls:
                tool = tool_cls()
                result = await tool.execute(task.description, "system")
                results["output"] = result
        
        elif any(kw in task_lower for kw in ["صورة", "image", "رسم"]):
            tool_cls = ToolRegistry.get_tool("generate_image")
            if tool_cls:
                tool = tool_cls()
                result = await tool.execute(task.description, "system")
                results["output"] = result
        
        return results


class ToolExecutorAgent(BaseAgent):
    """Agent لتنفيذ الأدوات"""
    
    def __init__(self, llm=None):
        super().__init__(AgentRole.TOOL_EXECUTOR, llm)
        self.available_tools = []
        self._load_available_tools()
    
    def _load_available_tools(self):
        """تحميل الأدوات المتاحة"""
        from backend.tools.registry import ToolRegistry
        self.available_tools = ToolRegistry.list_tools()
    
    def _setup_capabilities(self):
        self.capabilities = [
            AgentCapability(
                name="tool_execution",
                description="تنفيذ أي أداة",
                keywords=["استخدم", "use", "نفذ", "execute", "أداة", "tool"],
                priority=2
            ),
            AgentCapability(
                name="file_operations",
                description="عمليات الملفات",
                keywords=["ملف", "file", "حفظ", "save", "تحميل", "download"],
                priority=2
            ),
            AgentCapability(
                name="calculations",
                description="حسابات ومعادلات",
                keywords=["احسب", "calculate", "حساب", "math", "رياضيات"],
                priority=2
            )
        ]
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """تنفيذ أداة محددة"""
        logger.info(f"⚡ ToolExecutorAgent executing: {task.description[:50]}...")
        
        tool_name = task.input_data.get("tool_name")
        tool_input = task.input_data.get("tool_input", task.description)
        
        from backend.tools.registry import ToolRegistry
        
        try:
            tool_cls = ToolRegistry.get_tool(tool_name)
            if tool_cls:
                tool = tool_cls()
                result = await tool.execute(tool_input, "system")
                return {
                    "success": True,
                    "agent": self.role.value,
                    "tool": tool_name,
                    "result": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class ReflectionAgent(BaseAgent):
    """Agent للمراجعة والتحقق"""
    
    def __init__(self, llm=None):
        super().__init__(AgentRole.REFLECTOR, llm)
    
    def _setup_capabilities(self):
        self.capabilities = [
            AgentCapability(
                name="quality_check",
                description="فحص الجودة",
                keywords=["تحقق", "verify", "راجع", "review", "جودة", "quality"],
                priority=2
            ),
            AgentCapability(
                name="error_detection",
                description="اكتشاف الأخطاء",
                keywords=["خطأ", "error", "مشكلة", "problem", "صحح", "fix"],
                priority=2
            ),
            AgentCapability(
                name="improvement",
                description="اقتراح تحسينات",
                keywords=["حسن", "improve", "طور", "enhance", "أفضل", "better"],
                priority=1
            )
        ]
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """مراجعة نتائج المهام الأخرى"""
        logger.info(f"🔄 ReflectionAgent reviewing: {task.description[:50]}...")
        
        previous_results = task.input_data.get("previous_results", [])
        
        # تقييم النتائج
        evaluation = {
            "success": True,
            "agent": self.role.value,
            "quality_score": 0.0,
            "issues": [],
            "suggestions": [],
            "final_decision": "continue"
        }
        
        # حساب نسبة النجاح
        successful = sum(1 for r in previous_results if r.get("success", False))
        total = len(previous_results) or 1
        evaluation["quality_score"] = successful / total
        
        # قرار الاستمرار أو التوقف
        if evaluation["quality_score"] >= 0.7:
            evaluation["final_decision"] = "complete"
        elif evaluation["quality_score"] >= 0.4:
            evaluation["final_decision"] = "retry_partial"
        else:
            evaluation["final_decision"] = "restart"
        
        return evaluation


class AgentOrchestrator:
    """
    🎭 المنسق الرئيسي للـ Multi-Agent System
    
    يدير تنسيق العمل بين الـ Agents المختلفة:
    1. تحليل المهمة
    2. توزيع المهام على الـ Agents المناسبة
    3. تنسيق التنفيذ (تسلسلي/متوازي)
    4. تجميع النتائج
    5. مراجعة وتحقق
    """
    
    def __init__(self, llm=None):
        self.llm = llm
        self.agents: Dict[AgentRole, BaseAgent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """تهيئة جميع الـ Agents"""
        self.agents = {
            AgentRole.RESEARCHER: ResearchAgent(self.llm),
            AgentRole.CREATIVE: CreativeAgent(self.llm),
            AgentRole.TOOL_EXECUTOR: ToolExecutorAgent(self.llm),
            AgentRole.REFLECTOR: ReflectionAgent(self.llm),
        }
        logger.info(f"🎭 Orchestrator initialized with {len(self.agents)} agents")
    
    def select_agents(self, task_description: str) -> List[AgentRole]:
        """اختيار الـ Agents المناسبة للمهمة"""
        scores = {}
        
        for role, agent in self.agents.items():
            score = agent.can_handle(task_description)
            if score > 0.1:
                scores[role] = score
        
        # ترتيب حسب الأعلى score
        sorted_roles = sorted(scores.keys(), key=lambda r: scores[r], reverse=True)
        
        # إرجاع أعلى agents (حتى 3)
        selected = sorted_roles[:3]
        
        # دائماً نضيف Reflector في النهاية
        if AgentRole.REFLECTOR not in selected:
            selected.append(AgentRole.REFLECTOR)
        
        logger.info(f"📋 Selected agents: {[r.value for r in selected]}")
        return selected
    
    async def execute_parallel(self, tasks: List[AgentTask]) -> List[Dict[str, Any]]:
        """تنفيذ مهام متعددة بالتوازي"""
        async def run_task(task: AgentTask) -> Dict[str, Any]:
            agent = self.agents.get(task.role)
            if agent:
                try:
                    return await agent.execute(task)
                except Exception as e:
                    return {"success": False, "error": str(e)}
            return {"success": False, "error": "Agent not found"}
        
        results = await asyncio.gather(*[run_task(t) for t in tasks])
        return list(results)
    
    async def execute_sequential(self, tasks: List[AgentTask]) -> List[Dict[str, Any]]:
        """تنفيذ مهام بالتسلسل"""
        results = []
        previous_results = []
        
        for task in tasks:
            # تمرير نتائج المهام السابقة
            task.input_data["previous_results"] = previous_results
            
            agent = self.agents.get(task.role)
            if agent:
                try:
                    result = await agent.execute(task)
                    results.append(result)
                    previous_results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
        
        return results
    
    async def orchestrate(self, user_request: str, user_id: str = "system") -> Dict[str, Any]:
        """
        🎯 التنسيق الكامل لتنفيذ طلب المستخدم
        
        1. تحليل الطلب
        2. اختيار الـ Agents
        3. إنشاء المهام
        4. تنفيذ المهام
        5. مراجعة النتائج
        6. إرجاع الناتج النهائي
        """
        logger.info(f"🎭 Orchestrating request: {user_request[:50]}...")
        
        # 1. اختيار الـ Agents المناسبة
        selected_roles = self.select_agents(user_request)
        
        # 2. إنشاء المهام
        tasks = []
        for i, role in enumerate(selected_roles):
            task = AgentTask(
                id=f"task_{i}",
                description=user_request,
                role=role
            )
            tasks.append(task)
        
        # 3. تنفيذ المهام (متوازي للمستقلة، تسلسلي للمعتمدة)
        # نفذ كل شيء ما عدا Reflector بالتوازي
        parallel_tasks = [t for t in tasks if t.role != AgentRole.REFLECTOR]
        reflection_task = next((t for t in tasks if t.role == AgentRole.REFLECTOR), None)
        
        # تنفيذ متوازي
        parallel_results = await self.execute_parallel(parallel_tasks)
        
        # مراجعة النتائج
        all_results = parallel_results
        if reflection_task:
            reflection_task.input_data["previous_results"] = parallel_results
            reflection_result = await self.agents[AgentRole.REFLECTOR].execute(reflection_task)
            all_results.append(reflection_result)
        
        # 4. تجميع النتائج النهائية
        final_output = {
            "success": True,
            "request": user_request,
            "agents_used": [r.value for r in selected_roles],
            "results": all_results,
            "quality_score": reflection_result.get("quality_score", 0.8) if reflection_task else 0.8,
            "final_answer": self._generate_final_answer(all_results)
        }
        
        logger.info(f"✅ Orchestration complete. Quality: {final_output['quality_score']:.0%}")
        return final_output
    
    def _generate_final_answer(self, results: List[Dict[str, Any]]) -> str:
        """توليد الإجابة النهائية من نتائج الـ Agents"""
        parts = []
        
        for result in results:
            if result.get("success"):
                agent = result.get("agent", "unknown")
                
                if "output" in result:
                    output = result["output"]
                    if isinstance(output, dict):
                        if "output" in output:
                            parts.append(output["output"])
                        elif "result" in output:
                            parts.append(str(output["result"]))
                    else:
                        parts.append(str(output))
                
                elif "findings" in result and result["findings"]:
                    for finding in result["findings"]:
                        if isinstance(finding, dict) and "output" in finding:
                            parts.append(finding["output"])
                
                elif "result" in result:
                    parts.append(str(result["result"]))
        
        if not parts:
            return "✅ تم تنفيذ المهمة بنجاح!"
        
        return "\n\n".join(parts)


# ============= Integration with existing system =============

async def run_with_multi_agent(
    user_request: str,
    user_id: str = "system",
    llm=None
) -> Dict[str, Any]:
    """
    تشغيل طلب باستخدام نظام الـ Multi-Agent
    
    Args:
        user_request: طلب المستخدم
        user_id: معرف المستخدم
        llm: نموذج اللغة (اختياري)
    
    Returns:
        Dict مع النتائج
    """
    orchestrator = AgentOrchestrator(llm)
    return await orchestrator.orchestrate(user_request, user_id)


# للاستخدام في graph.py
def get_orchestrator(llm=None) -> AgentOrchestrator:
    """الحصول على instance من الـ Orchestrator"""
    return AgentOrchestrator(llm)
