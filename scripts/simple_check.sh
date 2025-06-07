#!/bin/bash

# 简化版代码质量检查脚本
# 使用方法: ./scripts/simple_check.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 激活虚拟环境
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

echo -e "${BLUE}🔧 简化版代码质量检查${NC}"
echo ""

ISSUES_FOUND=0

# 1. Ruff 检查
echo -e "${BLUE}1. Ruff 代码质量检查...${NC}"
if ! ruff check core/ api/ --output-format=concise; then
    ISSUES_FOUND=1
    echo -e "${RED}❌ Ruff 发现代码质量问题${NC}"
else
    echo -e "${GREEN}✅ Ruff 检查通过${NC}"
fi
echo ""

# 2. MyPy 类型检查 (只检查少数关键文件)
echo -e "${BLUE}2. MyPy 类型检查 (关键文件)...${NC}"
KEY_FILES=(
    "core/handler/ticker_analysis_handler.py"
    "core/models/ticker.py"
    "core/utils/utils.py"
)

for file in "${KEY_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "检查 $file..."
        if ! mypy "$file" --ignore-missing-imports --no-strict-optional 2>/dev/null; then
            ISSUES_FOUND=1
            echo -e "${RED}❌ MyPy 在 $file 中发现类型问题${NC}"
        else
            echo -e "${GREEN}✅ $file 类型检查通过${NC}"
        fi
    fi
done
echo ""

# 3. 安全检查 (只检查关键目录)
echo -e "${BLUE}3. Bandit 安全检查...${NC}"
if ! bandit -r core/auth/ core/database/ -f txt -ll; then
    echo -e "${YELLOW}⚠️ Bandit 发现潜在安全问题${NC}"
else
    echo -e "${GREEN}✅ Bandit 安全检查通过${NC}"
fi
echo ""

# 总结
if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo -e "${GREEN}🎉 简化检查通过！${NC}"
else
    echo -e "${RED}❌ 发现一些问题，请查看上方输出。${NC}"
    echo -e "${YELLOW}💡 运行 'make format' 来自动修复格式问题${NC}"
    exit 1
fi
