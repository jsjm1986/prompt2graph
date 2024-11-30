from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from models import db, KnowledgeGraph, Entity, Relation, GraphHistory
from forms import GraphForm, EntityForm, RelationForm
from knowledge_graph import KnowledgeGraphBuilder
from graph_visualization import GraphVisualizer, DomainSpecificVisualizer
from utils import DeepSeekAPI, DataCleaner, FileHandler
import json
import os
from datetime import datetime

graph = Blueprint('graph', __name__)

@graph.route('/my_graphs')
@login_required
def my_graphs():
    """显示用户的所有知识图谱"""
    graphs = KnowledgeGraph.query.filter_by(user_id=current_user.id).all()
    return render_template('graph/my_graphs.html', graphs=graphs)

@graph.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建新的知识图谱"""
    form = GraphForm()
    if form.validate_on_submit():
        # 创建新的知识图谱
        graph = KnowledgeGraph(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(graph)
        db.session.commit()

        # 处理输入数据
        if form.file.data:
            file_handler = FileHandler(current_app.config['ALLOWED_EXTENSIONS'])
            text = file_handler.extract_text(form.file.data)
        else:
            text = form.text_input.data

        # 使用DeepSeek API提取实体和关系
        api = DeepSeekAPI(current_app.config['DEEPSEEK_API_KEY'])
        extracted_data = api.extract_entities(text)

        # 添加实体和关系到数据库
        for entity_data in extracted_data['entities']:
            entity = Entity(
                entity_id=entity_data['id'],
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

        db.session.commit()

        # 记录操作历史
        history = GraphHistory(
            graph_id=graph.id,
            user_id=current_user.id,
            operation='create',
            details={'method': 'api_extraction'}
        )
        db.session.add(history)
        db.session.commit()

        return jsonify({'success': True, 'graph_id': graph.id})

    return render_template('graph/create.html', form=form)

@graph.route('/<int:graph_id>')
@login_required
def view(graph_id):
    """查看知识图谱"""
    graph = KnowledgeGraph.query.get_or_404(graph_id)
    return render_template('graph/view.html', graph=graph)

@graph.route('/<int:graph_id>/edit', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def visualize(graph_id):
    """可视化知识图谱"""
    graph_data = KnowledgeGraph.query.get_or_404(graph_id)
    
    # 获取可视化参数
    viz_type = request.args.get('type', 'basic')
    include_temporal = request.args.get('temporal', 'false').lower() == 'true'
    include_probabilistic = request.args.get('probabilistic', 'false').lower() == 'true'
    
    # 创建输出目录
    output_dir = os.path.join(current_app.static_folder, 'graphs', str(current_user.id))
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
        visualizer = DomainSpecificVisualizer(
            domain=graph_data.domain,
            enable_temporal=include_temporal,
            enable_probabilistic=include_probabilistic
        )
        
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
        visualizer = DomainSpecificVisualizer(
            enable_temporal=True,
            enable_probabilistic=False
        )
        output_file = os.path.join(output_dir, f'graph_{graph_id}_temporal.html')
        temporal_relations = [r for r in relations 
                            if ('temporal' in r.source.properties or 
                                'temporal' in r.target.properties)]
        visualizer.visualize_temporal(temporal_relations, output_file)
    
    elif viz_type == 'probabilistic':
        visualizer = DomainSpecificVisualizer(
            enable_temporal=False,
            enable_probabilistic=True
        )
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
        user_id=current_user.id,
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
@login_required
def export(graph_id):
    """导出知识图谱"""
    graph = KnowledgeGraph.query.get_or_404(graph_id)
    format_type = request.args.get('format', 'json')
    
    if format_type == 'json':
        data = graph.to_dict()
        return jsonify(data)
    
    elif format_type == 'csv':
        output_dir = os.path.join(current_app.static_folder, 'exports', str(current_user.id))
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
        output_dir = os.path.join(current_app.static_folder, 'exports', str(current_user.id))
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

@graph.route('/batch', methods=['POST'])
@login_required
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
                        entity_id=entity_data['id'],
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
