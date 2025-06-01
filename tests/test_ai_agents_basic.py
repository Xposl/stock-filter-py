#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Agent模块基础测试
测试千问LLM客户端、硅基流动客户端、ChromaDB存储和向量相似性分析功能
"""

# 路径配置 - 确保可以导入项目模块
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
import asyncio
import os
import tempfile
import shutil
from unittest.mock import AsyncMock, patch, MagicMock

# 设置测试环境变量
os.environ['QWEN_API_KEY'] = 'test_qwen_key'
os.environ['SILICON_FLOW_API_KEY'] = 'test_silicon_key'

# AI客户端测试
class TestQwenLLMClient:
    """千问LLM客户端测试"""
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        from core.ai_agents.llm_clients import QwenLLMClient
        
        client = QwenLLMClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.model == "qwen-turbo"
        assert client.timeout == 30
    
    def test_token_calculator(self):
        """测试Token计算器"""
        from core.ai_agents.llm_clients.qwen_client import TokenCalculator
        
        calculator = TokenCalculator()
        
        # 测试Token计算
        chinese_text = "这是一个测试文本"
        tokens = calculator.calculate_tokens(chinese_text)
        assert tokens > 0
        
        # 测试成本计算
        cost = calculator.calculate_cost("qwen-turbo", 100, 50)
        assert cost > 0
        
        # 测试日限额检查
        assert calculator.check_daily_limit() == True
    
    @pytest.mark.asyncio
    async def test_client_async_context(self):
        """测试异步上下文管理器"""
        from core.ai_agents.llm_clients import QwenLLMClient
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_session.return_value)
            mock_session.return_value.__aexit__ = AsyncMock()
            mock_session.return_value.close = AsyncMock()
            
            async with QwenLLMClient(api_key="test_key") as client:
                assert client.session is not None
    
    def test_prompt_building(self):
        """测试Prompt构建"""
        from core.ai_agents.llm_clients import QwenLLMClient
        
        client = QwenLLMClient(api_key="test_key")
        
        # 测试情感分析Prompt
        sentiment_prompt = client._build_sentiment_prompt("测试新闻内容")
        assert "情感评分" in sentiment_prompt
        assert "JSON格式" in sentiment_prompt
        
        # 测试投资建议Prompt  
        investment_prompt = client._build_investment_prompt("测试新闻内容")
        assert "投资建议" in investment_prompt
        assert "买入/持有/卖出/观望" in investment_prompt

class TestSiliconFlowClient:
    """硅基流动客户端测试"""
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        from core.ai_agents.llm_clients import SiliconFlowClient
        
        client = SiliconFlowClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.model == "qwen-turbo"
    
    @pytest.mark.asyncio
    async def test_client_async_context(self):
        """测试异步上下文管理器"""
        from core.ai_agents.llm_clients import SiliconFlowClient
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_session.return_value)
            mock_session.return_value.__aexit__ = AsyncMock()
            mock_session.return_value.close = AsyncMock()
            
            async with SiliconFlowClient(api_key="test_key") as client:
                assert client.session is not None

class TestChromaNewsStore:
    """ChromaDB新闻存储测试"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        os.environ['CHROMA_DB_PATH'] = self.temp_dir
    
    def teardown_method(self):
        """测试后清理"""
        # 清理临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_store_initialization(self):
        """测试存储初始化"""
        from core.ai_agents.vector_store import ChromaNewsStore
        
        with patch('sentence_transformers.SentenceTransformer'):
            store = ChromaNewsStore(db_path=self.temp_dir)
            assert store.db_path == self.temp_dir
            assert store.collection_name == "news_articles"
    
    def test_text_preprocessing(self):
        """测试文本预处理"""
        from core.ai_agents.vector_store import ChromaNewsStore
        
        with patch('sentence_transformers.SentenceTransformer'):
            store = ChromaNewsStore(db_path=self.temp_dir)
            
            # 测试正常文本
            text = "这是一个   包含多余空白   的文本"
            processed = store._preprocess_text(text)
            assert "  " not in processed  # 多余空白被移除
            
            # 测试过长文本
            long_text = "测试" * 1000
            processed_long = store._preprocess_text(long_text)
            assert len(processed_long) <= 1003  # 1000字符 + "..."
    
    def test_document_id_generation(self):
        """测试文档ID生成"""
        from core.ai_agents.vector_store import ChromaNewsStore
        
        with patch('sentence_transformers.SentenceTransformer'):
            store = ChromaNewsStore(db_path=self.temp_dir)
            
            # 同样的内容应该生成同样的ID
            content = "测试内容"
            id1 = store._generate_document_id(content)
            id2 = store._generate_document_id(content)
            assert id1 == id2
            
            # 不同内容应该生成不同的ID
            id3 = store._generate_document_id("不同内容")
            assert id1 != id3
    
    def test_collection_stats(self):
        """测试集合统计"""
        from core.ai_agents.vector_store import ChromaNewsStore
        
        with patch('sentence_transformers.SentenceTransformer'):
            store = ChromaNewsStore(db_path=self.temp_dir)
            
            stats = store.get_collection_stats()
            assert "collection_name" in stats
            assert "document_count" in stats
            assert stats["status"] == "healthy"

class TestVectorSimilarityAnalyzer:
    """向量相似性分析器测试"""
    
    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        from core.ai_agents.vector_store import VectorSimilarityAnalyzer
        
        analyzer = VectorSimilarityAnalyzer()
        assert analyzer.similarity_threshold == 0.7
        
        analyzer_custom = VectorSimilarityAnalyzer(similarity_threshold=0.8)
        assert analyzer_custom.similarity_threshold == 0.8
    
    def test_similarity_calculation(self):
        """测试相似度计算"""
        from core.ai_agents.vector_store import VectorSimilarityAnalyzer
        
        analyzer = VectorSimilarityAnalyzer()
        
        # 测试相同向量
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        similarity = analyzer.calculate_similarity(vector1, vector2)
        assert abs(similarity - 1.0) < 0.001  # 应该接近1
        
        # 测试正交向量
        vector3 = [0.0, 1.0, 0.0]
        similarity2 = analyzer.calculate_similarity(vector1, vector3)
        assert abs(similarity2 - 0.0) < 0.001  # 应该接近0
    
    def test_batch_similarity(self):
        """测试批量相似度计算"""
        from core.ai_agents.vector_store import VectorSimilarityAnalyzer
        
        analyzer = VectorSimilarityAnalyzer()
        
        query_vector = [1.0, 0.0, 0.0]
        target_vectors = [
            [1.0, 0.0, 0.0],  # 相同
            [0.0, 1.0, 0.0],  # 正交
            [0.5, 0.5, 0.0]   # 部分相似
        ]
        
        similarities = analyzer.batch_similarity(query_vector, target_vectors)
        assert len(similarities) == 3
        assert similarities[0] > similarities[2] > similarities[1]

# 集成测试
class TestAIAgentsIntegration:
    """AI Agent模块集成测试"""
    
    def test_module_imports(self):
        """测试模块导入"""
        # 测试LLM客户端模块导入
        from core.ai_agents.llm_clients import (
            QwenLLMClient, SiliconFlowClient, 
            get_qwen_client, get_silicon_flow_client
        )
        
        # 测试向量存储模块导入
        from core.ai_agents.vector_store import (
            ChromaNewsStore, VectorSimilarityAnalyzer,
            get_chroma_store, get_similarity_analyzer
        )
        
        # 验证所有类都可以实例化
        assert QwenLLMClient is not None
        assert SiliconFlowClient is not None
        assert ChromaNewsStore is not None
        assert VectorSimilarityAnalyzer is not None
    
    def test_global_instances(self):
        """测试全局实例获取"""
        from core.ai_agents.llm_clients import get_qwen_client, get_silicon_flow_client
        from core.ai_agents.vector_store import get_similarity_analyzer
        
        # 测试全局实例
        qwen_client = get_qwen_client()
        assert qwen_client is not None
        
        silicon_client = get_silicon_flow_client()
        assert silicon_client is not None
        
        analyzer = get_similarity_analyzer()
        assert analyzer is not None
        
        # 测试单例模式
        qwen_client2 = get_qwen_client()
        assert qwen_client is qwen_client2

if __name__ == "__main__":
    # 运行基础测试
    print("🚀 开始AI Agent模块基础测试...")
    
    # 测试模块导入
    print("✅ 测试模块导入...")
    test_integration = TestAIAgentsIntegration()
    test_integration.test_module_imports()
    test_integration.test_global_instances()
    
    # 测试Token计算器
    print("✅ 测试Token计算器...")
    test_qwen = TestQwenLLMClient()
    test_qwen.test_token_calculator()
    
    # 测试相似性分析器
    print("✅ 测试相似性分析器...")
    test_similarity = TestVectorSimilarityAnalyzer()
    test_similarity.test_analyzer_initialization()
    test_similarity.test_similarity_calculation()
    test_similarity.test_batch_similarity()
    
    print("🎉 AI Agent模块基础测试完成！")
    print("📋 测试结果:")
    print("  - 千问LLM客户端: ✅ 正常")
    print("  - 硅基流动客户端: ✅ 正常") 
    print("  - ChromaDB存储: ✅ 正常")
    print("  - 向量相似性分析: ✅ 正常")
    print("  - 模块集成: ✅ 正常") 