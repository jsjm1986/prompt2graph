from graph_models import Entity, Relation
from graph_visualization import GraphVisualizer, DomainSpecificVisualizer
import os
from typing import List, Dict, Any
import json
import time
from datetime import datetime
import networkx as nx

def create_tech_knowledge_graph():
    """
    创建技术领域的示例知识图谱
    """
    # 创建实体
    entities = {
        'ai': Entity(id='1', name='人工智能', type='Technology', properties={'field': 'Computer Science'}),
        'ml': Entity(id='2', name='机器学习', type='Technology', properties={'field': 'AI'}),
        'dl': Entity(id='3', name='深度学习', type='Technology', properties={'field': 'ML', 'temporal': '2012-present'}),
        'cnn': Entity(id='4', name='卷积神经网络', type='Algorithm', properties={'field': 'DL', 'temporal': '2012'}),
        'transformer': Entity(id='5', name='Transformer', type='Architecture', properties={'field': 'DL', 'temporal': '2017'}),
        'bert': Entity(id='6', name='BERT', type='Model', properties={'field': 'NLP', 'temporal': '2018'}),
        'gpt': Entity(id='7', name='GPT', type='Model', properties={'field': 'NLP', 'temporal': '2018-present'})
    }
    
    # 创建关系
    relations = [
        Relation(
            source=entities['ml'],
            target=entities['ai'],
            relation_type='is_part_of',
            confidence=0.95,
            properties={}
        ),
        Relation(
            source=entities['dl'],
            target=entities['ml'],
            relation_type='is_part_of',
            confidence=0.95,
            properties={}
        ),
        Relation(
            source=entities['cnn'],
            target=entities['dl'],
            relation_type='is_type_of',
            confidence=0.9,
            properties={}
        ),
        Relation(
            source=entities['transformer'],
            target=entities['dl'],
            relation_type='revolutionized',
            confidence=0.85,
            properties={'year': '2017'}
        ),
        Relation(
            source=entities['bert'],
            target=entities['transformer'],
            relation_type='based_on',
            confidence=0.95,
            properties={}
        ),
        Relation(
            source=entities['gpt'],
            target=entities['transformer'],
            relation_type='based_on',
            confidence=0.95,
            properties={}
        ),
        Relation(
            source=entities['bert'],
            target=entities['gpt'],
            relation_type='competes_with',
            confidence=0.7,
            properties={'aspect': 'architecture'}
        )
    ]
    
    return entities, relations

def demonstrate_visualization_features():
    """
    演示知识图谱可视化系统的各种功能
    """
    print("开始知识图谱可视化功能演示...")
    
    # 创建示例知识图谱
    entities, relations = create_tech_knowledge_graph()
    
    # 1. 基础可视化
    print("\n1. 创建基础可视化...")
    basic_visualizer = GraphVisualizer()
    basic_visualizer.visualize_interactive(
        relations,
        "output/basic_graph.html"
    )
    
    # 2. 领域特定可视化
    print("\n2. 创建技术领域特定可视化...")
    tech_visualizer = DomainSpecificVisualizer(
        domain='tech',
        enable_temporal=True,
        enable_probabilistic=True
    )
    
    tech_visualizer.visualize_domain(
        relations,
        output_file="output/tech_domain_graph.html",
        include_legend=True,
        include_filters=True,
        include_search=True,
        include_export=True,
        include_stats=True
    )
    
    # 3. 时序可视化
    print("\n3. 创建时序关系可视化...")
    tech_visualizer.visualize_temporal(
        relations,
        "output/temporal_graph.html"
    )
    
    # 4. 概率关系可视化
    print("\n4. 创建概率关系可视化...")
    tech_visualizer.visualize_probabilistic(
        relations,
        "output/probabilistic_graph.html"
    )
    
    print("\n可视化演示完成！生成的文件：")
    print("- output/basic_graph.html - 基础知识图谱")
    print("- output/tech_domain_graph.html - 技术领域特定图谱（包含所有高级特性）")
    print("- output/temporal_graph.html - 时序关系图谱")
    print("- output/probabilistic_graph.html - 概率关系图谱")

def demonstrate_export_features(relations):
    """演示知识图谱导出功能"""
    print("\n开始演示导出功能...")
    
    # 1. JSON导出
    print("\n1. 导出为JSON格式...")
    json_file = "output/knowledge_graph.json"
    basic_visualizer = GraphVisualizer()
    basic_visualizer.export_to_json(relations, json_file)
    
    # 2. CSV导出
    print("\n2. 导出为CSV格式...")
    csv_dir = "output/csv"
    basic_visualizer.export_to_csv(relations, csv_dir)
    
    # 3. RDF导出（多种格式）
    print("\n3. 导出为RDF格式...")
    # Turtle格式
    basic_visualizer.export_to_rdf(relations, "output/knowledge_graph.ttl", format="turtle")
    # N-Triples格式
    basic_visualizer.export_to_rdf(relations, "output/knowledge_graph.nt", format="nt")
    # JSON-LD格式
    basic_visualizer.export_to_rdf(relations, "output/knowledge_graph.jsonld", format="json-ld")
    
    print("\n导出完成！生成的文件：")
    print("- output/knowledge_graph.json - JSON格式")
    print("- output/csv/entities.csv - 实体CSV")
    print("- output/csv/relations.csv - 关系CSV")
    print("- output/knowledge_graph.ttl - RDF (Turtle格式)")
    print("- output/knowledge_graph.nt - RDF (N-Triples格式)")
    print("- output/knowledge_graph.jsonld - RDF (JSON-LD格式)")

def demonstrate_analysis_features(relations):
    """演示图分析功能"""
    print("\n开始演示图分析功能...")
    
    # 创建分析器
    analyzer = GraphAnalyzer()
    
    # 1. 执行全面分析
    print("\n1. 执行图分析...")
    metrics = analyzer.analyze(relations)
    
    # 打印基础指标
    print("\n基础指标:")
    print(f"- 节点数量: {metrics.node_count}")
    print(f"- 边数量: {metrics.edge_count}")
    print(f"- 图密度: {metrics.density:.4f}")
    print(f"- 平均度: {metrics.avg_degree:.2f}")
    
    # 打印结构指标
    print("\n结构指标:")
    print(f"- 聚类系数: {metrics.clustering_coefficient:.4f}")
    print(f"- 连通分量数: {metrics.components_count}")
    if metrics.avg_path_length:
        print(f"- 平均路径长度: {metrics.avg_path_length:.2f}")
    if metrics.diameter:
        print(f"- 图直径: {metrics.diameter}")
    
    # 2. 路径分析
    print("\n2. 路径分析...")
    if len(relations) >= 2:
        source_id = relations[0].source.id
        target_id = relations[-1].target.id
        
        # 最短路径
        shortest_path = analyzer.find_shortest_path(source_id, target_id)
        if shortest_path:
            print(f"\n最短路径 ({source_id} -> {target_id}):")
            print(" -> ".join(shortest_path))
        
        # 所有路径
        all_paths = analyzer.find_all_paths(source_id, target_id)
        if all_paths:
            print(f"\n所有路径 (最多3跳):")
            for i, path in enumerate(all_paths, 1):
                print(f"{i}. " + " -> ".join(path))
    
    # 3. 节点重要性分析
    print("\n3. 重要节点:")
    print("\nPageRank Top-5:")
    for node_id, score in metrics.top_nodes[:5]:
        print(f"- {node_id}: {score:.4f}")
    
    # 4. 社区分析
    print("\n4. 社区分析:")
    for i, community in enumerate(metrics.communities[:3], 1):
        print(f"\n社区 {i} (大小: {len(community)}):")
        print(f"示例节点: {', '.join(community[:5])}")
    
    # 5. 相似节点分析
    if relations:
        print("\n5. 相似节点分析:")
        node_id = relations[0].source.id
        similar_nodes = analyzer.find_similar_nodes(node_id)
        print(f"\n与节点 {node_id} 相似的节点:")
        for similar_id, similarity in similar_nodes:
            print(f"- {similar_id}: 相似度 {similarity:.4f}")

def demonstrate_query_features(relations):
    """演示查询功能"""
    print("\n开始演示查询功能...")
    
    # 创建查询引擎
    query_engine = QueryEngine()
    
    # 构建图
    graph = nx.DiGraph()
    for relation in relations:
        graph.add_node(relation.source.id, **relation.source.__dict__)
        graph.add_node(relation.target.id, **relation.target.__dict__)
        graph.add_edge(relation.source.id, relation.target.id,
                      type=relation.relation_type,
                      **relation.__dict__)
    
    query_engine.set_graph(graph)
    
    # 1. 路径查询
    print("\n1. 路径查询示例:")
    path_query = "查找深度学习和计算机视觉之间的关系"
    result = query_engine.natural_language_query(path_query)
    print(f"查询: {path_query}")
    print(f"找到 {len(result.paths)} 条路径")
    for i, path in enumerate(result.paths[:3], 1):
        print(f"路径 {i}: {' -> '.join(path)}")
    print(f"置信度: {result.confidence:.2f}")
    
    # 2. 邻居查询
    print("\n2. 邻居查询示例:")
    neighbor_query = "查找与机器学习相关的技术"
    result = query_engine.natural_language_query(neighbor_query)
    print(f"查询: {neighbor_query}")
    print(f"找到 {len(result.nodes)} 个相关节点:")
    for node in result.nodes[:5]:
        print(f"- {node['id']}: {node['properties'].get('name', '')}")
    print(f"置信度: {result.confidence:.2f}")
    
    # 3. 子图查询
    print("\n3. 子图查询示例:")
    subgraph_query = "提取关于深度学习和神经网络的知识子图"
    result = query_engine.natural_language_query(subgraph_query)
    print(f"查询: {subgraph_query}")
    print(f"子图包含 {len(result.nodes)} 个节点和 {len(result.edges)} 条边")
    print("主要概念:")
    for node in result.nodes[:5]:
        print(f"- {node['id']}")
    print(f"置信度: {result.confidence:.2f}")
    
    # 4. 通用搜索
    print("\n4. 通用搜索示例:")
    search_query = "查找用于图像处理的深度学习模型"
    result = query_engine.natural_language_query(search_query)
    print(f"查询: {search_query}")
    print(f"找到 {len(result.nodes)} 个相关节点:")
    for node in result.nodes[:5]:
        print(f"- {node['id']}: {node['properties'].get('name', '')}")
    print(f"置信度: {result.confidence:.2f}")

def demonstrate_query_optimization(relations):
    """演示查询优化功能"""
    print("\n开始演示查询优化功能...")
    
    # 创建查询优化器
    optimizer = QueryOptimizer()
    
    # 构建图
    graph = nx.DiGraph()
    for relation in relations:
        graph.add_node(relation.source.id, **relation.source.__dict__)
        graph.add_node(relation.target.id, **relation.target.__dict__)
        graph.add_edge(relation.source.id, relation.target.id,
                      type=relation.relation_type,
                      **relation.__dict__)
    
    optimizer.set_graph(graph)
    
    # 1. 查询优化
    print("\n1. 查询优化示例:")
    queries = [
        "查找深度学习和计算机视觉之间的关系",
        "分析与机器学习相关的技术",
        "提取神经网络领域的知识图谱"
    ]
    
    for query in queries:
        print(f"\n原始查询: {query}")
        plan = optimizer.optimize_query(query)
        print("执行计划:")
        for i, step in enumerate(plan.steps, 1):
            print(f"步骤 {i}: {step['description']} (预估成本: {step['estimated_cost']:.2f})")
        print(f"总预估成本: {plan.estimated_cost:.2f}")
        print(f"缓存命中: {plan.cache_hits}")
        print(f"优化时间: {plan.optimization_time:.3f}秒")
    
    # 2. 查询建议
    print("\n2. 查询建议示例:")
    test_queries = [
        "机器学习的应用",
        "深度学习模型比较",
        "图像识别技术"
    ]
    
    for query in test_queries:
        print(f"\n原始查询: {query}")
        suggestions = optimizer.suggest_queries(query)
        print("建议查询:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"建议 {i}: {suggestion.suggested_query}")
            print(f"置信度: {suggestion.confidence:.2f}")
            print(f"说明: {suggestion.explanation}")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/csv", exist_ok=True)
    
    # 创建示例知识图谱
    entities, relations = create_tech_knowledge_graph()
    
    # 运行可视化演示
    demonstrate_visualization_features()
    
    # 运行导出演示
    demonstrate_export_features(relations)
    
    # 运行分析演示
    demonstrate_analysis_features(relations)
    
    # 运行查询演示
    demonstrate_query_features(relations)
    
    # 运行查询优化演示
    demonstrate_query_optimization(relations)
