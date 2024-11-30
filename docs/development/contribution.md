# 贡献指南

## 开发流程

### 1. 分支管理

#### 1.1 分支命名
- 主分支: `main`
- 开发分支: `dev`
- 功能分支: `feature/功能名称`
- 修复分支: `fix/问题描述`
- 发布分支: `release/版本号`

#### 1.2 工作流程
1. 从 `dev` 分支创建功能分支
2. 在功能分支上开发
3. 提交 Pull Request 到 `dev` 分支
4. 代码审查
5. 合并到 `dev` 分支
6. 定期将 `dev` 合并到 `main`

### 2. 提交规范

#### 2.1 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 2.2 Type 类型
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

#### 2.3 示例
```
feat(graph): 添加时序关系支持

- 实现时序关系数据结构
- 添加时序查询接口
- 更新可视化组件

Closes #123
```

### 3. 代码规范

#### 3.1 Python代码规范
```python
# 类定义
class GraphManager:
    """图谱管理器类
    
    负责处理图谱的创建、更新和删除操作。
    
    Attributes:
        graph_type (str): 图谱类型
        config (dict): 配置信息
    """
    
    def __init__(self, graph_type: str, config: dict):
        """初始化图谱管理器
        
        Args:
            graph_type (str): 图谱类型
            config (dict): 配置信息
        """
        self.graph_type = graph_type
        self.config = config
        
    def create_graph(self, name: str) -> bool:
        """创建新图谱
        
        Args:
            name (str): 图谱名称
            
        Returns:
            bool: 是否创建成功
        
        Raises:
            ValueError: 当图谱名称无效时
        """
        if not name:
            raise ValueError("图谱名称不能为空")
        # 实现创建逻辑
        return True
```

#### 3.2 JavaScript代码规范
```javascript
// 组件定义
class GraphVisualizer {
  /**
   * 创建图谱可视化器
   * @param {string} containerId - 容器ID
   * @param {Object} options - 可视化选项
   */
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.options = {
      width: 800,
      height: 600,
      ...options
    };
    
    this.init();
  }
  
  /**
   * 初始化可视化器
   * @private
   */
  init() {
    // 实现初始化逻辑
  }
  
  /**
   * 更新可视化
   * @param {Object} data - 图谱数据
   * @returns {boolean} 是否更新成功
   */
  update(data) {
    if (!data) {
      console.error('数据不能为空');
      return false;
    }
    // 实现更新逻辑
    return true;
  }
}
```

### 4. 文档规范

#### 4.1 文档结构
```
docs/
├── api/                # API文档
│   ├── overview.md
│   └── endpoints/
├── development/        # 开发文档
│   ├── setup.md
│   └── guidelines.md
└── user/              # 用户文档
    ├── getting-started.md
    └── tutorials/
```

#### 4.2 文档模板
```markdown
# 模块名称

## 功能描述

简要描述模块的主要功能和用途。

## 安装方法

详细说明如何安装和配置该模块。

## 使用方法

### 基础用法
提供基本的使用示例。

### 高级特性
说明更高级的功能和用法。

## API参考

### 类/方法
详细说明每个公开的类和方法。

## 注意事项

列出使用时需要注意的问题。

## 更新日志

记录重要的更新内容。
```

### 5. 测试规范

#### 5.1 单元测试
```python
# test_graph_manager.py
import pytest
from graph_manager import GraphManager

class TestGraphManager:
    @pytest.fixture
    def graph_manager(self):
        config = {"type": "test"}
        return GraphManager("test", config)
    
    def test_create_graph(self, graph_manager):
        """测试创建图谱"""
        # 准备测试数据
        name = "test_graph"
        
        # 执行测试
        result = graph_manager.create_graph(name)
        
        # 验证结果
        assert result is True
        
    def test_create_graph_with_empty_name(self, graph_manager):
        """测试使用空名称创建图谱"""
        with pytest.raises(ValueError):
            graph_manager.create_graph("")
```

#### 5.2 集成测试
```python
# test_integration.py
import pytest
from graph_manager import GraphManager
from query_engine import QueryEngine

@pytest.mark.integration
class TestGraphIntegration:
    def test_create_and_query(self):
        """测试创建图谱并查询"""
        # 创建图谱
        manager = GraphManager("test", {})
        manager.create_graph("test_graph")
        
        # 执行查询
        engine = QueryEngine()
        results = engine.query("test_graph", "test_query")
        
        # 验证结果
        assert len(results) > 0
```

### 6. 代码审查

#### 6.1 审查清单
- [ ] 代码符合规范
- [ ] 测试覆盖充分
- [ ] 文档完整准确
- [ ] 性能符合要求
- [ ] 安全性考虑周全

#### 6.2 审查流程
1. 提交代码审查请求
2. 指派审查人员
3. 审查人员提供反馈
4. 开发者进行修改
5. 审查人员确认修改
6. 合并代码

### 7. 发布流程

#### 7.1 版本号规范
- 主版本号: 不兼容的API修改
- 次版本号: 向下兼容的功能性新增
- 修订号: 向下兼容的问题修正

#### 7.2 发布步骤
1. 创建发布分支
2. 更新版本号
3. 更新文档
4. 执行测试
5. 创建标签
6. 合并到主分支
7. 部署新版本

### 8. 问题报告

#### 8.1 Bug报告模板
```markdown
## 问题描述

详细描述遇到的问题。

## 复现步骤

1. 第一步
2. 第二步
3. ...

## 预期结果

描述期望的正确结果。

## 实际结果

描述实际观察到的结果。

## 环境信息

- 操作系统:
- Python版本:
- 项目版本:
```

#### 8.2 功能请求模板
```markdown
## 功能描述

详细描述需要的功能。

## 使用场景

描述该功能的使用场景。

## 实现建议

提供可能的实现方案。

## 补充信息

其他相关信息。
```

### 9. 持续集成

#### 9.1 CI配置
```yaml
# .github/workflows/ci.yml
name: CI

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
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest
    
    - name: Run linting
      run: flake8
```

### 10. 社区互动

#### 10.1 行为准则
- 尊重所有贡献者
- 友善交流
- 专注于技术讨论
- 欢迎建设性意见

#### 10.2 贡献方式
- 提交代码
- 改进文档
- 报告问题
- 回答问题
- 参与讨论
