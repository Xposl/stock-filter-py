#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time

# 将项目根目录添加到Python路径中
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 导入雪球API
from core.API.Helper.XueqiuHelper import Xueqiu

def main():
    """
    测试雪球API，验证是否能正确获取token而无需重新下载浏览器
    """
    print("开始测试雪球API...")
    
    # 显示环境变量设置
    print("\n环境变量信息:")
    print(f"PYPPETEER_CHROMIUM_PATH: {os.environ.get('PYPPETEER_CHROMIUM_PATH', '未设置')}")
    print(f"PYPPETEER_HOME: {os.environ.get('PYPPETEER_HOME', '未设置')}")
    print(f"PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: {os.environ.get('PUPPETEER_SKIP_CHROMIUM_DOWNLOAD', '未设置')}")
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 创建雪球API实例
        print("\n创建雪球API实例...")
        xq = Xueqiu()
        
        # 记录结束时间
        end_time = time.time()
        
        # 显示用时
        print(f"\n成功获取雪球token！")
        print(f"耗时: {end_time - start_time:.2f}秒")
        
        # 测试一个API调用
        print("\n测试获取股票信息...")
        stock_info = xq.getStockDetail("SZ000001", "平安银行")
        
        if stock_info:
            print(f"成功获取股票信息: {stock_info['name']} ({stock_info['code']})")
            if 'remark' in stock_info:
                remark = stock_info['remark']
                print(f"公司简介: {remark[:100]}..." if len(remark) > 100 else remark)
        else:
            print("获取股票信息失败")
        
        print("\n测试完成！")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
