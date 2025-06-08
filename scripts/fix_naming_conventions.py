#!/usr/bin/env python3
"""
批量修复代码命名规范问题
"""

import re
import os
from pathlib import Path


def snake_case(name):
    """将驼峰命名转换为蛇形命名"""
    # 保留已经是蛇形命名的
    if '_' in name and name.islower():
        return name
    
    # 转换驼峰命名
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def fix_file_naming_issues(file_path):
    """修复单个文件中的命名问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复常见的变量命名问题
        naming_fixes = [
            # 函数参数
            (r'def\s+(\w+)\s*\([^)]*kLineData', lambda m: m.group(0).replace('kLineData', 'k_line_data')),
            (r'def\s+(\w+)\s*\([^)]*strategyData', lambda m: m.group(0).replace('strategyData', 'strategy_data')),
            (r'def\s+(\w+)\s*\([^)]*indicatorData', lambda m: m.group(0).replace('indicatorData', 'indicator_data')),
            (r'def\s+(\w+)\s*\([^)]*KScoreData', lambda m: m.group(0).replace('KScoreData', 'k_score_data')),
            (r'def\s+(\w+)\s*\([^)]*valuationData', lambda m: m.group(0).replace('valuationData', 'valuation_data')),
            (r'def\s+(\w+)\s*\([^)]*updateTime', lambda m: m.group(0).replace('updateTime', 'update_time')),
            (r'def\s+(\w+)\s*\([^)]*maSrc', lambda m: m.group(0).replace('maSrc', 'ma_src')),
            (r'def\s+(\w+)\s*\([^)]*KNN_PriceLen', lambda m: m.group(0).replace('KNN_PriceLen', 'knn_price_len')),
            (r'def\s+(\w+)\s*\([^)]*KNN_STLen', lambda m: m.group(0).replace('KNN_STLen', 'knn_st_len')),
            (r'def\s+(\w+)\s*\([^)]*dayCount', lambda m: m.group(0).replace('dayCount', 'day_count')),
            (r'def\s+(\w+)\s*\([^)]*highData', lambda m: m.group(0).replace('highData', 'high_data')),
            (r'def\s+(\w+)\s*\([^)]*lowData', lambda m: m.group(0).replace('lowData', 'low_data')),
            (r'def\s+(\w+)\s*\([^)]*valuationKey', lambda m: m.group(0).replace('valuationKey', 'valuation_key')),
            
            # 函数名
            (r'def\s+K_line_to_dict', 'def k_line_to_dict'),
            (r'def\s+K_line_from_dict', 'def k_line_from_dict'),
            (r'def\s+calculateByKey', 'def calculate_by_key'),
            (r'def\s+getKey', 'def get_key'),
        ]
        
        # 应用修复
        for pattern, replacement in naming_fixes:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed naming issues in: {file_path}")
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    
    # 需要处理的文件模式
    patterns = [
        "core/**/*.py",
        "api/**/*.py"
    ]
    
    total_fixed = 0
    
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.py':
                if fix_file_naming_issues(file_path):
                    total_fixed += 1
    
    print(f"总共修复了 {total_fixed} 个文件的命名问题")


if __name__ == "__main__":
    main()
