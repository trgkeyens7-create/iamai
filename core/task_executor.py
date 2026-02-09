"""
多线程任务执行器模块
"""

from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Callable, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
import threading
import time
import os


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "等待中"
    RUNNING = "处理中"
    SUCCESS = "成功"
    FAILED = "失败"
    CANCELLED = "已取消"


@dataclass
class TaskItem:
    """任务项"""
    index: int
    title: str
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    error: str = ""


class TaskExecutor:
    """多线程任务执行器"""
    
    def __init__(self, max_workers: int = 3):
        """
        初始化任务执行器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers
        self.executor: Optional[ThreadPoolExecutor] = None
        self.tasks: List[TaskItem] = []
        self.futures: Dict[int, Future] = {}
        
        self._is_running = False
        self._is_paused = False
        self._should_cancel = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初始状态为非暂停
        
        # 回调函数
        self.on_task_start: Optional[Callable[[int, str], None]] = None
        self.on_task_complete: Optional[Callable[[int, str, bool, str], None]] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None
        self.on_all_complete: Optional[Callable[[], None]] = None
    
    def set_tasks(self, titles: List[str]):
        """
        设置任务列表
        
        Args:
            titles: 标题列表
        """
        self.tasks = [
            TaskItem(index=i, title=title)
            for i, title in enumerate(titles)
        ]
    
    def start(
        self, 
        process_func: Callable[[str], tuple[bool, str]],
        output_dir: str
    ):
        """
        开始执行任务
        
        Args:
            process_func: 处理函数，接收标题，返回 (是否成功, 内容或错误)
            output_dir: 输出目录
        """
        if self._is_running:
            return
        
        self._is_running = True
        self._should_cancel = False
        self._pause_event.set()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 在后台线程中执行任务
        threading.Thread(
            target=self._execute_tasks,
            args=(process_func, output_dir),
            daemon=True
        ).start()
    
    def _execute_tasks(self, process_func: Callable, output_dir: str):
        """执行所有任务"""
        completed_count = 0
        total_count = len(self.tasks)
        
        for task in self.tasks:
            # 检查是否应该取消
            if self._should_cancel:
                task.status = TaskStatus.CANCELLED
                continue
            
            # 等待暂停恢复
            self._pause_event.wait()
            
            if self._should_cancel:
                task.status = TaskStatus.CANCELLED
                continue
            
            # 更新任务状态为运行中
            task.status = TaskStatus.RUNNING
            if self.on_task_start:
                self.on_task_start(task.index, task.title)
            
            try:
                # 执行任务
                success, result = process_func(task.title)
                
                if success:
                    task.status = TaskStatus.SUCCESS
                    task.result = result
                    
                    # 保存结果到文件
                    safe_title = self._safe_filename(task.title)
                    output_path = os.path.join(output_dir, f"{task.index + 1:03d}_{safe_title}.txt")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(f"标题：{task.title}\n\n")
                        f.write(result)
                else:
                    task.status = TaskStatus.FAILED
                    task.error = result
                    
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
            
            completed_count += 1
            
            # 回调
            if self.on_task_complete:
                self.on_task_complete(
                    task.index, 
                    task.title, 
                    task.status == TaskStatus.SUCCESS,
                    task.result if task.status == TaskStatus.SUCCESS else task.error
                )
            
            if self.on_progress:
                self.on_progress(completed_count, total_count)
        
        self._is_running = False
        
        if self.on_all_complete:
            self.on_all_complete()
    
    def _safe_filename(self, title: str, max_length: int = 50) -> str:
        """将标题转换为安全的文件名"""
        # 移除或替换不安全的字符
        unsafe_chars = '<>:"/\\|?*'
        safe_title = title
        for char in unsafe_chars:
            safe_title = safe_title.replace(char, '_')
        
        # 限制长度
        if len(safe_title) > max_length:
            safe_title = safe_title[:max_length]
        
        return safe_title.strip()
    
    def pause(self):
        """暂停执行"""
        if self._is_running and not self._is_paused:
            self._is_paused = True
            self._pause_event.clear()
    
    def resume(self):
        """恢复执行"""
        if self._is_running and self._is_paused:
            self._is_paused = False
            self._pause_event.set()
    
    def cancel(self):
        """取消执行"""
        self._should_cancel = True
        self._pause_event.set()  # 确保不会卡在暂停状态
        
        if self.executor:
            self.executor.shutdown(wait=False)
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        """是否暂停"""
        return self._is_paused
    
    def get_statistics(self) -> Dict[str, int]:
        """获取任务统计"""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                stats["pending"] += 1
            elif task.status == TaskStatus.RUNNING:
                stats["running"] += 1
            elif task.status == TaskStatus.SUCCESS:
                stats["success"] += 1
            elif task.status == TaskStatus.FAILED:
                stats["failed"] += 1
            elif task.status == TaskStatus.CANCELLED:
                stats["cancelled"] += 1
        
        return stats
