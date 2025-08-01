"""
雪球数据访问基础客户端
统一管理会话、令牌获取和HTTP请求
"""

import asyncio
import gzip
import logging
import os
import ssl
import urllib.request
from abc import ABC, abstractmethod
from http.cookiejar import CookieJar
from typing import Any, Optional

import aiohttp

# 可选依赖：pyppeteer
try:
    from pyppeteer import launch

    PYPPETEER_AVAILABLE = True
except ImportError:
    PYPPETEER_AVAILABLE = False

logger = logging.getLogger(__name__)


class XueqiuBaseClient(ABC):
    """雪球数据访问基础客户端"""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """
        初始化雪球基础客户端

        Args:
            session: 可选的aiohttp客户端会话
        """
        self.session = session
        self._own_session = session is None  # 只有我们创建的会话才由我们管理
        self.xqat = None  # 雪球访问令牌

        # 标准请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://xueqiu.com/",
            "Origin": "https://xueqiu.com",
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 只有当我们需要创建自己的会话时才创建
        if self._own_session and self.session is None:
            connector = aiohttp.TCPConnector(
                limit=100, limit_per_host=30, ssl=False  # 处理SSL证书问题
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers=self.headers
            )
            logger.debug("创建新的HTTP会话")
        elif self.session:
            logger.debug("使用外部提供的HTTP会话")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 只关闭我们自己创建的会话
        if self._own_session and self.session:
            await self.session.close()
            self.session = None
            logger.debug("关闭自有HTTP会话")
        # 对于外部传入的会话，不关闭，由外部管理

    async def _get_token_with_puppeteer(self) -> Optional[str]:
        """使用pyppeteer获取雪球的token"""
        if not PYPPETEER_AVAILABLE:
            logger.warning("pyppeteer未安装，无法使用浏览器方式获取token")
            return None

        try:
            # 获取环境变量或使用默认设置
            chromium_executable_path = os.environ.get("PYPPETEER_CHROMIUM_PATH")

            # 构建launch参数
            launch_args = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            }

            # 如果环境变量中指定了chromium路径，则使用它
            if chromium_executable_path and os.path.exists(chromium_executable_path):
                launch_args["executablePath"] = chromium_executable_path

            browser = await launch(**launch_args)
            page = await browser.newPage()

            # 设置User-Agent
            await page.setUserAgent(self.headers["User-Agent"])

            # 访问雪球网站
            await page.goto("https://xueqiu.com/", {"waitUntil": "networkidle0"})

            # 获取所有cookie
            cookies = await page.cookies()
            xqat = None

            # 查找xqat cookie
            for cookie in cookies:
                if cookie.get("name") == "xqat":
                    xqat = cookie.get("value")
                    break

            await browser.close()

            if xqat:
                logger.info("成功通过pyppeteer获取雪球token")
            else:
                logger.warning("pyppeteer获取token失败：未找到xqat cookie")

            return xqat

        except Exception as e:
            logger.error(f"使用pyppeteer获取token失败: {e}")
            return None

    def _get_token_with_urllib(self) -> Optional[str]:
        """使用urllib获取雪球token（备用方法）"""
        try:
            # 创建SSL上下文，处理证书验证问题
            context = ssl.create_default_context()
            
            # 在开发环境中，如果遇到证书问题，可以临时禁用验证
            # 生产环境建议配置正确的证书
            if os.environ.get("XUEQIU_DISABLE_SSL_VERIFY", "false").lower() == "true":
                logger.warning("已禁用SSL证书验证（仅用于开发环境）")
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            cookie = CookieJar()
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener = urllib.request.build_opener(handler)
            opener.addheaders = [
                ("Host", "xueqiu.com"),
                ("User-Agent", self.headers["User-Agent"]),
                ("Accept", self.headers["Accept"]),
                ("Accept-Language", self.headers["Accept-Language"]),
            ]

            # 使用SSL上下文打开URL
            opener.open("https://xueqiu.com/", context=context)

            for item in cookie:
                if item.name == "xqat":
                    logger.info("成功通过urllib获取雪球token")
                    return item.value

            logger.warning("urllib获取token失败：未找到xqat cookie")
            return None

        except ssl.SSLCertVerificationError as e:
            logger.error(f"SSL证书验证失败: {e}")
            logger.info("尝试使用不安全的SSL连接...")
            try:
                # 创建不安全的SSL上下文作为备用方案
                unsafe_context = ssl.create_default_context()
                unsafe_context.check_hostname = False
                unsafe_context.verify_mode = ssl.CERT_NONE
                
                cookie = CookieJar()
                handler = urllib.request.HTTPCookieProcessor(cookie)
                opener = urllib.request.build_opener(handler)
                opener.addheaders = [
                    ("Host", "xueqiu.com"),
                    ("User-Agent", self.headers["User-Agent"]),
                    ("Accept", self.headers["Accept"]),
                    ("Accept-Language", self.headers["Accept-Language"]),
                ]

                opener.open("https://xueqiu.com/", context=unsafe_context)

                for item in cookie:
                    if item.name == "xqat":
                        logger.info("成功通过不安全的SSL连接获取雪球token")
                        return item.value

                logger.warning("不安全的SSL连接也无法获取token")
                return None
                
            except Exception as fallback_e:
                logger.error(f"备用SSL连接也失败: {fallback_e}")
                return None
                
        except Exception as e:
            logger.error(f"使用urllib获取token失败: {e}")
            return None

    async def _ensure_token(self) -> bool:
        """确保有可用的token"""
        if self.xqat:
            return True

        # 首先尝试使用pyppeteer获取token
        self.xqat = await self._get_token_with_puppeteer()

        # 如果pyppeteer失败，尝试使用urllib作为备用方法
        if not self.xqat:
            logger.info("pyppeteer获取token失败，尝试使用urllib备用方法...")
            # 在异步环境中运行同步函数
            self.xqat = await asyncio.get_event_loop().run_in_executor(
                None, self._get_token_with_urllib
            )

        if not self.xqat:
            logger.error("无法获取雪球token，请检查网络连接")
            return False

        return True

    async def _async_request(
        self, url: str, retry: bool = True
    ) -> Optional[dict[str, Any]]:
        """
        异步HTTP请求

        Args:
            url: 请求的URL
            retry: 是否在请求失败时尝试重新获取token并重试

        Returns:
            解码后的JSON响应或None
        """
        # 确保有token
        if not await self._ensure_token():
            return None

        headers = self.headers.copy()
        headers["Cookie"] = f"xqat={self.xqat};"

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"雪球API HTTP错误 {response.status}: {url}")
                    return None

        except Exception as e:
            # 如果请求失败且允许重试，则尝试重新获取token并重试
            if retry:
                logger.warning(f"请求失败: {e}，正在尝试重新获取token...")
                # 重置token并重新获取
                self.xqat = None
                if await self._ensure_token():
                    # 重新请求（禁用重试以避免无限循环）
                    return await self._async_request(url, retry=False)

            logger.error(f"异步请求失败: {e}")
            return None

    def _sync_request(self, url: str, retry: bool = True) -> Optional[str]:
        """
        同步HTTP请求（兼容现有代码）

        Args:
            url: 请求的URL
            retry: 是否在请求失败时尝试重新获取token并重试

        Returns:
            解码后的响应内容或None
        """
        # 确保有token
        if not self.xqat:
            # 在同步环境中获取token
            self.xqat = self._get_token_with_urllib()
            if not self.xqat:
                logger.error("无法获取雪球token")
                return None

        headers = {
            "Host": "stock.xueqiu.com",
            "User-Agent": self.headers["User-Agent"],
            "Accept-Encoding": "gzip, deflate",
            "Cookie": f"xqat={self.xqat};",
        }

        try:
            # 创建安全的SSL上下文
            # URL安全验证
            if not self._is_safe_url(url):
                raise ValueError(f"不安全的URL方案: {url}")
                
            context = ssl.create_default_context()
            # 仅在必要时才禁用证书验证
            # context.check_hostname = False
            # context.verify_mode = ssl.CERT_NONE
            r = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(r, context=context)

            # 处理gzip压缩的响应
            content = response.read()
            if response.info().get("Content-Encoding") == "gzip":
                content = gzip.decompress(content)

            return content.decode("utf-8")

        except Exception as e:
            # 如果请求失败且允许重试，则尝试重新获取token并重试
            if retry:
                logger.warning(f"同步请求失败: {e}，正在尝试重新获取token...")
                # 重置token并重新获取
                self.xqat = None
                self.xqat = self._get_token_with_urllib()
                if self.xqat:
                    # 重新请求（禁用重试以避免无限循环）
                    return self._sync_request(url, retry=False)

            logger.error(f"同步请求失败: {e}")
            return None

    @staticmethod
    def _get_symbol(code: str) -> str:
        """转化股票代码"""
        if code.startswith("SZ") or code.startswith("SH"):
            return f"{code[:2]}{code[3:]}"
        return code[3:]

    def _is_safe_url(self, url: str) -> bool:
        """
        验证URL是否安全
        
        Args:
            url: 要验证的URL
            
        Returns:
            是否为安全的URL
        """
        # 允许的URL方案白名单
        safe_schemes = ["http", "https"]
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # 检查方案是否在白名单中
            if parsed.scheme.lower() not in safe_schemes:
                return False
                
            # 检查是否为雪球域名
            allowed_hosts = [
                "xueqiu.com",
                "stock.xueqiu.com", 
                "api.xueqiu.com",
                "api-dev.xueqiu.com"
            ]
            
            hostname = parsed.hostname
            if hostname:
                hostname = hostname.lower()
                # 检查是否为允许的主机或其子域名
                for allowed_host in allowed_hosts:
                    if hostname == allowed_host or hostname.endswith('.' + allowed_host):
                        return True
            
            return False
            
        except Exception:
            # URL解析失败，认为不安全
            return False

    # 抽象方法，子类必须实现
    @abstractmethod
    def get_client_type(self) -> str:
        """返回客户端类型"""
        pass
