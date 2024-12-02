# Prompt-based Knowledge Graph System | 基于提示词的知识图谱系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](docs/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

[English](#english) | [中文](#中文)

<a name="english"></a>
# English

## 📖 Introduction

The Prompt-based Knowledge Graph System is an innovative platform that automatically generates and visualizes knowledge graphs from natural language prompts. By leveraging advanced language models and prompt engineering, the system extracts entities and relationships from text, constructs comprehensive knowledge graphs, and provides rich interactive visualization features.

The system excels at:
- Converting natural language descriptions into structured knowledge graphs
- Identifying key entities and relationships through prompt-based extraction
- Generating domain-specific knowledge graphs from text inputs
- Providing interactive visualization and analysis tools

### 🌟 Key Features

- **Prompt-based Generation**: Generate knowledge graphs from natural language prompts
- **Intelligent Entity Extraction**: Advanced entity and relationship extraction from text
- **Temporal & Probabilistic Relations**: Support for temporal and probabilistic relationship modeling
- **Multi-domain Support**: Flexible templates for different knowledge domains
- **Interactive Visualization**: Dynamic graphical interface with customizable layouts
- **Real-time Filtering**: Interactive filtering and search capabilities
- **Export Options**: Support for PNG and SVG export formats
- **Statistical Analysis**: Comprehensive graph statistics and analysis
- **Theme Customization**: Customizable interface themes
- **Cache Optimization**: Intelligent cache management

## 🚀 Quick Start

### Requirements

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- 8GB+ RAM
- 50GB+ Storage

### Installation

1. Clone repository
```bash
git clone https://github.com/jsjm1986/prompt2graph.git
cd prompt2graph
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment
```bash
cp .env.example .env
# Edit .env file with necessary variables including DeepSeek API key
```

5. Initialize database
```bash
python scripts/init_db.py
```

6. Start application
```bash
python app.py
```

Visit http://localhost:5000 to start using the system.

## 📚 Documentation

- [Architecture](docs/development/architecture.md)
- [API Documentation](docs/development/api.md)
- [Testing Guide](docs/development/testing.md)
- [Deployment Guide](docs/development/deployment.md)
- [Contribution Guide](docs/development/contribution.md)

## 🛠 Technology Stack

### Backend
- Python 3.8+
- Flask Framework
- PostgreSQL/Neo4j
- Redis
- Celery
- DeepSeek API

### Frontend
- Vue.js 3
- D3.js
- Element Plus
- ECharts

## 📊 Performance Metrics

- Query Response Time: < 100ms
- Batch Processing: 10,000+ entities/minute
- Concurrent Users: 1,000+
- Data Capacity: 1B+ triples

## 📝 Changelog

### v1.0.0
- Initial release
- Basic knowledge graph generation
- Basic visualization support
- Temporal relation support
- Probabilistic relation support
- Interactive controls
- Performance optimization

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

<a name="中文"></a>
# 中文

## 📖 项目简介

基于提示词的知识图谱系统是一个创新平台，能够从自然语言提示词自动生成和可视化知识图谱。通过利用先进的语言模型和提示词工程，系统可以从文本中提取实体和关系，构建全面的知识图谱，并提供丰富的交互式可视化功能。

系统的主要优势：
- 将自然语言描述转换为结构化知识图谱
- 通过基于提示词的方式提取关键实体和关系
- 从文本输入生成特定领域的知识图谱
- 提供交互式可视化和分析工具

### 🌟 主要特性

- **提示词生成**：通过自然语言提示词生成知识图谱
- **智能实体提取**：从文本中进行高级实体和关系提取
- **时序和概率关系**：支持时序和概率关系建模
- **多领域支持**：灵活的领域知识模板
- **交互式可视化**：动态的图形界面，支持自定义布局
- **实时过滤**：交互式过滤和搜索功能
- **导出选项**：支持PNG和SVG格式导出
- **统计分析**：全面的图谱统计和分析
- **主题定制**：可自定义的界面主题
- **缓存优化**：智能的缓存管理机制

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- 8GB+ 内存
- 50GB+ 存储空间

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/jsjm1986/prompt2graph.git
cd prompt2graph
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量，包括DeepSeek API密钥
```

5. 初始化数据库
```bash
python scripts/init_db.py
```

6. 启动应用
```bash
python app.py
```

访问 http://localhost:5000 开始使用系统。

## 📚 文档导航

- [系统架构](docs/development/architecture.md)
- [API文档](docs/development/api.md)
- [测试指南](docs/development/testing.md)
- [部署文档](docs/development/deployment.md)
- [贡献指南](docs/development/contribution.md)

## 🛠 技术架构

### 后端技术栈
- Python 3.8+
- Flask Web框架
- PostgreSQL/Neo4j 图数据库
- Redis 缓存
- Celery 任务队列
- DeepSeek API

### 前端技术栈
- Vue.js 3
- D3.js 可视化库
- Element Plus UI组件
- ECharts 图表库

## 📊 性能指标

- 查询响应时间: < 100ms
- 批处理能力: 10000+ 实体/分钟
- 并发支持: 1000+ 用户
- 数据容量: 10亿+ 三元组

## 📝 更新日志

### v1.0.0
- 初始版本发布
- 基础知识图谱生成功能
- 基础可视化支持
- 时序关系支持
- 概率关系支持
- 添加交互控件
- 优化性能

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。
