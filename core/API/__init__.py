import pymysql.cursors
from .Ticker import Ticker
from .TickerDayLine import TickerDayLine
from .Strategy import Strategy
from .TickerStrategy import TickerStrategy
from .TickerIndicator import TickerIndicator
from .TickerScore import TickerScore
from .TickerValuation import TickerValuation

from .ProjectTicker import ProjectTicker

mysqlEnv = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='xposl1990',
    database='invest_note',
    cursorclass=pymysql.cursors.DictCursor
)

class APIHelper:

    def getMysqlEnv(self):
        return mysqlEnv

    def ticker(self):
        return Ticker(mysqlEnv)

    def tickerDayLine(self):
        return TickerDayLine(mysqlEnv)

    def strategy(self):
        return Strategy(mysqlEnv)

    def tickerStrategy(self):
        return TickerStrategy(mysqlEnv)

    def tickerIndicator(self):
        return TickerIndicator(mysqlEnv)

    def tickerScore(self):
        return TickerScore(mysqlEnv)
    
    def tickerValuation(self):
        return TickerValuation(mysqlEnv)
    
    def projectTicker(self):
        return ProjectTicker(mysqlEnv)

        

    
    

    


