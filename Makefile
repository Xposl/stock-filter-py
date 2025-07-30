# InvestNote-py 项目 Makefile

.PHONY: help install dev-setup format check test clean lint security docs quick simple-check

# 默认目标
help:
	@echo "InvestNote-py 项目开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install     - 安装项目依赖"
	@echo "  dev-setup   - 配置开发环境（包含git hooks）"
	@echo "  format      - 自动格式化代码"
	@echo "  check       - 代码质量检查"
	@echo "  simple-check - 简化版代码质量检查"
	@echo "  quick FILE  - 快速检查单个文件"
	@echo "  lint        - 运行所有linter"
	@echo "  security    - 安全检查"
	@echo "  test        - 运行测试"
	@echo "  clean       - 清理临时文件"
	@echo "  docs        - 生成文档"
	@echo ""
	@echo "示例:"
	@echo "  make format"
	@echo "  make check"
	@echo "  make quick FILE=core/handler/ticker_analysis_handler.py"

# 安装依赖
install:
	@echo "📦 安装项目依赖..."
	pip install -r requirements.txt

# 开发环境设置
dev-setup: install
	@echo "🔧 配置开发环境..."
	pre-commit install
	@echo "✅ 开发环境配置完成"

# 代码格式化
format:
	@echo "🎨 格式化代码..."
	black core/ api/
	isort core/ api/
	autopep8 --in-place --recursive --aggressive --aggressive core/ api/
	@echo "✅ 代码格式化完成"

# 代码质量检查
check:
	@echo "🔍 运行代码质量检查..."
	./scripts/code_quality.sh check

# 简化版代码质量检查
simple-check:
	@echo "🔍 运行简化版代码质量检查..."
	./scripts/simple_check.sh

# 快速检查单个文件
quick:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ 请指定文件: make quick FILE=path/to/file.py"; \
		exit 1; \
	fi
	@echo "⚡ 快速检查文件: $(FILE)"
	./scripts/quick_check.sh $(FILE)

# Lint检查
lint:
	@echo "🔎 运行Lint检查..."
	ruff check core/ api/
	mypy core/ api/ --ignore-missing-imports
	pylint core/ api/ || true

# 安全检查  
security:
	@echo "🔒 运行安全检查..."
	bandit -r core/ api/
	@echo "⚠️  Safety 暂时禁用，与packaging版本冲突"

# 测试
test:
	@echo "🧪 运行测试..."
	python -m pytest tests/ -v --cov=core --cov=api --cov-report=html --cov-report=term

# 清理
clean:
	@echo "🧹 清理临时文件..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete  
	find . -type f -name "*~" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf build/ dist/
	@echo "✅ 清理完成"

# 文档生成
docs:
	@echo "📚 生成文档..."
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html docs/ docs/_build/html; \
	else \
		echo "⚠️  Sphinx未安装，跳过文档生成"; \
	fi

# CI流水线检查
ci-check: format lint security
	@echo "🚀 CI检查完成"

# 本地开发检查（较宽松）
dev-check:
	@echo "💻 开发环境检查..."
	black core/ api/ --check || echo "⚠️  建议运行 make format"
	ruff check core/ api/ || echo "⚠️  发现代码质量问题"
	mypy core/ api/ --ignore-missing-imports || echo "⚠️  发现类型问题"
