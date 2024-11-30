# API 文档

## RESTful API

### 1. 图谱管理

#### 1.1 创建图谱
```http
POST /api/v1/graphs
Content-Type: application/json

{
    "name": "示例图谱",
    "description": "这是一个示例知识图谱",
    "domain": "technology",
    "config": {
        "enable_temporal": true,
        "enable_probabilistic": true
    }
}
```

响应：
```json
{
    "graph_id": "graph_123",
    "created_at": "2024-01-15T10:30:00Z",
    "status": "created"
}
```

#### 1.2 更新图谱
```http
PUT /api/v1/graphs/{graph_id}
Content-Type: application/json

{
    "name": "更新后的图谱名称",
    "description": "更新后的描述"
}
```

#### 1.3 删除图谱
```http
DELETE /api/v1/graphs/{graph_id}
```

#### 1.4 获取图谱信息
```http
GET /api/v1/graphs/{graph_id}
```

### 2. 实体管理

#### 2.1 添加实体
```http
POST /api/v1/graphs/{graph_id}/entities
Content-Type: application/json

{
    "id": "entity_1",
    "name": "Python",
    "type": "Technology",
    "properties": {
        "version": "3.8",
        "release_date": "2019-10-14"
    }
}
```

#### 2.2 批量添加实体
```http
POST /api/v1/graphs/{graph_id}/entities/batch
Content-Type: application/json

{
    "entities": [
        {
            "id": "entity_1",
            "name": "Python",
            "type": "Technology"
        },
        {
            "id": "entity_2",
            "name": "Django",
            "type": "Framework"
        }
    ]
}
```

#### 2.3 更新实体
```http
PUT /api/v1/graphs/{graph_id}/entities/{entity_id}
Content-Type: application/json

{
    "name": "Python",
    "properties": {
        "version": "3.9"
    }
}
```

### 3. 关系管理

#### 3.1 添加关系
```http
POST /api/v1/graphs/{graph_id}/relations
Content-Type: application/json

{
    "source": "entity_1",
    "target": "entity_2",
    "type": "depends_on",
    "confidence": 0.95,
    "properties": {
        "since": "2024-01-01"
    }
}
```

#### 3.2 批量添加关系
```http
POST /api/v1/graphs/{graph_id}/relations/batch
Content-Type: application/json

{
    "relations": [
        {
            "source": "entity_1",
            "target": "entity_2",
            "type": "depends_on"
        },
        {
            "source": "entity_2",
            "target": "entity_3",
            "type": "uses"
        }
    ]
}
```

### 4. 查询接口

#### 4.1 图谱查询
```http
POST /api/v1/graphs/{graph_id}/query
Content-Type: application/json

{
    "query": "MATCH (n:Technology)-[r:depends_on]->(m) RETURN n, r, m",
    "limit": 10,
    "offset": 0
}
```

#### 4.2 路径查询
```http
POST /api/v1/graphs/{graph_id}/paths
Content-Type: application/json

{
    "source": "entity_1",
    "target": "entity_2",
    "max_depth": 3
}
```

### 5. 分析接口

#### 5.1 图谱统计
```http
GET /api/v1/graphs/{graph_id}/statistics
```

响应：
```json
{
    "entity_count": 100,
    "relation_count": 150,
    "entity_types": {
        "Technology": 30,
        "Framework": 20
    },
    "relation_types": {
        "depends_on": 50,
        "uses": 100
    }
}
```

#### 5.2 中心度分析
```http
POST /api/v1/graphs/{graph_id}/centrality
Content-Type: application/json

{
    "algorithm": "pagerank",
    "params": {
        "alpha": 0.85,
        "max_iter": 100
    }
}
```

### 6. 可视化接口

#### 6.1 获取可视化数据
```http
GET /api/v1/graphs/{graph_id}/visualization
```

#### 6.2 更新可视化配置
```http
PUT /api/v1/graphs/{graph_id}/visualization/config
Content-Type: application/json

{
    "layout": "force",
    "node_size": 30,
    "edge_width": 2,
    "show_labels": true
}
```

## WebSocket API

### 1. 实时更新

#### 1.1 订阅图谱更新
```javascript
// 连接 WebSocket
const ws = new WebSocket('ws://api.example.com/ws/graphs/{graph_id}');

// 订阅更新
ws.send(JSON.stringify({
    "action": "subscribe",
    "events": ["entity_added", "relation_added"]
}));

// 接收更新
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received update:', data);
};
```

#### 1.2 图谱编辑
```javascript
// 发送编辑操作
ws.send(JSON.stringify({
    "action": "edit",
    "operation": "add_entity",
    "data": {
        "id": "entity_1",
        "name": "Python",
        "type": "Technology"
    }
}));
```

## GraphQL API

### 1. 查询示例

```graphql
query {
  graph(id: "graph_123") {
    name
    description
    entities {
      id
      name
      type
      properties
    }
    relations {
      source {
        id
        name
      }
      target {
        id
        name
      }
      type
      confidence
    }
  }
}
```

### 2. 变更示例

```graphql
mutation {
  addEntity(
    graphId: "graph_123"
    input: {
      name: "Python"
      type: "Technology"
      properties: {
        version: "3.8"
      }
    }
  ) {
    id
    name
    type
  }
}
```

## 错误处理

### 1. 错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式和值 |
| 401 | 未授权 | 检查认证信息 |
| 403 | 禁止访问 | 检查权限设置 |
| 404 | 资源不存在 | 检查资源ID是否正确 |
| 429 | 请求过于频繁 | 降低请求频率 |
| 500 | 服务器错误 | 联系技术支持 |

### 2. 错误响应格式

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {
            "field": "错误字段",
            "reason": "具体原因"
        }
    }
}
```

## 认证和授权

### 1. API 密钥认证
```http
GET /api/v1/graphs
Authorization: Bearer your_api_key
```

### 2. OAuth2 认证
```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=your_client_id
&client_secret=your_client_secret
```

## 速率限制

- 基本限制：100次/分钟
- 批量操作：10次/分钟
- 分析接口：5次/分钟

超出限制时响应：
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

## 版本控制

- 当前版本：v1
- URL 格式：`/api/v{version}/...`
- 支持版本：v1, v2 (beta)

## 最佳实践

### 1. 查询优化
- 使用适当的查询限制
- 选择合适的查询深度
- 利用缓存机制
- 避免复杂嵌套查询

### 2. 批量操作
- 使用批量接口处理大量数据
- 控制每批数据大小
- 实现错误重试机制
- 记录操作日志

### 3. 错误处理
- 实现请求重试
- 记录错误信息
- 设置超时处理
- 优雅降级策略
