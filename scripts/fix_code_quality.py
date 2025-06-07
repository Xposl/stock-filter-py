#!/usr/bin/env python3
"""
自动修复代码质量问题的脚本
主要解决类型注解现代化和未使用导入等问题
"""

import re
import subprocess
from pathlib import Path


class CodeQualityFixer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.python_files = list(self.project_root.glob("**/*.py"))

    def run_ruff_fix(self) -> bool:
        """使用 ruff 自动修复可以自动修复的问题"""
        print("🔧 使用 ruff 自动修复代码质量问题...")
        try:
            cmd = ["ruff", "check", "--fix", str(self.project_root)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                print("✅ Ruff 自动修复完成")
                return True
            else:
                print(f"⚠️ Ruff 修复时有一些问题: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Ruff 修复失败: {e}")
            return False

    def modernize_typing_imports(self, file_path: Path) -> bool:
        """现代化类型注解导入"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # 替换常见的类型注解
            replacements = {
                r'from typing import.*?Dict.*?': '',
                r'from typing import.*?List.*?': '',
                r'from typing import.*?Tuple.*?': '',
                r'from typing import.*?Set.*?': '',
                r'from typing import.*?FrozenSet.*?': '',
                r'typing\.Dict': 'dict',
                r'typing\.List': 'list',
                r'typing\.Tuple': 'tuple',
                r'typing\.Set': 'set',
                r'typing\.FrozenSet': 'frozenset',
                r'\bDict\b': 'dict',
                r'\bList\b': 'list',
                r'\bTuple\b': 'tuple',
                r'\bSet\b': 'set',
                r'\bFrozenSet\b': 'frozenset',
            }

            for pattern, replacement in replacements.items():
                content = re.sub(pattern, replacement, content)

            # 移除不必要的 UTF-8 编码声明
            content = re.sub(r'^#.*?coding[:=]\s*([-\w.]+).*?\n', '', content, flags=re.MULTILINE)

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            return False
        except Exception as e:
            print(f"❌ 处理文件 {file_path} 时出错: {e}")
            return False

    def remove_unused_imports(self) -> bool:
        """移除未使用的导入"""
        print("🧹 移除未使用的导入...")
        try:
            cmd = ["autoflake", "--remove-all-unused-imports", "--in-place", "--recursive", str(self.project_root)]
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ autoflake 失败: {e}")
            return False

    def fix_all(self) -> None:
        """执行所有修复"""
        print("🚀 开始修复代码质量问题...")

        # 1. 首先使用 ruff 自动修复
        self.run_ruff_fix()

        # 2. 手动现代化类型注解
        print("🔧 现代化类型注解...")
        fixed_files = 0
        for file_path in self.python_files:
            if self.modernize_typing_imports(file_path):
                fixed_files += 1
        print(f"✅ 修复了 {fixed_files} 个文件的类型注解")

        # 3. 移除未使用的导入
        self.remove_unused_imports()

        # 4. 重新格式化代码
        print("🎨 重新格式化代码...")
        subprocess.run(["black", str(self.project_root)], cwd=self.project_root)
        subprocess.run(["isort", str(self.project_root)], cwd=self.project_root)

        print("✅ 代码质量修复完成!")


if __name__ == "__main__":
    fixer = CodeQualityFixer(".")
    fixer.fix_all()
