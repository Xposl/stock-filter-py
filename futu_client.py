import numpy as np
from core.Handler import DataSourceHelper
from custom.client import FutuClient
import datetime
import sys

projectId = 1
endDate =  datetime.datetime.now().strftime('%Y-%m-%d')

dataSource = DataSourceHelper()
dataSource.setEndDate(endDate)

keeGroup = ['大环境','目标池','观察池','我的组合','特别关注','埋伏','概念','大环境']
group = {
    '0':'目标池',
    '1':'我的组合',
    '2':'特别关注',
    '3':'推荐',
    '98':'埋伏',
    '99': '观察池'
}

## 组合
if sys.argv[1] == '-r':
    print('更新推荐列表')
    startKey = None
    if len(sys.argv) > 2:
        startKey = sys.argv[2].upper()
    tickers = dataSource.getRecommendTickers(startKey)
    FutuClient().updateWatchList(keeGroup,tickers)

if sys.argv[1] == '-p':
    print('展示股票池')
    startKey = None
    if len(sys.argv) > 2:
        startKey = sys.argv[2].upper()
    tickers = dataSource.getProjectTickerCodes(projectId,startKey)
    FutuClient().updateWatchList(keeGroup,tickers)

if sys.argv[1] == '-rcp':
    tickers = dataSource.getRecommendProjectTickers()
    FutuClient().updateWatchList(keeGroup,tickers)

if sys.argv[1] == '-rp':
    startKey = None
    if len(sys.argv) > 2:
        startKey = sys.argv[2].upper()
        print('更新{}开头的股票池推荐列表'.format(startKey))
    else:
        print('更新股票池推荐列表')
    codeList = []
    ptickers = dataSource.getProjectTickerCodes(projectId,startKey)
    rtickers = dataSource.getRecommendTickers(startKey)
    for code in rtickers:
        if code in ptickers:
            codeList.append(code)
    FutuClient().updateWatchList(keeGroup,codeList)


if sys.argv[1] == '-test':
    groupName = '我的组合'
    startKey = None
    if len(sys.argv) > 2:
        if sys.argv[2] in group:
            groupName = group[sys.argv[2]]
        else:
            startKey = sys.argv[2].upper()
    if len(sys.argv) > 3:
        startKey = sys.argv[3].upper()
    print('分析股票分组{}'.format(groupName))
    tickers = FutuClient().getTickers(groupName)
    tickersList = np.array(tickers)
    for code in np.sort(tickersList):
        if startKey != None:
            if code.startswith(startKey) == False:
                continue
        dataSource.updateTickerByCode(code,True)
        dataSource.analysisTicker(code,250)

if sys.argv[1] == '-testo':
    groupName = '我的组合'
    startKey = None
    if len(sys.argv) > 2:
        if sys.argv[2] in group:
            groupName = group[sys.argv[2]]
        else:
            startKey = sys.argv[2].upper()
    if len(sys.argv) > 3:
        startKey = sys.argv[3].upper()
    tickers = FutuClient().getTickers(groupName)
    print('分析即时股票分组{}'.format(groupName))
    tickersList = np.array(tickers)
    for code in np.sort(tickersList):
        if startKey != None:
            if code.startswith(startKey) == False:
                continue
        print(code)
        dataSource.updateTickerByCode(code,True)
        dataSource.analysisTickerOnTime(code,250)

if sys.argv[1] == '-diff':
    tickers = FutuClient().getTickers('特别关注')
    ptickers = dataSource.getProjectTickerCodes(projectId)
    for code in tickers:
        if code not in ptickers:
            if len(sys.argv) > 2 and sys.argv[2] == 'f':
                print('添加项目{}到股票池'.format(code))
                dataSource.addProjectTicker(projectId,code)
            else:
                print('存在未关注的股票',code)