# 配置管理系统

本文档详细说明了知识图谱项目的配置管理系统，包括环境变量管理、配置验证、备份恢复和热重载等功能。

## 目录结构

```
config/
├── environments/           # 环境配置文件
│   ├── development.env
│   ├── staging.env
│   └── production.env
├── secrets/               # 密钥配置文件（不提交到版本控制）
│   ├── development.json
│   ├── staging.json
│   └── production.json
├── backups/              # 配置备份目录
├── env_manager.py        # 环境变量管理器
├── config_validator.py   # 配置验证器
├── config_backup.py      # 配置备份管理器
└── config_reloader.py    # 配置热重载管理器
```

## 环境变量管理

### 基本用法

```python
from config.env_manager import env_manager

# 获取配置值
debug_mode = env_manager.get_bool('APP_DEBUG', False)
max_workers = env_manager.get_int('MAX_WORKERS', 4)
allowed_origins = env_manager.get_list('CORS_ORIGINS')

# 获取数据库配置
db_url = env_manager.get_database_url()

# 获取Redis配置
redis_url = env_manager.get_redis_url()

# 获取存储配置
storage_config = env_manager.get_storage_config()
```

### 支持的数据类型

- 字符串: `get(key, default)`
- 整数: `get_int(key, default)`
- 浮点数: `get_float(key, default)`
- 布尔值: `get_bool(key, default)`
- 列表: `get_list(key, separator=',', default)`
- 字典: `get_dict(key, default)`

## 配置验证

### 验证规则

```python
from config.config_validator import ConfigValidator

validator = ConfigValidator(env_manager)

# 验证所有配置
errors = validator.validate_all()
if errors:
    print("Configuration errors:", errors)

# 验证数据库连接
if not validator.validate_database_connection():
    print("Database connection failed")

# 验证Redis连接
if not validator.validate_redis_connection():
    print("Redis connection failed")
```

### 配置规则定义

```python
CONFIG_RULES = {
    'APP_ENV': ConfigRule(
        required=True,
        allowed_values=['development', 'staging', 'production']
    ),
    'APP_PORT': ConfigRule(
        type=int,
        min_value=1,
        max_value=65535
    ),
    'JWT_SECRET': ConfigRule(
        required=True,
        pattern=r'^[A-Za-z0-9_\-]{32,}$'
    )
}
```

## 配置备份

### 创建备份

```python
from config.config_backup import ConfigBackup

backup_manager = ConfigBackup()

# 创建备份
backup_path = backup_manager.create_backup('production')
if backup_path:
    print(f"Backup created at: {backup_path}")

# 列出所有备份
backups = backup_manager.list_backups()
for backup in backups:
    print(f"Backup: {backup['name']} ({backup['timestamp']})")

# 恢复备份
if backup_manager.restore_backup('production_20230815_120000'):
    print("Backup restored successfully")

# 清理旧备份
backup_manager.cleanup_old_backups(max_backups=10)
```

## 配置热重载

### 基本用法

```python
from config.config_reloader import ConfigReloader

reloader = ConfigReloader(env_manager)

# 启动配置监控
reloader.start()

# 注册配置变更回调
def on_debug_change():
    print("Debug mode changed")

reloader.register_callback('APP_DEBUG', on_debug_change)

# 添加监控路径
reloader.add_watch_path('config/custom')

# 停止配置监控
reloader.stop()
```

## 安全注意事项

1. 密钥管理
   - 所有敏感信息存储在 `secrets/` 目录
   - 确保 `secrets/` 目录已添加到 `.gitignore`
   - 使用环境变量或密钥管理服务存储生产环境密钥

2. 环境隔离
   - 不同环境使用独立的配置文件
   - 生产环境禁用调试模式
   - 限制生产环境的访问来源

3. 配置验证
   - 部署前验证所有必需的配置
   - 验证配置值的有效性
   - 记录配置更改

## 最佳实践

1. 配置管理
   - 使用有意义的配置键名
   - 为所有配置提供合理的默认值
   - 记录所有配置的用途和限制

2. 环境管理
   - 为每个环境维护独立的配置
   - 使用版本控制管理配置模板
   - 定期备份生产环境配置

3. 安全性
   - 加密敏感配置
   - 限制配置访问权限
   - 定期轮换密钥和凭证

4. 可维护性
   - 保持配置文件的组织性
   - 记录配置更改
   - 实现配置热重载
   - 自动化配置验证

## 常见问题

1. 配置未生效
   - 检查环境变量是否正确设置
   - 验证配置文件格式
   - 确认配置加载顺序

2. 密钥泄露
   - 立即轮换受影响的密钥
   - 审查版本控制历史
   - 加强访问控制

3. 性能问题
   - 优化配置加载频率
   - 实现配置缓存
   - 减少配置文件大小

## 配置项说明

### 应用配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| APP_ENV | str | development | 运行环境 |
| APP_DEBUG | bool | False | 调试模式 |
| APP_PORT | int | 8000 | 服务端口 |
| APP_HOST | str | 0.0.0.0 | 服务地址 |

### 数据库配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| DB_HOST | str | localhost | 数据库主机 |
| DB_PORT | int | 5432 | 数据库端口 |
| DB_NAME | str | knowledge_graph | 数据库名称 |
| DB_USER | str | postgres | 数据库用户 |
| DB_PASSWORD | str | | 数据库密码 |

### 缓存配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| REDIS_HOST | str | localhost | Redis主机 |
| REDIS_PORT | int | 6379 | Redis端口 |
| REDIS_DB | int | 0 | Redis数据库 |
| REDIS_PASSWORD | str | | Redis密码 |

### 性能配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| MAX_WORKERS | int | 4 | 最大工作进程数 |
| BATCH_SIZE | int | 1000 | 批处理大小 |
| CACHE_TTL | int | 3600 | 缓存过期时间 |

### 安全配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| JWT_SECRET | str | | JWT密钥 |
| API_RATE_LIMIT | int | 100 | API速率限制 |

## 更新日志

### v0.1.0
- 初始版本
- 实现基本的配置管理功能
- 添加配置验证
- 实现配置备份
- 添加配置热重载
