# InvestNote-py

一个基于 Python 和 FastAPI 开发的投资笔记与分析系统，帮助投资者进行投资决策、分析和追踪。

## 功能特点

- 📊 多市场数据支持（A股、港股、美股）
- 📈 技术分析与指标计算
- 📝 投资笔记与决策记录
- �� 股票筛选与评分系统
- 📊 回测与策略评估
- 📈 可视化分析与报告生成
- 🔔 投资提醒与监控
- 🌐 RESTful API 接口

## 技术栈

- Python 3.7+
- FastAPI + Uvicorn
- SQLite/PostgreSQL
- Pandas + NumPy
- Matplotlib
- AKShare
- Futu API

## 快速开始

### 环境要求

- Python 3.7+
- pip (Python包管理器)
- Node.js (可选，用于前端开发)

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/InvestNote-py.git
cd InvestNote-py
```

2. 创建并激活虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 启动服务：
```bash
python main.py
```

服务将在 http://localhost:8000 启动，API 文档可在 http://localhost:8000/docs 访问。

## 项目结构
InvestNote-py/
├── main.py # FastAPI 服务入口
├── invest_note.py # 命令行/交互入口
├── api.py # API 路由定义
├── requirements.txt # 项目依赖
├── core/ # 核心功能模块
│ ├── handler/ # 数据处理与调度
│ ├── analysis/ # 回测与策略评估
│ ├── strategy/ # 策略实现
│ ├── indicator/ # 技术指标
│ ├── score/ # 评分体系
│ ├── filter/ # 股票过滤器
│ ├── valuation/ # 估值相关
│ ├── enum/ # 枚举类型
│ ├── models/ # 数据模型
│ ├── service/ # 数据库服务
│ └── utils.py # 工具函数
├── output/ # 输出结果
└── tools/ # 辅助工具

## 使用示例

### API 服务

启动 API 服务：
```bash
python main.py --host 0.0.0.0 --port 8000 --reload
```

### 命令行工具

分析股票数据：
```bash
python invest_note.py -a hk 00700  # 分析港股
python invest_note.py -a us AAPL   # 分析美股
```

### 数据库管理

如果遇到数据库锁定问题：
```bash
fuser investnote.db
kill -9 <PID>
```

## 开发指南

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am '添加新功能'`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交 Pull Request

## 许可证

[MIT](LICENSE)