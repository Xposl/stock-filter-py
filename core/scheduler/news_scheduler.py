"""
新闻定时抓取调度器
使用APScheduler实现定时新闻抓取任务
"""

import logging
from datetime import datetime
from typing import Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..database.database import get_database_url
from ..news_aggregator.news_aggregator_manager import NewsAggregatorManager

logger = logging.getLogger(__name__)


class NewsScheduler:
    """新闻定时抓取调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._session_factory = None
        self._is_running = False

    async def initialize(self):
        """初始化调度器"""
        # 初始化数据库连接
        database_url = get_database_url()
        engine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # 添加默认的定时任务
        await self._setup_default_jobs()

        logger.info("新闻调度器初始化完成")

    async def _setup_default_jobs(self):
        """设置默认的定时任务"""

        # 1. 每小时抓取一次新闻（工作时间：9:00-18:00）
        self.scheduler.add_job(
            func=self._fetch_news_job,
            trigger=CronTrigger(
                hour="9-18", minute="0", timezone="Asia/Shanghai"  # 工作时间  # 整点抓取
            ),
            id="hourly_news_fetch",
            name="每小时新闻抓取",
            replace_existing=True,
            misfire_grace_time=300,  # 5分钟容错时间
        )

        # 2. 每30分钟抓取一次新闻（工作日的核心交易时间）
        self.scheduler.add_job(
            func=self._fetch_news_job,
            trigger=CronTrigger(
                day_of_week="mon-fri",  # 工作日
                hour="9-15",  # 交易时间
                minute="0,30",  # 每半小时
                timezone="Asia/Shanghai",
            ),
            id="trading_hours_news_fetch",
            name="交易时间新闻抓取",
            replace_existing=True,
            misfire_grace_time=300,
        )

        # 3. 早上8点抓取晨间新闻
        self.scheduler.add_job(
            func=self._fetch_morning_news_job,
            trigger=CronTrigger(hour="8", minute="0", timezone="Asia/Shanghai"),
            id="morning_news_fetch",
            name="晨间新闻抓取",
            replace_existing=True,
            misfire_grace_time=600,  # 10分钟容错时间
        )

        # 4. 晚上6点抓取收盘后新闻
        self.scheduler.add_job(
            func=self._fetch_evening_news_job,
            trigger=CronTrigger(hour="18", minute="0", timezone="Asia/Shanghai"),
            id="evening_news_fetch",
            name="收盘新闻抓取",
            replace_existing=True,
            misfire_grace_time=600,
        )

        logger.info("默认定时任务设置完成")

    async def _fetch_news_job(self):
        """标准新闻抓取任务"""
        try:
            logger.info("开始执行定时新闻抓取任务")

            manager = NewsAggregatorManager()
            results = await manager.fetch_all_active_sources()

            # 统计结果
            total_articles = sum(r.get("articles_count", 0) for r in results)
            success_sources = len([r for r in results if r.get("status") == "success"])
            error_sources = len([r for r in results if r.get("status") == "error"])

            logger.info(
                f"定时新闻抓取完成: {success_sources}个源成功, {error_sources}个源失败, 共获取{total_articles}篇文章")

            return {
                "task_type": "regular_fetch",
                "success_sources": success_sources,
                "error_sources": error_sources,
                "total_articles": total_articles,
                "completed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"定时新闻抓取任务失败: {str(e)}")
            return {"task_type": "regular_fetch", "error": str(e)}

    async def _fetch_morning_news_job(self):
        """晨间新闻抓取任务（更全面）"""
        try:
            logger.info("开始执行晨间新闻抓取任务")

            manager = NewsAggregatorManager()

            # 晨间新闻抓取更全面，包括暂停的源也尝试抓取
            results = await manager.fetch_all_active_sources()

            total_articles = sum(r.get("articles_count", 0) for r in results)
            success_sources = len([r for r in results if r.get("status") == "success"])
            error_sources = len([r for r in results if r.get("status") == "error"])

            logger.info(
                f"晨间新闻抓取完成: {success_sources}个源成功, {error_sources}个源失败, 共获取{total_articles}篇文章")

            return {
                "task_type": "morning_fetch",
                "success_sources": success_sources,
                "error_sources": error_sources,
                "total_articles": total_articles,
                "completed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"晨间新闻抓取任务失败: {str(e)}")
            return {"task_type": "morning_fetch", "error": str(e)}

    async def _fetch_evening_news_job(self):
        """收盘新闻抓取任务"""
        try:
            logger.info("开始执行收盘新闻抓取任务")

            manager = NewsAggregatorManager()
            results = await manager.fetch_all_active_sources()

            total_articles = sum(r.get("articles_count", 0) for r in results)
            success_sources = len([r for r in results if r.get("status") == "success"])
            error_sources = len([r for r in results if r.get("status") == "error"])

            logger.info(
                f"收盘新闻抓取完成: {success_sources}个源成功, {error_sources}个源失败, 共获取{total_articles}篇文章")

            return {
                "task_type": "evening_fetch",
                "success_sources": success_sources,
                "error_sources": error_sources,
                "total_articles": total_articles,
                "completed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"收盘新闻抓取任务失败: {str(e)}")
            return {"task_type": "evening_fetch", "error": str(e)}

    def start(self):
        """启动调度器"""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("新闻调度器已启动")

    def shutdown(self):
        """关闭调度器"""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("新闻调度器已关闭")

    def add_custom_job(
        self, func, trigger_type: str = "interval", **trigger_args
    ) -> str:
        """添加自定义定时任务

        Args:
            func: 要执行的函数
            trigger_type: 触发器类型 ("interval" 或 "cron")
            **trigger_args: 触发器参数

        Returns:
            任务ID
        """
        import uuid

        job_id = f"custom_job_{uuid.uuid4().hex[:8]}"

        if trigger_type == "interval":
            trigger = IntervalTrigger(**trigger_args)
        elif trigger_type == "cron":
            trigger = CronTrigger(**trigger_args)
        else:
            raise ValueError(f"不支持的触发器类型: {trigger_type}")

        self.scheduler.add_job(
            func=func, trigger=trigger, id=job_id, replace_existing=True
        )

        logger.info(f"添加自定义任务: {job_id}")
        return job_id

    def remove_job(self, job_id: str):
        """移除指定任务"""
        self.scheduler.remove_job(job_id)
        logger.info(f"移除任务: {job_id}")

    def get_jobs(self) -> dict[str, Any]:
        """获取所有任务信息"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                    "trigger": str(job.trigger),
                }
            )

        return {"total_jobs": len(jobs), "is_running": self._is_running, "jobs": jobs}

    async def trigger_manual_fetch(
        self, source_ids: Optional[list] = None
    ) -> dict[str, Any]:
        """手动触发新闻抓取"""
        try:
            logger.info("手动触发新闻抓取")

            manager = NewsAggregatorManager()

            if source_ids:
                results = await manager.fetch_specific_sources(source_ids)
            else:
                results = await manager.fetch_all_active_sources()

            total_articles = sum(r.get("articles_count", 0) for r in results)
            success_sources = len([r for r in results if r.get("status") == "success"])
            error_sources = len([r for r in results if r.get("status") == "error"])

            logger.info(
                f"手动新闻抓取完成: {success_sources}个源成功, {error_sources}个源失败, 共获取{total_articles}篇文章")

            return {
                "task_type": "manual_fetch",
                "success_sources": success_sources,
                "error_sources": error_sources,
                "total_articles": total_articles,
                "results": results,
                "completed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"手动新闻抓取失败: {str(e)}")
            return {"task_type": "manual_fetch", "error": str(e)}


# 全局调度器实例
_global_scheduler: Optional[NewsScheduler] = None


async def get_news_scheduler() -> NewsScheduler:
    """获取全局新闻调度器实例"""
    global _global_scheduler

    if _global_scheduler is None:
        _global_scheduler = NewsScheduler()
        await _global_scheduler.initialize()

    return _global_scheduler


async def start_news_scheduler():
    """启动新闻调度器"""
    scheduler = await get_news_scheduler()
    scheduler.start()
    return scheduler


def stop_news_scheduler():
    """停止新闻调度器"""
    global _global_scheduler
    if _global_scheduler:
        _global_scheduler.shutdown()
        _global_scheduler = None
