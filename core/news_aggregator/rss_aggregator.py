"""
RSS新闻聚合器
负责从RSS源抓取新闻数据
"""

import asyncio
import aiohttp
import feedparser
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
import time
from newspaper import Article
import re
import ssl

from ..models.news_source import NewsSource, NewsSourceType, NewsSourceStatus
from ..models.news_article import NewsArticle, ArticleStatus

logger = logging.getLogger(__name__)

class RSSAggregator:
    """RSS新闻聚合器"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """
        初始化RSS聚合器
        
        Args:
            session: 可选的aiohttp客户端会话
        """
        self.session = session
        self._own_session = session is None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self._own_session:
            # SSL配置 - 添加更宽松的设置以处理证书问题
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                limit=100, 
                limit_per_host=30,
                ssl=ssl_context  # 使用宽松的SSL配置
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'InvestNote RSS Aggregator 1.0'
                }
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._own_session and self.session:
            await self.session.close()
    
    async def fetch_rss_feed(self, news_source: NewsSource) -> List[Dict[str, Any]]:
        """
        抓取RSS源
        
        Args:
            news_source: 新闻源配置
            
        Returns:
            新闻文章列表
        """
        try:
            logger.info(f"开始抓取RSS源: {news_source.name} ({news_source.url})")
            
            # 下载RSS内容
            rss_content = await self._download_rss_content(news_source.url)
            if not rss_content:
                raise ValueError("无法获取RSS内容")
            
            # 解析RSS
            feed = feedparser.parse(rss_content)
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS解析警告: {feed.bozo_exception}")
            
            # 提取文章
            articles = []
            max_articles = news_source.max_articles_per_fetch or 50
            
            for entry in feed.entries[:max_articles]:
                try:
                    article_data = await self._parse_rss_entry(entry, news_source)
                    if article_data and self._should_include_article(article_data, news_source):
                        articles.append(article_data)
                except Exception as e:
                    logger.error(f"解析RSS条目失败: {e}", exc_info=True)
                    continue
            
            logger.info(f"成功抓取 {len(articles)} 篇文章从 {news_source.name}")
            return articles
            
        except Exception as e:
            logger.error(f"抓取RSS源失败 {news_source.name}: {e}", exc_info=True)
            raise
    
    async def _download_rss_content(self, url: str) -> Optional[str]:
        """下载RSS内容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
                else:
                    logger.error(f"HTTP错误 {response.status}: {url}")
                    return None
        except Exception as e:
            logger.error(f"下载RSS内容失败 {url}: {e}")
            return None
    
    async def _parse_rss_entry(self, entry: Any, news_source: NewsSource) -> Optional[Dict[str, Any]]:
        """
        解析RSS条目
        
        Args:
            entry: feedparser条目
            news_source: 新闻源配置
            
        Returns:
            解析后的文章数据
        """
        try:
            # 基础信息提取
            title = self._clean_text(getattr(entry, 'title', ''))
            url = getattr(entry, 'link', '')
            
            if not title or not url:
                return None
            
            # 生成URL哈希用于去重
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
            
            # 时间处理
            published_at = self._parse_publish_time(entry)
            
            # 内容提取
            summary = self._extract_summary(entry)
            content = await self._extract_full_content(url)
            
            # 作者信息
            author = self._extract_author(entry)
            
            # 分类信息
            category = self._extract_category(entry)
            
            article_data = {
                'title': title,
                'url': url,
                'url_hash': url_hash,
                'content': content,
                'summary': summary,
                'author': author,
                'source_id': news_source.id,
                'source_name': news_source.name,
                'category': category,
                'published_at': published_at,
                'language': news_source.language,
                'region': news_source.region,
                'status': ArticleStatus.PENDING.value,
                'word_count': len(content) if content else len(summary) if summary else 0
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"解析RSS条目失败: {e}", exc_info=True)
            return None
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 规范化空白字符
        text = ' '.join(text.split())
        return text.strip()
    
    def _parse_publish_time(self, entry: Any) -> Optional[datetime]:
        """解析发布时间"""
        # 尝试多个时间字段
        time_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in time_fields:
            time_struct = getattr(entry, field, None)
            if time_struct:
                try:
                    return datetime(*time_struct[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    continue
        
        # 尝试解析字符串时间
        string_fields = ['published', 'updated', 'created']
        for field in string_fields:
            time_str = getattr(entry, field, None)
            if time_str:
                try:
                    # 使用feedparser的内置时间解析
                    parsed_time = feedparser._parse_date(time_str)
                    if parsed_time:
                        return datetime(*parsed_time[:6], tzinfo=timezone.utc)
                except:
                    continue
        
        return None
    
    def _extract_summary(self, entry: Any) -> str:
        """提取摘要"""
        # 尝试多个摘要字段
        summary_fields = ['summary', 'description', 'content', 'subtitle']
        
        for field in summary_fields:
            summary = getattr(entry, field, None)
            if summary:
                if isinstance(summary, list) and summary:
                    summary = summary[0].get('value', '') if isinstance(summary[0], dict) else str(summary[0])
                elif isinstance(summary, dict):
                    summary = summary.get('value', '')
                
                summary = self._clean_text(str(summary))
                if summary:
                    # 限制摘要长度
                    return summary[:1000] + "..." if len(summary) > 1000 else summary
        
        return ""
    
    async def _extract_full_content(self, url: str) -> Optional[str]:
        """提取文章全文内容"""
        try:
            # 使用newspaper3k提取全文
            article = Article(url, language='zh')
            article.download()
            article.parse()
            
            if article.text:
                return self._clean_text(article.text)
                
        except Exception as e:
            logger.debug(f"提取全文内容失败 {url}: {e}")
        
        return None
    
    def _extract_author(self, entry: Any) -> Optional[str]:
        """提取作者信息"""
        # 尝试多个作者字段
        author_fields = ['author', 'author_detail', 'creator']
        
        for field in author_fields:
            author = getattr(entry, field, None)
            if author:
                if isinstance(author, dict):
                    author = author.get('name', '') or author.get('email', '')
                elif isinstance(author, list) and author:
                    author = author[0]
                    if isinstance(author, dict):
                        author = author.get('name', '') or author.get('email', '')
                
                author = self._clean_text(str(author))
                if author:
                    return author[:255]  # 限制长度
        
        return None
    
    def _extract_category(self, entry: Any) -> Optional[str]:
        """提取分类信息"""
        # 尝试标签和分类字段
        if hasattr(entry, 'tags') and entry.tags:
            categories = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            if categories:
                return ', '.join(categories[:3])  # 最多3个分类
        
        # 尝试category字段
        category = getattr(entry, 'category', None)
        if category:
            return self._clean_text(str(category))[:100]
        
        return None
    
    def _should_include_article(self, article_data: Dict[str, Any], news_source: NewsSource) -> bool:
        """
        判断是否应该包含这篇文章
        
        Args:
            article_data: 文章数据
            news_source: 新闻源配置
            
        Returns:
            是否包含
        """
        # 检查关键词过滤
        if news_source.filter_keywords:
            title_and_summary = f"{article_data.get('title', '')} {article_data.get('summary', '')}".lower()
            
            # 如果没有包含任何关键词，则过滤掉
            has_keyword = any(keyword.lower() in title_and_summary 
                            for keyword in news_source.filter_keywords)
            if not has_keyword:
                return False
        
        # 检查分类过滤
        if news_source.filter_categories:
            article_category = article_data.get('category', '').lower()
            if article_category:
                has_category = any(category.lower() in article_category 
                                 for category in news_source.filter_categories)
                if not has_category:
                    return False
        
        # 检查发布时间（只获取最近的文章）
        published_at = article_data.get('published_at')
        if published_at:
            # 只获取最近7天的文章
            time_diff = datetime.now(timezone.utc) - published_at
            if time_diff.days > 7:
                return False
        
        return True 