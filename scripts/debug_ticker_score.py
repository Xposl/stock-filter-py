#!/usr/bin/env python3

"""
调试ticker_id=2的评分数据
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_source_helper import DataSourceHelper  # noqa: E402
from core.database.db_adapter import DbAdapter  # noqa: E402
from core.service.ticker_score_repository import TickerScoreRepository  # noqa: E402


def check_ticker_score_data():
    """检查ticker_id=2的评分数据"""
    print("🔍 查看ticker_id=2的评分数据...")

    # 1. 直接查询数据库
    db = DbAdapter()
    results = db.query(
        "SELECT id, ticker_id, time_key, score, create_time FROM ticker_score WHERE ticker_id = 2 ORDER BY time_key DESC, create_time DESC LIMIT 10"
    )

    print("\n📊 数据库中的最新10条记录:")
    for i, row in enumerate(results, 1):
        print(f"  {i}. ID: {row['id']}, time_key: {row['time_key']}, score: {row['score']}, create_time: {row['create_time']}")

    # 2. 通过Repository查询
    repo = TickerScoreRepository()
    scores = repo.get_items_by_ticker_id(2)

    print(f"\n📋 通过Repository获取的记录数量: {len(scores)}")
    if scores:
        print("前5条记录：")
        for i, score in enumerate(scores[:5], 1):
            print(f"  {i}. ID={score.id}, time_key={score.time_key}, score={score.score}")

    # 3. 通过DataSourceHelper智能获取
    helper = DataSourceHelper()
    intelligent_score = helper.get_ticker_score("HK.02589", days=600)

    print("\n🧠 智能获取的评分数据:")
    if intelligent_score:
        print(f"   返回记录数量: {len(intelligent_score)}")
        print("   前5条记录：")
        for i, score in enumerate(intelligent_score[:5], 1):
            print(f"     {i}. ID={score.id}, time_key={score.time_key}, score={score.score}")
    else:
        print("   返回: None")

    return results, scores, intelligent_score

if __name__ == "__main__":
    check_ticker_score_data()
