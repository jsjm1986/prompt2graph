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

class VisualizationConfig:
    """可视化配置类"""
    
    def __init__(self):
        # 基础配置
        self.theme = {
            'light': {
                'background': '#ffffff',
                'node_color': '#3498db',
                'edge_color': '#95a5a6',
                'text_color': '#2c3e50',
                'highlight_color': '#e74c3c'
            },
            'dark': {
                'background': '#2c3e50',
                'node_color': '#3498db',
                'edge_color': '#7f8c8d',
                'text_color': '#ecf0f1',
                'highlight_color': '#e74c3c'
            }
        }
        
        # 节点样式
        self.node_styles = {
            'size': {
                'min': 10,
                'max': 50,
                'default': 20
            },
            'opacity': {
                'normal': 0.8,
                'highlight': 1.0,
                'dim': 0.3
            },
            'border': {
                'width': 2,
                'color': '#ffffff'
            },
            'label': {
                'font_family': 'Arial',
                'font_size': 12,
                'max_length': 20
            }
        }
        
        # 边样式
        self.edge_styles = {
            'width': {
                'min': 1,
                'max': 10,
                'default': 2
            },
            'opacity': {
                'normal': 0.6,
                'highlight': 0.9,
                'dim': 0.2
            },
            'arrow': {
                'size': 15,
                'enabled': True
            },
            'curve': {
                'style': 'curved',  # 'curved', 'straight', 'dynamic'
                'roundness': 0.5
            }
        }
        
        # 布局配置
        self.layout = {
            'force_directed': {
                'spring_length': 200,
                'spring_strength': 0.05,
                'damping': 0.09,
                'gravity': -1200
            },
            'hierarchical': {
                'direction': 'UD',  # 'UD', 'DU', 'LR', 'RL'
                'sort_method': 'directed',  # 'directed', 'hubsize'
                'level_separation': 150
            }
        }
        
        # 交互配置
        self.interaction = {
            'drag_nodes': True,
            'drag_view': True,
            'zoom': True,
            'hover': True,
            'select': True,
            'multi_select': True,
            'navigation_buttons': True
        }
        
        # 动画配置
        self.animation = {
            'enabled': True,
            'duration': 1000,
            'easing': 'easeInOutQuad'
        }
        
        # 图例配置
        self.legend = {
            'enabled': True,
            'position': 'bottom-right',
            'width': 200,
            'font_size': 12
        }
        
        # 工具提示配置
        self.tooltip = {
            'enabled': True,
            'delay': 300,
            'duration': 2000,
            'max_width': 200
        }
        
        # 聚类可视化配置
        self.clustering = {
            'min_size': 3,
            'color_scheme': 'rainbow',  # 'rainbow', 'spectral', 'paired'
            'opacity_by_size': True,
            'show_labels': True
        }
        
        # 时序可视化配置
        self.temporal = {
            'animation_speed': 1000,
            'show_timeline': True,
            'timeline_height': 100,
            'interpolation': 'linear'  # 'linear', 'step', 'basis'
        }
        
        # 层次可视化配置
        self.hierarchical = {
            'level_style': 'layered',  # 'layered', 'tree', 'radial'
            'node_spacing': 100,
            'level_separation': 150,
            'direction': 'TB'  # 'TB', 'BT', 'LR', 'RL'
        }
        
        # 性能配置
        self.performance = {
            'max_nodes_visible': 1000,
            'edge_limit': 2000,
            'label_threshold': 50,
            'dynamic_styling': True
        }

    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), dict):
                    getattr(self, key).update(value)
                else:
                    setattr(self, key, value)

    def get_theme(self, name='light'):
        """获取主题配置"""
        return self.theme.get(name, self.theme['light'])

    def get_node_style(self, node_type: str, is_highlighted: bool = False) -> dict:
        """获取节点样式"""
        base_style = {
            'size': self.node_styles['size']['default'],
            'color': self.theme['light']['node_color'],
            'border_width': self.node_styles['border']['width'],
            'border_color': self.node_styles['border']['color'],
            'opacity': self.node_styles['opacity']['normal']
        }
        
        if is_highlighted:
            base_style.update({
                'opacity': self.node_styles['opacity']['highlight'],
                'border_color': self.theme['light']['highlight_color']
            })
        
        return base_style

    def get_edge_style(self, edge_type: str, weight: float = 1.0) -> dict:
        """获取边样式"""
        base_style = {
            'width': min(
                self.edge_styles['width']['max'],
                max(
                    self.edge_styles['width']['min'],
                    self.edge_styles['width']['default'] * weight
                )
            ),
            'color': self.theme['light']['edge_color'],
            'opacity': self.edge_styles['opacity']['normal'],
            'arrows': {
                'to': {
                    'enabled': self.edge_styles['arrow']['enabled'],
                    'size': self.edge_styles['arrow']['size']
                }
            }
        }
        
        return base_style

class StyleManager:
    """样式管理器"""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.current_theme = 'light'
        
    def apply_theme(self, theme_name: str):
        """应用主题"""
        if theme_name in self.config.theme:
            self.current_theme = theme_name
            
    def get_node_color(self, node_type: str) -> str:
        """获取节点颜色"""
        return self.config.theme[self.current_theme]['node_color']
        
    def get_edge_color(self, edge_type: str) -> str:
        """获取边颜色"""
        return self.config.theme[self.current_theme]['edge_color']
        
    def get_text_color(self) -> str:
        """获取文本颜色"""
        return self.config.theme[self.current_theme]['text_color']
        
    def get_background_color(self) -> str:
        """获取背景颜色"""
        return self.config.theme[self.current_theme]['background_color']
        
    def create_gradient(self, start_color: str, end_color: str, steps: int) -> List[str]:
        """创建渐变色"""
        import colorsys
        
        # 转换为HSV颜色空间
        def hex_to_hsv(hex_color):
            # 移除#号并转换为RGB
            rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
            return colorsys.rgb_to_hsv(*rgb)
        
        def hsv_to_hex(hsv):
            rgb = colorsys.hsv_to_rgb(*hsv)
            return '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
        
        start_hsv = hex_to_hsv(start_color)
        end_hsv = hex_to_hsv(end_color)
        
        # 计算步长
        h_step = (end_hsv[0] - start_hsv[0]) / (steps - 1)
        s_step = (end_hsv[1] - start_hsv[1]) / (steps - 1)
        v_step = (end_hsv[2] - start_hsv[2]) / (steps - 1)
        
        # 生成渐变色
        gradient = []
        for i in range(steps):
            hsv = (
                start_hsv[0] + h_step * i,
                start_hsv[1] + s_step * i,
                start_hsv[2] + v_step * i
            )
            gradient.append(hsv_to_hex(hsv))
        
        return gradient

class GraphVisualizer:
    """知识图谱可视化器"""
    
    def __init__(self, enable_temporal=False, enable_probabilistic=False):
        logger.info("初始化知识图谱可视化器")
        logger.info(f"时序支持: {enable_temporal}, 概率支持: {enable_probabilistic}")
        
        self.enable_temporal = enable_temporal
        self.enable_probabilistic = enable_probabilistic
        
        # 使用新的配置类
        self.config = VisualizationConfig()
        self.style_manager = StyleManager(self.config)
        
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
                        color = self.style_manager.get_node_color(relation.source.type)
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
                        color = self.style_manager.get_node_color(relation.target.type)
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
                    style = self.style_manager.get_edge_style(relation.relation_type)
                    
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

    def visualize_clusters(self, relations: List[Any], output_file: str,
                         algorithm: str = 'louvain', min_size: int = 3) -> Dict[str, Any]:
        """可视化社区聚类结果
        
        Args:
            relations: 关系列表
            output_file: 输出文件路径
            algorithm: 聚类算法 ('louvain', 'label_prop', 'greedy_modularity')
            min_size: 最小社区大小
            
        Returns:
            Dict: 聚类统计信息
        """
        try:
            # 构建NetworkX图
            G = nx.Graph()
            for relation in relations:
                G.add_edge(relation.source.id, relation.target.id)
            
            # 执行社区检测
            if algorithm == 'louvain':
                import community
                communities = community.best_partition(G)
            elif algorithm == 'label_prop':
                communities = nx.community.label_propagation_communities(G)
            else:  # greedy_modularity
                communities = nx.community.greedy_modularity_communities(G)
            
            # 为每个社区分配颜色
            import colorsys
            n_communities = len(set(communities.values())) if isinstance(communities, dict) else len(communities)
            colors = [colorsys.hsv_to_rgb(i/n_communities, 0.7, 0.95) for i in range(n_communities)]
            
            # 创建可视化
            plt.figure(figsize=(15, 15))
            
            # 绘制节点和边
            if isinstance(communities, dict):
                nx.draw_networkx_nodes(G, nx.spring_layout(G), node_color=[communities[node] for node in G.nodes()],
                                     cmap=plt.cm.rainbow, node_size=500)
            else:
                for i, community in enumerate(communities):
                    nx.draw_networkx_nodes(G, nx.spring_layout(G), nodelist=list(community),
                                         node_color=[colors[i]], node_size=500)
            
            nx.draw_networkx_edges(G, nx.spring_layout(G), alpha=0.2)
            nx.draw_networkx_labels(G, nx.spring_layout(G))
            
            plt.title(f"社区聚类结果 (算法: {algorithm})")
            plt.savefig(output_file)
            plt.close()
            
            # 计算统计信息
            stats = {
                'total_communities': n_communities,
                'avg_size': len(G.nodes()) / n_communities,
                'modularity': nx.community.modularity(G, communities) if isinstance(communities, list) else None
            }
            
            return stats
        except Exception as e:
            logger.error(f"社区聚类可视化失败: {str(e)}")
            raise

    def visualize_temporal_evolution(self, relations: List[Any], output_file: str,
                                   time_window: str = 'month') -> Dict[str, Any]:
        """可视化图的时间演化
        
        Args:
            relations: 关系列表
            output_file: 输出文件路径
            time_window: 时间窗口 ('day', 'week', 'month', 'year')
            
        Returns:
            Dict: 时间演化统计信息
        """
        try:
            from datetime import datetime, timedelta
            import pandas as pd
            
            # 提取时间信息
            time_data = []
            for relation in relations:
                if hasattr(relation, 'timestamp'):
                    time_data.append({
                        'timestamp': relation.timestamp,
                        'source': relation.source.id,
                        'target': relation.target.id,
                        'type': relation.relation_type
                    })
            
            if not time_data:
                raise ValueError("没有找到时间信息")
            
            # 转换为DataFrame并按时间排序
            df = pd.DataFrame(time_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # 按时间窗口统计
            if time_window == 'day':
                grouped = df.groupby(df['timestamp'].dt.date)
            elif time_window == 'week':
                grouped = df.groupby(df['timestamp'].dt.isocalendar().week)
            elif time_window == 'month':
                grouped = df.groupby(df['timestamp'].dt.to_period('M'))
            else:  # year
                grouped = df.groupby(df['timestamp'].dt.year)
            
            # 计算统计信息
            stats = grouped.agg({
                'source': 'count',
                'type': lambda x: len(set(x))
            }).rename(columns={
                'source': 'relation_count',
                'type': 'unique_types'
            })
            
            # 创建可视化
            plt.figure(figsize=(15, 8))
            
            # 绘制关系数量变化
            ax1 = plt.gca()
            ax2 = ax1.twinx()
            
            stats['relation_count'].plot(color='blue', ax=ax1, label='关系数量')
            stats['unique_types'].plot(color='red', ax=ax2, label='关系类型数')
            
            ax1.set_xlabel(f'时间 ({time_window})')
            ax1.set_ylabel('关系数量', color='blue')
            ax2.set_ylabel('关系类型数', color='red')
            
            plt.title('知识图谱时间演化')
            plt.savefig(output_file)
            plt.close()
            
            return stats.to_dict()
        except Exception as e:
            logger.error(f"时间演化可视化失败: {str(e)}")
            raise

    def visualize_hierarchical(self, relations: List[Any], output_file: str,
                             root_type: str = None) -> Dict[str, Any]:
        """创建层次化可视化
        
        Args:
            relations: 关系列表
            output_file: 输出文件路径
            root_type: 根节点类型
            
        Returns:
            Dict: 层次结构统计信息
        """
        try:
            # 构建层次结构
            hierarchy = {}
            node_levels = {}
            
            # 找到根节点
            if root_type:
                roots = [r.source for r in relations if r.source.type == root_type]
            else:
                # 使用入度为0的节点作为根节点
                G = nx.DiGraph()
                for relation in relations:
                    G.add_edge(relation.source.id, relation.target.id)
                roots = [node for node in G.nodes() if G.in_degree(node) == 0]
            
            # 使用BFS构建层次结构
            def build_hierarchy(node, level=0):
                if node.id in node_levels:
                    return
                node_levels[node.id] = level
                if level not in hierarchy:
                    hierarchy[level] = []
                hierarchy[level].append(node)
                children = [r.target for r in relations if r.source.id == node.id]
                for child in children:
                    build_hierarchy(child, level + 1)
            
            for root in roots:
                build_hierarchy(root)
            
            # 创建可视化
            plt.figure(figsize=(20, 12))
            pos = {}
            
            # 计算节点位置
            max_level = max(hierarchy.keys())
            level_widths = [len(nodes) for nodes in hierarchy.values()]
            max_width = max(level_widths)
            
            for level, nodes in hierarchy.items():
                y = 1 - (level / max_level)
                for i, node in enumerate(nodes):
                    x = (i + 1) / (len(nodes) + 1)
                    pos[node.id] = (x, y)
            
            # 绘制节点和边
            G = nx.DiGraph()
            for relation in relations:
                G.add_edge(relation.source.id, relation.target.id)
            
            nx.draw_networkx_nodes(G, pos, node_color='lightblue',
                                 node_size=1000, alpha=0.6)
            nx.draw_networkx_edges(G, pos, edge_color='gray',
                                 arrows=True, arrowsize=20)
            nx.draw_networkx_labels(G, pos)
            
            plt.title("层次化知识图谱")
            plt.axis('off')
            plt.savefig(output_file)
            plt.close()
            
            # 计算统计信息
            stats = {
                'total_levels': len(hierarchy),
                'max_width': max_width,
                'total_nodes': sum(len(nodes) for nodes in hierarchy.values()),
                'level_distribution': {level: len(nodes) for level, nodes in hierarchy.items()}
            }
            
            return stats
        except Exception as e:
            logger.error(f"层次化可视化失败: {str(e)}")
            raise

    def export_to_d3(self, relations: List[Any], output_file: str) -> None:
        """导出为D3.js可视化格式
        
        Args:
            relations: 关系列表
            output_file: 输出文件路径
        """
        try:
            # 准备数据
            nodes = {}
            links = []
            
            for relation in relations:
                # 添加节点
                if relation.source.id not in nodes:
                    nodes[relation.source.id] = {
                        'id': relation.source.id,
                        'name': relation.source.name,
                        'type': relation.source.type,
                        'properties': relation.source.properties
                    }
                
                if relation.target.id not in nodes:
                    nodes[relation.target.id] = {
                        'id': relation.target.id,
                        'name': relation.target.name,
                        'type': relation.target.type,
                        'properties': relation.target.properties
                    }
                
                # 添加关系
                links.append({
                    'source': relation.source.id,
                    'target': relation.target.id,
                    'type': relation.relation_type,
                    'properties': relation.properties
                })
            
            # 创建D3.js数据结构
            d3_data = {
                'nodes': list(nodes.values()),
                'links': links
            }
            
            # 生成HTML模板
            template = Template("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>知识图谱可视化</title>
                <script src="https://d3js.org/d3.v7.min.js"></script>
                <style>
                    .node { stroke: #fff; stroke-width: 1.5px; }
                    .link { stroke: #999; stroke-opacity: 0.6; }
                    .node text { font: 12px sans-serif; }
                </style>
            </head>
            <body>
                <div id="graph"></div>
                <script>
                    const data = {{ data|tojson }};
                    
                    const width = window.innerWidth;
                    const height = window.innerHeight;
                    
                    const svg = d3.select("#graph")
                        .append("svg")
                        .attr("width", width)
                        .attr("height", height);
                    
                    const simulation = d3.forceSimulation(data.nodes)
                        .force("link", d3.forceLink(data.links).id(d => d.id))
                        .force("charge", d3.forceManyBody())
                        .force("center", d3.forceCenter(width / 2, height / 2));
                    
                    const link = svg.append("g")
                        .selectAll("line")
                        .data(data.links)
                        .enter().append("line")
                        .attr("class", "link");
                    
                    const node = svg.append("g")
                        .selectAll("circle")
                        .data(data.nodes)
                        .enter().append("circle")
                        .attr("class", "node")
                        .attr("r", 5)
                        .call(d3.drag()
                            .on("start", dragstarted)
                            .on("drag", dragged)
                            .on("end", dragended));
                    
                    node.append("title")
                        .text(d => d.name);
                    
                    simulation.on("tick", () => {
                        link
                            .attr("x1", d => d.source.x)
                            .attr("y1", d => d.source.y)
                            .attr("x2", d => d.target.x)
                            .attr("y2", d => d.target.y);
                        
                        node
                            .attr("cx", d => d.x)
                            .attr("cy", d => d.y);
                    });
                    
                    function dragstarted(event) {
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        event.subject.fx = event.subject.x;
                        event.subject.fy = event.subject.y;
                    }
                    
                    function dragged(event) {
                        event.subject.fx = event.x;
                        event.subject.fy = event.y;
                    }
                    
                    function dragended(event) {
                        if (!event.active) simulation.alphaTarget(0);
                        event.subject.fx = null;
                        event.subject.fy = null;
                    }
                </script>
            </body>
            </html>
            """)
            
            # 生成HTML文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(template.render(data=d3_data))
            
            logger.info(f"D3.js可视化已导出到: {output_file}")
        
        except Exception as e:
            logger.error(f"导出D3.js可视化失败: {str(e)}")
            raise

class DomainSpecificVisualizer:
    """领域特定的知识图谱可视化器"""
    
    def __init__(self, domain='tech', enable_temporal=False, enable_probabilistic=False):
        """初始化可视化器
        
        Args:
            domain (str): 领域名称，如'tech', 'medical', 'business'等
            enable_temporal (bool): 是否启用时序支持
            enable_probabilistic (bool): 是否启用概率支持
        """
        self.domain = domain
        self.config = VisualizationConfig()
        self.style_manager = StyleManager(self.config)
        self.graph_visualizer = GraphVisualizer(
            enable_temporal=enable_temporal,
            enable_probabilistic=enable_probabilistic
        )
        
        # 设置领域特定的样式
        self._setup_domain_styles()
    
    def _setup_domain_styles(self):
        """设置领域特定的样式"""
        if self.domain == 'tech':
            self.config.theme['light'].update({
                'background': '#f8f9fa',
                'node_color': '#4a90e2',
                'edge_color': '#95a5a6',
                'text_color': '#2c3e50',
                'highlight_color': '#e74c3c'
            })
            
            # 技术领域的节点类型颜色
            self.tech_colors = {
                'Technology': '#3498db',
                'Organization': '#2ecc71',
                'Person': '#e74c3c',
                'Project': '#f1c40f',
                'Default': '#95a5a6'
            }
    
    def visualize_domain(self, relations, output_file, include_stats=True, 
                        show_clusters=True, show_timeline=True):
        """生成领域特定的知识图谱可视化
        
        Args:
            relations (List[Relation]): 关系列表
            output_file (str): 输出文件路径
            include_stats (bool): 是否包含统计信息
            show_clusters (bool): 是否显示聚类
            show_timeline (bool): 是否显示时间线
        """
        # 收集所有实体
        entities = {}
        for relation in relations:
            if relation.source.id not in entities:
                entities[relation.source.id] = relation.source
            if relation.target.id not in entities:
                entities[relation.target.id] = relation.target
        
        # 应用领域特定的样式
        for entity in entities.values():
            if self.domain == 'tech':
                entity.color = self.tech_colors.get(entity.type, self.tech_colors['Default'])
        
        # 生成可视化
        self.graph_visualizer.visualize(
            relations,
            output_file=output_file,
            config=self.config,
            style_manager=self.style_manager
        )
        
        # 添加统计信息
        if include_stats:
            self._add_statistics(entities, relations, output_file)
        
        # 添加聚类视图
        if show_clusters:
            self._add_clusters(relations, output_file)
        
        # 添加时间线
        if show_timeline:
            self._add_timeline(relations, output_file)
    
    def _add_statistics(self, entities, relations, output_file):
        """添加统计信息"""
        stats = {
            'entity_count': len(entities),
            'relation_count': len(relations),
            'entity_types': {},
            'relation_types': {}
        }
        
        # 统计实体类型
        for entity in entities.values():
            if entity.type not in stats['entity_types']:
                stats['entity_types'][entity.type] = 0
            stats['entity_types'][entity.type] += 1
        
        # 统计关系类型
        for relation in relations:
            if relation.relation_type not in stats['relation_types']:
                stats['relation_types'][relation.relation_type] = 0
            stats['relation_types'][relation.relation_type] += 1
        
        # 将统计信息添加到可视化中
        # TODO: 实现统计信息的可视化
    
    def _add_clusters(self, relations, output_file):
        """添加聚类视图"""
        # TODO: 实现聚类视图
        pass
    
    def _add_timeline(self, relations, output_file):
        """添加时间线"""
        # TODO: 实现时间线视图
        pass
