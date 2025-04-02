#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import tempfile

# 将项目根目录添加到Python路径中
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 导入pyppeteer
from pyppeteer import launch
import pyppeteer.chromium_downloader as downloader

async def download_browser():
    """
    预先下载Chromium浏览器，避免每次运行时重新下载
    """
    print("开始下载和配置Chromium浏览器...")
    
    # 显示将要下载的浏览器版本
    chromium_revision = downloader.REVISION
    print(f"Chromium版本: {chromium_revision}")
    
    # 获取可能的下载路径
    user_home = os.path.expanduser('~')
    possible_paths = [
        os.path.join(user_home, '.pyppeteer'),
        os.path.join(user_home, '.local', 'share', 'pyppeteer'),
        os.path.join(user_home, 'AppData', 'Local', 'pyppeteer'),  # Windows
        os.path.join(user_home, 'Library', 'Application Support', 'pyppeteer')  # macOS
    ]
    
    # 尝试找到或创建下载目录
    download_path = None
    for path in possible_paths:
        if os.path.exists(path):
            download_path = path
            break
    
    if not download_path:
        # 如果未找到现有目录，创建一个
        download_path = possible_paths[0]  # 默认使用第一个路径
        os.makedirs(download_path, exist_ok=True)
    
    print(f"Chromium下载路径: {download_path}")
    
    # 尝试查找浏览器可执行文件的路径
    try:
        executable_path = downloader.chromium_executable()
        print(f"找到Chromium可执行文件: {executable_path}")
        browser_already_exists = os.path.exists(executable_path)
    except Exception:
        browser_already_exists = False
        print("未找到现有的Chromium可执行文件")
    
    try:
        if not browser_already_exists:
            print("正在下载Chromium浏览器，这可能需要几分钟时间...")
        
        # 下载浏览器（如果尚未下载）并启动它
        browser = await launch(headless=True)
        await browser.close()
        
        # 再次尝试获取浏览器路径
        try:
            executable_path = downloader.chromium_executable()
            print(f"\n浏览器下载和配置成功完成！")
            print(f"浏览器已安装到: {executable_path}")
            
            # 设置环境变量的提示
            print("\n如需避免未来重新下载，可以在系统中添加以下环境变量:")
            print(f"PYPPETEER_CHROMIUM_PATH={executable_path}")
            print(f"PYPPETEER_HOME={download_path}")
            print("PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true")
            
            # 添加到.env文件的建议
            env_file = os.path.join(project_root, '.env')
            if os.path.exists(env_file):
                print("\n也可以将以下行添加到项目的.env文件中:")
                print(f"PYPPETEER_CHROMIUM_PATH={executable_path}")
                print(f"PYPPETEER_HOME={download_path}")
                print("PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true")
        except Exception as e:
            print(f"获取浏览器路径失败: {e}")
            
    except Exception as e:
        print(f"下载浏览器时出错: {e}")
        return False
    
    return True

def main():
    """主函数"""
    # 创建新的事件循环，避免使用已弃用的get_event_loop()
    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(download_browser())
    except Exception as e:
        print(f"运行异步任务时出错: {e}")
        success = False
    
    if success:
        print("\n初始化完成，现在您可以运行项目而无需重新下载浏览器。")
    else:
        print("\n初始化失败，请检查错误信息并重试。")
        sys.exit(1)

if __name__ == "__main__":
    main()
