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
from datetime import datetime


def create_log_file():
    """创建带时间戳的日志文件"""
    # 确保logs目录存在
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"test_logs-{timestamp}.log"
    
    return log_file


def run_command(cmd, description, log_file=None):
    """运行命令并输出描述"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"执行命令: {' '.join(cmd)}")
    if log_file:
        print(f"📝 日志文件: {log_file}")
    print("-" * 60)
    
    # 准备输出重定向
    if log_file:
        # 创建日志文件并写入命令信息
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"🚀 {description}\n")
            f.write(f"{'='*60}\n")
            f.write(f"执行命令: {' '.join(cmd)}\n")
            f.write(f"开始时间: {datetime.now()}\n")
            f.write("-" * 60 + "\n")
        
        # 运行命令并同时输出到控制台和文件
        with open(log_file, 'a', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            
            # 输出到控制台
            print(result.stdout)
            
            # 写入日志文件
            f.write(result.stdout)
            f.write(f"\n结束时间: {datetime.now()}\n")
            f.write(f"退出码: {result.returncode}\n")
            f.write("="*60 + "\n")
    else:
        # 不使用日志文件时的原有逻辑
        result = subprocess.run(cmd, capture_output=False)
    
    success = result.returncode == 0
    if success:
        print(f"\n✅ {description} - 成功")
    else:
        print(f"\n❌ {description} - 失败 (退出码: {result.returncode})")
    
    return success


def main():
    parser = argparse.ArgumentParser(description="InvestNote-py 测试运行器")
    parser.add_argument("--type", "-t", 
                       choices=["unit", "integration", "api", "slow", "debug", "pocketflow", "akshare", "xueqiu", "news", "all"],
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
    parser.add_argument("--log", "-l", action="store_true",
                       help="输出测试日志到文件")
    parser.add_argument("--log-file", 
                       help="指定日志文件路径（默认自动生成）")
    
    args = parser.parse_args()
    
    # 确保在项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 InvestNote-py 测试运行器")
    print(f"📁 工作目录: {project_root}")
    
    # 创建日志文件
    log_file = None
    if args.log or args.log_file:
        if args.log_file:
            log_file = Path(args.log_file)
            # 确保父目录存在
            log_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            log_file = create_log_file()
        
        print(f"📝 测试日志将保存到: {log_file}")
        
        # 写入日志文件头部信息
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("InvestNote-py 测试日志\n")
            f.write(f"开始时间: {datetime.now()}\n")
            f.write(f"工作目录: {project_root}\n")
            f.write(f"Python版本: {sys.version}\n")
            f.write("="*60 + "\n")
    
    # 安装测试依赖
    if args.install_deps:
        deps_cmd = [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "pytest-cov", "pytest-html"]
        if not run_command(deps_cmd, "安装测试依赖", log_file):
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
    
    # 添加HTML报告
    if log_file:
        html_report = log_file.parent / f"test_report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        cmd.extend(["--html", str(html_report), "--self-contained-html"])
    
    # 添加测试类型标记
    test_descriptions = {
        "unit": "运行单元测试",
        "integration": "运行集成测试", 
        "api": "运行API测试",
        "slow": "运行慢速测试",
        "debug": "运行调试测试",
        "pocketflow": "运行PocketFlow AI测试",
        "akshare": "运行AKShare数据源测试",
        "xueqiu": "运行雪球数据源测试",
        "news": "运行新闻聚合测试",
        "all": "运行所有测试"
    }
    
    if args.type != "all":
        cmd.extend(["-m", args.type])
        if args.type == "slow":
            cmd.append("--run-slow")
        description = test_descriptions.get(args.type, f"运行 {args.type} 测试")
    else:
        description = test_descriptions["all"]
    
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
    success = run_command(cmd, description, log_file)
    
    # 输出总结信息
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n测试运行完成\n")
            f.write(f"结果: {'✅ 成功' if success else '❌ 失败'}\n")
            f.write(f"结束时间: {datetime.now()}\n")
        
        print(f"\n📊 测试日志已保存: {log_file}")
        if html_report.exists() if 'html_report' in locals() else False:
            print(f"📊 HTML报告已生成: {html_report}")
    
    # 如果生成了HTML覆盖率报告，提示查看
    if args.html_coverage and success:
        html_path = project_root / "htmlcov" / "index.html"
        if html_path.exists():
            print(f"\n📊 HTML覆盖率报告: {html_path}")
            print(f"🌐 在浏览器中打开: file://{html_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 