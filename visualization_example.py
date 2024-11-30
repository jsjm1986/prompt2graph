from graph_models import Entity, Relation
from graph_visualization import DomainSpecificVisualizer
import random
from datetime import datetime, timedelta
import os

def generate_sample_data():
    """生成示例数据"""
    # 创建一些实体
    entities = {
        # 技术实体
        'python': Entity('1', 'Python', 'Technology', {'version': '3.8'}),
        'django': Entity('2', 'Django', 'Technology', {'version': '4.2'}),
        'flask': Entity('3', 'Flask', 'Technology', {'version': '2.0'}),
        'sqlalchemy': Entity('4', 'SQLAlchemy', 'Technology', {'version': '1.4'}),
        
        # 组织实体
        'company': Entity('5', '科技公司', 'Organization', {'size': '500+'}),
        'team_a': Entity('6', '开发团队A', 'Organization', {'members': '10'}),
        'team_b': Entity('7', '开发团队B', 'Organization', {'members': '8'}),
        
        # 人员实体
        'dev1': Entity('8', '张工程师', 'Person', {'role': '全栈开发'}),
        'dev2': Entity('9', '李工程师', 'Person', {'role': '后端开发'}),
        'dev3': Entity('10', '王工程师', 'Person', {'role': '前端开发'}),
        
        # 项目实体
        'project1': Entity('11', '电商平台', 'Project', {
            'status': '进行中',
            'temporal': datetime.now().strftime('%Y-%m-%d')
        }),
        'project2': Entity('12', '数据分析系统', 'Project', {
            'status': '规划中',
            'temporal': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        })
    }
    
    # 创建关系
    relations = [
        # 技术依赖关系
        Relation(source=entities['django'], relation_type='depends_on', target=entities['python'], confidence=0.95, properties={}),
        Relation(source=entities['flask'], relation_type='depends_on', target=entities['python'], confidence=0.95, properties={}),
        Relation(source=entities['django'], relation_type='uses', target=entities['sqlalchemy'], confidence=0.85, properties={}),
        Relation(source=entities['flask'], relation_type='uses', target=entities['sqlalchemy'], confidence=0.85, properties={}),
        
        # 组织关系
        Relation(source=entities['team_a'], relation_type='part_of', target=entities['company'], confidence=1.0, properties={}),
        Relation(source=entities['team_b'], relation_type='part_of', target=entities['company'], confidence=1.0, properties={}),
        
        # 人员关系
        Relation(source=entities['dev1'], relation_type='belongs_to', target=entities['team_a'], confidence=0.9, properties={}),
        Relation(source=entities['dev2'], relation_type='belongs_to', target=entities['team_a'], confidence=0.9, properties={}),
        Relation(source=entities['dev3'], relation_type='belongs_to', target=entities['team_b'], confidence=0.9, properties={}),
        
        # 项目关系
        Relation(source=entities['team_a'], relation_type='manages', target=entities['project1'], confidence=0.95, properties={
            'start_date': '2023-01-01'
        }),
        Relation(source=entities['team_b'], relation_type='manages', target=entities['project2'], confidence=0.8, properties={
            'start_date': '2024-01-01'
        }),
        
        # 技能关系
        Relation(source=entities['dev1'], relation_type='skilled_in', target=entities['python'], confidence=0.9, properties={}),
        Relation(source=entities['dev1'], relation_type='skilled_in', target=entities['django'], confidence=0.85, properties={}),
        Relation(source=entities['dev2'], relation_type='skilled_in', target=entities['python'], confidence=0.95, properties={}),
        Relation(source=entities['dev2'], relation_type='skilled_in', target=entities['flask'], confidence=0.9, properties={}),
        Relation(source=entities['dev3'], relation_type='skilled_in', target=entities['python'], confidence=0.8, properties={}),
        
        # 时序关系
        Relation(source=entities['project1'], relation_type='happens_before', target=entities['project2'], confidence=0.7, properties={}),
        
        # 概率关系
        Relation(source=entities['project1'], relation_type='probably_causes', target=entities['project2'], confidence=0.6, properties={}),
        Relation(source=entities['dev1'], relation_type='likely_related', target=entities['dev2'], confidence=0.5, properties={})
    ]
    
    return relations

def main():
    """主函数"""
    # 生成示例数据
    relations = generate_sample_data()
    
    # 创建可视化器
    visualizer = DomainSpecificVisualizer(
        domain='tech',
        enable_temporal=True,
        enable_probabilistic=True
    )
    
    # 生成可视化
    output_file = os.path.join(os.getcwd(), 'output', f'knowledge_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    visualizer.visualize_domain(
        relations,
        output_file=output_file,
        include_legend=True,
        include_filters=True,
        include_search=True,
        include_export=True
    )

if __name__ == '__main__':
    main()
