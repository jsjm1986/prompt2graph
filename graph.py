from flask import Blueprint, render_template, request, jsonify, current_app, send_file, redirect, url_for
from models import db, KnowledgeGraph, Entity, Relation, GraphHistory
from forms import GraphForm, EntityForm, RelationForm
from knowledge_graph import KnowledgeGraphBuilder
from graph_visualization import GraphVisualizer
from utils import DeepSeekAPI, DataCleaner, FileHandler
import json
import os
from datetime import datetime

graph = Blueprint('graph', __name__)

@graph.route('/my_graphs')
def my_graphs():
    """显示所有知识图谱"""
    graphs = KnowledgeGraph.query.all()
    return render_template('graph/my_graphs.html', graphs=graphs)

@graph.route('/templates')
def manage_templates():
    """管理图谱模板"""
    return render_template('graph/templates.html')

@graph.route('/create', methods=['GET', 'POST'])
def create_graph():
    """创建新的知识图谱"""
    form = GraphForm()
    if form.validate_on_submit():
        try:
            # 创建新的知识图谱
            graph = KnowledgeGraph(
                name=form.name.data,
                description=form.description.data,
                domain=form.domain.data,
                enable_temporal=form.enable_temporal.data,
                enable_probabilistic=form.enable_probabilistic.data,
                enable_multi_hop=form.enable_multi_hop.data,
                confidence_threshold=form.confidence_threshold.data
            )
            db.session.add(graph)
            db.session.commit()

            # 处理输入数据
            text = None
            if form.file.data:
                file_handler = FileHandler(current_app.config.get('ALLOWED_EXTENSIONS', {'txt', 'pdf', 'doc', 'docx'}))
                text = file_handler.extract_text(form.file.data)
            elif form.text_input.data:
                text = form.text_input.data.strip()

            if text:  # 只有当有输入文本时才处理
                # 使用DeepSeek API提取实体和关系
                api = DeepSeekAPI()
                extracted_data = api.extract_entities(text)
                
                current_app.logger.info(f"Extracted data: {extracted_data}")  # 添加日志

                # 创建实体字典用于跟踪ID映射
                entity_id_map = {}

                # 添加实体到数据库
                for entity_data in extracted_data['entities']:
                    entity = Entity(
                        name=entity_data['name'],
                        type=entity_data['type'],
                        properties=entity_data.get('properties', {}),
                        graph=graph
                    )
                    db.session.add(entity)
                    db.session.flush()  # 获取自动生成的ID
                    entity_id_map[entity_data['id']] = entity.id

                db.session.commit()

                # 添加关系到数据库
                for relation_data in extracted_data['relations']:
                    source_id = entity_id_map.get(relation_data['source_id'])
                    target_id = entity_id_map.get(relation_data['target_id'])
                    
                    if source_id and target_id:
                        relation = Relation(
                            source_id=source_id,
                            target_id=target_id,
                            relation_type=relation_data['relation_type'],  # 修改这里：使用 relation_type
                            properties=relation_data.get('properties', {}),
                            confidence=relation_data.get('confidence', 1.0),
                            graph=graph
                        )
                        db.session.add(relation)

                db.session.commit()

            return redirect(url_for('graph.view', graph_id=graph.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating graph: {str(e)}")
            return render_template('graph/create.html', form=form, error="创建图谱时发生错误，请重试。")

    return render_template('graph/create.html', form=form)

@graph.route('/view/<int:graph_id>')
def view(graph_id):
    """查看知识图谱"""
    graph_data = KnowledgeGraph.query.get_or_404(graph_id)
    
    # 获取实体和关系
    entities = Entity.query.filter_by(graph_id=graph_id).all()
    relations = Relation.query.filter_by(graph_id=graph_id).all()
    
    # 准备可视化数据
    nodes = []
    edges = []
    
    # 添加节点
    for entity in entities:
        nodes.append({
            'id': entity.id,
            'label': entity.name,
            'title': f'类型: {entity.type}<br>属性: {json.dumps(entity.properties, ensure_ascii=False)}',
            'group': entity.type,  # 用于颜色分组
            'properties': entity.properties
        })
    
    # 添加边
    for relation in relations:
        edges.append({
            'from': relation.source_id,
            'to': relation.target_id,
            'label': relation.relation_type,  
            'title': f'置信度: {relation.confidence}<br>属性: {json.dumps(relation.properties, ensure_ascii=False)}',
            'arrows': 'to',
            'properties': relation.properties
        })
    
    # 构建完整的图数据
    visualization_data = {
        'nodes': nodes,
        'edges': edges
    }
    
    return render_template('graph/view.html', 
                         graph=graph_data,
                         graph_data=json.dumps(visualization_data, ensure_ascii=False),
                         entities=entities,
                         relations=relations)

@graph.route('/<int:graph_id>/edit', methods=['GET', 'POST'])
def edit(graph_id):
    """编辑知识图谱"""
    graph = KnowledgeGraph.query.get_or_404(graph_id)
    form = GraphForm(obj=graph)
    
    if form.validate_on_submit():
        form.populate_obj(graph)
        db.session.commit()
        return jsonify({'success': True})
    
    return render_template('graph/edit.html', form=form, graph=graph)

@graph.route('/<int:graph_id>/merge', methods=['POST'])
def merge(graph_id):
    """合并两个知识图谱"""
    target_graph_id = request.json.get('target_graph_id')
    if not target_graph_id:
        return jsonify({'error': 'Target graph ID is required'}), 400

    source_graph = KnowledgeGraph.query.get_or_404(graph_id)
    target_graph = KnowledgeGraph.query.get_or_404(target_graph_id)

    # 合并实体
    entity_mapping = {}
    for entity in source_graph.entities:
        existing_entity = Entity.query.filter_by(
            name=entity.name,
            type=entity.type,
            graph_id=target_graph.id
        ).first()
        
        if existing_entity:
            entity_mapping[entity.entity_id] = existing_entity.entity_id
        else:
            new_entity = Entity(
                name=entity.name,
                type=entity.type,
                properties=entity.properties,
                graph_id=target_graph.id
            )
            db.session.add(new_entity)
            db.session.flush()
            entity_mapping[entity.entity_id] = new_entity.entity_id

    # 合并关系
    for relation in source_graph.relations:
        source_id = entity_mapping.get(relation.source_id)
        target_id = entity_mapping.get(relation.target_id)
        
        if source_id and target_id:
            new_relation = Relation(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation.relation_type,
                properties=relation.properties,
                graph_id=target_graph.id
            )
            db.session.add(new_relation)

    db.session.commit()
    return jsonify({'success': True})

@graph.route('/<int:graph_id>/visualize', methods=['GET'])
def visualize(graph_id):
    """可视化知识图谱"""
    graph_data = KnowledgeGraph.query.get_or_404(graph_id)
    
    # 获取可视化参数
    viz_type = request.args.get('type', 'basic')
    include_temporal = request.args.get('temporal', 'false').lower() == 'true'
    include_probabilistic = request.args.get('probabilistic', 'false').lower() == 'true'
    
    # 创建输出目录
    output_dir = os.path.join(current_app.static_folder, 'graphs')
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备实体和关系数据
    entities = {}
    for entity in graph_data.entities:
        entities[entity.entity_id] = Entity(
            entity.entity_id,
            entity.name,
            entity.type,
            json.loads(entity.properties) if entity.properties else {}
        )
    
    relations = []
    for relation in graph_data.relations:
        if relation.source_id in entities and relation.target_id in entities:
            relations.append(Relation(
                entities[relation.source_id],
                relation.relation_type,
                entities[relation.target_id],
                float(relation.confidence) if relation.confidence else 1.0,
                json.loads(relation.properties) if relation.properties else {}
            ))
    
    # 选择可视化器
    if viz_type == 'domain':
        visualizer = GraphVisualizer()
        
        # 设置领域特定样式
        visualizer.set_color_scheme({
            'Technology': '#4CAF50',
            'Person': '#2196F3',
            'Organization': '#9C27B0',
            'Project': '#FF9800',
            'Default': '#607D8B'
        })
        
        # 生成可视化
        output_file = os.path.join(output_dir, f'graph_{graph_id}_domain.html')
        visualizer.visualize_domain(
            relations,
            output_file=output_file,
            include_legend=True,
            include_filters=True,
            include_search=True,
            include_export=True,
            include_stats=True
        )
    
    elif viz_type == 'temporal':
        visualizer = GraphVisualizer()
        output_file = os.path.join(output_dir, f'graph_{graph_id}_temporal.html')
        temporal_relations = [r for r in relations 
                            if ('temporal' in r.source.properties or 
                                'temporal' in r.target.properties)]
        visualizer.visualize_temporal(temporal_relations, output_file)
    
    elif viz_type == 'probabilistic':
        visualizer = GraphVisualizer()
        output_file = os.path.join(output_dir, f'graph_{graph_id}_probabilistic.html')
        uncertain_relations = [r for r in relations if r.confidence < 0.9]
        visualizer.visualize_probabilistic(uncertain_relations, output_file)
    
    else:  # basic visualization
        visualizer = GraphVisualizer()
        output_file = os.path.join(output_dir, f'graph_{graph_id}_basic.html')
        visualizer.visualize_interactive(relations, output_file)
    
    # 记录可视化历史
    history = GraphHistory(
        graph_id=graph_id,
        operation='visualize',
        details={
            'type': viz_type,
            'temporal': include_temporal,
            'probabilistic': include_probabilistic,
            'timestamp': datetime.now().isoformat()
        }
    )
    db.session.add(history)
    db.session.commit()
    
    # 返回可视化结果
    relative_path = os.path.relpath(output_file, current_app.static_folder)
    return jsonify({
        'success': True,
        'visualization_url': f'/static/{relative_path}',
        'type': viz_type
    })

@graph.route('/<int:graph_id>/export', methods=['GET'])
def export(graph_id):
    """导出知识图谱"""
    graph = KnowledgeGraph.query.get_or_404(graph_id)
    format_type = request.args.get('format', 'json')
    
    if format_type == 'json':
        data = graph.to_dict()
        return jsonify(data)
    
    elif format_type == 'csv':
        output_dir = os.path.join(current_app.static_folder, 'exports')
        os.makedirs(output_dir, exist_ok=True)
        
        # 导出节点
        nodes_file = os.path.join(output_dir, f'graph_{graph_id}_nodes.csv')
        with open(nodes_file, 'w', encoding='utf-8') as f:
            f.write('id,name,type,properties\n')
            for entity in graph.entities:
                f.write(f'{entity.entity_id},{entity.name},{entity.type},{entity.properties}\n')
        
        # 导出边
        edges_file = os.path.join(output_dir, f'graph_{graph_id}_edges.csv')
        with open(edges_file, 'w', encoding='utf-8') as f:
            f.write('source,target,type,confidence,properties\n')
            for relation in graph.relations:
                f.write(f'{relation.source_id},{relation.target_id},{relation.relation_type},' +
                       f'{relation.confidence},{relation.properties}\n')
        
        # 打包CSV文件
        import zipfile
        zip_file = os.path.join(output_dir, f'graph_{graph_id}_export.zip')
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.write(nodes_file, os.path.basename(nodes_file))
            zf.write(edges_file, os.path.basename(edges_file))
        
        return send_file(
            zip_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'graph_{graph_id}_export.zip'
        )
    
    elif format_type == 'rdf':
        # 实现RDF导出
        from rdflib import Graph as RDFGraph, Literal, URIRef
        from rdflib.namespace import RDF, RDFS
        
        g = RDFGraph()
        ns = URIRef('http://example.org/kg/')
        
        # 添加实体
        for entity in graph.entities:
            entity_uri = URIRef(ns + f'entity/{entity.entity_id}')
            g.add((entity_uri, RDF.type, URIRef(ns + 'Entity')))
            g.add((entity_uri, RDFS.label, Literal(entity.name)))
            g.add((entity_uri, URIRef(ns + 'type'), Literal(entity.type)))
        
        # 添加关系
        for relation in graph.relations:
            source_uri = URIRef(ns + f'entity/{relation.source_id}')
            target_uri = URIRef(ns + f'entity/{relation.target_id}')
            relation_uri = URIRef(ns + f'relation/{relation.relation_type}')
            g.add((source_uri, relation_uri, target_uri))
        
        # 导出RDF
        output_dir = os.path.join(current_app.static_folder, 'exports')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f'graph_{graph_id}.ttl')
        g.serialize(destination=output_file, format='turtle')
        
        return send_file(
            output_file,
            mimetype='text/turtle',
            as_attachment=True,
            download_name=f'graph_{graph_id}.ttl'
        )
    
    return jsonify({'error': 'Unsupported format'}), 400

@graph.route('/<int:graph_id>/delete', methods=['POST'])
def delete_graph(graph_id):
    """删除知识图谱"""
    graph = KnowledgeGraph.query.get_or_404(graph_id)
    try:
        # 删除相关的实体和关系
        Entity.query.filter_by(graph_id=graph_id).delete()
        Relation.query.filter_by(graph_id=graph_id).delete()
        db.session.delete(graph)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting graph: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@graph.route('/batch', methods=['POST'])
def batch_process():
    """批量处理数据"""
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    results = []
    file_handler = FileHandler(current_app.config['ALLOWED_EXTENSIONS'])
    api = DeepSeekAPI(current_app.config['DEEPSEEK_API_KEY'])

    for file in files:
        if file and file_handler.allowed_file(file.filename):
            try:
                # 提取文本
                text = file_handler.extract_text(file)
                
                # 使用API提取实体和关系
                extracted_data = api.extract_entities(text)
                
                # 创建新的知识图谱
                graph = KnowledgeGraph(
                    name=f"Batch - {file.filename}",
                    description=f"Generated from {file.filename}"
                )
                db.session.add(graph)
                db.session.flush()

                # 添加实体和关系
                for entity_data in extracted_data['entities']:
                    entity = Entity(
                        name=entity_data['name'],
                        type=entity_data['type'],
                        graph_id=graph.id
                    )
                    db.session.add(entity)

                for relation_data in extracted_data['relations']:
                    relation = Relation(
                        source_id=relation_data['source'],
                        target_id=relation_data['target'],
                        relation_type=relation_data['relation'],
                        graph_id=graph.id
                    )
                    db.session.add(relation)

                results.append({
                    'filename': file.filename,
                    'status': 'success',
                    'graph_id': graph.id
                })
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(e)
                })

    db.session.commit()
    return jsonify({'results': results})
