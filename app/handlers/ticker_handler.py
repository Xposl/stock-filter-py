"""
股票处理器
实现股票相关的业务逻辑
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from app.entities import Ticker, TickerStatus, TickerType
from app.entities.ticker import TickerCreate, TickerUpdate, TickerDTO
from app.repositories.ticker_repository import TickerRepository
from app.services.database_service import get_database_service
from app.handlers.base_handler import BaseHandler
from app.utils.data_sources.xueqiu_source import XueqiuTicker
from app.utils.dongcai_ticker import DongCaiTicker
from app.utils.utils import UtilsHelper

logger = logging.getLogger(__name__)

class TickerHandler(BaseHandler):
    """股票业务逻辑处理器"""
    
    def __init__(self):
        super().__init__()
        self.db_service = get_database_service()
        self.ticker_repo = TickerRepository(self.db_service)
    
    async def create_ticker(
        self,
        code: str,
        name: str,
        ticker_type: int = 1,  # TickerType.STOCK.value
        market_id: int = 0,
        source: int = 1,
        remark: Optional[str] = None,
        pe_forecast: Optional[float] = None,
        pettm: Optional[float] = None,
        pb: Optional[float] = None,
        total_share: Optional[float] = None,
        lot_size: int = 100,
        update_date: Optional[datetime] = None,
        listed_date: Optional[datetime] = None
    ) -> Ticker:
        """创建新股票
        
        Args:
            code: 股票代码
            name: 股票名称
            ticker_type: 股票类型 (对应TickerType枚举)
            market_id: 市场ID，关联markets表
            source: 数据来源
            remark: 备注信息
            pe_forecast: 预测市盈率
            pettm: 市盈率
            pb: 市净率
            total_share: 总股本
            lot_size: 每手股数
            update_date: 更新日期
            listed_date: 上市日期
            
        Returns:
            创建的股票实体
        """
        try:
            # 验证必填字段
            self._validate_required_field(code, "股票代码")
            self._validate_required_field(name, "股票名称")
            
            # 验证股票代码格式
            self._validate_ticker_code(code)
            
            # 验证股票类型
            valid_types = [t.value for t in TickerType]
            if ticker_type not in valid_types:
                raise ValueError(f"ticker_type必须是以下值之一: {valid_types}")
            
            # 检查股票代码是否已存在
            existing_ticker = await self.ticker_repo.get_by_code(code)
            if existing_ticker:
                raise ValueError(f"股票代码已存在: {code}")
            
            # 创建股票数据
            ticker_data = {
                "code": code.strip(),
                "name": name.strip(),
                "type": ticker_type,
                "market_id": market_id,
                "source": source,
                "status": TickerStatus.ACTIVE.value,
                "is_deleted": False,
                "remark": remark,
                "pe_forecast": pe_forecast,
                "pettm": pettm,
                "pb": pb,
                "total_share": total_share,
                "lot_size": lot_size,
                "update_date": update_date,
                "listed_date": listed_date
            }
            
            # 使用字典创建实体
            create_model = TickerCreate(**ticker_data)
            
            # 创建股票
            ticker = await self.ticker_repo.create(create_model)
            
            self._log_operation("create", str(ticker.id), "system", {"code": code, "name": name})
            logger.info(f"✅ 创建股票: {ticker.id}, 代码: {code}, 名称: {name}")
            return ticker
            
        except Exception as e:
            logger.error(f"❌ 创建股票失败: {e}")
            raise ValueError(f"创建股票失败: {e}") from e
        
    def get_sources_tickers(self) -> dict[str, Ticker]:
        """获取股票列表
        Returns:
            dict: 以股票代码为键的股票信息字典
        """
        data = {}
        tickers = DongCaiTicker().get_tickers()
        for ticker in tickers:
            data[ticker.code] = ticker
        return data
        
    def sync_tickers(self) -> bool:
        """同步所有股票数据并插入到数据库

        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取最新的股票列表
            new_tickers = self.get_sources_tickers()
            # 获取现有的股票数据
            existing_tickers = {ticker.code: ticker for ticker in self.ticker_repo.get_active_tickers(limit=-1)} 

            # 使用单独的数据库连接进行批量处理，避免锁冲突
            db_adapter = self.ticker_repository.db

            # 处理新增和更新股票
            processed_count = 0
            total = len(new_tickers)
            batch_size = 5  # 减小批处理大小，更频繁地提交事务

            xueqiu = XueqiuTicker()
            for i, code in enumerate(new_tickers):
                try:
                    UtilsHelper().run_process(i, total, "处理项目", f"{code}")
                    ticker = new_tickers[code]
                    if code not in existing_tickers:
                        # 获取新股详情
                        new_ticker = xueqiu.get_ticker(ticker.code, ticker.name)
                        if new_ticker:
                            value = new_ticker.model_dump()
                            value["id"] = None
                            self.ticker_repo.create(
                                **value
                            )
                            processed_count += 1
                    elif code in existing_tickers:
                        self.ticker_repo.soft_delete_ticker(existing_tickers[code]['id'])
                except Exception as e:
                    logger.error(f"处理股票 {code} 时出错: {e}", exc_info=True)
                    continue

            # 处理已删除的股票
            for i, code in enumerate(existing_tickers):
                if code not in new_tickers:
                    UtilsHelper().run_process(
                        i, len(existing_tickers), "删除项目", f"{code}"
                    )
                    self.ticker_repo.soft_delete_ticker(existing_tickers[code]['id'])
            return True

        except Exception as e:
            logger.error(f"更新股票数据出错: {str(e)}")
            return False
    
    async def get_ticker_by_id(
        self,
        ticker_id: int
    ) -> Optional[Ticker]:
        """
        根据ID获取股票
        
        Args:
            ticker_id: 股票ID
            
        Returns:
            股票实体或None
        """
        try:
            ticker = await self.ticker_repo.get_by_id(ticker_id)
            
            if ticker:
                logger.info(f"✅ 获取股票: {ticker_id}")
            else:
                logger.warning(f"⚠️ 股票不存在: {ticker_id}")
            
            return ticker
                
        except Exception as e:
            logger.error(f"❌ 获取股票失败: {e}")
            raise Exception(f"获取股票失败: {str(e)}")
    
    async def get_ticker_by_code(
        self,
        code: str
    ) -> Optional[Ticker]:
        """
        根据股票代码获取股票
        
        Args:
            code: 股票代码
            
        Returns:
            股票实体或None
        """
        try:
            ticker = await self.ticker_repo.get_by_code(code)
            
            if ticker:
                logger.info(f"✅ 获取股票: {code}")
            else:
                logger.warning(f"⚠️ 股票不存在: {code}")
            
            return ticker
                
        except Exception as e:
            logger.error(f"❌ 获取股票失败: {e}")
            raise Exception(f"获取股票失败: {str(e)}")
    
    async def search_tickers(
        self,
        keyword: str,
        ticker_type: Optional[int] = None,
        market_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Ticker], int]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            ticker_type: 股票类型过滤
            market_id: 市场ID过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            (匹配的股票列表, 总数)
        """
        try:
            if not keyword or not keyword.strip():
                # 如果没有关键词，返回空结果
                return [], 0
            
            keyword = keyword.strip()
            
            # 转换股票类型
            ticker_type_enum = None
            if ticker_type:
                try:
                    ticker_type_enum = TickerType(ticker_type)
                except ValueError:
                    raise ValueError(f"无效的股票类型: {ticker_type}")
            
            # 使用Repository的搜索方法
            tickers = await self.ticker_repo.search_tickers(
                keyword=keyword,
                ticker_type=ticker_type_enum,
                market_id=market_id,
                limit=limit,
                offset=offset
            )
            
            # 计算搜索结果总数（简化实现）
            total = len(tickers)
            
            logger.info(f"✅ 搜索股票: 关键词: {keyword}, 类型: {ticker_type}, 市场: {market_id}, 结果: {len(tickers)}")
            return tickers, total
            
        except Exception as e:
            logger.error(f"❌ 搜索股票失败: {e}")
            raise Exception(f"搜索股票失败: {str(e)}")
    
    async def get_active_tickers(
        self,
        ticker_type: Optional[int] = None,
        market_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Ticker], int]:
        """
        获取活跃股票列表
        
        Args:
            ticker_type: 股票类型过滤
            market_id: 市场ID过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            (股票列表, 总数)
        """
        try:
            # 转换股票类型
            ticker_type_enum = None
            if ticker_type:
                try:
                    ticker_type_enum = TickerType(ticker_type)
                except ValueError:
                    raise ValueError(f"无效的股票类型: {ticker_type}")
            
            if ticker_type_enum:
                # 按类型获取
                tickers = await self.ticker_repo.get_by_type(ticker_type_enum)
                total = len(tickers)
            elif market_id:
                # 按市场获取
                tickers = await self.ticker_repo.get_by_market_id(market_id)
                total = len(tickers)
            else:
                # 获取所有活跃股票
                tickers = await self.ticker_repo.get_active_tickers(limit=limit, offset=offset)
                # 获取总数（简化实现）
                total = len(tickers)
            
            logger.info(f"✅ 获取活跃股票: 类型: {ticker_type}, 市场: {market_id}, 数量: {len(tickers)}")
            return tickers, total
            
        except Exception as e:
            logger.error(f"❌ 获取活跃股票失败: {e}")
            raise Exception(f"获取活跃股票失败: {str(e)}")
    
    async def update_ticker(
        self,
        ticker_id: int,
        name: Optional[str] = None,
        ticker_type: Optional[int] = None,
        market_id: Optional[int] = None,
        source: Optional[int] = None,
        status: Optional[str] = None,
        remark: Optional[str] = None,
        pe_forecast: Optional[float] = None,
        pettm: Optional[float] = None,
        pb: Optional[float] = None,
        total_share: Optional[float] = None,
        lot_size: Optional[int] = None,
        update_date: Optional[datetime] = None,
        listed_date: Optional[datetime] = None
    ) -> Optional[Ticker]:
        """
        更新股票信息
        
        Args:
            ticker_id: 股票ID
            name: 新名称
            ticker_type: 新股票类型
            market_id: 新市场ID
            source: 新数据来源
            status: 新状态
            remark: 新备注信息
            pe_forecast: 新预测市盈率
            pettm: 新市盈率
            pb: 新市净率
            total_share: 新总股本
            lot_size: 新每手股数
            update_date: 新更新日期
            listed_date: 新上市日期
            
        Returns:
            更新后的股票实体
        """
        try:
            # 先获取股票验证存在性
            ticker = await self.ticker_repo.get_by_id(ticker_id)
            if not ticker:
                logger.warning(f"⚠️ 股票不存在: {ticker_id}")
                return None
            
            # 准备更新数据
            update_data = {}
            if name is not None:
                self._validate_required_field(name, "股票名称")
                update_data["name"] = name.strip()
            
            if ticker_type is not None:
                valid_types = [t.value for t in TickerType]
                if ticker_type not in valid_types:
                    raise ValueError(f"ticker_type必须是以下值之一: {valid_types}")
                update_data["type"] = ticker_type
            
            if market_id is not None:
                update_data["market_id"] = market_id
            
            if source is not None:
                update_data["source"] = source
            
            if status is not None:
                valid_statuses = [s.value for s in TickerStatus]
                if status not in valid_statuses:
                    raise ValueError(f"status必须是以下值之一: {valid_statuses}")
                update_data["status"] = status
            
            if remark is not None:
                update_data["remark"] = remark
            
            if pe_forecast is not None:
                update_data["pe_forecast"] = pe_forecast
            
            if pettm is not None:
                update_data["pettm"] = pettm
            
            if pb is not None:
                update_data["pb"] = pb
            
            if total_share is not None:
                update_data["total_share"] = total_share
            
            if lot_size is not None:
                update_data["lot_size"] = lot_size
            
            if update_date is not None:
                update_data["update_date"] = update_date
            
            if listed_date is not None:
                update_data["listed_date"] = listed_date
            
            # 如果没有任何更新数据，返回原股票
            if not update_data:
                logger.info(f"✅ 无更新数据，返回原股票: {ticker_id}")
                return ticker
            
            # 执行更新
            update_model = TickerUpdate(**update_data)
            updated_ticker = await self.ticker_repo.update(
                ticker_id, update_model
            )
            
            self._log_operation("update", str(ticker_id), "system", update_data)
            logger.info(f"✅ 更新股票: {ticker_id}")
            return updated_ticker
                
        except Exception as e:
            logger.error(f"❌ 更新股票失败: {e}")
            raise Exception(f"更新股票失败: {str(e)}")
    
    async def delete_ticker(
        self,
        ticker_id: int,
        soft_delete: bool = True
    ) -> bool:
        """
        删除股票
        
        Args:
            ticker_id: 股票ID
            soft_delete: 是否软删除（更新状态）
            
        Returns:
            删除是否成功
        """
        try:
            # 验证存在性
            ticker = await self.ticker_repo.get_by_id(ticker_id)
            if not ticker:
                logger.warning(f"⚠️ 股票不存在: {ticker_id}")
                return False
            
            if soft_delete:
                # 软删除：更新状态为已删除
                update_data = TickerUpdate(
                    status=TickerStatus.DELETED.value,
                    is_deleted=True
                )
                await self.ticker_repo.update(ticker_id, update_data)
                logger.info(f"✅ 软删除股票: {ticker_id}")
            else:
                # 硬删除：物理删除记录
                success = await self.ticker_repo.delete(ticker_id)
                if success:
                    logger.info(f"✅ 硬删除股票: {ticker_id}")
                else:
                    logger.error(f"❌ 硬删除股票失败: {ticker_id}")
                    return False
            
            self._log_operation("delete", str(ticker_id), "system", {"soft_delete": soft_delete})
            return True
                
        except Exception as e:
            logger.error(f"❌ 删除股票失败: {e}")
            raise Exception(f"删除股票失败: {str(e)}")
    
    async def get_ticker_statistics(self) -> Dict[str, Any]:
        """
        获取股票统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = await self.ticker_repo.get_ticker_statistics()
            
            logger.info(f"✅ 获取股票统计信息")
            return stats
                
        except Exception as e:
            logger.error(f"❌ 获取股票统计信息失败: {e}")
            return {
                "total_count": 0,
                "active_count": 0,
                "inactive_count": 0,
                "deleted_count": 0,
                "stock_count": 0,
                "index_count": 0,
                "bond_count": 0,
                "etf_count": 0,
                "market_count": 0,
                "error": str(e)
            }
    
    async def get_tickers_by_market(
        self,
        market_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Ticker], int]:
        """
        根据市场获取股票列表
        
        Args:
            market_id: 市场ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            (股票列表, 总数)
        """
        try:
            tickers = await self.ticker_repo.get_by_market_id(market_id)
            total = len(tickers)
            
            logger.info(f"✅ 获取市场股票: {market_id}, 数量: {len(tickers)}")
            return tickers, total
            
        except Exception as e:
            logger.error(f"❌ 获取市场股票失败: {e}")
            raise Exception(f"获取市场股票失败: {str(e)}")
    
    async def get_tickers_with_market_info(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取带市场信息的股票列表
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            带市场信息的股票列表
        """
        try:
            tickers_with_market = await self.ticker_repo.get_tickers_with_market_info(limit=limit, offset=offset)
            
            logger.info(f"✅ 获取带市场信息的股票: 数量: {len(tickers_with_market)}")
            return tickers_with_market
            
        except Exception as e:
            logger.error(f"❌ 获取带市场信息的股票失败: {e}")
            raise Exception(f"获取带市场信息的股票失败: {str(e)}")
    
    def _validate_ticker_code(self, code: str) -> None:
        """
        验证股票代码格式
        
        Args:
            code: 股票代码
            
        Raises:
            ValueError: 格式错误时抛出
        """
        if not code or not code.strip():
            raise ValueError("股票代码不能为空")
        
        # 验证市场前缀格式
        valid_prefixes = ['SH.', 'SZ.', 'HK.', 'US.']
        if not any(code.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f"股票代码格式错误，必须以以下前缀开头: {', '.join(valid_prefixes)}")
        
        # 验证代码长度
        if len(code) < 6 or len(code) > 20:
            raise ValueError("股票代码长度必须在6-20字符之间")

# 单例模式 - 保存handler实例
_ticker_handler_instance = None

def get_ticker_handler() -> TickerHandler:
    """获取股票处理器实例 (单例模式)"""
    global _ticker_handler_instance
    if _ticker_handler_instance is None:
        _ticker_handler_instance = TickerHandler()
    return _ticker_handler_instance 