"""
基础仓储抽象类
定义通用的数据访问接口和操作
"""

import json
import logging
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.services.database_service import DatabaseService
from app.logging_config import logger

# 泛型类型变量
T = TypeVar('T', bound=BaseModel)
CreateT = TypeVar('CreateT', bound=BaseModel)
UpdateT = TypeVar('UpdateT', bound=BaseModel)


class QueryPerformanceMonitor:
    """查询性能监控器"""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # 1秒
        self.query_stats = {}
    
    async def monitor_query(self, query_name: str, query_func):
        """监控查询执行"""
        start_time = time.time()
        
        try:
            result = await query_func()
            execution_time = time.time() - start_time
            
            # 记录统计信息
            self._record_query_stats(query_name, execution_time, True)
            
            # 检查慢查询
            if execution_time > self.slow_query_threshold:
                logger.warning(f"慢查询检测: {query_name} 执行时间: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_query_stats(query_name, execution_time, False)
            raise
    
    def _record_query_stats(self, query_name: str, execution_time: float, success: bool):
        """记录查询统计"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                "total_count": 0,
                "success_count": 0,
                "total_time": 0,
                "max_time": 0,
                "min_time": float('inf')
            }
        
        stats = self.query_stats[query_name]
        stats["total_count"] += 1
        if success:
            stats["success_count"] += 1
        
        stats["total_time"] += execution_time
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["min_time"] = min(stats["min_time"], execution_time)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {}
        
        for query_name, stats in self.query_stats.items():
            avg_time = stats["total_time"] / stats["total_count"] if stats["total_count"] > 0 else 0
            success_rate = (stats["success_count"] / stats["total_count"] * 100) if stats["total_count"] > 0 else 0
            
            report[query_name] = {
                "total_executions": stats["total_count"],
                "success_rate": f"{success_rate:.1f}%",
                "avg_execution_time": f"{avg_time:.3f}s",
                "max_execution_time": f"{stats['max_time']:.3f}s",
                "min_execution_time": f"{stats['min_time']:.3f}s",
                "total_time": f"{stats['total_time']:.3f}s"
            }
        
        return report


class BaseRepository(Generic[T, CreateT, UpdateT], ABC):
    """
    基础仓储抽象类
    
    提供通用的CRUD操作接口
    """
    
    def __init__(self, db_service: DatabaseService):
        """初始化仓储"""
        self.db_service = db_service
        
        # 性能监控器
        self.performance_monitor = QueryPerformanceMonitor()
        
        # 缓存配置
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._default_ttl = 300  # 5分钟
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """表名"""
        pass
    
    @property
    @abstractmethod
    def entity_class(self) -> Type[T]:
        """实体类"""
        pass
    
    @property
    @abstractmethod
    def create_class(self) -> Type[CreateT]:
        """创建模型类"""
        pass
    
    @property
    @abstractmethod
    def update_class(self) -> Type[UpdateT]:
        """更新模型类"""
        pass
    
    @abstractmethod
    def get_json_fields(self) -> List[str]:
        """获取JSON字段列表"""
        pass
    
    def _serialize_json_field(self, value: Any) -> Optional[str]:
        """序列化JSON字段"""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    
    def _deserialize_json_field(self, value: Any) -> Any:
        """反序列化JSON字段"""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return value
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> T:
        """将字典转换为实体对象"""
        try:
            # 反序列化JSON字段
            for field in self.get_json_fields():
                if field in data:
                    data[field] = self._deserialize_json_field(data[field])
            
            return self.entity_class.from_dict(data)
        except Exception as e:
            logger.error(f"将字典转换为{self.entity_class.__name__}实体失败: {e}, 数据: {data}")
            raise ValueError(f"将字典转换为实体失败: {e}") from e
    
    async def create(self, entity_data: CreateT) -> T:
        """创建新实体"""
        query_name = f"{self.table_name}_create"
        
        async def _create():
            try:
                async with self.db_service.get_async_session() as session:
                    # 获取创建数据 - 使用完整数据，不排除默认值
                    create_dict = entity_data.model_dump()
                    
                    # 过滤掉值为 None 的字段（但保留其他默认值如 UUID）
                    filtered_dict = {k: v for k, v in create_dict.items() if v is not None}
                    
                    # 构建插入SQL
                    columns = list(filtered_dict.keys())
                    placeholders = [f":{col}" for col in columns]
                    
                    sql = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    # 处理JSON字段
                    params = {}
                    for key, value in filtered_dict.items():
                        if key in self.get_json_fields():
                            params[key] = self._serialize_json_field(value)
                        else:
                            params[key] = value
                    
                    # 执行插入
                    result = await session.execute(text(sql), params)
                    await session.commit()
                    
                    # 获取插入的ID
                    entity_id = result.lastrowid
                    
                    # 返回创建的实体
                    return await self.get_by_id(entity_id)
                    
            except Exception as e:
                logger.error(f"创建{self.table_name}实体失败: {e}")
                raise
        
        return await self.performance_monitor.monitor_query(query_name, _create)
    
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """根据ID获取实体"""
        cache_key = f"{self.table_name}_get_by_id_{entity_id}"
        query_name = f"{self.table_name}_get_by_id"
        
        async def _get():
            try:
                async with self.db_service.get_async_session() as session:
                    sql = f"SELECT * FROM {self.table_name} WHERE id = :id"
                    result = await session.execute(text(sql), {"id": entity_id})
                    row = result.fetchone()
                    
                    if not row:
                        return None
                    
                    # 转换为字典
                    data = dict(row._mapping)
                    return self._dict_to_entity(data)
                    
            except Exception as e:
                logger.error(f"根据ID获取{self.table_name}实体失败: {e}")
                raise
        
        return await self._get_cached_or_execute(
            cache_key,
            lambda: self.performance_monitor.monitor_query(query_name, _get),
            ttl=300
        )
    
    async def update(self, entity_id: int, update_data: Union[UpdateT, Dict[str, Any]]) -> Optional[T]:
        """更新实体"""
        query_name = f"{self.table_name}_update"
        
        async def _update():
            try:
                async with self.db_service.get_async_session() as session:
                    # 获取更新数据
                    if isinstance(update_data, dict):
                        update_dict = update_data
                    else:
                        update_dict = update_data.model_dump(exclude_unset=True)
                    
                    if not update_dict:
                        return await self.get_by_id(entity_id)
                    
                    # 构建更新SQL
                    set_clauses = [f"{col} = :{col}" for col in update_dict.keys()]
                    sql = f"""
                        UPDATE {self.table_name} 
                        SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :entity_id
                    """
                    
                    # 处理JSON字段
                    params = {"entity_id": entity_id}
                    for key, value in update_dict.items():
                        if key in self.get_json_fields():
                            params[key] = self._serialize_json_field(value)
                        else:
                            params[key] = value
                    
                    # 执行更新
                    await session.execute(text(sql), params)
                    await session.commit()
                    
                    if params["entity_id"] == entity_id:
                        # 清除相关缓存
                        self._invalidate_cache(f"{self.table_name}_get_by_id_{entity_id}")
                        return await self.get_by_id(entity_id)
                    
                    return None
                    
            except Exception as e:
                logger.error(f"更新{self.table_name}实体失败: {e}")
                raise
        
        return await self.performance_monitor.monitor_query(query_name, _update)
    
    async def delete(self, entity_id: int) -> bool:
        """删除实体"""
        query_name = f"{self.table_name}_delete"
        
        async def _delete():
            try:
                async with self.db_service.get_async_session() as session:
                    sql = f"DELETE FROM {self.table_name} WHERE id = :id"
                    result = await session.execute(text(sql), {"id": entity_id})
                    await session.commit()
                    
                    success = result.rowcount > 0
                    if success:
                        # 清除相关缓存
                        self._invalidate_cache(f"{self.table_name}_get_by_id_{entity_id}")
                    
                    return success
                    
            except Exception as e:
                logger.error(f"删除{self.table_name}实体失败: {e}")
                raise
        
        return await self.performance_monitor.monitor_query(query_name, _delete)
    
    async def _execute_query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行查询并返回结果列表"""
        try:
            async with self.db_service.get_async_session() as session:
                result = await session.execute(text(sql), params or {})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
    
    async def _execute_query_one(self, sql: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """执行查询并返回单个结果"""
        try:
            async with self.db_service.get_async_session() as session:
                result = await session.execute(text(sql), params or {})
                row = result.fetchone()
                return dict(row._mapping) if row else None
        except Exception as e:
            logger.error(f"执行单个查询失败: {e}")
            raise
    
    async def _execute_insert(self, sql: str, params: Dict[str, Any] = None) -> int:
        """执行插入并返回插入的ID"""
        try:
            async with self.db_service.get_async_session() as session:
                result = await session.execute(text(sql), params or {})
                await session.commit()
                return result.lastrowid
        except Exception as e:
            logger.error(f"执行插入失败: {e}")
            raise
    
    async def _execute_update(self, sql: str, params: Dict[str, Any] = None) -> int:
        """执行更新并返回影响的行数"""
        try:
            async with self.db_service.get_async_session() as session:
                result = await session.execute(text(sql), params or {})
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"执行更新失败: {e}")
            raise
    
    async def _execute_delete(self, sql: str, params: Dict[str, Any] = None) -> int:
        """执行删除并返回影响的行数"""
        try:
            async with self.db_service.get_async_session() as session:
                result = await session.execute(text(sql), params or {})
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"执行删除失败: {e}")
            raise
    
    async def list_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        order_by: str = "id",
        order_direction: str = "DESC"
    ) -> List[T]:
        """获取实体列表"""
        query_name = f"{self.table_name}_list_all"
        
        async def _list():
            try:
                async with self.db_service.get_async_session() as session:
                    sql = f"""
                        SELECT * FROM {self.table_name}
                        ORDER BY {order_by} {order_direction}
                        LIMIT :limit OFFSET :offset
                    """
                    
                    result = await session.execute(text(sql), {
                        "limit": limit,
                        "offset": offset
                    })
                    rows = result.fetchall()
                    
                    return [self._dict_to_entity(dict(row._mapping)) for row in rows]
                    
            except Exception as e:
                logger.error(f"获取{self.table_name}列表失败: {e}")
                raise
        
        return await self.performance_monitor.monitor_query(query_name, _list)
    
    async def count(self, where_clause: str = "", params: Dict[str, Any] = None) -> int:
        """获取实体数量"""
        query_name = f"{self.table_name}_count"
        
        async def _count():
            try:
                async with self.db_service.get_async_session() as session:
                    sql = f"SELECT COUNT(*) as count FROM {self.table_name}"
                    if where_clause:
                        sql += f" WHERE {where_clause}"
                    
                    result = await session.execute(text(sql), params or {})
                    row = result.fetchone()
                    return row.count if row else 0
                    
            except Exception as e:
                logger.error(f"获取{self.table_name}数量失败: {e}")
                raise
        
        return await self.performance_monitor.monitor_query(query_name, _count)
    
    async def exists(self, entity_id: int) -> bool:
        """检查实体是否存在"""
        query_name = f"{self.table_name}_exists"
        
        async def _exists():
            try:
                async with self.db_service.get_async_session() as session:
                    sql = f"SELECT 1 FROM {self.table_name} WHERE id = :id LIMIT 1"
                    result = await session.execute(text(sql), {"id": entity_id})
                    return result.fetchone() is not None
                    
            except Exception as e:
                logger.error(f"检查{self.table_name}实体存在性失败: {e}")
                raise
        
        return await self.performance_monitor.monitor_query(query_name, _exists)
    
    # 缓存相关方法
    async def _get_cached_or_execute(
        self,
        cache_key: str,
        query_func,
        ttl: Optional[int] = None
    ):
        """缓存或执行查询"""
        current_time = time.time()
        
        # 检查缓存
        if (cache_key in self._cache and 
            cache_key in self._cache_ttl and 
            current_time < self._cache_ttl[cache_key]):
            logger.debug(f"缓存命中: {cache_key}")
            return self._cache[cache_key]
        
        # 执行查询
        result = await query_func()
        
        # 更新缓存
        self._cache[cache_key] = result
        self._cache_ttl[cache_key] = current_time + (ttl or self._default_ttl)
        logger.debug(f"缓存更新: {cache_key}")
        
        return result
    
    def _invalidate_cache(self, pattern: str = None):
        """清除缓存"""
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_ttl.pop(key, None)
            logger.debug(f"清除匹配缓存: {pattern}, 数量: {len(keys_to_remove)}")
        else:
            self._cache.clear()
            self._cache_ttl.clear()
            logger.debug("清除所有缓存")
    
    # 查询计划分析
    async def explain_query(self, sql: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """查询计划分析"""
        explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
        
        try:
            async with self.db_service.get_async_session() as session:
                result = await session.execute(text(explain_sql), params or {})
                row = result.fetchone()
                
                explain_result = json.loads(row[0]) if row else {}
                
                # 分析关键指标
                analysis = self._analyze_explain_result(explain_result)
                
                return {
                    "sql": sql,
                    "explain_result": explain_result,
                    "analysis": analysis,
                    "recommendations": self._get_optimization_recommendations(analysis)
                }
        except Exception as e:
            logger.error(f"查询计划分析失败: {e}")
            return {"error": str(e)}

    def _analyze_explain_result(self, explain_result: Dict) -> Dict[str, Any]:
        """分析查询计划结果"""
        analysis = {
            "total_cost": 0,
            "rows_examined": 0,
            "using_index": False,
            "using_filesort": False,
            "using_temporary": False,
            "full_table_scan": False,
            "performance_issues": []
        }
        
        def traverse_plan(node):
            if isinstance(node, dict):
                # 检查成本
                if "cost_info" in node:
                    analysis["total_cost"] += node["cost_info"].get("read_cost", 0)
                
                # 检查行数
                if "rows_examined_per_scan" in node:
                    analysis["rows_examined"] += node["rows_examined_per_scan"]
                
                # 检查索引使用
                if "used_key_parts" in node:
                    analysis["using_index"] = True
                
                # 检查性能问题
                if "using_filesort" in node.get("extra_info", ""):
                    analysis["using_filesort"] = True
                    analysis["performance_issues"].append("Using filesort")
                
                if "using_temporary" in node.get("extra_info", ""):
                    analysis["using_temporary"] = True
                    analysis["performance_issues"].append("Using temporary table")
                
                if node.get("access_type") == "ALL":
                    analysis["full_table_scan"] = True
                    analysis["performance_issues"].append("Full table scan")
                
                # 递归处理子节点
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        traverse_plan(value)
            elif isinstance(node, list):
                for item in node:
                    traverse_plan(item)
        
        traverse_plan(explain_result)
        return analysis

    def _get_optimization_recommendations(self, analysis: Dict) -> List[str]:
        """获取优化建议"""
        recommendations = []
        
        if analysis["full_table_scan"]:
            recommendations.append("考虑添加索引以避免全表扫描")
        
        if analysis["using_filesort"]:
            recommendations.append("考虑添加覆盖索引以避免文件排序")
        
        if analysis["using_temporary"]:
            recommendations.append("优化查询以避免临时表的使用")
        
        if analysis["total_cost"] > 1000:
            recommendations.append("查询成本较高，考虑分解为多个简单查询")
        
        if analysis["rows_examined"] > 10000:
            recommendations.append("检查行数过多，考虑添加更精确的WHERE条件")
        
        return recommendations

    # 性能监控方法
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return self.performance_monitor.get_performance_report()
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self.performance_monitor.query_stats.clear()
        logger.info(f"已重置{self.table_name}性能统计")

    # 优化后的分页查询方法
    async def get_paginated_optimized(
        self,
        where_clause: str = "",
        params: Dict[str, Any] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "id",
        order_direction: str = "DESC"
    ) -> tuple[List[T], int]:
        """优化的分页查询"""
        query_name = f"{self.table_name}_paginated"
        
        async def _paginated():
            params_dict = params or {}
            params_dict.update({"limit": limit, "offset": offset})
            
            # 优化：使用覆盖索引避免回表
            if offset == 0:
                # 首页查询：使用LIMIT优化
                data_sql = f"""
                    SELECT * FROM {self.table_name}
                    {"WHERE " + where_clause if where_clause else ""}
                    ORDER BY {order_by} {order_direction}
                    LIMIT :limit
                """
            else:
                # 深度分页：使用游标优化
                data_sql = f"""
                    SELECT t.* FROM {self.table_name} t
                    INNER JOIN (
                        SELECT id FROM {self.table_name}
                        {"WHERE " + where_clause if where_clause else ""}
                        ORDER BY {order_by} {order_direction}
                        LIMIT :limit OFFSET :offset
                    ) sub ON t.id = sub.id
                    ORDER BY t.{order_by} {order_direction}
                """
            
            # 统计查询优化：使用覆盖索引
            count_sql = f"""
                SELECT COUNT(*) as total FROM {self.table_name}
                {"WHERE " + where_clause if where_clause else ""}
            """
            
            # 并行执行查询
            data_task = self._execute_query(data_sql, params_dict)
            count_task = self._execute_query_one(count_sql, {k: v for k, v in params_dict.items() if k not in ["limit", "offset"]})
            
            data_rows, count_row = await asyncio.gather(data_task, count_task)
            
            entities = [self._dict_to_entity(row) for row in data_rows]
            total = count_row["total"] if count_row else 0
            
            return entities, total
        
        return await self.performance_monitor.monitor_query(query_name, _paginated) 