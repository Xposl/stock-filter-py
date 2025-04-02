"""
API模块初始化文件 - 使用DBAdapter支持SQLite和PostgreSQL
"""
import os

# 导入基于pydantic的仓库类
from .TickerRepository import TickerRepository
from .ticker_score_repository import TickerScoreRepository
from .ticker_strategy_repository import TickerStrategyRepository
from .ticker_indicator_repository import TickerIndicatorRepository
from .ticker_valuation_repository import TickerValuationRepository

# 导入传统API类（仅在需要时使用）
# 惰性导入以避免在导入时连接数据库
def _import_legacy_api():
    # 移除了Strategy, Project, ProjectTicker, TickerScore, TickerValuation
    return {
        'TickerStrategy': TickerStrategyRepository,
        'TickerIndicator': TickerIndicatorRepository,
    }

class APIHelper:
    """API帮助类 - 支持SQLite和传统MySQL连接"""
    
    def __init__(self):
        """初始化API帮助类"""
        self._db_connection = None
        self._legacy_api_classes = None
    
    @property
    def db_connection(self):
        """获取数据库连接（惰性加载）"""
        if self._db_connection is None:
            # 检查是否要使用传统MySQL连接
            use_legacy = os.getenv('USE_LEGACY_API', 'false').lower() == 'true'
            
            if use_legacy:
                # 使用传统MySQL连接
                import pymysql.cursors
                self._db_connection = pymysql.connect(
                    host=os.getenv('DB_HOST', '127.0.0.1'),
                    user=os.getenv('DB_USER', 'root'),
                    password=os.getenv('DB_PASSWORD', ''),
                    database=os.getenv('DB_NAME', 'invest_note'),
                    cursorclass=pymysql.cursors.DictCursor
                )
            else:
                # 使用DBAdapter
                from ..DB.DBAdapter import DBAdapter
                self._db_connection = DBAdapter()
        
        return self._db_connection
    
    @property
    def legacy_api_classes(self):
        """获取传统API类（惰性加载）"""
        if self._legacy_api_classes is None:
            self._legacy_api_classes = _import_legacy_api()
        return self._legacy_api_classes
    
    def getMysqlEnv(self):
        """获取数据库连接（兼容旧版API）"""
        return self.db_connection

    # 新版API - 基于pydantic模型
    def ticker_repository(self):
        """获取Ticker仓库实例"""
        return TickerRepository(self.db_connection)
    
    # 兼容旧版API的方法
    def ticker(self):
        """获取传统Ticker API实例"""
        return self.legacy_api_classes['Ticker'](self.db_connection)

    def strategy(self):
        """获取传统Strategy API实例（已废弃）"""
        import logging
        logging.warning("strategy() 方法已废弃，请使用ticker_strategy_repository()替代")
        return self.ticker_strategy_repository()

    def ticker_strategy_repository(self):
        """获取TickerStrategyRepository实例"""
        return self.legacy_api_classes['TickerStrategy'](self.db_connection)
    
    def tickerStrategy(self):
        """获取传统TickerStrategy API实例（兼容旧版API）"""
        return self.ticker_strategy_repository()

    def tickerIndicator(self):
        """获取传统TickerIndicator API实例"""
        return self.legacy_api_classes['TickerIndicator'](self.db_connection)

    def tickerScore(self):
        """获取TickerScore API实例（直接使用TickerScoreRepository）"""
        from .TickerScore import TickerScore
        return TickerScore(self.db_connection)
    
    def ticker_valuation_repository(self):
        """获取TickerValuationRepository实例"""
        return TickerValuationRepository(self.db_connection)
        
    def tickerValuation(self):
        """获取TickerValuation API实例（直接使用TickerValuationRepository）"""
        return self.ticker_valuation_repository()
    
    def projectTicker(self):
        """获取传统ProjectTicker API实例（已废弃）"""
        import logging
        logging.warning("projectTicker() 方法已废弃")
        return None

# 创建默认APIHelper实例
api_helper = APIHelper()
