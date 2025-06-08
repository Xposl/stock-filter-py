#!/usr/bin/env python3
"""
修复f-string多行语法错误的脚本
"""
import os
import re
import glob


def fix_fstring_multiline(file_path):
    """修复文件中的f-string多行语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复模式1: f"SELECT * FROM {\n                self.table} WHERE ..."
        pattern1 = r'f"([^"]*)\{\s*\n\s*([^}]+)\}([^"]*)"'
        content = re.sub(pattern1, r'f"\1{\2}\3"', content)
        
        # 修复模式2: f"INSERT INTO {\n                    self.table} ({\n                    ', '.join(fields)}) VALUES ({\n                    ', '.join(placeholders)})"
        pattern2 = r'f"([^"]*)\{\s*\n\s*([^}]+)\}\s*\(\{\s*\n\s*([^}]+)\}\)\s*VALUES\s*\(\{\s*\n\s*([^}]+)\}\)([^"]*)"'
        content = re.sub(pattern2, r'f"\1{\2} ({\3}) VALUES ({\4})\5"', content)
        
        # 修复模式3: f"UPDATE {\n                    self.table} SET {\n                    ', '.join(set_clauses)} WHERE ..."
        pattern3 = r'f"([^"]*)\{\s*\n\s*([^}]+)\}\s*SET\s*\{\s*\n\s*([^}]+)\}([^"]*)"'
        content = re.sub(pattern3, r'f"\1{\2} SET {\3}\4"', content)
        
        # 修复更复杂的多行模式
        # 查找并修复跨多行的f-string
        lines = content.split('\n')
        in_fstring = False
        fstring_start = -1
        fstring_content = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测f-string开始
            if not in_fstring and ('f"' in stripped or "f'" in stripped):
                # 检查是否是未完成的f-string（包含{但没有对应的}或引号未闭合）
                quote_char = '"' if 'f"' in stripped else "'"
                start_pos = stripped.find(f'f{quote_char}')
                if start_pos != -1:
                    remaining = stripped[start_pos + 2:]
                    open_braces = remaining.count('{')
                    close_braces = remaining.count('}')
                    quotes = remaining.count(quote_char)
                    
                    if (open_braces > close_braces) or (quotes == 0):
                        in_fstring = True
                        fstring_start = i
                        fstring_content = [line]
                        continue
            
            if in_fstring:
                fstring_content.append(line)
                
                # 检查是否到达f-string结尾
                current_content = '\n'.join(fstring_content)
                quote_char = '"' if 'f"' in current_content else "'"
                
                # 简单检查：如果当前行包含结束引号且大括号匹配
                if quote_char in line:
                    open_braces = current_content.count('{')
                    close_braces = current_content.count('}')
                    if open_braces == close_braces:
                        # 合并多行f-string为单行
                        merged_line = current_content.replace('\n', ' ')
                        # 清理多余的空格
                        merged_line = re.sub(r'\s+', ' ', merged_line)
                        
                        # 替换原始行
                        for j in range(fstring_start, i + 1):
                            if j == fstring_start:
                                lines[j] = merged_line
                            else:
                                lines[j] = ''  # 标记为删除
                        
                        in_fstring = False
                        fstring_content = []
        
        # 重新组装内容，移除空行
        content = '\n'.join(line for line in lines if line is not None)
        
        # 清理连续的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复了 {file_path}")
            return True
        else:
            print(f"⏭️  {file_path} 无需修复")
            return False
            
    except Exception as e:
        print(f"❌ 修复 {file_path} 时出错: {e}")
        return False


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 查找所有Python文件
    python_files = []
    for root, dirs, files in os.walk(os.path.join(project_root, 'core')):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    for root, dirs, files in os.walk(os.path.join(project_root, 'api')):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"🔍 找到 {len(python_files)} 个Python文件")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_fstring_multiline(file_path):
            fixed_count += 1
    
    print(f"\n🎉 总共修复了 {fixed_count} 个文件")


if __name__ == "__main__":
    main()
