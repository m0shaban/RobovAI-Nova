"""
⚡ Nova Agent - Parallel Tool Executor
======================================

نظام تنفيذ متوازي للأدوات:
- تنفيذ أدوات متعددة في وقت واحد
- إدارة الـ dependencies بين الأدوات
- Caching ذكي للنتائج
- Error recovery تلقائي
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class ToolTask:
    """مهمة أداة واحدة"""
    id: str
    tool_name: str
    input_data: str
    user_id: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 2
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass 
class ExecutionBatch:
    """مجموعة مهام للتنفيذ المتوازي"""
    batch_id: str
    tasks: List[ToolTask]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"


class ResultCache:
    """
    📦 Cache للنتائج
    
    يحفظ نتائج الأدوات لتجنب التكرار
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, Dict] = {}
        self._access_times: Dict[str, datetime] = {}
    
    def _make_key(self, tool_name: str, input_data: str) -> str:
        """إنشاء مفتاح فريد"""
        content = f"{tool_name}:{input_data}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def get(self, tool_name: str, input_data: str) -> Optional[Any]:
        """الحصول على نتيجة من الـ cache"""
        key = self._make_key(tool_name, input_data)
        
        if key in self._cache:
            # فحص الصلاحية
            access_time = self._access_times.get(key)
            if access_time and datetime.now() - access_time < self.ttl:
                logger.debug(f"📦 Cache hit for {tool_name}")
                return self._cache[key]
            else:
                # منتهي الصلاحية
                del self._cache[key]
                del self._access_times[key]
        
        return None
    
    def set(self, tool_name: str, input_data: str, result: Any):
        """حفظ نتيجة في الـ cache"""
        # تنظيف إذا امتلأ
        if len(self._cache) >= self.max_size:
            self._cleanup()
        
        key = self._make_key(tool_name, input_data)
        self._cache[key] = result
        self._access_times[key] = datetime.now()
        logger.debug(f"📦 Cached result for {tool_name}")
    
    def _cleanup(self):
        """تنظيف النتائج القديمة"""
        now = datetime.now()
        old_keys = [
            k for k, t in self._access_times.items()
            if now - t > self.ttl
        ]
        for key in old_keys:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
        
        # إذا لسه ممتلئ، احذف الأقدم
        if len(self._cache) >= self.max_size:
            sorted_keys = sorted(
                self._access_times.keys(),
                key=lambda k: self._access_times[k]
            )
            for key in sorted_keys[:len(self._cache) - self.max_size + 10]:
                self._cache.pop(key, None)
                self._access_times.pop(key, None)
    
    def clear(self):
        """مسح الـ cache"""
        self._cache.clear()
        self._access_times.clear()


class ParallelExecutor:
    """
    ⚡ المنفذ المتوازي للأدوات
    
    ينفذ أدوات متعددة في وقت واحد مع:
    - إدارة الـ dependencies
    - Caching
    - Error recovery
    - Rate limiting
    """
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.cache = ResultCache()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._running_tasks: Dict[str, ToolTask] = {}
        self._results: Dict[str, Any] = {}
    
    async def execute_tool(self, task: ToolTask) -> Dict[str, Any]:
        """تنفيذ أداة واحدة"""
        async with self.semaphore:
            task.status = "running"
            task.started_at = datetime.now().isoformat()
            
            # فحص الـ cache أولاً
            cached = self.cache.get(task.tool_name, task.input_data)
            if cached is not None:
                task.status = "completed"
                task.result = cached
                task.completed_at = datetime.now().isoformat()
                return {"success": True, "cached": True, "result": cached}
            
            try:
                # تنفيذ الأداة
                from backend.tools.registry import ToolRegistry
                
                tool_cls = ToolRegistry.get_tool(task.tool_name)
                if not tool_cls:
                    raise ValueError(f"Tool '{task.tool_name}' not found")
                
                tool = tool_cls()
                
                # تنفيذ مع timeout
                result = await asyncio.wait_for(
                    tool.execute(task.input_data, task.user_id),
                    timeout=task.timeout
                )
                
                task.status = "completed"
                task.result = result
                task.completed_at = datetime.now().isoformat()
                
                # حفظ في الـ cache إذا نجح
                if result.get("success", False):
                    self.cache.set(task.tool_name, task.input_data, result)
                
                return {"success": True, "result": result}
                
            except asyncio.TimeoutError:
                task.status = "failed"
                task.error = f"Timeout after {task.timeout}s"
                return {"success": False, "error": task.error}
                
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                
                # إعادة المحاولة
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = "pending"
                    logger.warning(f"🔄 Retrying {task.tool_name} ({task.retry_count}/{task.max_retries})")
                    return await self.execute_tool(task)
                
                return {"success": False, "error": str(e)}
    
    async def execute_batch(self, batch: ExecutionBatch) -> List[Dict[str, Any]]:
        """تنفيذ مجموعة مهام بالتوازي"""
        batch.status = "running"
        logger.info(f"⚡ Executing batch {batch.batch_id} with {len(batch.tasks)} tasks")
        
        # تقسيم حسب الـ dependencies
        independent = [t for t in batch.tasks if not t.dependencies]
        dependent = [t for t in batch.tasks if t.dependencies]
        
        results = []
        
        # تنفيذ المستقلة بالتوازي
        if independent:
            independent_results = await asyncio.gather(
                *[self.execute_tool(t) for t in independent],
                return_exceptions=True
            )
            
            for task, result in zip(independent, independent_results):
                if isinstance(result, Exception):
                    results.append({"success": False, "error": str(result), "task_id": task.id})
                else:
                    results.append({**result, "task_id": task.id})
                    self._results[task.id] = result
        
        # تنفيذ المعتمدة بالتسلسل
        for task in dependent:
            # التحقق من اكتمال الـ dependencies
            deps_ready = all(
                self._results.get(dep_id, {}).get("success", False)
                for dep_id in task.dependencies
            )
            
            if deps_ready:
                result = await self.execute_tool(task)
                results.append({**result, "task_id": task.id})
                self._results[task.id] = result
            else:
                results.append({
                    "success": False,
                    "error": "Dependencies not met",
                    "task_id": task.id
                })
        
        batch.status = "completed"
        logger.info(f"✅ Batch {batch.batch_id} completed")
        
        return results
    
    async def execute_parallel(self, tool_calls: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """
        تنفيذ قائمة tool calls بالتوازي
        
        Args:
            tool_calls: قائمة الأدوات المطلوب تنفيذها
            user_id: معرف المستخدم
        
        Returns:
            قائمة النتائج
        """
        # إنشاء المهام
        tasks = []
        for i, tc in enumerate(tool_calls):
            task = ToolTask(
                id=f"task_{i}",
                tool_name=tc.get("tool_name") or tc.get("name"),
                input_data=tc.get("input") or tc.get("arguments", {}),
                user_id=user_id,
                dependencies=tc.get("dependencies", []),
                priority=tc.get("priority", 1)
            )
            tasks.append(task)
        
        # ترتيب حسب الأولوية
        tasks.sort(key=lambda t: t.priority, reverse=True)
        
        # إنشاء batch وتنفيذ
        batch = ExecutionBatch(
            batch_id=f"batch_{datetime.now().strftime('%H%M%S')}",
            tasks=tasks
        )
        
        return await self.execute_batch(batch)
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التنفيذ"""
        return {
            "cache_size": len(self.cache._cache),
            "running_tasks": len(self._running_tasks),
            "max_concurrent": self.max_concurrent,
            "total_results": len(self._results)
        }


# ============= Integration Functions =============

_executor: Optional[ParallelExecutor] = None

def get_parallel_executor() -> ParallelExecutor:
    """الحصول على instance من ParallelExecutor"""
    global _executor
    if _executor is None:
        _executor = ParallelExecutor()
    return _executor


async def execute_tools_parallel(
    tool_calls: List[Dict[str, Any]],
    user_id: str = "system"
) -> List[Dict[str, Any]]:
    """
    تنفيذ أدوات بالتوازي (helper function)
    
    Usage:
        results = await execute_tools_parallel([
            {"tool_name": "web_search", "input": "AI news"},
            {"tool_name": "weather", "input": "Cairo"}
        ], user_id="user123")
    """
    executor = get_parallel_executor()
    return await executor.execute_parallel(tool_calls, user_id)


async def execute_with_retry(
    tool_name: str,
    input_data: str,
    user_id: str = "system",
    max_retries: int = 2,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    تنفيذ أداة مع إعادة المحاولة
    
    Usage:
        result = await execute_with_retry(
            "presentation",
            "اعمل برزنتيشن عن مصر",
            max_retries=3
        )
    """
    task = ToolTask(
        id="single_task",
        tool_name=tool_name,
        input_data=input_data,
        user_id=user_id,
        max_retries=max_retries,
        timeout=timeout
    )
    
    executor = get_parallel_executor()
    return await executor.execute_tool(task)
