import time
from datetime import datetime, timedelta
from typing import Optional

import akshare as ak
from dateutil.relativedelta import relativedelta

from core.handler.ticker_analysis_handler import TickerAnalysisHandler
from core.handler.ticker_k_line_handler import TickerKLineHandler
from core.models.ticker import Ticker
from core.models.ticker_score import TickerScore
from core.schema.k_line import KLine
from core.repository.market_repository import MarketRepository
from core.repository.ticker_repository import TickerRepository
from core.repository.ticker_score_repository import TickerScoreRepository
from core.utils.utils import UtilsHelper

from .handler.ticker_handler import TickerHandler
from .handler.ticker_indicator_handler import TickerIndicatorHandler
from .handler.ticker_score_handler import TickerScoreHandler
from .handler.ticker_strategy_handler import TickerStrategyHandler
from .handler.ticker_valuation_handler import TickerValuationHandler


class DataSourceHelper:

    strategies = None
    indicators = None
    valuations = None
    score_rule = None
    filter_rule = None

    def __init__(self):
        """初始化DataSourceHelper"""
        self.market_repo = MarketRepository()
        self.ticker_repo = TickerRepository()
        self.score_repo = TickerScoreRepository()

    def set_strategies(self, strategies: Optional[list] = None):
        """
        设置策略
        """
        self.strategies = strategies

    def set_indicators(self, indicators: Optional[list] = None):
        """
        设置指标
        """
        self.indicators = indicators

    def set_score_rule(self, score_rule: Optional[list] = None):
        """
        设置评分规则
        """
        self.score_rule = score_rule

    def set_filter_rule(self, filter_rule: Optional[list] = None):
        """
        设置过滤规则
        """
        self.filter_rule = filter_rule

    def set_valuations(self, valuations: Optional[list] = None):
        """
        设置估值规则
        """
        self.valuations = valuations

    def _get_last_trading_date(self) -> str:
        """
        获取最后交易日（使用akshare工具日期获取）

        Returns:
            最后交易日期字符串，格式：YYYY-MM-DD
        """
        try:
            # 使用akshare获取A股交易日历
            from datetime import datetime, timedelta

            import akshare as ak

            # 获取当前日期
            today = datetime.now()

            # 获取过去30天的交易日历，确保能找到最近的交易日
            (today - timedelta(days=30)).strftime("%Y%m%d")
            today.strftime("%Y%m%d")

            # 获取交易日历
            trade_cal = ak.tool_trade_date_hist_sina()
            if trade_cal is not None and len(trade_cal) > 0:
                # 转换日期格式并排序
                trade_dates = []
                for _, row in trade_cal.iterrows():
                    try:
                        date_str = str(row["trade_date"])
                        if len(date_str) == 8:  # YYYYMMDD格式
                            trade_date = datetime.strptime(date_str, "%Y%m%d")
                        else:  # 其他格式尝试解析
                            trade_date = datetime.strptime(date_str, "%Y-%m-%d")
                        trade_dates.append(trade_date)
                    except BaseException:
                        continue

                # 找到最近的交易日
                trade_dates.sort(reverse=True)
                for trade_date in trade_dates:
                    if trade_date.date() <= today.date():
                        return trade_date.strftime("%Y-%m-%d")

        except Exception as e:
            print(f"获取交易日历失败: {e}")

        # 如果获取失败，使用简单逻辑
        today = datetime.now()
        weekday = today.weekday()  # 0=Monday, 6=Sunday

        if weekday == 5:  # Saturday
            last_trading_date = today - timedelta(days=1)  # Friday
        elif weekday == 6:  # Sunday
            last_trading_date = today - timedelta(days=2)  # Friday
        else:
            last_trading_date = today

        return last_trading_date.strftime("%Y-%m-%d")

    def _get_end_date(self) -> str:
        """
        获取最后交易日
        """
        # A股最后交易日
        try:
            stock_sse_summary_df = ak.stock_sse_summary()
            report_time_row = stock_sse_summary_df[
                stock_sse_summary_df.iloc[:, 0] == "报告时间"
            ]
            if not report_time_row.empty:
                # 获取"股票"列的值（第2列，索引为1）
                report_time_str = report_time_row.iloc[0, 1]
                # 格式化日期字符串
                return f"{report_time_str[:4]}-{report_time_str[4:6]}-{report_time_str[6:]}"
        except Exception:
            print("获取失败")
            return self._get_last_trading_date()

    def _calc_start_end_date(self, days: Optional[int] = 600) -> tuple[str, str]:
        """
        计算开始和结束日期
        :param days: 天数
        :return: 开始和结束日期
        """
        end_date = self._get_end_date()
        start_date = (
            datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(days=days)
        ).strftime("%Y-%m-%d")
        return start_date, end_date

    def _need_update_ticker_data(self, ticker: Ticker) -> bool:
        """
        检查是否需要更新股票数据 - 智能缓存决策逻辑

        判断条件：
        1. 最新评分时间 < 最新K线时间
        2. 当前是交易日且市场开市
        3. 距离上次更新超过一定时间间隔（默认30分钟）
        4. 数据源发生变化时需要重新计算

        Args:
            ticker: 股票对象

        Returns:
            是否需要更新
        """
        try:
            # 获取股票的最新评分记录
            latest_scores = self.score_repo.get_items_by_ticker_id(ticker.id)
            if not latest_scores or len(latest_scores) == 0:
                # 没有评分记录，需要更新
                return True

            latest_score = latest_scores[0]  # 获取最新的评分
            score_date = latest_score.time_key
            last_kline_time = latest_score.last_kline_time

            # 获取最后交易日
            last_trading_date = self._get_last_trading_date()
            
            # 获取当前K线数据的最新时间
            current_kline_time = self._get_latest_kline_time(ticker)
            
            # 获取市场状态
            market_status = self._get_market_trading_status(ticker)

            # 判断是否需要更新
            if score_date < last_trading_date:
                # 评分数据早于最后交易日，需要更新
                return True

            if last_kline_time and current_kline_time and last_kline_time < current_kline_time:
                # K线数据有更新，需要重新计算
                return True

            if market_status["is_trading_day"] and market_status["market_open"]:
                # 当前是交易日且市场开市，检查更新间隔
                next_update_time = latest_score.next_update_time
                if next_update_time is None or datetime.now() > next_update_time:
                    return True

            # 数据源发生变化时需要重新计算（通过cache_version判断）
            if latest_score.cache_version is None or latest_score.cache_version < 1:
                return True

            return False

        except Exception as e:
            print(f"检查更新需求失败: {e}")
            # 出错时保守处理，返回需要更新
            return True

    def _get_latest_kline_time(self, ticker: Ticker) -> str:
        """
        获取当前K线数据的最新时间

        Args:
            ticker: 股票对象

        Returns:
            最新K线时间字符串
        """
        try:
            # 获取最近1天的K线数据来确定最新时间
            current_date = datetime.now().strftime("%Y-%m-%d")
            k_line_data = TickerKLineHandler().get_kl(
                ticker.code, ticker.source, current_date, current_date
            )
            
            if k_line_data and len(k_line_data) > 0:
                # 获取最后一条K线的时间
                last_kline = k_line_data[-1]
                if hasattr(last_kline, "time_key"):
                    return last_kline.time_key
                elif isinstance(last_kline, dict):
                    return last_kline.get("time_key", current_date)
            
            return current_date
            
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")

    

    def get_ticker_score(
        self, code: str, days: Optional[int] = 600
    ) -> Optional[list[TickerScore]]:
        """
        智能获取股票评分，避免不必要的API调用

        Args:
            code: 股票代码，必须包含市场前缀，格式如下：
                - A股：SH.600000 (上交所) 或 SZ.000001 (深交所)
                - 港股：HK.00700 (5位数字，不足5位前面补0)
                - 美股：US.AAPL
            days: 获取的历史数据天数，默认600天

        Returns:
            TickerScore对象列表，如果股票不存在或获取失败则返回None

        Example:
            scores = helper.get_ticker_score("SH.600000")
            scores = helper.get_ticker_score("HK.00700")
            scores = helper.get_ticker_score("US.AAPL")
        """
        try:
            # 1. 获取股票基础信息
            ticker = self.ticker_repo.get_by_code(code)
            if ticker is None:
                print(f"未找到股票: {code}")
                return None

            # 2. 检查是否需要更新数据
            if not self._need_update_ticker_data(ticker):
                # 不需要更新，直接返回现有评分数据
                existing_scores = self.score_repo.get_items_by_ticker_id(ticker.id)
                if existing_scores:
                    print(f"使用现有评分数据: {code} (共{len(existing_scores)}条记录)")
                    return existing_scores

            # 3. 需要更新数据，调用更新函数
            print(f"更新股票数据: {code}")
            ticker, kl_data, score_data = self._update_ticker(ticker, days)

            if score_data:
                print(f"成功获取评分数据: {code} (共{len(score_data)}条记录)")
                return score_data
            else:
                print(f"未获取到评分数据: {code}")
                return None

        except Exception as e:
            print(f"获取股票评分失败 {code}: {e}")
            return None

    def get_ticker_score_with_cache_info(
        self, code: str, days: Optional[int] = 600
    ) -> dict:
        """
        获取股票评分及缓存信息

        Args:
            code: 股票代码，必须包含市场前缀
            days: 获取的历史数据天数，默认600天

        Returns:
            dict: 包含评分数据和缓存信息的字典
            {
                "ticker": Ticker对象,
                "kline_data": list[KLine],
                "score_data": list[TickerScore],
                "cache_info": {
                    "last_updated": "2024-01-01T10:00:00Z",
                    "is_cached": bool,
                    "next_update": "2024-01-01T16:00:00Z",
                    "cache_strategy": str,
                    "data_source": str
                }
            }
        """
        try:
            # 获取股票基础信息
            ticker = self.ticker_repo.get_by_code(code)
            if ticker is None:
                return {
                    "ticker": None,
                    "kline_data": [],
                    "score_data": [],
                    "cache_info": {
                        "last_updated": None,
                        "is_cached": False,
                        "next_update": None,
                        "cache_strategy": "no_data",
                        "data_source": "unknown",
                        "error": "股票未找到"
                    }
                }

            # 检查缓存策略
            need_update = self._need_update_ticker_data(ticker)
            
            if not need_update:
                # 使用缓存数据
                existing_scores = self.score_repo.get_items_by_ticker_id(ticker.id)
                if existing_scores:
                    latest_score = existing_scores[0]
                    
                    return {
                        "ticker": ticker,
                        "kline_data": [],  # 缓存时不返回K线数据以节省带宽
                        "score_data": existing_scores,
                        "cache_info": {
                            "last_updated": latest_score.create_time.isoformat() if latest_score.create_time else None,
                            "is_cached": True,
                            "next_update": latest_score.next_update_time.isoformat() if latest_score.next_update_time else None,
                            "cache_strategy": "time_based",
                            "data_source": "cache",
                            "cache_version": latest_score.cache_version or 1
                        }
                    }

            # 需要更新数据
            ticker, kl_data, score_data = self._update_ticker(ticker, days)
            
            if score_data:
                latest_score = score_data[0] if score_data else None
                return {
                    "ticker": ticker,
                    "kline_data": kl_data,
                    "score_data": score_data,
                    "cache_info": {
                        "last_updated": latest_score.create_time.isoformat() if latest_score else datetime.now().isoformat(),
                        "is_cached": False,
                        "next_update": latest_score.next_update_time.isoformat() if latest_score and latest_score.next_update_time else None,
                        "cache_strategy": "real_time",
                        "data_source": "api"
                    }
                }
            else:
                return {
                    "ticker": ticker,
                    "kline_data": kl_data,
                    "score_data": [],
                    "cache_info": {
                        "last_updated": None,
                        "is_cached": False,
                        "next_update": None,
                        "cache_strategy": "error",
                        "data_source": "api",
                        "error": "无法获取评分数据"
                    }
                }

        except Exception as e:
            return {
                "ticker": None,
                "kline_data": [],
                "score_data": [],
                "cache_info": {
                    "last_updated": None,
                    "is_cached": False,
                    "next_update": None,
                    "cache_strategy": "error",
                    "data_source": "unknown",
                    "error": str(e)
                }
            }

    def _get_on_time_kline_data(self, ticker: Ticker, days: Optional[int] = 600):
        """
        获取指定股票的K线数据
        """
        # 从在线API获取K线数据和实时数据
        current_date = datetime.now()
        end_date = current_date.strftime("%Y-%m-%d")
        start_date = (current_date - relativedelta(days=days)).strftime("%Y-%m-%d")

        k_line_data, used_source = TickerKLineHandler().get_kl(
            ticker.code, ticker.source, start_date, end_date
        )
        on_time_data, used_source_on_time = TickerKLineHandler().get_kl_on_time(
            ticker.code, ticker.source
        )
        # 同步source字段
        if (
            used_source is not None
            and used_source != ticker.source
            and k_line_data is not None
            and len(k_line_data) > 0
        ):
            TickerRepository().update(ticker.code, ticker.name, {"source": used_source})
            ticker.source = used_source
        # 确保时间是字符串格式
        time_key = end_date
        if on_time_data is not None:
            ontime_date = (
                on_time_data["time_key"]
                if isinstance(on_time_data, dict)
                else getattr(on_time_data, "time_key", None)
            )
            # 使用import的datetime类进行检查
            from datetime import date
            from datetime import datetime as dt

            if isinstance(ontime_date, (dt, date)):
                ontime_date = ontime_date.strftime("%Y-%m-%d")
            if k_line_data is None:
                k_line_data = [on_time_data]
            elif isinstance(ontime_date, str) and time_key < ontime_date:
                k_line_data.append(on_time_data)
            elif time_key == ontime_date:
                k_line_data[len(k_line_data) - 1] = on_time_data
        return time_key, k_line_data

    def _update_ticker_data(
        self, ticker: Ticker, end_date: str, kl_data: list[KLine]
    ) -> tuple[Ticker, list[KLine], list[TickerScore]]:
        """
        更新指定股票的分析数据
        """
        score_data = []
        if kl_data:
            # 使用格式化后的字符串日期
            strategy_data = TickerStrategyHandler().update_ticker_strategy(
                ticker, kl_data, end_date
            )
            indicator_data = TickerIndicatorHandler(
                end_date, self.indicators
            ).update_ticker_indicator(ticker, kl_data)
            valuation_data = TickerValuationHandler(
                end_date, self.valuations
            ).update_ticker_valuation(ticker)
            score_data = TickerScoreHandler(self.score_rule).update_ticker_score(
                ticker, kl_data, strategy_data, indicator_data, valuation_data
            )
            
            # 更新缓存相关元数据
            if score_data:
                latest_kline_time = end_date
                if kl_data:
                    last_kline = kl_data[-1]
                    if hasattr(last_kline, 'time_key'):
                        latest_kline_time = last_kline.time_key
                    elif isinstance(last_kline, dict):
                        latest_kline_time = last_kline.get('time_key', end_date)
                
                # 为每个评分记录添加缓存元数据
                for score in score_data:
                    score.last_kline_time = latest_kline_time
                    score.next_update_time = market_status["next_update_time"]
                    score.cache_version = 1
                    
        return ticker, kl_data, score_data

    def _update_ticker(
        self, ticker: Ticker, days: Optional[int] = 600, source: Optional[int] = None
    ):
        """
        更新指定股票数据
        """
        from core.repository.ticker_repository import TickerRepository

        # 统一获取和格式化日期
        start_date, end_date = self._calc_start_end_date(days)
        kl_data, used_source = TickerKLineHandler().get_kl(
            ticker.code,
            source if source is not None else ticker.source,
            start_date,
            end_date,
        )
        # 同步source字段
        if (
            used_source is not None
            and used_source != ticker.source
            and kl_data is not None
            and len(kl_data) > 0
        ):
            TickerRepository().update(ticker.code, ticker.name, {"source": used_source})
            ticker.source = used_source
        return self._update_ticker_data(ticker, end_date, kl_data)

    def _update_tickers(
        self, tickers: Optional[list] = None, days: Optional[int] = 600
    ):
        """
        更新指定股票数据
        """
        total = len(tickers)
        end_date = self._get_end_date()
        for i in range(total):
            ticker = tickers[i]
            UtilsHelper().run_process(
                i,
                total,
                f"update({i + 1}/{total})",
                f"({ticker.id}){ticker.code}",
            )
            k_score = TickerScoreRepository().get_items_by_ticker_id(ticker.id)

            if (
                k_score is not None
                and len(k_score) > 0
                and k_score[0].time_key == end_date
            ):
                continue
            try:
                self._update_ticker(ticker, days, i % 2 + 1)
            except Exception as e:
                print(f"更新数据失败[{ticker.id}]{ticker.code} {str(e)}")
            time.sleep(1)

    def get_ticker_code(self, market: str, ticker_code: str) -> str:
        """
        将原始股票代码转换为系统标准格式（包含市场前缀）

        Args:
            market: 市场标识（不区分大小写）
                - "zh" 或 "ZH": 中国A股市场
                - "hk" 或 "HK": 香港股市
                - "us" 或 "US": 美国股市
            ticker_code: 原始股票代码（不含前缀）
                - A股：如 "600000", "000001"
                - 港股：如 "700", "00700"
                - 美股：如 "AAPL", "TSLA"

        Returns:
            str: 标准格式的股票代码
                - A股：SH.600000 或 SZ.000001 (自动判断交易所)
                - 港股：HK.00700 (自动补零到5位)
                - 美股：US.AAPL

        Example:
            get_ticker_code("zh", "600000")  # 返回 "SH.600000"
            get_ticker_code("HK", "000001")  # 返回 "SZ.000001"
            get_ticker_code("hk", "700")     # 返回 "HK.00700"
            get_ticker_code("US", "AAPL")    # 返回 "US.AAPL"
        """
        # 将市场代码转换为小写以支持大小写不敏感
        market_lower = market.lower()
        code = None

        if market_lower == "hk":
            code = f"HK.{ticker_code.zfill(5)}"
        elif market_lower == "zh":
            code = ticker_code.zfill(6)
            if code.startswith("0") or code.startswith("3"):
                code = f"SZ.{code}"
            elif code.startswith("6") or code.startswith("7") or code.startswith("9"):
                code = f"SH.{code}"
        elif market_lower == "us":
            code = f"US.{ticker_code}"

        if code is None:
            raise ValueError(f"Unsupported market: {market}")
        return code

    def update_ticker_list(self):
        """
        更新股票列表
        """
        TickerHandler().update_tickers()

    def get_kline_data(self, code: str, days: Optional[int] = 600):
        """
        获取指定股票的K线数据
        """
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return
        # 统一获取和格式化日期
        start_date, end_date = self._calc_start_end_date(days)
        k_line_data = TickerKLineHandler().get_kl(
            ticker.code, ticker.source, start_date, end_date
        )
        return k_line_data

    def update_all_tickers(self):
        """
        更新所有股票数据
        """
        tickers = TickerRepository().get_all_available()
        self._update_tickers(tickers)

    def update_tickers_start_with(self, start_key):
        """
        更新start_key开头的数据
        """
        print("更新" + start_key + "开头的项目的数据")
        tickers = TickerRepository().get_all_available_start_with(start_key)
        self._update_tickers(tickers)

    def get_ticker_data(
        self, code: str, days: Optional[int] = 600
    ) -> tuple[Ticker, list[KLine], list[TickerScore]]:
        """
        获取指定股票数据

        Args:
            code: 股票代码，必须包含市场前缀，格式如下：
                - A股：SH.600000 (上交所) 或 SZ.000001 (深交所)
                - 港股：HK.00700 (5位数字，不足5位前面补0)
                - 美股：US.AAPL
                注意：不支持纯数字代码，必须包含市场前缀
            days: 获取的历史数据天数，默认600天

        Returns:
            tuple[Ticker, List[KLine], List[TickerScore]]:
                - Ticker: 股票基础信息，如果股票不存在则返回None
                - List[KLine]: K线数据列表
                - List[TickerScore]: 评分数据列表

        Example:
            ticker, kl_data, score_data = helper.get_ticker_data("SH.600000", 250)
            ticker, kl_data, score_data = helper.get_ticker_data("HK.00700", 180)
            ticker, kl_data, score_data = helper.get_ticker_data("US.AAPL", 365)
        """
        ticker = TickerRepository().get_by_code(code)
        ticker, kl_data, score_data = self._update_ticker(ticker, days)
        return ticker, kl_data, score_data

    def get_ticker_data_on_time(
        self, code: str, days: Optional[int] = 600
    ) -> Optional[tuple]:
        """
        获取即时项目数据
        """
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return

        # 从在线API获取K线数据和实时数据
        time_key, k_line_data = self._get_on_time_kline_data(ticker, days)
        strategy_data = TickerStrategyHandler(time_key).calculate(k_line_data)
        indicator_data = TickerIndicatorHandler(time_key).calculate(k_line_data)
        score_data = TickerScoreHandler(self.score_rule).calculate(
            ticker, k_line_data, strategy_data, indicator_data, None
        )
        return ticker, k_line_data, score_data

    def analysis_ticker(self, code: str, days: Optional[int] = 600):
        """
        分析项目数据
        """
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return

        ticker, k_line_data, score_data = self._update_ticker(ticker, days)
        # 将List[TickerScore]转换为字典列表，供TickerAnalysisHandler使用
        if score_data and isinstance(score_data[0], TickerScore):
            from core.models.ticker_score import ticker_score_to_dict

            score_dict_list = [ticker_score_to_dict(score) for score in score_data]
        else:
            score_dict_list = score_data
        TickerAnalysisHandler().run(ticker, k_line_data, score_dict_list)

    def analysis_ticker_on_time(
        self, code: str, days: Optional[int] = 600, k_line_data=None
    ):
        """
        分析即时项目数据
        """
        ticker, k_line_data, score_data = self.get_ticker_data_on_time(
            code, days, k_line_data
        )
        # 将List[TickerScore]转换为字典列表，供TickerAnalysisHandler使用
        if score_data and isinstance(score_data[0], TickerScore):
            from core.models.ticker_score import ticker_score_to_dict

            score_dict_list = [ticker_score_to_dict(score) for score in score_data]
        else:
            score_dict_list = score_data
        TickerAnalysisHandler().run(ticker, k_line_data, score_dict_list)
