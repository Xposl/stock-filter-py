from pocketflow import Flow
from core.ai_agents.news_analysis_flow.nodes import NewsClassifierNode, TickerAnalysisNode, TickerIndustryFinderNode, TickerScoreUpdate


def news_analysis_flow():
  news_classifier = NewsClassifierNode()
  ticker_industry_finder = TickerIndustryFinderNode()
  ticker_score_update = TickerScoreUpdate()
  ticker_analysis = TickerAnalysisNode()

  news_classifier - "industry_focused" >> ticker_industry_finder
  news_classifier - "stock_specific" >> ticker_score_update

  ticker_industry_finder >> ticker_score_update

  ticker_score_update >> ticker_analysis

  return Flow(start=news_classifier)