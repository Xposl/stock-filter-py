# 千问客户端使用指南

## 概述

新的千问客户端基于OpenAI Python库的设计模式实现，使用阿里云百炼的OpenAI兼容接口，提供简洁易用的API。

## 特性

- 🔄 **OpenAI兼容**: 采用OpenAI库的设计模式和接口风格
- 🚀 **同步/异步**: 支持同步和异步两种调用方式
- 📡 **流式输出**: 支持实时流式响应
- 🛠️ **便捷函数**: 提供简化的便捷函数
- 🎯 **多模型支持**: 支持千问系列所有模型
- 🔧 **Function Calling**: 支持工具调用功能
- 📝 **完整类型提示**: 提供完整的Python类型提示

## 快速开始

### 1. 安装依赖

```bash
pip install openai>=1.0.0 dashscope>=1.14.0
```

### 2. 设置API密钥

```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

或在代码中设置：

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

client = QwenClient(api_key="your_api_key_here")
```

## 基础用法

### 同步客户端

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

# 创建客户端
client = QwenClient()

# 简单对话
response = client.simple_chat("你好，请介绍一下自己")
print(response)

# 带系统提示的对话
response = client.simple_chat(
    "现在几点了？",
    system_prompt="你是一个友好的助手"
)
print(response)

# 完整API调用
messages = [
    {"role": "system", "content": "你是一个投资顾问"},
    {"role": "user", "content": "请分析一下当前股市"}
]

response = client.chat_completions_create(
    messages=messages,
    temperature=0.7,
    max_tokens=500
)

print(f"回复: {response.content}")
print(f"模型: {response.model}")
print(f"Token使用: {response.usage}")
```

### 异步客户端

```python
import asyncio
from core.ai_agents.llm_clients.qwen_client import AsyncQwenClient

async def main():
    client = AsyncQwenClient()
    
    # 异步简单对话
    response = await client.simple_chat("解释一下什么是人工智能")
    print(response)
    
    # 异步完整API调用
    messages = [
        {"role": "user", "content": "用Python写一个Hello World程序"}
    ]
    
    response = await client.chat_completions_create(
        messages=messages,
        temperature=0.3
    )
    
    print(response.content)

# 运行异步函数
asyncio.run(main())
```

## 流式输出

### 同步流式

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

client = QwenClient()

messages = [
    {"role": "user", "content": "请讲一个关于AI的故事"}
]

# 流式响应
stream_response = client.chat_completions_create(
    messages=messages,
    stream=True,
    temperature=0.8
)

print("流式输出:")
for chunk in stream_response:
    if chunk.content:
        print(chunk.content, end="", flush=True)
print("\n")
```

### 异步流式

```python
import asyncio
from core.ai_agents.llm_clients.qwen_client import AsyncQwenClient

async def stream_demo():
    client = AsyncQwenClient()
    
    messages = [
        {"role": "user", "content": "解释深度学习的基本概念"}
    ]
    
    stream_response = await client.chat_completions_create(
        messages=messages,
        stream=True
    )
    
    print("异步流式输出:")
    async for chunk in stream_response:
        if chunk.content:
            print(chunk.content, end="", flush=True)
    print("\n")

asyncio.run(stream_demo())
```

## 便捷函数

### 同步便捷函数

```python
from core.ai_agents.llm_clients.qwen_client import chat, stream_chat

# 简单对话
response = chat("你好，世界！")
print(response)

# 流式对话
print("流式输出:")
for chunk in stream_chat("请介绍一下机器学习"):
    print(chunk, end="", flush=True)
print("\n")
```

### 异步便捷函数

```python
import asyncio
from core.ai_agents.llm_clients.qwen_client import async_chat, async_stream_chat

async def convenience_demo():
    # 异步简单对话
    response = await async_chat("解释量子计算")
    print(response)
    
    # 异步流式对话
    print("异步流式输出:")
    async for chunk in async_stream_chat("什么是区块链技术？"):
        print(chunk, end="", flush=True)
    print("\n")

asyncio.run(convenience_demo())
```

## 高级用法

### 使用QwenMessage对象

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient, QwenMessage

client = QwenClient()

# 使用QwenMessage对象
messages = [
    QwenMessage(role="system", content="你是一个技术专家"),
    QwenMessage(role="user", content="解释什么是微服务架构")
]

response = client.chat_completions_create(messages=messages)
print(response.content)
```

### 多模型切换

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

# 使用不同的模型
models = ["qwen-turbo", "qwen-plus", "qwen-max"]

for model in models:
    client = QwenClient(model=model)
    response = client.simple_chat("你好")
    print(f"模型 {model}: {response[:50]}...")
```

### Function Calling（工具调用）

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

client = QwenClient()

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

messages = [
    {"role": "user", "content": "北京今天天气怎么样？"}
]

response = client.function_call(
    messages=messages,
    tools=tools,
    model="qwen-max"
)

print(response.content)
if response.choices[0].message.tool_calls:
    print("工具调用:", response.choices[0].message.tool_calls)
```

### 全局客户端

```python
from core.ai_agents.llm_clients.qwen_client import get_qwen_client, get_async_qwen_client

# 获取全局同步客户端
client = get_qwen_client()
response = client.simple_chat("测试全局客户端")

# 获取全局异步客户端
async_client = get_async_qwen_client()
# response = await async_client.simple_chat("测试全局异步客户端")
```

## 配置选项

### 客户端初始化参数

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

client = QwenClient(
    api_key="your_api_key",                    # API密钥
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 基础URL
    model="qwen-plus",                         # 默认模型
    timeout=60,                                # 超时时间（秒）
    max_retries=3                              # 最大重试次数
)
```

### 支持的模型列表

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

print("支持的模型:", QwenClient.SUPPORTED_MODELS)
```

输出：
```
['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-max-latest', 
 'qwen-long', 'qwen-vl-plus', 'qwen-vl-max', 'qwen-vl-max-latest',
 'qwen-vl-ocr-latest', 'qwen-math-plus', 'qwen-math-turbo',
 'qwen-coder-plus', 'qwen-coder-turbo', 'qwq-32b-preview']
```

## 响应对象

### QwenResponse

```python
response = client.chat_completions_create(messages=messages)

print(f"响应ID: {response.id}")
print(f"模型: {response.model}")
print(f"内容: {response.content}")
print(f"完成原因: {response.finish_reason}")
print(f"Token使用情况: {response.usage}")
print(f"创建时间: {response.created}")
```

### QwenStreamResponse

```python
for chunk in client.chat_completions_create(messages=messages, stream=True):
    print(f"片段ID: {chunk.id}")
    print(f"内容: {chunk.content}")
    print(f"完成原因: {chunk.finish_reason}")
```

## 错误处理

```python
from core.ai_agents.llm_clients.qwen_client import QwenClient

try:
    client = QwenClient(api_key="invalid_key")
    response = client.simple_chat("测试")
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"API调用错误: {e}")
```

## 最佳实践

### 1. 环境变量配置

```bash
# .env 文件
DASHSCOPE_API_KEY=your_api_key_here
```

### 2. 异步使用

对于高并发场景，建议使用异步客户端：

```python
import asyncio
from core.ai_agents.llm_clients.qwen_client import AsyncQwenClient

async def batch_process():
    client = AsyncQwenClient()
    
    tasks = []
    for prompt in ["问题1", "问题2", "问题3"]:
        task = client.simple_chat(prompt)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### 3. 流式处理长文本

对于长文本生成，使用流式输出提升用户体验：

```python
def generate_article(topic):
    client = QwenClient()
    
    messages = [
        {"role": "user", "content": f"请写一篇关于{topic}的文章"}
    ]
    
    content = ""
    for chunk in client.chat_completions_create(messages=messages, stream=True):
        if chunk.content:
            content += chunk.content
            print(chunk.content, end="", flush=True)
    
    return content
```

### 4. 错误重试

```python
import time
from core.ai_agents.llm_clients.qwen_client import QwenClient

def robust_chat(prompt, max_retries=3):
    client = QwenClient()
    
    for attempt in range(max_retries):
        try:
            return client.simple_chat(prompt)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"重试 {attempt + 1}/{max_retries}: {e}")
            time.sleep(2 ** attempt)  # 指数退避
```

## 迁移指南

### 从旧版本迁移

如果您之前使用的是旧版本的QwenLLMClient，可以这样迁移：

```python
# 旧版本
async with QwenLLMClient() as client:
    response = await client.chat_completion(messages)
    content = response.content

# 新版本
client = QwenClient()
response = client.chat_completions_create(messages=messages)
content = response.content
```

### 向后兼容

新版本提供了向后兼容的别名：

```python
from core.ai_agents.llm_clients.qwen_client import QwenLLMClient

# QwenLLMClient 是 QwenClient 的别名
client = QwenLLMClient()  # 等同于 QwenClient()
```

## 常见问题

### Q: 如何选择合适的模型？

A: 
- `qwen-turbo`: 速度快，成本低，适合简单任务
- `qwen-plus`: 平衡性能和成本，推荐日常使用
- `qwen-max`: 最强性能，适合复杂任务

### Q: 如何处理Token限制？

A: 使用`max_tokens`参数控制输出长度：

```python
response = client.chat_completions_create(
    messages=messages,
    max_tokens=500  # 限制输出长度
)
```

### Q: 如何使用不同的温度参数？

A: 
- `temperature=0.0`: 确定性输出
- `temperature=0.7`: 平衡创造性和准确性
- `temperature=1.0`: 最大创造性

```python
response = client.chat_completions_create(
    messages=messages,
    temperature=0.7
)
```

## 更多资源

- [阿里云百炼控制台](https://bailian.console.aliyun.com/)
- [DashScope API文档](https://help.aliyun.com/zh/dashscope/)
- [OpenAI Python库文档](https://github.com/openai/openai-python) 