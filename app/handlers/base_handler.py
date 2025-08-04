"""
Handler基类
为所有Handler提供通用功能和接口规范
遵循三层架构规范
"""

import logging
from abc import ABC
from typing import Any, Dict, Optional


class BaseHandler(ABC):
    """
    Handler基类
    
    提供所有Handler的通用功能：
    - 日志记录
    - 错误处理
    - 通用工具方法
    """
    
    def __init__(self):
        """初始化基类"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _validate_required_field(self, value: Any, field_name: str) -> None:
        """
        验证必填字段
        
        Args:
            value: 字段值
            field_name: 字段名称
            
        Raises:
            ValueError: 字段为空时抛出
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{field_name}不能为空")
    
    def _validate_string_length(
        self, 
        value: str, 
        field_name: str, 
        max_length: int,
        min_length: int = 0
    ) -> None:
        """
        验证字符串长度
        
        Args:
            value: 字符串值
            field_name: 字段名称
            max_length: 最大长度
            min_length: 最小长度
            
        Raises:
            ValueError: 长度不符合要求时抛出
        """
        if value is None:
            return
        
        if len(value) < min_length:
            raise ValueError(f"{field_name}长度不能少于{min_length}字符")
        
        if len(value) > max_length:
            raise ValueError(f"{field_name}长度不能超过{max_length}字符")
    
    def _sanitize_string(self, value: Optional[str]) -> Optional[str]:
        """
        清理字符串（去除首尾空格）
        
        Args:
            value: 原始字符串
            
        Returns:
            清理后的字符串，如果原始值为None则返回None
        """
        if value is None:
            return None
        return value.strip() if isinstance(value, str) else str(value).strip()
    
    def _log_operation(
        self, 
        operation: str, 
        entity_id: str, 
        user_id: str = "system",
        extra_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录操作日志
        
        Args:
            operation: 操作类型
            entity_id: 实体ID
            user_id: 操作用户ID
            extra_info: 额外信息
        """
        log_data = {
            "operation": operation,
            "entity_id": entity_id,
            "user_id": user_id
        }
        
        if extra_info:
            log_data.update(extra_info)
        
        self.logger.info(f"操作记录: {log_data}")
    
    def _handle_repository_error(self, error: Exception, operation: str) -> None:
        """
        处理Repository层错误
        
        Args:
            error: 原始错误
            operation: 操作描述
            
        Raises:
            ValueError: 业务逻辑错误
            RuntimeError: 系统错误
        """
        error_msg = str(error)
        
        # 数据库约束错误
        if "UNIQUE constraint failed" in error_msg or "Duplicate entry" in error_msg:
            raise ValueError("数据已存在，请检查唯一性约束")
        
        # 外键约束错误
        if "FOREIGN KEY constraint failed" in error_msg or "foreign key constraint" in error_msg:
            raise ValueError("关联数据不存在，请检查数据完整性")
        
        # 其他数据库错误
        self.logger.error(f"{operation}失败: {error}", exc_info=True)
        raise RuntimeError(f"{operation}失败: {error_msg}")
    
    def _build_error_response(
        self, 
        error: Exception, 
        operation: str,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建错误响应
        
        Args:
            error: 错误对象
            operation: 操作描述
            entity_id: 实体ID
            
        Returns:
            错误响应字典
        """
        error_response = {
            "success": False,
            "error": str(error),
            "operation": operation
        }
        
        if entity_id:
            error_response["entity_id"] = entity_id
        
        return error_response
    
    def _build_success_response(
        self, 
        data: Any, 
        operation: str,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建成功响应
        
        Args:
            data: 响应数据
            operation: 操作描述
            message: 成功消息
            
        Returns:
            成功响应字典
        """
        response = {
            "success": True,
            "data": data,
            "operation": operation
        }
        
        if message:
            response["message"] = message
        
        return response 