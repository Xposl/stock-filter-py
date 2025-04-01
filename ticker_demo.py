#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ticker模型和TickerRepository使用示例
"""

import os
from datetime import datetime
from core.models.ticker import Ticker, TickerCreate, TickerUpdate
from core.API.TickerRepository import TickerRepository

def main():
    """
    主函数，展示Ticker模型和TickerRepository的使用
    """
    print("===== Ticker Pydantic模型和Repository示例 =====")
    
    # 确保使用SQLite
    os.environ['DB_TYPE'] = 'sqlite'
    os.environ['SQLITE_DB_PATH'] = 'investnote.db'
    
    # 初始化TickerRepository
    repo = TickerRepository()
    
    try:
        # 示例1: 创建新的股票
        print("\n1. 使用Pydantic模型创建新股票:")
        
        # 使用TickerCreate模型创建新的股票
        new_ticker_data = TickerCreate(
            code="TSLA",
            name="特斯拉",
            group_id=1,
            type=1,
            status=1,
            update_date=datetime.now()
        )
        
        # 检查股票是否已存在
        existing = repo.get_by_code("TSLA")
        if existing:
            print(f"  - 股票 {existing.code} ({existing.name}) 已存在")
        else:
            # 创建新股票
            created_ticker = repo.create("TSLA", "特斯拉", new_ticker_data)
            if created_ticker:
                print(f"  - 已创建新股票: {created_ticker.code} ({created_ticker.name})")
                print(f"    ID: {created_ticker.id}")
                print(f"    分组: {created_ticker.group_id}")
                print(f"    创建时间: {created_ticker.create_time}")
        
        # 示例2: 更新股票信息
        print("\n2. 使用Pydantic模型更新股票:")
        
        # 使用TickerUpdate模型更新股票信息
        update_data = TickerUpdate(
            name="特斯拉公司",
            close=800.0,
            high=820.0,
            low=790.0,
            volume=10000000
        )
        
        # 更新股票
        updated_ticker = repo.update("TSLA", "特斯拉公司", update_data)
        if updated_ticker:
            print(f"  - 已更新股票: {updated_ticker.code} ({updated_ticker.name})")
            print(f"    收盘价: {updated_ticker.close}")
            print(f"    最高价: {updated_ticker.high}")
            print(f"    最低价: {updated_ticker.low}")
            print(f"    成交量: {updated_ticker.volume}")
        
        # 示例3: 查询所有可用股票
        print("\n3. 查询所有可用股票:")
        available_tickers = repo.get_all_available()
        print(f"  - 可用股票数量: {len(available_tickers)}")
        for idx, ticker in enumerate(available_tickers[:5]):  # 只显示前5个
            print(f"    {idx+1}. {ticker.code} ({ticker.name})")
        
        if len(available_tickers) > 5:
            print(f"    ...共 {len(available_tickers)} 个")
        
        # 示例4: 使用字典创建或更新股票
        print("\n4. 使用字典创建或更新股票:")
        dict_data = {
            "code": "NVDA",
            "name": "英伟达",
            "group_id": 1,
            "type": 1,
            "status": 1,
            "open": 700.0,
            "close": 720.0,
            "high": 730.0,
            "low": 695.0,
            "volume": 8000000
        }
        
        # 创建或更新
        nvidia_ticker = repo.update_or_create("NVDA", "英伟达", dict_data)
        if nvidia_ticker:
            print(f"  - 已创建或更新股票: {nvidia_ticker.code} ({nvidia_ticker.name})")
            print(f"    ID: {nvidia_ticker.id}")
            print(f"    开盘价: {nvidia_ticker.open}")
            print(f"    收盘价: {nvidia_ticker.close}")
        
        # 示例5: 获取股票信息并转换为Pydantic模型
        print("\n5. 获取股票详细信息:")
        apple = repo.get_by_code("AAPL")
        if apple:
            print(f"  - 股票信息: {apple.code} ({apple.name})")
            print(f"    ID: {apple.id}")
            print(f"    分组: {apple.group_id}")
            print(f"    状态: {'活跃' if apple.status == 1 else '非活跃'}")
            print(f"    是否删除: {apple.is_deleted}")
            
            # 使用Pydantic模型验证和序列化
            print("\n  - Pydantic模型序列化:")
            apple_dict = apple.model_dump()
            print(f"    模型包含 {len(apple_dict)} 个字段")
            print(f"    部分字段: code={apple_dict.get('code')}, name={apple_dict.get('name')}, id={apple_dict.get('id')}")
    
    except Exception as e:
        print(f"操作失败: {e}")
    
    print("\n===== 示例结束 =====")

if __name__ == "__main__":
    main()
