from typing import List, Dict, Any, Optional
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
from datetime import datetime
import os
import logging
import json
from jinja2 import Template
import csv
from rdflib import Graph, Namespace, RDF, BNode, Literal
from performance_monitor import PerformanceMonitor
from cache_manager import GraphCacheManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphVisualizationError(Exception):
    """知识图谱可视化错误基类"""
    pass

class FileOperationError(GraphVisualizationError):
    """文件操作错误"""
    pass

class GraphVisualizer:
    """知识图谱可视化器"""
    
    def __init__(self, enable_temporal=False, enable_probabilistic=False):
        logger.info("初始化知识图谱可视化器")
        logger.info(f"时序支持: {enable_temporal}, 概率支持: {enable_probabilistic}")
        
        self.enable_temporal = enable_temporal
        self.enable_probabilistic = enable_probabilistic
        
        self.color_scheme = {
            # 实体类型颜色
            'Person': '#FF6B6B',
            'Organization': '#4ECDC4',
            'Location': '#45B7D1',
            'Event': '#96CEB4',
            'Concept': '#FFEEAD',
            'Technology': '#4A90E2',
            'Product': '#D4A5A5',
            'Disease': '#FF9999',
            'Symptom': '#FFB366',
            'Drug': '#99FF99',
            'Legal': '#9999FF',
            'Financial': '#FFB366',
            'Default': '#CCCCCC'
        }
        
        self.edge_styles = {
            # 基础关系样式
            'is_a': {'color': '#2C3E50', 'width': 2},
            'part_of': {'color': '#34495E', 'width': 2, 'dashes': True},
            'is_part_of': {'color': '#34495E', 'width': 2, 'dashes': True},
            
            # 技术关系样式
            'uses': {'color': '#3498DB', 'width': 2},
            'depends_on': {'color': '#2980B9', 'width': 2, 'dashes': True},
            'implements': {'color': '#1ABC9C', 'width': 2},
            'is_type_of': {'color': '#2C3E50', 'width': 2},
            'revolutionized': {'color': '#E74C3C', 'width': 3},
            'based_on': {'color': '#3498DB', 'width': 2},
            'competes_with': {'color': '#E67E22', 'width': 2, 'dashes': True},
            
            # 业务关系样式
            'reports_to': {'color': '#E74C3C', 'width': 2, 'arrows': 'to'},
            'manages': {'color': '#C0392B', 'width': 2, 'arrows': 'to'},
            'collaborates_with': {'color': '#E67E22', 'width': 2},
            
            # 医疗关系样式
            'causes': {'color': '#8E44AD', 'width': 2, 'arrows': 'to'},
            'treats': {'color': '#9B59B6', 'width': 2, 'arrows': 'to'},
            'indicates': {'color': '#7D3C98', 'width': 2, 'dashes': True},
            
            # 时序关系样式
            'happens_before': {'color': '#D35400', 'width': 2, 'arrows': 'to'},
            'happens_after': {'color': '#E67E22', 'width': 2, 'arrows': 'to'},
            'happens_during': {'color': '#F39C12', 'width': 2},
            
            # 概率关系样式
            'probably_causes': {'color': '#8E44AD', 'width': 2, 'arrows': 'to', 'dashes': True},
            'likely_related': {'color': '#9B59B6', 'width': 1, 'dashes': True},
            
            # 默认样式
            'default': {'color': '#BDC3C7', 'width': 1}
        }
        
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = GraphCacheManager()
    
    def visualize_interactive(self, relations: List[Any], output_file: str,
                            height: str = "750px", width: str = "100%",
                            bgcolor: str = "#ffffff", font_color: str = "black", use_cache: bool = True) -> None:
        """创建交互式知识图谱可视化"""
        start_time = self.performance_monitor.start_operation("interactive_visualization")
        
        # 生成缓存键
        cache_key = self.cache_manager._generate_key(relations, "interactive_viz")
        
        # 检查缓存
        if use_cache:
            cached_html = self.cache_manager.get_visualization(cache_key)
            if cached_html:
                logger.info("使用缓存的可视化结果")
                return cached_html
        
        try:
            logger.info(f"开始创建交互式可视化: {output_file}")
            
            # 验证输出路径
            output_dir = os.path.dirname(output_file)
            if output_dir:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    logger.info(f"创建输出目录: {output_dir}")
                except OSError as e:
                    error_msg = f"创建输出目录失败: {str(e)}"
                    logger.error(error_msg)
                    raise FileOperationError(error_msg)
            
            # 验证关系列表
            if not relations:
                error_msg = "关系列表为空"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 创建网络对象
            net = Network(notebook=False, height=height, width=width, bgcolor=bgcolor, font_color=font_color)
            net.force_atlas_2based()
            
            # 收集所有实体
            entities = {}
            for relation in relations:
                try:
                    # 添加源实体
                    if relation.source.id not in entities:
                        entities[relation.source.id] = relation.source
                        color = self.color_scheme.get(relation.source.type, self.color_scheme['Default'])
                        node_info = self._format_entity_info(relation.source)
                        
                        if self.enable_temporal and 'temporal' in relation.source.properties:
                            node_info += f"\n时间: {relation.source.properties['temporal']}"
                        
                        net.add_node(
                            relation.source.id,
                            label=relation.source.name,
                            title=node_info,
                            color=color
                        )
                        logger.debug(f"添加节点: {relation.source.name} ({relation.source.type})")
                    
                    # 添加目标实体
                    if relation.target.id not in entities:
                        entities[relation.target.id] = relation.target
                        color = self.color_scheme.get(relation.target.type, self.color_scheme['Default'])
                        node_info = self._format_entity_info(relation.target)
                        
                        if self.enable_temporal and 'temporal' in relation.target.properties:
                            node_info += f"\n时间: {relation.target.properties['temporal']}"
                        
                        net.add_node(
                            relation.target.id,
                            label=relation.target.name,
                            title=node_info,
                            color=color
                        )
                        logger.debug(f"添加节点: {relation.target.name} ({relation.target.type})")
                    
                    # 添加边
                    style = self.edge_styles.get(relation.relation_type, self.edge_styles['default'])
                    
                    # 根据置信度调整边的样式
                    if self.enable_probabilistic:
                        confidence = relation.confidence
                        style = style.copy()  # 创建副本以避免修改原始样式
                        style['width'] = max(1, style.get('width', 1) * confidence)
                        if confidence < 0.5:
                            style['dashes'] = True
                    
                    title = self._format_relation_info(relation)
                    
                    net.add_edge(
                        relation.source.id,
                        relation.target.id,
                        title=title,
                        **style
                    )
                    logger.debug(f"添加边: {relation.source.name} --{relation.relation_type}--> {relation.target.name}")
                
                except AttributeError as e:
                    error_msg = f"关系对象格式错误: {str(e)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            # 保存可视化结果
            try:
                net.save_graph(output_file)
                logger.info(f"可视化结果已保存到: {output_file}")
            except Exception as e:
                error_msg = f"保存可视化结果失败: {str(e)}"
                logger.error(error_msg)
                raise FileOperationError(error_msg)
        
        except Exception as e:
            logger.error(f"可视化过程中发生错误: {str(e)}")
            raise
        
        finally:
            self.performance_monitor.end_operation(
                start_time=start_time,
                node_count=len(entities),
                edge_count=len(relations),
                operation_type="interactive_visualization"
            )
            self._check_performance()
            
            # 缓存结果
            if use_cache:
                with open(output_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                self.cache_manager.cache_visualization(cache_key, html_content)
    
    def _format_entity_info(self, entity: Any) -> str:
        """格式化实体信息"""
        info = [
            f"ID: {entity.id}",
            f"名称: {entity.name}",
            f"类型: {entity.type}"
        ]
        
        # 添加属性信息
        if entity.properties:
            for key, value in entity.properties.items():
                info.append(f"{key}: {value}")
        
        return "\n".join(info)
    
    def _format_relation_info(self, relation: Any) -> str:
        """格式化关系信息"""
        info = [
            f"类型: {relation.relation_type}",
            f"置信度: {relation.confidence:.2f}"
        ]
        
        # 添加属性信息
        if relation.properties:
            for key, value in relation.properties.items():
                info.append(f"{key}: {value}")
        
        return "\n".join(info)
    
    def _check_performance(self):
        """检查性能并记录建议"""
        summary = self.performance_monitor.get_performance_summary()
        suggestions = self.performance_monitor.get_optimization_suggestions()
        
        if suggestions:
            logger.info("性能优化建议:")
            for suggestion in suggestions:
                logger.info(f"- {suggestion}")
        
        # 如果性能指标超过阈值，记录详细信息
        if summary.get("avg_cpu_percent", 0) > 70 or \
           summary.get("avg_memory_percent", 0) > 60 or \
           summary.get("avg_render_time", 0) > 3:
            logger.warning("性能指标摘要:")
            logger.warning(f"- 平均CPU使用率: {summary.get('avg_cpu_percent', 0):.2f}%")
            logger.warning(f"- 平均内存使用率: {summary.get('avg_memory_percent', 0):.2f}%")
            logger.warning(f"- 平均渲染时间: {summary.get('avg_render_time', 0):.2f}秒")
            logger.warning(f"- 最大渲染时间: {summary.get('max_render_time', 0):.2f}秒")
