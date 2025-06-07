#!/bin/bash

# 快速单文件代码质量检查脚本
# 使用方法: ./scripts/quick_check.sh <文件路径>

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [[ $# -eq 0 ]]; then
    echo "使用方法: $0 <文件路径>"
    echo "示例: $0 core/handler/ticker_analysis_handler.py"
    exit 1
fi

FILE_PATH="$1"

if [[ ! -f "$FILE_PATH" ]]; then
    echo -e "${RED}错误: 文件 '$FILE_PATH' 不存在${NC}"
    exit 1
fi

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 激活虚拟环境
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

echo -e "${BLUE}🔧 快速检查文件: $FILE_PATH${NC}"
echo ""

ISSUES_FOUND=0

# 1. Black 格式检查
echo -e "${BLUE}1. Black 格式检查...${NC}"
if ! black "$FILE_PATH" --check --diff --color; then
    ISSUES_FOUND=1
    echo -e "${RED}❌ Black 发现格式问题${NC}"
    echo -e "${YELLOW}💡 运行 'black $FILE_PATH' 来修复${NC}"
else
    echo -e "${GREEN}✅ Black 格式正确${NC}"
fi
echo ""

# 2. isort 导入检查
echo -e "${BLUE}2. isort 导入顺序检查...${NC}"
if ! isort "$FILE_PATH" --check-only --diff --color; then
    ISSUES_FOUND=1
    echo -e "${RED}❌ isort 发现导入顺序问题${NC}"
    echo -e "${YELLOW}💡 运行 'isort $FILE_PATH' 来修复${NC}"
else
    echo -e "${GREEN}✅ 导入顺序正确${NC}"
fi
echo ""

# 3. Ruff 检查
echo -e "${BLUE}3. Ruff 代码质量检查...${NC}"
if ! ruff check "$FILE_PATH"; then
    ISSUES_FOUND=1
    echo -e "${RED}❌ Ruff 发现代码质量问题${NC}"
    echo -e "${YELLOW}💡 运行 'ruff check $FILE_PATH --fix' 来自动修复${NC}"
else
    echo -e "${GREEN}✅ Ruff 检查通过${NC}"
fi
echo ""

# 4. MyPy 类型检查
echo -e "${BLUE}4. MyPy 类型检查...${NC}"
if ! mypy "$FILE_PATH" --ignore-missing-imports; then
    ISSUES_FOUND=1
    echo -e "${RED}❌ MyPy 发现类型问题${NC}"
else
    echo -e "${GREEN}✅ MyPy 类型检查通过${NC}"
fi
echo ""

# 总结
if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo -e "${GREEN}🎉 文件检查通过！代码质量良好。${NC}"
else
    echo -e "${RED}❌ 发现代码质量问题，请查看上方输出。${NC}"
    echo ""
    echo -e "${YELLOW}💡 快速修复命令:${NC}"
    echo "black $FILE_PATH"
    echo "isort $FILE_PATH" 
    echo "ruff check $FILE_PATH --fix"
    exit 1
fi
