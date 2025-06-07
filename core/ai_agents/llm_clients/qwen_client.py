#!/usr/bin/env python3

"""
千问LLM客户端
基于OpenAI库设计模式实现的阿里云百炼千问模型客户端
支持OpenAI兼容接口，提供同步和异步操作
"""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from typing import Any, Optional, Union

from dotenv import load_dotenv

try:
    from openai import AsyncOpenAI, OpenAI
    from openai.types.chat import ChatCompletion
    from openai.types.chat.chat_completion import Choice
except ImportError as e:
    raise ImportError("需要安装 openai 库: pip install openai>=1.0.0") from e

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


@dataclass
class QwenMessage:
    """千问消息对象"""

    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class QwenResponse:
    """千问响应对象"""

    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]
    usage: Optional[dict[str, int]] = None
    system_fingerprint: Optional[str] = None

    @property
    def content(self) -> Optional[str]:
        """获取响应内容"""
        if self.choices and len(self.choices) > 0:
            return self.choices[0].message.content
        return None

    @property
    def finish_reason(self) -> Optional[str]:
        """获取完成原因"""
        if self.choices and len(self.choices) > 0:
            return self.choices[0].finish_reason
        return None


@dataclass
class QwenStreamResponse:
    """千问流式响应对象"""

    id: str
    object: str
    created: int
    model: str
    choices: list[dict]
    usage: Optional[dict[str, int]] = None

    @property
    def content(self) -> Optional[str]:
        """获取增量内容"""
        if self.choices and len(self.choices) > 0:
            delta = self.choices[0].get("delta", {})
            return delta.get("content")
        return None

    @property
    def finish_reason(self) -> Optional[str]:
        """获取完成原因"""
        if self.choices and len(self.choices) > 0:
            return self.choices[0].get("finish_reason")
        return None


class QwenClient:
    """
    千问同步客户端
    基于OpenAI库设计模式，使用阿里云百炼OpenAI兼容接口
    """

    # 阿里云百炼支持的模型列表
    SUPPORTED_MODELS = [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-max-latest",
        "qwen-long",
        "qwen-vl-plus",
        "qwen-vl-max",
        "qwen-vl-max-latest",
        "qwen-vl-ocr-latest",
        "qwen-math-plus",
        "qwen-math-turbo",
        "qwen-coder-plus",
        "qwen-coder-turbo",
        "qwq-32b-preview",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen-turbo",
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        初始化千问客户端

        Args:
            api_key: 阿里云百炼API密钥，默认从环境变量DASHSCOPE_API_KEY获取
            base_url: API基础URL，默认使用阿里云百炼OpenAI兼容端点
            model: 默认使用的模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            **kwargs: 其他OpenAI客户端参数
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供API密钥，可通过api_key参数或DASHSCOPE_API_KEY环境变量设置")

        # 使用阿里云百炼的OpenAI兼容端点
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建OpenAI客户端
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

        logger.info(f"千问客户端初始化完成: model={model}, base_url={self.base_url}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 对于同步客户端，直接返回自身
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        # 同步客户端无需特殊清理操作
        pass

    # 添加chat_completion方法以支持测试脚本中的调用
    async def chat_completion(
        self,
        messages: list[Union[dict[str, str], QwenMessage]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, list[str]]] = None,
        **kwargs,
    ) -> Union[QwenResponse, Generator[QwenStreamResponse, None, None]]:
        """
        异步兼容的聊天完成方法（别名）

        这是为了兼容测试脚本中的调用方式而添加的方法
        实际上调用同步的chat_completions_create方法
        """
        return self.chat_completions_create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            tools=tools,
            tool_choice=tool_choice,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            n=n,
            stop=stop,
            **kwargs,
        )

    def chat_completions_create(
        self,
        messages: list[Union[dict[str, str], QwenMessage]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, list[str]]] = None,
        **kwargs,
    ) -> Union[QwenResponse, Generator[QwenStreamResponse, None, None]]:
        """
        创建聊天完成

        Args:
            messages: 对话消息列表
            model: 使用的模型名称
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数量
            top_p: 核心采样参数
            stream: 是否使用流式输出
            tools: 工具列表（function calling）
            tool_choice: 工具选择策略
            presence_penalty: 存在惩罚
            frequency_penalty: 频率惩罚
            n: 生成候选数量
            stop: 停止词
            **kwargs: 其他参数

        Returns:
            QwenResponse或流式响应生成器
        """
        try:
            # 处理消息格式
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, QwenMessage):
                    formatted_messages.append(msg.to_dict())
                elif isinstance(msg, dict):
                    formatted_messages.append(msg)
                else:
                    raise ValueError(f"不支持的消息格式: {type(msg)}")

            # 构建请求参数
            request_params = {
                "model": model or self.model,
                "messages": formatted_messages,
                "stream": stream,
            }

            # 添加可选参数
            if temperature is not None:
                request_params["temperature"] = temperature
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            if top_p is not None:
                request_params["top_p"] = top_p
            if tools is not None:
                request_params["tools"] = tools
            if tool_choice is not None:
                request_params["tool_choice"] = tool_choice
            if presence_penalty is not None:
                request_params["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                request_params["frequency_penalty"] = frequency_penalty
            if n is not None:
                request_params["n"] = n
            if stop is not None:
                request_params["stop"] = stop

            # 添加额外参数
            request_params.update(kwargs)

            logger.info(f"发送千问API请求: model={request_params['model']}, stream={stream}")

            # 调用OpenAI兼容接口
            response = self._client.chat.completions.create(**request_params)

            if stream:
                return self._handle_stream_response(response)
            else:
                return self._handle_response(response)

        except Exception as e:
            logger.error(f"千问API调用失败: {e}")
            raise

    def _handle_response(self, response: ChatCompletion) -> QwenResponse:
        """处理非流式响应"""
        return QwenResponse(
            id=response.id,
            object=response.object,
            created=response.created,
            model=response.model,
            choices=response.choices,
            usage=response.usage.model_dump() if response.usage else None,
            system_fingerprint=response.system_fingerprint,
        )

    def _handle_stream_response(
        self, response
    ) -> Generator[QwenStreamResponse, None, None]:
        """处理流式响应"""
        for chunk in response:
            yield QwenStreamResponse(
                id=chunk.id,
                object=chunk.object,
                created=chunk.created,
                model=chunk.model,
                choices=[choice.model_dump() for choice in chunk.choices]
                if chunk.choices
                else [],
                usage=chunk.usage.model_dump()
                if hasattr(chunk, "usage") and chunk.usage
                else None,
            )

    def simple_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        简单对话接口

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            model: 使用的模型
            **kwargs: 其他参数

        Returns:
            模型回复内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.chat_completions_create(
            messages=messages, model=model, **kwargs
        )

        return response.content or ""

    def function_call(
        self,
        messages: list[dict[str, str]],
        tools: list[dict],
        model: Optional[str] = None,
        **kwargs,
    ) -> QwenResponse:
        """
        函数调用接口

        Args:
            messages: 对话消息
            tools: 可用工具列表
            model: 使用的模型
            **kwargs: 其他参数

        Returns:
            包含工具调用的响应
        """
        return self.chat_completions_create(
            messages=messages, tools=tools, model=model, **kwargs
        )


class AsyncQwenClient:
    """
    千问异步客户端
    基于OpenAI库设计模式，使用阿里云百炼OpenAI兼容接口
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen-plus",
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        初始化千问异步客户端

        Args:
            api_key: 阿里云百炼API密钥
            base_url: API基础URL
            model: 默认使用的模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            **kwargs: 其他OpenAI客户端参数
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供API密钥，可通过api_key参数或DASHSCOPE_API_KEY环境变量设置")

        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建异步OpenAI客户端
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

        logger.info(f"千问异步客户端初始化完成: model={model}, base_url={self.base_url}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        # 异步客户端可以选择在这里关闭连接
        # 目前OpenAI客户端会自动管理连接，所以无需特殊处理
        pass

    # 添加chat_completion方法以支持测试脚本中的调用
    async def chat_completion(
        self,
        messages: list[Union[dict[str, str], QwenMessage]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        **kwargs,
    ) -> Union[QwenResponse, AsyncGenerator[QwenStreamResponse, None]]:
        """
        聊天完成方法（别名）

        这是为了兼容测试脚本中的调用方式而添加的方法
        实际上调用chat_completions_create方法
        """
        return await self.chat_completions_create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs,
        )

    async def chat_completions_create(
        self,
        messages: list[Union[dict[str, str], QwenMessage]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        **kwargs,
    ) -> Union[QwenResponse, AsyncGenerator[QwenStreamResponse, None]]:
        """
        异步创建聊天完成

        Args:
            messages: 对话消息列表
            model: 使用的模型名称
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            QwenResponse或异步流式响应生成器
        """
        try:
            # 处理消息格式
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, QwenMessage):
                    formatted_messages.append(msg.to_dict())
                elif isinstance(msg, dict):
                    formatted_messages.append(msg)
                else:
                    raise ValueError(f"不支持的消息格式: {type(msg)}")

            # 构建请求参数
            request_params = {
                "model": model or self.model,
                "messages": formatted_messages,
                "stream": stream,
            }

            # 添加可选参数
            if temperature is not None:
                request_params["temperature"] = temperature
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            if top_p is not None:
                request_params["top_p"] = top_p
            if tools is not None:
                request_params["tools"] = tools
            if tool_choice is not None:
                request_params["tool_choice"] = tool_choice

            request_params.update(kwargs)

            logger.info(
                f"发送千问异步API请求: model={request_params['model']}, stream={stream}"
            )

            # 调用异步OpenAI兼容接口
            response = await self._client.chat.completions.create(**request_params)

            if stream:
                return self._handle_async_stream_response(response)
            else:
                return self._handle_response(response)

        except Exception as e:
            logger.error(f"千问异步API调用失败: {e}")
            raise

    def _handle_response(self, response: ChatCompletion) -> QwenResponse:
        """处理非流式响应"""
        return QwenResponse(
            id=response.id,
            object=response.object,
            created=response.created,
            model=response.model,
            choices=response.choices,
            usage=response.usage.model_dump() if response.usage else None,
            system_fingerprint=response.system_fingerprint,
        )

    async def _handle_async_stream_response(
        self, response
    ) -> AsyncGenerator[QwenStreamResponse, None]:
        """处理异步流式响应"""
        async for chunk in response:
            yield QwenStreamResponse(
                id=chunk.id,
                object=chunk.object,
                created=chunk.created,
                model=chunk.model,
                choices=[choice.model_dump() for choice in chunk.choices]
                if chunk.choices
                else [],
                usage=chunk.usage.model_dump()
                if hasattr(chunk, "usage") and chunk.usage
                else None,
            )

    async def simple_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        异步简单对话接口

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            model: 使用的模型
            **kwargs: 其他参数

        Returns:
            模型回复内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.chat_completions_create(
            messages=messages, model=model, **kwargs
        )

        return response.content or ""


# 全局客户端实例（便捷使用）
_global_client: Optional[QwenClient] = None
_global_async_client: Optional[AsyncQwenClient] = None


def get_qwen_client(**kwargs) -> QwenClient:
    """
    获取全局千问客户端实例

    Args:
        **kwargs: 客户端初始化参数

    Returns:
        QwenClient实例
    """
    global _global_client
    if _global_client is None:
        _global_client = QwenClient(**kwargs)
    return _global_client


def get_async_qwen_client(**kwargs) -> AsyncQwenClient:
    """
    获取全局千问异步客户端实例

    Args:
        **kwargs: 客户端初始化参数

    Returns:
        AsyncQwenClient实例
    """
    global _global_async_client
    if _global_async_client is None:
        _global_async_client = AsyncQwenClient(**kwargs)
    return _global_async_client


# 便捷函数
def chat(prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
    """
    便捷的同步对话函数

    Args:
        prompt: 用户输入
        system_prompt: 系统提示词
        **kwargs: 其他参数

    Returns:
        模型回复
    """
    client = get_qwen_client()
    return client.simple_chat(prompt, system_prompt, **kwargs)


async def async_chat(prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
    """
    便捷的异步对话函数

    Args:
        prompt: 用户输入
        system_prompt: 系统提示词
        **kwargs: 其他参数

    Returns:
        模型回复
    """
    client = get_async_qwen_client()
    return await client.simple_chat(prompt, system_prompt, **kwargs)


def stream_chat(
    prompt: str, system_prompt: Optional[str] = None, **kwargs
) -> Generator[str, None, None]:
    """
    便捷的流式对话函数

    Args:
        prompt: 用户输入
        system_prompt: 系统提示词
        **kwargs: 其他参数

    Yields:
        模型回复片段
    """
    client = get_qwen_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    stream_response = client.chat_completions_create(
        messages=messages, stream=True, **kwargs
    )

    for chunk in stream_response:
        if chunk.content:
            yield chunk.content


async def async_stream_chat(
    prompt: str, system_prompt: Optional[str] = None, **kwargs
) -> AsyncGenerator[str, None]:
    """
    便捷的异步流式对话函数

    Args:
        prompt: 用户输入
        system_prompt: 系统提示词
        **kwargs: 其他参数

    Yields:
        模型回复片段
    """
    client = get_async_qwen_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    stream_response = await client.chat_completions_create(
        messages=messages, stream=True, **kwargs
    )

    async for chunk in stream_response:
        if chunk.content:
            yield chunk.content


# 向后兼容的类名
QwenLLMClient = QwenClient

if __name__ == "__main__":
    # 示例使用
    import asyncio

    def test_sync_client():
        """测试同步客户端"""
        print("=== 测试同步千问客户端 ===")

        try:
            client = QwenClient()

            # 简单对话
            response = client.simple_chat("你好，请介绍一下自己")
            print(f"简单对话回复: {response}")

            # 流式对话
            print("\n流式对话:")
            for chunk in stream_chat("讲一个简短的故事"):
                print(chunk, end="", flush=True)
            print("\n")

        except Exception as e:
            print(f"同步客户端测试失败: {e}")

    async def test_async_client():
        """测试异步客户端"""
        print("\n=== 测试异步千问客户端 ===")

        try:
            client = AsyncQwenClient()

            # 异步简单对话
            response = await client.simple_chat("你好，请介绍一下自己")
            print(f"异步对话回复: {response}")

            # 异步流式对话
            print("\n异步流式对话:")
            async for chunk in async_stream_chat("讲一个简短的故事"):
                print(chunk, end="", flush=True)
            print("\n")

        except Exception as e:
            print(f"异步客户端测试失败: {e}")

    # 运行测试
    test_sync_client()
    asyncio.run(test_async_client())
