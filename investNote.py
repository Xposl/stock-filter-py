#coding=UTF-8
# from core.Valuation.ResearchReportValuation import ResearchReportValuation
import sys
from core.handler import DataSourceHelper

# from custom.TickerScoreFilter import TickerScoreFilter
# from custom.TickerHighValuation import TickerHighValuation
import datetime


dataSource = DataSourceHelper()


if sys.argv[1] == '-ticker':
  dataSource.update_ticker_list()

if sys.argv[1] == '-a':
    code = None
    if sys.argv[2] == 'hk':
        code = 'HK.%s'%sys.argv[3].zfill(5)
    elif sys.argv[2] == 'zh':
        code = sys.argv[3].zfill(6)
        if code.startswith('0') or code.startswith('3'):
            code  = 'SZ.%s'%code
        elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
            code  = 'SH.%s'%code
    elif sys.argv[2] == 'us':
        code = 'US.%s'%sys.argv[3]

    if code is not None:
        dataSource.analysis_ticker(code)

if sys.argv[1] == '-ao':
    code = None
    if sys.argv[2] == 'hk':
        code = 'HK.%s'%sys.argv[3].zfill(5)
    elif sys.argv[2] == 'zh':
        code = sys.argv[3].zfill(6)
        if code.startswith('0') or code.startswith('3'):
            code  = 'SZ.%s'%code
        elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
            code  = 'SH.%s'%code
    elif sys.argv[2] == 'us':
        code = 'US.%s'%sys.argv[3]
    if code is not None:
        dataSource.analysis_ticker_on_time(code,400)