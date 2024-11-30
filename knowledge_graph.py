import json
import requests
import networkx as nx
from pyvis.network import Network
import pandas as pd
from typing import List, Dict, Any
from relation_extraction import HybridRelationExtractor
from graph_models import Entity, Relation

class KnowledgeGraphBuilder:
    def __init__(self, api_key: str):
        """
        初始化知识图谱构建器
        :param api_key: DeepSeek API密钥
        """
        self.api_key = api_key
        self.graph = nx.DiGraph()
        self.relation_extractor = HybridRelationExtractor(api_key)
        
    def extract_entities_relations(self, text: str) -> Dict[str, Any]:
        """
        使用混合方法从文本中提取实体和关系
        :param text: 输入文本
        :return: 包含实体和关系的字典
        """
        # 使用混合提取器提取关系
        relations = self.relation_extractor.extract_relations(text)
        
        # 转换为API格式
        entities = {}
        api_relations = []
        
        for relation in relations:
            # 添加源实体
            if relation.source.id not in entities:
                entities[relation.source.id] = Entity(
                    id=relation.source.id,
                    name=relation.source.name,
                    type=relation.source.type,
                    properties=relation.source.properties or {}
                )
            
            # 添加目标实体
            if relation.target.id not in entities:
                entities[relation.target.id] = Entity(
                    id=relation.target.id,
                    name=relation.target.name,
                    type=relation.target.type,
                    properties=relation.target.properties or {}
                )
            
            # 添加关系
            api_relations.append(Relation(
                source=relation.source.id,
                target=relation.target.id,
                relation=relation.relation_type.value,
                properties=relation.properties or {},
                confidence=relation.confidence
            ))
        
        return {
            "entities": list(entities.values()),
            "relations": api_relations
        }

    def build_graph(self, data: Dict[str, Any]) -> None:
        """
        根据提取的实体和关系构建图
        :param data: 包含实体和关系的字典
        """
        # 添加节点
        for entity in data["entities"]:
            self.graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                properties=entity.properties
            )
        
        # 添加边
        for relation in data["relations"]:
            self.graph.add_edge(
                relation.source,
                relation.target,
                relation=relation.relation,
                properties=relation.properties,
                confidence=relation.confidence
            )

    def visualize(self, output_file: str = "knowledge_graph.html") -> None:
        """
        可视化知识图谱
        :param output_file: 输出HTML文件路径
        """
        net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
        
        # 配置物理布局
        net.force_atlas_2based()
        
        # 添加节点，使用不同颜色表示不同类型的实体
        colors = {
            "Person": "#ff7675",
            "Organization": "#74b9ff",
            "Location": "#55efc4",
            "Event": "#ffeaa7",
            "Concept": "#a29bfe",
            "Default": "#dfe6e9"
        }
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            color = colors.get(node_data["type"], colors["Default"])
            
            net.add_node(
                node_id,
                label=node_data["name"],
                title=f"Type: {node_data['type']}\nProperties: {json.dumps(node_data['properties'], indent=2)}",
                color=color
            )
        
        # 添加边，使用不同的样式表示不同类型的关系
        edge_styles = {
            "is_a": {"color": "#2d3436", "width": 2},
            "part_of": {"color": "#636e72", "width": 2, "dashes": True},
            "default": {"color": "#b2bec3", "width": 1}
        }
        
        for edge in self.graph.edges(data=True):
            source, target, data = edge
            style = edge_styles.get(data["relation"], edge_styles["default"])
            
            net.add_edge(
                source,
                target,
                title=f"Relation: {data['relation']}\nConfidence: {data.get('confidence', 1.0):.2f}",
                **style
            )
        
        # 保存为HTML文件
        net.show(output_file)

    def export_to_csv(self, nodes_file: str = "nodes.csv", edges_file: str = "edges.csv") -> None:
        """
        将图数据导出为CSV文件
        :param nodes_file: 节点CSV文件路径
        :param edges_file: 边CSV文件路径
        """
        # 导出节点
        nodes_data = []
        for node_id, data in self.graph.nodes(data=True):
            nodes_data.append({
                "id": node_id,
                "name": data["name"],
                "type": data["type"],
                "properties": json.dumps(data["properties"])
            })
        pd.DataFrame(nodes_data).to_csv(nodes_file, index=False)
        
        # 导出边
        edges_data = []
        for source, target, data in self.graph.edges(data=True):
            edges_data.append({
                "source": source,
                "target": target,
                "relation": data["relation"],
                "properties": json.dumps(data.get("properties", {})),
                "confidence": data.get("confidence", 1.0)
            })
        pd.DataFrame(edges_data).to_csv(edges_file, index=False)

def main():
    # 示例用法
    api_key = "your_deepseek_api_key"  # 替换为你的API密钥
    
    # 创建知识图谱构建器实例
    kg_builder = KnowledgeGraphBuilder(api_key)
    
    # 示例文本
    sample_text = """
    华为是一家中国的科技公司，总部位于深圳。任正非是华为的创始人。
    华为主要生产智能手机和通信设备。华为的Mate系列是其旗舰手机产品线。
    """
    
    # 提取实体和关系
    extracted_data = kg_builder.extract_entities_relations(sample_text)
    
    # 构建图
    kg_builder.build_graph(extracted_data)
    
    # 可视化
    kg_builder.visualize()
    
    # 导出数据
    kg_builder.export_to_csv()

if __name__ == "__main__":
    main()
