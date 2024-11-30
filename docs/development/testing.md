# 测试文档

## 测试架构

### 1. 测试类型

#### 1.1 单元测试
- 测试独立组件功能
- 验证边界条件
- 测试异常处理
- 检查性能要求

#### 1.2 集成测试
- 测试组件交互
- 验证数据流
- 测试配置变更
- 检查资源使用

#### 1.3 性能测试
- 负载测试
- 压力测试
- 并发测试
- 内存使用测试

#### 1.4 端到端测试
- 验证完整流程
- 测试用户场景
- 检查系统集成
- 验证数据一致性

### 2. 测试框架

#### 2.1 单元测试框架
```python
# test_relation_extraction.py
import pytest
from relation_extraction import RelationExtractor

def test_extract_entities():
    extractor = RelationExtractor()
    text = "Python是一种编程语言"
    entities = extractor.extract_entities(text)
    
    assert len(entities) == 2
    assert entities[0].name == "Python"
    assert entities[0].type == "Technology"

@pytest.mark.parametrize("text,expected_count", [
    ("Python和Java是编程语言", 3),
    ("Django是Python的Web框架", 3),
])
def test_extract_entities_parametrized(text, expected_count):
    extractor = RelationExtractor()
    entities = extractor.extract_entities(text)
    assert len(entities) == expected_count
```

#### 2.2 集成测试框架
```python
# test_integration.py
import pytest
from graph_manager import GraphManager
from query_engine import QueryEngine

@pytest.fixture
def graph_manager():
    manager = GraphManager()
    # 设置测试数据
    yield manager
    # 清理测试数据

def test_query_workflow(graph_manager):
    # 创建图谱
    graph = graph_manager.create_graph("test_graph")
    
    # 添加数据
    graph.add_entity(...)
    graph.add_relation(...)
    
    # 执行查询
    query_engine = QueryEngine(graph)
    results = query_engine.execute_query(...)
    
    # 验证结果
    assert len(results) > 0
```

#### 2.3 性能测试框架
```python
# test_performance.py
import pytest
import time
from locust import HttpUser, task, between

class GraphAPIUser(HttpUser):
    wait_time = between(1, 2)
    
    @task
    def query_graph(self):
        self.client.get("/api/v1/graphs/1")
    
    @task
    def search_entities(self):
        self.client.post("/api/v1/search", json={
            "query": "Python",
            "limit": 10
        })

def test_query_performance():
    start_time = time.time()
    # 执行查询
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 1.0  # 确保查询在1秒内完成
```

### 3. 测试数据

#### 3.1 测试数据生成器
```python
# test_data_generator.py
import random
from typing import List
from models import Entity, Relation

class TestDataGenerator:
    def generate_entities(self, count: int) -> List[Entity]:
        entities = []
        for i in range(count):
            entity = Entity(
                id=f"entity_{i}",
                name=f"Test Entity {i}",
                type=random.choice(["Person", "Organization", "Technology"]),
                properties={
                    "created_at": "2024-01-15",
                    "score": random.random()
                }
            )
            entities.append(entity)
        return entities
    
    def generate_relations(self, entities: List[Entity], count: int) -> List[Relation]:
        relations = []
        for i in range(count):
            source = random.choice(entities)
            target = random.choice(entities)
            relation = Relation(
                source=source,
                target=target,
                type=random.choice(["knows", "works_for", "uses"]),
                confidence=random.random(),
                properties={}
            )
            relations.append(relation)
        return relations
```

#### 3.2 测试夹具
```python
# conftest.py
import pytest
from test_data_generator import TestDataGenerator

@pytest.fixture
def test_data():
    generator = TestDataGenerator()
    entities = generator.generate_entities(100)
    relations = generator.generate_relations(entities, 200)
    return {
        "entities": entities,
        "relations": relations
    }

@pytest.fixture
def mock_api_client(requests_mock):
    # 模拟API响应
    requests_mock.get(
        "http://api.example.com/entities",
        json={"entities": [...]}
    )
    return requests_mock
```

### 4. 测试覆盖率

#### 4.1 覆盖率配置
```ini
# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */migrations/*
    
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
```

#### 4.2 覆盖率报告
```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 5. 测试自动化

#### 5.1 CI/CD 配置
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

#### 5.2 预提交钩子
```yaml
# .pre-commit-config.yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v3.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/pytest-dev/pytest
    rev: 6.2.4
    hooks:
    -   id: pytest
        args: [tests/]
```

### 6. 测试最佳实践

#### 6.1 测试原则
- 测试应该是独立的
- 测试应该是可重复的
- 测试应该是简单的
- 测试应该是有意义的

#### 6.2 命名约定
```python
# 函数测试
def test_should_extract_entities_from_text():
    pass

# 类测试
class TestRelationExtractor:
    def test_should_initialize_with_default_config(self):
        pass
    
    def test_should_raise_error_for_invalid_input(self):
        pass
```

#### 6.3 测试组织
```
tests/
├── unit/
│   ├── test_relation_extraction.py
│   ├── test_query_engine.py
│   └── test_graph_analysis.py
├── integration/
│   ├── test_workflow.py
│   └── test_api.py
├── performance/
│   ├── test_load.py
│   └── test_stress.py
└── conftest.py
```

### 7. 测试监控

#### 7.1 测试指标
- 测试通过率
- 代码覆盖率
- 测试执行时间
- 测试稳定性

#### 7.2 测试报告
```python
# test_reporter.py
class TestReporter:
    def generate_report(self, results):
        report = {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.passed),
            "failed_tests": sum(1 for r in results if not r.passed),
            "execution_time": sum(r.duration for r in results),
            "coverage": self.calculate_coverage(results)
        }
        return report
    
    def export_report(self, report, format="html"):
        if format == "html":
            self.export_html_report(report)
        elif format == "json":
            self.export_json_report(report)
```

### 8. 故障排除

#### 8.1 常见问题
1. 测试失败
   - 检查测试环境
   - 验证测试数据
   - 检查依赖版本
   
2. 性能问题
   - 优化测试数据
   - 调整超时设置
   - 检查资源使用

#### 8.2 调试技巧
```python
# 使用 pytest 调试
pytest --pdb

# 使用日志调试
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_with_logging():
    logger.debug("Starting test")
    # 测试代码
    logger.debug("Test completed")
```
