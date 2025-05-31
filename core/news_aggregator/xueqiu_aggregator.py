"""
雪球新闻聚合器
专门处理雪球平台的投资动态和新闻数据
"""

import asyncio
import aiohttp
import hashlib
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin
import re

from ..models.news_source import NewsSource, NewsSourceType, NewsSourceStatus
from ..models.news_article import NewsArticle, ArticleStatus

logger = logging.getLogger(__name__)

class XueqiuAggregator:
    """雪球新闻聚合器"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """
        初始化雪球聚合器
        
        Args:
            session: 可选的aiohttp客户端会话
        """
        self.session = session
        self._own_session = session is None
        
        # 雪球API的请求头（模拟浏览器）
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://xueqiu.com/',
            'Origin': 'https://xueqiu.com'
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self._own_session:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._own_session and self.session:
            await self.session.close()
    
    async def fetch_xueqiu_timeline(self, news_source: NewsSource) -> List[Dict[str, Any]]:
        """
        抓取雪球时间线数据
        
        Args:
            news_source: 新闻源配置
            
        Returns:
            新闻文章列表
        """
        try:
            logger.info(f"开始抓取雪球数据: {news_source.name}")
            
            # 首先获取雪球的token（从首页获取）
            await self._init_xueqiu_session()
            
            # 抓取时间线数据
            timeline_data = await self._fetch_timeline_data(news_source.url)
            if not timeline_data:
                raise ValueError("无法获取雪球时间线数据")
            
            # 解析数据
            articles = []
            max_articles = news_source.max_articles_per_fetch or 20
            
            items = timeline_data.get('list', [])[:max_articles]
            
            for item in items:
                try:
                    article_data = await self._parse_xueqiu_item(item, news_source)
                    if article_data and self._should_include_article(article_data, news_source):
                        articles.append(article_data)
                except Exception as e:
                    logger.error(f"解析雪球条目失败: {e}", exc_info=True)
                    continue
            
            logger.info(f"成功抓取 {len(articles)} 篇雪球动态")
            return articles
            
        except Exception as e:
            logger.error(f"抓取雪球数据失败 {news_source.name}: {e}", exc_info=True)
            raise
    
    async def _init_xueqiu_session(self):
        """初始化雪球会话（获取必要的cookie和token）"""
        try:
            # 访问雪球首页，获取必要的session信息
            async with self.session.get('https://xueqiu.com/') as response:
                if response.status == 200:
                    logger.debug("雪球会话初始化成功")
                else:
                    logger.warning(f"雪球会话初始化警告: {response.status}")
        except Exception as e:
            logger.warning(f"雪球会话初始化失败: {e}")
    
    async def _fetch_timeline_data(self, url: str) -> Optional[Dict]:
        """获取时间线数据"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"雪球API HTTP错误 {response.status}: {url}")
                    return None
        except Exception as e:
            logger.error(f"获取雪球时间线数据失败 {url}: {e}")
            return None
    
    async def _parse_xueqiu_item(self, item: Dict, news_source: NewsSource) -> Optional[Dict[str, Any]]:
        """
        解析雪球条目
        
        Args:
            item: 雪球API返回的条目
            news_source: 新闻源配置
            
        Returns:
            解析后的文章数据
        """
        try:
            # 基础信息提取
            title = self._extract_title(item)
            text = self._extract_text(item)
            
            if not title and not text:
                return None
                
            # 构建URL
            status_id = item.get('id', '')
            url = f"https://xueqiu.com/statuses/show/{status_id}" if status_id else ""
            
            # 生成URL哈希
            content_for_hash = f"{title}_{text}_{status_id}"
            url_hash = hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()
            
            # 时间处理
            published_at = self._parse_created_time(item)
            
            # 用户信息
            author = self._extract_author(item)
            
            # 股票相关性检测
            stock_symbols = self._extract_stock_symbols(text)
            category = "雪球动态"
            if stock_symbols:
                category = f"雪球股票-{','.join(stock_symbols[:3])}"
            
            # 计算重要性（基于转发、评论、点赞数）
            importance_score = self._calculate_importance(item)
            
            article_data = {
                'title': title or text[:50] + "...",  # 如果没有标题，用内容前50字符
                'url': url,
                'url_hash': url_hash,
                'content': text,
                'summary': text[:200] + "..." if len(text) > 200 else text,
                'author': author,
                'source_id': news_source.id,
                'source_name': news_source.name,
                'category': category,
                'published_at': published_at,
                'language': news_source.language,
                'region': news_source.region,
                'status': ArticleStatus.PENDING.value,
                'word_count': len(text) if text else 0,
                'importance_score': importance_score,
                'metadata': json.dumps({
                    'platform': 'xueqiu',
                    'status_id': status_id,
                    'stock_symbols': stock_symbols,
                    'retweet_count': item.get('retweet_count', 0),
                    'reply_count': item.get('reply_count', 0),
                    'like_count': item.get('like_count', 0)
                }, ensure_ascii=False)
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"解析雪球条目失败: {e}", exc_info=True)
            return None
    
    def _extract_title(self, item: Dict) -> str:
        """提取标题"""
        # 雪球动态通常没有独立标题，从文本中提取第一行或关键部分
        text = item.get('text', '') or item.get('description', '')
        if not text:
            return ""
        
        # 清理HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 如果文本包含换行，取第一行作为标题
        lines = text.strip().split('\n')
        first_line = lines[0].strip()
        
        # 如果第一行太短或太长，处理一下
        if len(first_line) < 10 and len(lines) > 1:
            # 第一行太短，可能只是感叹词，取前两行
            first_line = ' '.join(lines[:2])
        elif len(first_line) > 100:
            # 第一行太长，截取前100字符
            first_line = first_line[:100]
        
        return first_line.strip()
    
    def _extract_text(self, item: Dict) -> str:
        """提取正文内容"""
        text = item.get('text', '') or item.get('description', '')
        if not text:
            return ""
        
        # 清理HTML标签但保留基本格式
        text = re.sub(r'<[^>]+>', '', text)
        # 规范化空白字符
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _parse_created_time(self, item: Dict) -> Optional[datetime]:
        """解析创建时间"""
        created_at = item.get('created_at')
        if not created_at:
            return None
        
        try:
            # 雪球时间戳通常是毫秒级
            if isinstance(created_at, (int, float)):
                if created_at > 1e12:  # 毫秒时间戳
                    created_at = created_at / 1000
                return datetime.fromtimestamp(created_at, tz=timezone.utc)
            elif isinstance(created_at, str):
                # 尝试解析字符串时间
                return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except (ValueError, TypeError) as e:
            logger.warning(f"解析雪球时间失败: {created_at}, {e}")
        
        return None
    
    def _extract_author(self, item: Dict) -> Optional[str]:
        """提取作者信息"""
        user = item.get('user', {})
        if user:
            return user.get('screen_name') or user.get('name') or user.get('id')
        return None
    
    def _extract_stock_symbols(self, text: str) -> List[str]:
        """从文本中提取股票代码"""
        if not text:
            return []
        
        # 匹配各种股票代码格式
        patterns = [
            r'\$([A-Z]{1,5})\$',  # $AAPL$ 格式
            r'\$([A-Z]{2}\d{5})\$',  # $SH600000$ 格式
            r'([A-Z]{2}\d{6})',  # SH600000 格式
            r'(\d{6})',  # 600000 格式（需要进一步验证）
        ]
        
        symbols = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            symbols.update(matches)
        
        return list(symbols)[:5]  # 最多返回5个股票代码
    
    def _calculate_importance(self, item: Dict) -> float:
        """计算内容重要性评分"""
        # 基于互动数据计算重要性
        retweet_count = item.get('retweet_count', 0)
        reply_count = item.get('reply_count', 0)
        like_count = item.get('like_count', 0)
        
        # 权重计算
        score = (
            retweet_count * 3 +    # 转发权重最高
            reply_count * 2 +      # 评论次之
            like_count * 1         # 点赞权重最低
        )
        
        # 标准化到0-1区间
        normalized_score = min(score / 1000, 1.0)
        
        return round(normalized_score, 3)
    
    def _should_include_article(self, article_data: Dict[str, Any], news_source: NewsSource) -> bool:
        """判断是否应该包含此文章"""
        # 基本长度检查
        content = article_data.get('content', '')
        if len(content) < 20:  # 内容太短
            return False
        
        # 关键词过滤
        filter_keywords = news_source.filter_keywords_list
        if filter_keywords:
            text_for_check = f"{article_data.get('title', '')} {content}".lower()
            if not any(keyword.lower() in text_for_check for keyword in filter_keywords):
                return False
        
        # 重要性过滤（雪球特有）
        importance_score = article_data.get('importance_score', 0)
        if importance_score < 0.001:  # 基本没有互动的内容可能不太重要
            return False
        
        return True

# 便捷函数
async def fetch_xueqiu_data(news_source: NewsSource) -> List[Dict[str, Any]]:
    """
    获取雪球数据的便捷函数
    
    Args:
        news_source: 雪球新闻源配置
        
    Returns:
        新闻文章列表
    """
    async with XueqiuAggregator() as aggregator:
        return await aggregator.fetch_xueqiu_timeline(news_source) 