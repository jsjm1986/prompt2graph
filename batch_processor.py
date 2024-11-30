from typing import List, Dict, Any, Optional, Callable
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import queue
import time
import logging
import json
import os
from functools import lru_cache
import numpy as np
from dataclasses import dataclass, asdict
import psutil
import weakref
from relation_extraction import Relation, Entity
from advanced_inference import AdvancedInferenceEngine
from performance_monitor import PerformanceMonitor, PerformanceOptimizer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    """批处理配置"""
    batch_size: int = 1000
    num_workers: int = mp.cpu_count()
    max_memory_percent: float = 75.0  # 最大内存使用百分比
    cache_size: int = 10000  # LRU缓存大小
    chunk_size: int = 100  # 数据分块大小
    prefetch_size: int = 5  # 预加载块数
    timeout: float = 30.0  # 处理超时时间（秒）

class MemoryManager:
    """内存管理器"""
    
    def __init__(self, max_memory_percent: float = 75.0):
        self.max_memory_percent = max_memory_percent
        self._memory_usage = {}
        self._lock = threading.Lock()
    
    def check_memory(self) -> bool:
        """检查内存使用情况"""
        memory = psutil.virtual_memory()
        return memory.percent < self.max_memory_percent
    
    def register_allocation(self, size: int, owner: str):
        """注册内存分配"""
        with self._lock:
            self._memory_usage[owner] = size
    
    def unregister_allocation(self, owner: str):
        """注销内存分配"""
        with self._lock:
            self._memory_usage.pop(owner, None)
    
    def get_total_allocated(self) -> int:
        """获取总分配内存"""
        with self._lock:
            return sum(self._memory_usage.values())
    
    def cleanup(self):
        """清理内存"""
        import gc
        gc.collect()

class Cache:
    """缓存管理器"""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self._cache = {}
        self._usage_count = {}
        self._lock = threading.Lock()
    
    @lru_cache(maxsize=1000)
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with self._lock:
            if key in self._cache:
                self._usage_count[key] += 1
                return self._cache[key]
            return None
    
    def put(self, key: str, value: Any):
        """添加缓存项"""
        with self._lock:
            if len(self._cache) >= self.capacity:
                # 移除最少使用的项
                min_key = min(self._usage_count.items(), key=lambda x: x[1])[0]
                del self._cache[min_key]
                del self._usage_count[min_key]
            
            self._cache[key] = value
            self._usage_count[key] = 1
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._usage_count.clear()

class DataChunk:
    """数据块"""
    
    def __init__(self, data: List[Any], chunk_id: int):
        self.data = data
        self.chunk_id = chunk_id
        self.processed = False
        self.result = None
        self.error = None

class ChunkProcessor:
    """数据块处理器"""
    
    def __init__(self, process_fn: Callable, chunk_size: int = 100):
        self.process_fn = process_fn
        self.chunk_size = chunk_size
        self.current_chunk = 0
    
    def create_chunks(self, data: List[Any]) -> List[DataChunk]:
        """创建数据块"""
        chunks = []
        for i in range(0, len(data), self.chunk_size):
            chunk_data = data[i:i + self.chunk_size]
            chunks.append(DataChunk(chunk_data, self.current_chunk))
            self.current_chunk += 1
        return chunks
    
    def process_chunk(self, chunk: DataChunk) -> DataChunk:
        """处理数据块"""
        try:
            chunk.result = self.process_fn(chunk.data)
            chunk.processed = True
        except Exception as e:
            chunk.error = str(e)
            logger.error(f"处理数据块 {chunk.chunk_id} 时出错: {e}")
        return chunk

class BatchProcessor:
    """批处理器"""
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.memory_manager = MemoryManager(self.config.max_memory_percent)
        self.cache = Cache(self.config.cache_size)
        self.inference_engine = AdvancedInferenceEngine()
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        self.performance_optimizer = PerformanceOptimizer(self.performance_monitor)
        
        # 启动监控
        self.performance_monitor.start_monitoring()
        
        # 创建处理池
        self.process_pool = ProcessPoolExecutor(max_workers=self.config.num_workers)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.num_workers * 2)
        
        # 创建数据队列
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self._stats_lock = threading.Lock()
        
        # 创建预加载线程
        self.prefetch_thread = threading.Thread(target=self._prefetch_worker)
        self.prefetch_thread.daemon = True
        self.prefetch_thread.start()
    
    def process_batch(self, data: List[Any], process_fn: Callable) -> List[Any]:
        """批量处理数据"""
        start_time = time.time()
        batch_size = len(data)
        
        try:
            if not data:
                return []
            
            # 检查内存
            if not self.memory_manager.check_memory():
                logger.warning("内存使用率过高，执行清理...")
                self.memory_manager.cleanup()
            
            # 创建数据块
            chunk_processor = ChunkProcessor(process_fn, self.config.chunk_size)
            chunks = chunk_processor.create_chunks(data)
            
            # 提交处理任务
            futures = []
            for chunk in chunks:
                # 检查缓存
                cache_key = self._get_cache_key(chunk)
                cached_result = self.cache.get(cache_key)
                
                with self._stats_lock:
                    if cached_result is not None:
                        self.stats['cache_hits'] += 1
                        chunk.result = cached_result
                        chunk.processed = True
                        continue
                    else:
                        self.stats['cache_misses'] += 1
                
                # 提交到进程池
                future = self.process_pool.submit(chunk_processor.process_chunk, chunk)
                futures.append((future, cache_key))
            
            # 收集结果
            results = []
            success_count = 0
            error_count = 0
            
            for future, cache_key in futures:
                try:
                    chunk = future.result(timeout=self.config.timeout)
                    if chunk.error:
                        logger.error(f"数据块 {chunk.chunk_id} 处理失败: {chunk.error}")
                        error_count += 1
                        continue
                    
                    # 缓存结果
                    if chunk.result is not None:
                        self.cache.put(cache_key, chunk.result)
                        results.extend(chunk.result)
                        success_count += 1
                
                except TimeoutError:
                    logger.error(f"数据块处理超时")
                    error_count += 1
                    continue
            
            # 更新统计信息
            with self._stats_lock:
                self.stats['total_processed'] += batch_size
                self.stats['success_count'] += success_count
                self.stats['error_count'] += error_count
            
            # 记录性能指标
            processing_time = time.time() - start_time
            throughput = batch_size / processing_time if processing_time > 0 else 0
            
            metrics = self.performance_monitor.get_current_metrics()
            metrics.batch_size = batch_size
            metrics.throughput = throughput
            metrics.success_rate = success_count / len(chunks) if chunks else 1.0
            metrics.error_rate = error_count / len(chunks) if chunks else 0.0
            metrics.cache_hit_rate = self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
            
            self.performance_monitor.record_metrics(metrics)
            
            # 检查是否需要优化
            if self.stats['total_processed'] % 1000 == 0:  # 每处理1000项检查一次
                optimization_result = self.performance_optimizer.analyze_performance()
                if optimization_result['recommendations']:
                    logger.info("性能优化建议：%s", optimization_result['recommendations'])
            
            return results
        
        except Exception as e:
            logger.error(f"批处理出错: {e}")
            return []
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'stats': self.stats,
            'performance_analysis': self.performance_optimizer.analyze_performance()
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """执行性能优化"""
        optimization_result = self.performance_optimizer.auto_optimize()
        
        # 应用优化建议
        for opt in optimization_result['optimizations']:
            if opt['parameter'] == 'num_workers':
                self.config.num_workers = opt['value']
                self.process_pool.shutdown()
                self.process_pool = ProcessPoolExecutor(max_workers=self.config.num_workers)
            
            elif opt['parameter'] == 'batch_size':
                self.config.batch_size = int(eval(opt['value'].replace('current_batch_size', str(self.config.batch_size))))
            
            elif opt['parameter'] == 'cache_size':
                new_cache_size = int(eval(opt['value'].replace('current_cache_size', str(self.config.cache_size))))
                self.cache = Cache(new_cache_size)
        
        return optimization_result
    
    def cleanup(self):
        """清理资源"""
        self.performance_monitor.stop_monitoring()
        self.performance_monitor.save_metrics()
        self.performance_monitor.plot_metrics()
        
        self.process_pool.shutdown()
        self.thread_pool.shutdown()
        self.cache.clear()
        self.memory_manager.cleanup()
    
    def _prefetch_worker(self):
        """预加载工作线程"""
        while True:
            try:
                # 检查输入队列
                if self.input_queue.qsize() < self.config.prefetch_size:
                    # 预加载数据
                    self._prefetch_data()
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"预加载出错: {e}")
    
    def _prefetch_data(self):
        """预加载数据"""
        try:
            # 这里实现具体的预加载逻辑
            pass
        except Exception as e:
            logger.error(f"预加载数据出错: {e}")
    
    def _get_cache_key(self, chunk: DataChunk) -> str:
        """生成缓存键"""
        # 使用数据的哈希作为缓存键
        data_str = json.dumps([str(item) for item in chunk.data])
        return f"chunk_{chunk.chunk_id}_{hash(data_str)}"

class AsyncBatchProcessor(BatchProcessor):
    """异步批处理器"""
    
    def __init__(self, config: BatchConfig = None):
        super().__init__(config)
        self.processing_queue = queue.Queue()
        self.result_callbacks = weakref.WeakValueDictionary()
        
        # 启动处理线程
        self.processing_thread = threading.Thread(target=self._process_worker)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def process_batch_async(self, data: List[Any], process_fn: Callable,
                          callback: Callable[[List[Any]], None] = None) -> int:
        """异步批处理"""
        batch_id = id(data)
        if callback:
            self.result_callbacks[batch_id] = callback
        
        self.processing_queue.put((batch_id, data, process_fn))
        return batch_id
    
    def _process_worker(self):
        """处理工作线程"""
        while True:
            try:
                batch_id, data, process_fn = self.processing_queue.get()
                results = self.process_batch(data, process_fn)
                
                # 调用回调函数
                callback = self.result_callbacks.get(batch_id)
                if callback:
                    self.thread_pool.submit(callback, results)
            
            except Exception as e:
                logger.error(f"异步处理出错: {e}")
            finally:
                self.processing_queue.task_done()

def create_batch_processor(async_mode: bool = False,
                         config: BatchConfig = None) -> BatchProcessor:
    """创建批处理器工厂函数"""
    if async_mode:
        return AsyncBatchProcessor(config)
    return BatchProcessor(config)
