# InvestNote-py

一个用Python开发的投资笔记应用，帮助投资者记录、分析和追踪投资决策和结果。

## 功能特点

- 记录投资笔记和想法
- 跟踪投资组合表现
- 分析历史交易数据
- 生成投资报告和图表
- 设置投资提醒和警报

## 安装

### 前提条件

- Python 3.7+
- pip (Python包管理器)

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/InvestNote-py.git
cd InvestNote-py
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用: venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

### 功能


### 示例

分析腾讯控股的股票数据:
```bash
python main.py -a hk 00700
```

添加苹果公司到投资组合:
```bash
python main.py -add us AAPL
```

## 项目结构

```
InvestNote-py/
├── main.py               # 应用入口点
├── investNote.py         # 旧版入口脚本(已弃用)
├── requirements.txt      # 项目依赖
├── core/                 # 核心功能模块
│   ├── API/              # API接口
│   ├── Enum/             # 枚举类型定义
│   ├── Handler/          # 数据处理模块
│   ├── Valuation/        # 估值模块
│   └── utils/            # 工具函数
├── custom/               # 自定义模块
│   ├── TickerScoreFilter.py
│   └── TickerHighValuation.py
├── data/                 # 数据存储
└── output/               # 输出结果
```

## 贡献指南

1. Fork 仓库
2. 创建功能分支：`git checkout -b my-new-feature`
3. 提交更改：`git commit -am '添加某功能'`
4. 推送到分支：`git push origin my-new-feature`
5. 提交Pull Request

## 许可证

[MIT](LICENSE)
