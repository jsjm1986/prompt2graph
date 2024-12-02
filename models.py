from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class KnowledgeGraph(db.Model):
    """知识图谱模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    domain = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 配置选项
    enable_temporal = db.Column(db.Boolean, default=False)
    enable_probabilistic = db.Column(db.Boolean, default=False)
    enable_multi_hop = db.Column(db.Boolean, default=False)
    enable_batch = db.Column(db.Boolean, default=False)
    confidence_threshold = db.Column(db.Float, default=0.7)
    
    # 关系
    entities = db.relationship('Entity', backref='graph', lazy=True, cascade='all, delete-orphan')
    relations = db.relationship('Relation', backref='graph', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('GraphHistory', backref='graph', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'domain': self.domain,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'enable_temporal': self.enable_temporal,
            'enable_probabilistic': self.enable_probabilistic,
            'enable_multi_hop': self.enable_multi_hop,
            'enable_batch': self.enable_batch,
            'confidence_threshold': self.confidence_threshold,
            'entities': [entity.to_dict() for entity in self.entities],
            'relations': [relation.to_dict() for relation in self.relations]
        }

class Entity(db.Model):
    """实体模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    properties = db.Column(db.JSON)
    graph_id = db.Column(db.Integer, db.ForeignKey('knowledge_graph.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'properties': self.properties,
            'graph_id': self.graph_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Relation(db.Model):
    """关系模型"""
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)
    properties = db.Column(db.JSON)
    confidence = db.Column(db.Float, default=1.0)
    graph_id = db.Column(db.Integer, db.ForeignKey('knowledge_graph.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = db.relationship('Entity', foreign_keys=[source_id], backref='outgoing_relations')
    target = db.relationship('Entity', foreign_keys=[target_id], backref='incoming_relations')

    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type,
            'properties': self.properties,
            'confidence': self.confidence,
            'graph_id': self.graph_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class GraphHistory(db.Model):
    """图谱操作历史"""
    id = db.Column(db.Integer, primary_key=True)
    graph_id = db.Column(db.Integer, db.ForeignKey('knowledge_graph.id'), nullable=False)
    operation = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'graph_id': self.graph_id,
            'operation': self.operation,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }
