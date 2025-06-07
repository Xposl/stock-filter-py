#!/usr/bin/env python3
"""
修复多行f-string问题的脚本
"""

import os
import re
import sys

def fix_multiline_fstring(content):
    """修复多行f-string问题"""
    
    # 模式1: f"text {
    #           variable} more text"
    pattern1 = r'f"([^"]*{)\s*\n\s*([^}]+)}([^"]*)"'
    content = re.sub(pattern1, r'f"\1\2}\3"', content, flags=re.MULTILINE)
    
    # 模式2: f"text {
    #           variable
    #        } more text"
    pattern2 = r'f"([^"]*{)\s*\n\s*([^}]+)\s*\n\s*}([^"]*)"'
    content = re.sub(pattern2, r'f"\1\2}\3"', content, flags=re.MULTILINE)
    
    # 模式3: f"text {
    #           variable1} text {
    #           variable2} more text"
    pattern3 = r'f"([^"]*{)\s*\n\s*([^}]+)}([^"]*{)\s*\n\s*([^}]+)}([^"]*)"'
    content = re.sub(pattern3, r'f"\1\2}\3\4}\5"', content, flags=re.MULTILINE)
    
    # 模式4: 更复杂的情况，手动处理最常见的模式
    lines = content.split('\n')
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检查是否是以 f" 开头并以 { 结尾的行
        if re.match(r'.*f"[^"]*{$', line.strip()):
            # 寻找对应的结束行
            fstring_parts = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                fstring_parts.append(next_line)
                if '}' in next_line and '"' in next_line:
                    break
                j += 1
            
            if j < len(lines):
                # 合并多行f-string
                combined = ""
                for part in fstring_parts:
                    # 移除多余的空白和缩进
                    cleaned = part.strip()
                    if cleaned.startswith('f"'):
                        combined = cleaned
                    elif cleaned.endswith('}"') or cleaned.endswith('}"):'):
                        # 移除开头的引号并添加到组合字符串中
                        if cleaned.startswith('"'):
                            cleaned = cleaned[1:]
                        combined = combined[:-1] + cleaned  # 移除最后的 { 然后添加
                        break
                    else:
                        # 中间部分
                        if cleaned.endswith('}'):
                            combined = combined[:-1] + cleaned  # 移除最后的 { 然后添加
                        else:
                            combined = combined[:-1] + cleaned + '{'
                
                # 保持原有的缩进
                original_indent = line[:len(line) - len(line.lstrip())]
                result_lines.append(original_indent + combined)
                i = j + 1
            else:
                result_lines.append(line)
                i += 1
        else:
            result_lines.append(line)
            i += 1
    
    return '\n'.join(result_lines)

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed_content = fix_multiline_fstring(content)
        
        if fixed_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed: {filepath}")
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """主函数"""
    # 获取有问题的文件列表
    problem_files = [
        "./core/news_aggregator/api_aggregator.py",
        "./core/news_aggregator/rss_aggregator.py", 
        "./core/indicator/volume_supertrend_ai_indicator.py",
        "./core/auth/auth_middleware.py",
        "./core/service/ticker_score_repository.py",
        "./core/service/ticker_repository.py",
        "./core/service/ticker_strategy_repository.py",
        "./core/service/ticker_indicator_repository.py",
        "./core/service/ticker_valuation_repository.py",
        "./core/ai_agents/llm_clients/silicon_flow_client.py"
    ]
    
    fixed_count = 0
    
    for filepath in problem_files:
        if os.path.exists(filepath):
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"File not found: {filepath}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()
