from typing import Dict, Any, Optional
import time
import psutil
import threading
from dataclasses import dataclass
import json
import logging
from datetime import datetime
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_io: Dict[str, float]
    processing_time: float
    batch_size: int
    throughput: float  # 每秒处理的项目数
    success_rate: float
    cache_hit_rate: float
    error_rate: float

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, metrics_dir: str = "metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics: Dict[str, list] = {
            'cpu': [],
            'memory': [],
            'disk_io': [],
            'processing_time': [],
            'throughput': [],
            'success_rate': [],
            'cache_hit_rate': [],
            'error_rate': []
        }
        
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread = None
    
    def start_monitoring(self, interval: float = 1.0):
        """开始监控"""
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,)
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
    
    def record_metrics(self, metrics: PerformanceMetrics):
        """记录性能指标"""
        with self._lock:
            self.metrics['cpu'].append(metrics.cpu_percent)
            self.metrics['memory'].append(metrics.memory_percent)
            self.metrics['disk_io'].append(sum(metrics.disk_io.values()))
            self.metrics['processing_time'].append(metrics.processing_time)
            self.metrics['throughput'].append(metrics.throughput)
            self.metrics['success_rate'].append(metrics.success_rate)
            self.metrics['cache_hit_rate'].append(metrics.cache_hit_rate)
            self.metrics['error_rate'].append(metrics.error_rate)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前性能指标"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_io_counters()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_io={
                'read_bytes': disk.read_bytes,
                'write_bytes': disk.write_bytes
            },
            processing_time=time.time() - self._start_time,
            batch_size=0,  # 需要外部设置
            throughput=0,  # 需要外部计算
            success_rate=0,
            cache_hit_rate=0,
            error_rate=0
        )
    
    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self._monitoring:
            try:
                metrics = self.get_current_metrics()
                self.record_metrics(metrics)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"监控错误: {e}")
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - self._start_time,
            'summary': {
                metric: {
                    'mean': np.mean(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'std': np.std(values)
                }
                for metric, values in self.metrics.items()
            }
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report
    
    def plot_metrics(self, output_dir: Optional[str] = None):
        """绘制性能指标图表"""
        output_dir = Path(output_dir) if output_dir else self.metrics_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置样式
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
        
        for metric, values in self.metrics.items():
            plt.figure()
            sns.lineplot(data=values)
            plt.title(f'{metric.replace("_", " ").title()} Over Time')
            plt.xlabel('Time (samples)')
            plt.ylabel(metric)
            
            output_file = output_dir / f'{metric}_plot.png'
            plt.savefig(output_file)
            plt.close()
    
    def save_metrics(self):
        """保存指标数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics_file = self.metrics_dir / f'metrics_{timestamp}.json'
        
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 75.0,
            'error_rate': 0.05
        }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析性能数据并提供优化建议"""
        report = self.monitor.generate_report()
        recommendations = []
        
        # CPU 使用率分析
        cpu_stats = report['summary']['cpu']
        if cpu_stats['mean'] > self.thresholds['cpu_percent']:
            recommendations.append({
                'component': 'CPU',
                'issue': 'CPU使用率过高',
                'suggestion': '考虑增加工作进程数或减小批处理大小'
            })
        
        # 内存使用率分析
        memory_stats = report['summary']['memory']
        if memory_stats['mean'] > self.thresholds['memory_percent']:
            recommendations.append({
                'component': 'Memory',
                'issue': '内存使用率过高',
                'suggestion': '考虑减小批处理大小或增加数据分块'
            })
        
        # 错误率分析
        error_stats = report['summary']['error_rate']
        if error_stats['mean'] > self.thresholds['error_rate']:
            recommendations.append({
                'component': 'Error Handling',
                'issue': '错误率过高',
                'suggestion': '检查错误日志并优化错误处理机制'
            })
        
        # 缓存效率分析
        cache_stats = report['summary']['cache_hit_rate']
        if cache_stats['mean'] < 0.5:  # 缓存命中率低于50%
            recommendations.append({
                'component': 'Cache',
                'issue': '缓存命中率低',
                'suggestion': '考虑调整缓存大小或优化缓存策略'
            })
        
        return {
            'analysis_time': datetime.now().isoformat(),
            'metrics_summary': report['summary'],
            'recommendations': recommendations
        }
    
    def auto_optimize(self) -> Dict[str, Any]:
        """自动优化性能参数"""
        analysis = self.analyze_performance()
        optimizations = []
        
        for rec in analysis['recommendations']:
            if rec['component'] == 'CPU':
                # CPU优化逻辑
                optimizations.append({
                    'parameter': 'num_workers',
                    'action': 'increase',
                    'value': psutil.cpu_count()
                })
            
            elif rec['component'] == 'Memory':
                # 内存优化逻辑
                optimizations.append({
                    'parameter': 'batch_size',
                    'action': 'decrease',
                    'value': 'current_batch_size * 0.75'
                })
            
            elif rec['component'] == 'Cache':
                # 缓存优化逻辑
                optimizations.append({
                    'parameter': 'cache_size',
                    'action': 'increase',
                    'value': 'current_cache_size * 1.5'
                })
        
        return {
            'optimization_time': datetime.now().isoformat(),
            'analysis': analysis,
            'optimizations': optimizations
        }

@dataclass
class PerformanceMetricsNew:
    """性能指标数据类"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    node_count: int
    edge_count: int
    render_time: float
    query_time: Optional[float] = None
    operation_type: str = "default"

class PerformanceMonitorNew:
    """性能监控器"""
    
    def __init__(self, metrics_file: str = "metrics/performance_metrics.json"):
        self.metrics_file = metrics_file
        self.metrics: list = []
        self.lock = threading.Lock()
        self.process = psutil.Process()
        self._ensure_metrics_dir()
    
    def _ensure_metrics_dir(self):
        """确保指标文件目录存在"""
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
    
    def start_operation(self, operation_type: str = "default") -> float:
        """开始监控操作"""
        return time.time()
    
    def end_operation(self, start_time: float, node_count: int, edge_count: int, 
                     operation_type: str = "default", query_time: Optional[float] = None) -> PerformanceMetricsNew:
        """结束监控操作并记录指标"""
        with self.lock:
            end_time = time.time()
            metrics = PerformanceMetricsNew(
                timestamp=end_time,
                cpu_percent=self.process.cpu_percent(),
                memory_percent=self.process.memory_percent(),
                node_count=node_count,
                edge_count=edge_count,
                render_time=end_time - start_time,
                query_time=query_time,
                operation_type=operation_type
            )
            self.metrics.append(metrics)
            self._save_metrics()
            self._log_performance_alert(metrics)
            return metrics
    
    def _save_metrics(self):
        """保存性能指标到文件"""
        try:
            metrics_data = [
                {
                    "timestamp": m.timestamp,
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "node_count": m.node_count,
                    "edge_count": m.edge_count,
                    "render_time": m.render_time,
                    "query_time": m.query_time,
                    "operation_type": m.operation_type
                }
                for m in self.metrics
            ]
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            logger.error(f"保存性能指标失败: {str(e)}")
    
    def _log_performance_alert(self, metrics: PerformanceMetricsNew):
        """记录性能警告"""
        if metrics.cpu_percent > 80:
            logger.warning(f"CPU使用率过高: {metrics.cpu_percent}%")
        if metrics.memory_percent > 75:
            logger.warning(f"内存使用率过高: {metrics.memory_percent}%")
        if metrics.render_time > 5:
            logger.warning(f"渲染时间过长: {metrics.render_time}秒")
        if metrics.query_time and metrics.query_time > 2:
            logger.warning(f"查询时间过长: {metrics.query_time}秒")
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.metrics:
            return {}
        
        recent_metrics = self.metrics[-100:]  # 最近100条记录
        
        return {
            "avg_cpu_percent": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "avg_memory_percent": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            "avg_render_time": sum(m.render_time for m in recent_metrics) / len(recent_metrics),
            "max_render_time": max(m.render_time for m in recent_metrics),
            "total_operations": len(recent_metrics),
            "operation_types": {op: len([m for m in recent_metrics if m.operation_type == op])
                              for op in set(m.operation_type for m in recent_metrics)},
            "timestamp": datetime.now().isoformat()
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        if not self.metrics:
            return []
        
        suggestions = []
        recent_metrics = self.metrics[-100:]
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_render = sum(m.render_time for m in recent_metrics) / len(recent_metrics)
        
        if avg_cpu > 70:
            suggestions.append("考虑实现数据分片处理或增加缓存机制来减少CPU使用率")
        if avg_memory > 60:
            suggestions.append("建议优化内存使用，考虑实现数据流式处理或清理不必要的缓存")
        if avg_render > 3:
            suggestions.append("建议优化图形渲染性能，考虑使用数据抽样或简化视图")
        
        return suggestions

    def clear_old_metrics(self, days: int = 7):
        """清理旧的性能指标"""
        if not self.metrics:
            return
        
        current_time = time.time()
        self.metrics = [m for m in self.metrics 
                       if current_time - m.timestamp < days * 24 * 3600]
        self._save_metrics()
