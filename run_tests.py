#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试运行脚本
提供便捷的测试执行命令
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """运行命令并输出描述"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"执行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n✅ {description} - 成功")
    else:
        print(f"\n❌ {description} - 失败 (退出码: {result.returncode})")
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="InvestNote-py 测试运行器")
    parser.add_argument("--type", "-t", 
                       choices=["unit", "integration", "api", "slow", "debug", "all"],
                       default="all",
                       help="测试类型")
    parser.add_argument("--coverage", "-c", action="store_true",
                       help="生成覆盖率报告")
    parser.add_argument("--html-coverage", action="store_true",
                       help="生成HTML覆盖率报告")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")
    parser.add_argument("--file", "-f", 
                       help="运行特定测试文件")
    parser.add_argument("--function", "-fn",
                       help="运行特定测试函数")
    parser.add_argument("--markers", "-m",
                       help="自定义pytest标记")
    parser.add_argument("--install-deps", action="store_true",
                       help="安装测试依赖")
    
    args = parser.parse_args()
    
    # 确保在项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 InvestNote-py 测试运行器")
    print(f"📁 工作目录: {project_root}")
    
    # 安装测试依赖
    if args.install_deps:
        deps_cmd = [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "pytest-cov"]
        if not run_command(deps_cmd, "安装测试依赖"):
            return 1
    
    # 构建pytest命令
    cmd = [sys.executable, "-m", "pytest"]
    
    # 添加详细输出
    if args.verbose:
        cmd.append("-v")
    
    # 添加覆盖率
    if args.coverage or args.html_coverage:
        cmd.extend(["--cov=core", "--cov=api"])
        if args.html_coverage:
            cmd.append("--cov-report=html")
    
    # 添加测试类型标记
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
        description = "运行单元测试"
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
        description = "运行集成测试"
    elif args.type == "api":
        cmd.extend(["-m", "api"])
        description = "运行API测试"
    elif args.type == "slow":
        cmd.extend(["-m", "slow", "--run-slow"])
        description = "运行慢速测试"
    elif args.type == "debug":
        cmd.extend(["-m", "debug"])
        description = "运行调试测试"
    else:
        description = "运行所有测试"
    
    # 自定义标记
    if args.markers:
        cmd.extend(["-m", args.markers])
        description = f"运行标记为 '{args.markers}' 的测试"
    
    # 特定文件
    if args.file:
        cmd.append(args.file)
        description = f"运行文件 {args.file} 中的测试"
    
    # 特定函数
    if args.function:
        if not args.file:
            print("❌ 错误: 指定函数时必须同时指定文件 (--file)")
            return 1
        cmd[-1] = f"{args.file}::{args.function}"
        description = f"运行函数 {args.function}"
    
    # 运行测试
    success = run_command(cmd, description)
    
    # 如果生成了HTML覆盖率报告，提示查看
    if args.html_coverage and success:
        html_path = project_root / "htmlcov" / "index.html"
        if html_path.exists():
            print(f"\n📊 HTML覆盖率报告: {html_path}")
            print(f"🌐 在浏览器中打开: file://{html_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 