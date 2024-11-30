# 部署文档

## 部署架构

### 1. 系统要求

#### 1.1 硬件要求
- CPU: 4核心及以上
- 内存: 8GB及以上
- 存储: 50GB及以上
- 网络: 100Mbps及以上

#### 1.2 软件要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx 1.18+

### 2. 环境配置

#### 2.1 Python环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 数据库配置
```sql
-- 创建数据库
CREATE DATABASE knowledge_graph;

-- 创建用户
CREATE USER kg_user WITH PASSWORD 'your_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE knowledge_graph TO kg_user;
```

#### 2.3 Redis配置
```bash
# 编辑Redis配置
vim /etc/redis/redis.conf

# 主要配置项
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
```

### 3. 应用部署

#### 3.1 使用Docker
```dockerfile
# Dockerfile
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV APP_ENV=production

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
    networks:
      - kg_network

  db:
    image: postgres:12
    environment:
      - POSTGRES_DB=knowledge_graph
      - POSTGRES_USER=kg_user
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - kg_network

  redis:
    image: redis:6
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - kg_network

networks:
  kg_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

#### 3.2 使用Kubernetes
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-graph
spec:
  replicas: 3
  selector:
    matchLabels:
      app: knowledge-graph
  template:
    metadata:
      labels:
        app: knowledge-graph
    spec:
      containers:
      - name: web
        image: knowledge-graph:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: production
        - name: DB_HOST
          value: postgres-service
        - name: REDIS_HOST
          value: redis-service
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4. 负载均衡

#### 4.1 Nginx配置
```nginx
# /etc/nginx/conf.d/knowledge-graph.conf
upstream knowledge_graph {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://knowledge_graph;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/static/;
        expires 30d;
    }

    location /api/ {
        proxy_pass http://knowledge_graph;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

### 5. 监控配置

#### 5.1 Prometheus配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'knowledge-graph'
    static_configs:
      - targets: ['localhost:8000']
```

#### 5.2 Grafana仪表板
```json
{
  "dashboard": {
    "title": "Knowledge Graph Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "http_request_duration_seconds"
          }
        ]
      }
    ]
  }
}
```

### 6. 备份策略

#### 6.1 数据库备份
```bash
#!/bin/bash
# backup.sh

# 设置变量
BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="knowledge_graph"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/backup_$DATE.sql

# 删除旧备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

#### 6.2 应用数据备份
```python
# backup_manager.py
import shutil
import os
from datetime import datetime

class BackupManager:
    def __init__(self, backup_dir="/backup/app"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
        
        # 备份数据目录
        shutil.copytree("data", backup_path)
        
        # 压缩备份
        shutil.make_archive(backup_path, 'zip', backup_path)
        
        # 删除临时目录
        shutil.rmtree(backup_path)
        
    def cleanup_old_backups(self, days=7):
        # 删除旧备份
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.getctime(item_path) < days * 86400:
                os.remove(item_path)
```

### 7. 安全配置

#### 7.1 SSL配置
```nginx
# SSL configuration
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
}
```

#### 7.2 防火墙配置
```bash
# UFW配置
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

### 8. 日志管理

#### 8.1 日志配置
```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### 9. 性能优化

#### 9.1 数据库优化
```sql
-- 数据库优化配置
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET work_mem = '32MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';

-- 创建索引
CREATE INDEX idx_entity_type ON entities(type);
CREATE INDEX idx_relation_type ON relations(type);
```

#### 9.2 缓存配置
```python
# cache_config.py
CACHING_CONFIG = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    }
}
```

### 10. 故障恢复

#### 10.1 数据库恢复
```bash
#!/bin/bash
# restore.sh

# 设置变量
BACKUP_FILE=$1
DB_NAME="knowledge_graph"

# 停止应用
systemctl stop knowledge-graph

# 删除现有数据库
dropdb $DB_NAME

# 创建新数据库
createdb $DB_NAME

# 恢复数据
gunzip -c $BACKUP_FILE | psql $DB_NAME

# 启动应用
systemctl start knowledge-graph
```

#### 10.2 应用恢复
```python
# recovery_manager.py
class RecoveryManager:
    def __init__(self):
        self.backup_manager = BackupManager()
        
    def restore_from_backup(self, backup_file):
        # 停止应用
        self.stop_application()
        
        # 解压备份
        with zipfile.ZipFile(backup_file, 'r') as zip_ref:
            zip_ref.extractall('data')
            
        # 启动应用
        self.start_application()
        
    def stop_application(self):
        # 实现应用停止逻辑
        pass
        
    def start_application(self):
        # 实现应用启动逻辑
        pass
```

### 11. 部署检查清单

#### 11.1 部署前检查
- [ ] 代码审查完成
- [ ] 测试通过
- [ ] 数据库备份
- [ ] 配置文件检查
- [ ] 依赖版本检查

#### 11.2 部署后检查
- [ ] 服务状态检查
- [ ] 日志检查
- [ ] 监控系统检查
- [ ] 性能测试
- [ ] 安全检查
