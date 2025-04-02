#coding=UTF-8
# from core.Valuation.ResearchReportValuation import ResearchReportValuation
from core.Handler import DataSourceHelper

# from custom.TickerScoreFilter import TickerScoreFilter
# from custom.TickerHighValuation import TickerHighValuation
import sys
import datetime

projectId = 1
endDate = datetime.datetime.now().strftime('%Y-%m-%d')
endDate = '2022-12-16'

dataSource = DataSourceHelper()
dataSource.setEndDate(endDate)
# dataSource.setFilterRule(TickerHighValuation())

# dataSource.updateTickerList()
dataSource.analysisTicker("HK.00700")

# if sys.argv[1] == '-ticker':
# dataSource.updateTickerList()

# if sys.argv[1] == '-a':
#     code = None
#     if sys.argv[2] == 'hk':
#         code = 'HK.%s'%sys.argv[3].zfill(5)
#     elif sys.argv[2] == 'zh':
#         code = sys.argv[3].zfill(6)
#         if code.startswith('0') or code.startswith('3'):
#             code  = 'SZ.%s'%code
#         elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
#             code  = 'SH.%s'%code
#     elif sys.argv[2] == 'us':
#         code = 'US.%s'%sys.argv[3]

#     if code is not None:
#         dataSource.updateTickerByCode(code)
#         dataSource.analysisTicker(code,250)

# if sys.argv[1] == '-ao':
#     code = None
#     if sys.argv[2] == 'hk':
#         code = 'HK.%s'%sys.argv[3].zfill(5)
#     elif sys.argv[2] == 'zh':
#         code = sys.argv[3].zfill(6)
#         if code.startswith('0') or code.startswith('3'):
#             code  = 'SZ.%s'%code
#         elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
#             code  = 'SH.%s'%code
#     elif sys.argv[2] == 'us':
#         code = 'US.%s'%sys.argv[3]
#     if code is not None:
#         dataSource.updateTickerByCode(code,True)
#         dataSource.analysisTickerOnTime(code,400)

# if sys.argv[1] == '-u':
#     if len(sys.argv) > 3 and sys.argv[2] == 'start':
#         dataSource.updateTickerStartWith(sys.argv[3])
#     elif len(sys.argv) > 2:
#         dataSource.updateTickerQuarter(sys.argv[2])
#     else:
#         dataSource.updateAllTicker()

# if sys.argv[1] == '-r':
#     dataSource.updateRecommendTickers()

# if sys.argv[1] == '-up':         
#     startKey = None
#     if len(sys.argv) > 2 and sys.argv[2] is not None:
#         startKey = sys.argv[2].upper()
#     tickers = dataSource.getProjectTickers(projectId,startKey)
#     dataSource.updateTickers(tickers)

# if sys.argv[1] == '-rp':
#     startKey = None
#     if len(sys.argv) > 2 and sys.argv[2] is not None:
#         startKey = sys.argv[2].upper()
#     tickers = dataSource.getProjectTickers(projectId,startKey)
#     dataSource.updateRecommendProjectTicker(tickers)
    
    
# if sys.argv[1] == '-rp':
#     startKey = None
#     if len(sys.argv) > 2:
#         startKey = sys.argv[2].upper()
#         tickers = dataSource.getProjectTickerCodes(projectId,startKey)
#         for code in tickers:
#             dataSource.delProjectTicker(projectId,code)


# if sys.argv[1] == '-add':
#     code = None
#     if sys.argv[2] == 'hk':
#         code = 'HK.%s'%sys.argv[3].zfill(5)
#     elif sys.argv[2] == 'zh':
#         code = sys.argv[3].zfill(6)
#         if code.startswith('0') or code.startswith('3'):
#             code  = 'SZ.%s'%code
#         elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
#             code  = 'SH.%s'%code
#     elif sys.argv[2] == 'us':
#         code = 'US.%s'%sys.argv[3]
#     if code is not None:
#         print('添加项目{}到股票池'.format(code))
#         dataSource.addProjectTicker(projectId,code)

# if sys.argv[1] == '-rm':
#     code = None
#     if sys.argv[2] == 'hk':
#         code = 'HK.%s'%sys.argv[3].zfill(5)
#     elif sys.argv[2] == 'zh':
#         code = sys.argv[3].zfill(6)
#         if code.startswith('0') or code.startswith('3'):
#             code  = 'SZ.%s'%code
#         elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
#             code  = 'SH.%s'%code
#     elif sys.argv[2] == 'us':
#         code = 'US.%s'%sys.argv[3]
#     if code is not None:
#         print('移除项目{}从股票池'.format(code))
#         dataSource.delProjectTicker(projectId,code)