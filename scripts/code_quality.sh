#!/bin/bash

# 代码质量检查脚本
# 使用方法: ./scripts/code_quality.sh [fix|check]

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

# 检查虚拟环境
if [[ ! -d "venv" ]]; then
    echo -e "${RED}错误: 虚拟环境不存在${NC}"
    echo "请运行: python -m venv venv && source venv/bin/activate"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

MODE=${1:-check}

echo -e "${BLUE}🔧 Python代码质量检查工具${NC}"
echo "模式: $MODE"
echo "项目根目录: $PROJECT_ROOT"
echo ""

# 创建输出目录
mkdir -p reports

case $MODE in
    "fix")
        echo -e "${YELLOW}🔧 自动修复模式${NC}"
        echo ""
        
        # 1. Black 格式化
        echo -e "${BLUE}1. 使用 Black 格式化代码...${NC}"
        black core/ api/ --diff --color
        black core/ api/
        
        # 2. isort 导入排序
        echo -e "${BLUE}2. 使用 isort 排序导入...${NC}"
        isort core/ api/ --diff --color
        isort core/ api/
        
        # 3. autopep8 自动修复
        echo -e "${BLUE}3. 使用 autopep8 修复 PEP8 问题...${NC}"
        autopep8 --in-place --recursive --aggressive --aggressive core/ api/
        
        # 4. Ruff 自动修复
        echo -e "${BLUE}4. 使用 Ruff 自动修复...${NC}"
        ruff check core/ api/ --fix
        
        echo -e "${GREEN}✅ 自动修复完成${NC}"
        ;;
        
    "check")
        echo -e "${YELLOW}🔍 检查模式${NC}"
        echo ""
        
        ISSUES_FOUND=0
        
        # 1. Black 检查
        echo -e "${BLUE}1. Black 格式检查...${NC}"
        if ! black core/ api/ --check --diff; then
            ISSUES_FOUND=1
            echo -e "${RED}❌ Black 发现格式问题${NC}"
        else
            echo -e "${GREEN}✅ Black 检查通过${NC}"
        fi
        echo ""
        
        # 2. isort 检查
        echo -e "${BLUE}2. isort 导入检查...${NC}"
        if ! isort core/ api/ --check-only --diff; then
            ISSUES_FOUND=1
            echo -e "${RED}❌ isort 发现导入顺序问题${NC}"
        else
            echo -e "${GREEN}✅ isort 检查通过${NC}"
        fi
        echo ""
        
        # 3. Ruff 检查
        echo -e "${BLUE}3. Ruff 代码质量检查...${NC}"
        if ! ruff check core/ api/ --output-format=github > reports/ruff_report.txt; then
            ISSUES_FOUND=1
            echo -e "${RED}❌ Ruff 发现代码质量问题${NC}"
            cat reports/ruff_report.txt
        else
            echo -e "${GREEN}✅ Ruff 检查通过${NC}"
        fi
        echo ""
        
        # 4. MyPy 类型检查
        echo -e "${BLUE}4. MyPy 类型检查...${NC}"
        if ! mypy core/ api/ --ignore-missing-imports > reports/mypy_report.txt 2>&1; then
            ISSUES_FOUND=1
            echo -e "${RED}❌ MyPy 发现类型问题${NC}"
            cat reports/mypy_report.txt
        else
            echo -e "${GREEN}✅ MyPy 检查通过${NC}"
        fi
        echo ""
        
        # 5. Bandit 安全检查
        echo -e "${BLUE}5. Bandit 安全检查...${NC}"
        if ! bandit -r core/ api/ -f json -o reports/bandit_report.json; then
            ISSUES_FOUND=1
            echo -e "${RED}❌ Bandit 发现安全问题${NC}"
            bandit -r core/ api/ -f txt
        else
            echo -e "${GREEN}✅ Bandit 安全检查通过${NC}"
        fi
        echo ""
        
        # 6. Vulture 死代码检查
        echo -e "${BLUE}6. Vulture 死代码检查...${NC}"
        if vulture core/ api/ --min-confidence 60 > reports/vulture_report.txt; then
            if [[ -s reports/vulture_report.txt ]]; then
                ISSUES_FOUND=1
                echo -e "${RED}❌ Vulture 发现死代码${NC}"
                cat reports/vulture_report.txt
            else
                echo -e "${GREEN}✅ Vulture 检查通过${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ Vulture 检查完成，可能有警告${NC}"
        fi
        echo ""
        
        # 7. Safety 依赖安全检查
        echo -e "${BLUE}7. Safety 依赖安全检查...${NC}"
        if ! safety check --json --output reports/safety_report.json; then
            ISSUES_FOUND=1
            echo -e "${RED}❌ Safety 发现安全漏洞${NC}"
            safety check
        else
            echo -e "${GREEN}✅ Safety 安全检查通过${NC}"
        fi
        echo ""
        
        # 8. Pylint 综合检查
        echo -e "${BLUE}8. Pylint 综合代码质量检查...${NC}"
        if ! pylint core/ api/ --output-format=json --reports=yes > reports/pylint_report.json 2>&1; then
            echo -e "${YELLOW}⚠️ Pylint 发现一些问题${NC}"
            pylint core/ api/ --output-format=text | head -20
        else
            echo -e "${GREEN}✅ Pylint 检查通过${NC}"
        fi
        echo ""
        
        # 9. pydocstyle 文档字符串检查
        echo -e "${BLUE}9. pydocstyle 文档检查...${NC}"
        if ! pydocstyle core/ api/ --convention=google > reports/pydocstyle_report.txt; then
            echo -e "${YELLOW}⚠️ pydocstyle 发现文档问题${NC}"
            cat reports/pydocstyle_report.txt | head -20
        else
            echo -e "${GREEN}✅ pydocstyle 检查通过${NC}"
        fi
        echo ""
        
        # 总结
        if [[ $ISSUES_FOUND -eq 0 ]]; then
            echo -e "${GREEN}🎉 所有检查通过！代码质量良好。${NC}"
        else
            echo -e "${RED}❌ 发现代码质量问题，请查看上方输出或 reports/ 目录中的详细报告。${NC}"
            echo -e "${YELLOW}💡 提示: 运行 './scripts/code_quality.sh fix' 来自动修复部分问题${NC}"
            exit 1
        fi
        ;;
        
    *)
        echo "使用方法: $0 [fix|check]"
        echo "  fix   - 自动修复可修复的问题"
        echo "  check - 仅检查不修复（默认）"
        exit 1
        ;;
esac
