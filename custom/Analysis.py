import tushare as ts # 获取股票数据用
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker # 用于日期刻度定制
# import mpl_finance as mpf
# 注释了上面一行的旧版，新版是mplfinance，少了一个下划线，运行没警告，新版绘制蜡烛图性能应该更高，但是限得比较死，
# 不好加子图，后面我们把关键代码拿出来自己绘制
from mplfinance import original_flavor as mpf # 用新版库里面的旧版实现(跟mpl_finance一模一样)
from matplotlib import colors as mcolors  # 用于颜色转换成渲染时顶点需要的颜色格式
from matplotlib.collections import LineCollection, PolyCollection # 用于绘制直线集合和多边形集合
import tools # 计算MACD和KDJ(没有使用talib，有缺陷)
 
# 获取数据
df = ts.get_k_data('603986', '2019-01-01') # 获取日K线数据
df.drop('code', axis=1, inplace=True) # 剔除多余的列
tools.calc_macd(df) # 计算MACD值，数据存于DataFrame中
tools.calc_kdj(df) # 计算KDJ值，数据存于DataFrame中
df = df[-150:] # 取最近的N天测试，列顺序为 date,open,close,high,low,volume,dif,dea,bar,k,d,j
 
# 日期转换成整数序列
date_tickers=df.date.values
df.date = range(0, len(df)) # 日期改变成序号
matix = df.values # 转换成绘制蜡烛图需要的数据格式(date, open, close, high, low, volume)
xdates = matix[:, 0] # X轴数据(这里用的天数索引)
 
# 设置外观效果
plt.rc('font', family='Microsoft YaHei') # 用中文字体，防止中文显示不出来
plt.rc('figure', fc='k') # 绘图对象背景图
plt.rc('text', c='#800000') # 文本颜色
plt.rc('axes', axisbelow=True, xmargin=0, fc='k', ec='#800000', lw=1.5, labelcolor='#800000', unicode_minus=False) # 坐标轴属性(置底，左边无空隙，背景色，边框色，线宽，文本颜色，中文负号修正)
plt.rc('xticker', c='#d43221') # x轴刻度文字颜色
plt.rc('yticker', c='#d43221') # y轴刻度文字颜色
plt.rc('grid', c='#800000', alpha=0.9, ls=':', lw=0.8) # 网格属性(颜色，透明值，线条样式，线宽)
plt.rc('lines', lw=0.8) # 全局线宽
 
# 创建绘图对象和4个坐标轴
fig = plt.figure(figsize=(16, 8))
left, width = 0.05, 0.9
ax1 = fig.add_axes([left, 0.6, width, 0.35]) # left, bottom, width, height
ax2 = fig.add_axes([left, 0.45, width, 0.15], sharex=ax1) # 共享ax1轴
ax3 = fig.add_axes([left, 0.25, width, 0.2], sharex=ax1) # 共享ax1轴
ax4 = fig.add_axes([left, 0.05, width, 0.2], sharex=ax1) # 共享ax1轴
plt.setp(ax1.get_xtickerlabels(), visible=False) # 使x轴刻度文本不可见，因为共享，不需要显示
plt.setp(ax2.get_xtickerlabels(), visible=False) # 使x轴刻度文本不可见，因为共享，不需要显示
plt.setp(ax3.get_xtickerlabels(), visible=False) # 使x轴刻度文本不可见，因为共享，不需要显示
 
# 绘制蜡烛图
def format_date(x, pos=None): return '' if x<0 or x>len(date_tickers)-1 else date_tickers[int(x)] # 日期格式化函数，根据天数索引取出日期值
ax1.xaxis.set_major_formatter(ticker.FuncFormatter(format_date)) # 设置自定义x轴格式化日期函数
ax1.xaxis.set_major_locator(ticker.MultipleLocator(max(int(len(df)/15), 5))) # 横向最多排15个左右的日期，最少5个，防止日期太拥挤
# mpf.candlesticker_ochl(ax1, matix, width=0.5, colorup='#ff3232', colordown='#54fcfc')
# # 下面这一段代码，替换了上面注释的这个函数，因为上面的这个函数达不到同花顺的效果
opens, closes, highs, lows = matix[:, 1], matix[:, 2], matix[:, 3], matix[:, 4] # 取出ochl值
avg_dist_between_points = (xdates[-1] - xdates[0]) / float(len(xdates)) # 计算每个日期之间的距离
delta = avg_dist_between_points / 4.0 # 用于K线实体(矩形)的偏移坐标计算
barVerts = [((date - delta, open), (date - delta, close), (date + delta, close), (date + delta, open)) for date, open, close in zip(xdates, opens, closes) ] # 生成K线实体(矩形)的4个顶点坐标
rangeSegLow   = [ ((date, low), (date, min(open, close))) for date, low, open, close in zip(xdates, lows, opens, closes) ] # 生成下影线顶点列表
rangeSegHigh  = [ ((date, high), (date, max(open, close))) for date, high, open, close in zip(xdates, highs, opens, closes) ] # 生成上影线顶点列表
rangeSegments = rangeSegLow + rangeSegHigh # 上下影线顶点列表
cmap = {True: mcolors.to_rgba('#000000', 1.0), False: mcolors.to_rgba('#54fcfc', 1.0)} # K线实体(矩形)中间的背景色(True是上涨颜色，False是下跌颜色)
inner_colors = [ cmap[opn < cls] for opn, cls in zip(opens, closes) ]  # K线实体(矩形)中间的背景色列表
cmap = {True: mcolors.to_rgba('#ff3232', 1.0), False: mcolors.to_rgba('#54fcfc', 1.0)} # K线实体(矩形)边框线颜色(上下影线和后面的成交量颜色也共用)
updown_colors = [ cmap[opn < cls] for opn, cls in zip(opens, closes) ] # K线实体(矩形)边框线颜色(上下影线和后面的成交量颜色也共用)列表
ax1.add_collection(LineCollection(rangeSegments, colors=updown_colors, linewidths=0.5, antialiaseds=False)) # 生成上下影线的顶点数据(颜色，线宽，反锯齿，反锯齿关闭好像没效果)
ax1.add_collection(PolyCollection(barVerts, facecolors=inner_colors, edgecolors=updown_colors, antialiaseds=False, linewidths=0.5)) # 生成多边形(矩形)顶点数据(背景填充色，边框色，反锯齿，线宽)
 
# 绘制均线
# mav_colors = ['#ffffff', '#d4ff07', '#ff80ff', '#00e600', '#02e2f4', '#ffffb9', '#2a6848'] # 均线循环颜色
# mav_period = [5, 10, 20, 30, 60, 120, 180] # 定义要绘制的均线周期，可增减
# n = len(df)
# for i in range(len(mav_period)):
#     if n >= mav_period[i]:
#         mav_vals = df['close'].rolling(mav_period[i]).mean().values
#         ax1.plot(xdates, mav_vals, c=mav_colors[i%len(mav_colors)], label='MA'+str(mav_period[i]))
# ax1.set_title('K线图') # 标题
# ax1.grid(True) # 画网格
# ax1.legend(loc='upper right') # 图例放置于右上角
# ax1.xaxis_date() # 好像要不要效果一样？
 
# 绘制成交量和成交量均线（5日，10日）
# ax2.bar(xdates, matix[:, 5], width= 0.5, color=updown_colors) # 绘制成交量柱状图
# barVerts = [((date - delta, 0), (date - delta, vol), (date + delta, vol), (date + delta, 0)) for date, vol in zip(xdates, matix[:,5]) ] # 生成K线实体(矩形)的4个顶点坐标
# ax2.add_collection(PolyCollection(barVerts, facecolors=inner_colors, edgecolors=updown_colors, antialiaseds=False, linewidths=0.5)) # 生成多边形(矩形)顶点数据(背景填充色，边框色，反锯齿，线宽)
# if n>=5: # 5日均线，作法类似前面的均线
#     vol5 = df['volume'].rolling(5).mean().values
#     ax2.plot(xdates, vol5, c='y', label='VOL5')
# if n>=10: # 10日均线，作法类似前面的均线
#     vol10 = df['volume'].rolling(10).mean().values
#     ax2.plot(xdates, vol10, c='w', label='VOL10')
# ax2.yaxis.set_tickers_position('right') # y轴显示在右边
# ax2.legend(loc='upper right') # 图例放置于右上角
# ax2.grid(True) # 画网格
# # ax2.set_ylabel('成交量') # y轴名称
 
# # 绘制MACD
# difs, deas, bars = matix[:, 6], matix[:, 7], matix[:, 8] # 取出MACD值
# ax3.axhline(0, ls='-', c='g', lw=0.5) # 水平线
# ax3.plot(xdates, difs, c='w', label='DIFF') # 绘制DIFF线
# ax3.plot(xdates, deas, c='y', label='DEA') # 绘制DEA线
# # ax3.bar(xdates, df['bar'], width= 0.05, color=bar_colors) # 绘制成交量柱状图(发现用bar绘制，线的粗细不一致，故使用下面的直线列表)
# cmap = {True: mcolors.to_rgba('r', 1.0), False: mcolors.to_rgba('g', 1.0)} # MACD线颜色，大于0为红色，小于0为绿色
# bar_colors = [ cmap[bar > 0] for bar in bars ]  # MACD线颜色列表
# vlines = [ ((date, 0), (date, bars[date])) for date in range(len(bars)) ] # 生成MACD线顶点列表
# ax3.add_collection(LineCollection(vlines, colors=bar_colors, linewidths=0.5, antialiaseds=False)) # 生成MACD线的顶点数据(颜色，线宽，反锯齿)
# ax3.legend(loc='upper right') # 图例放置于右上角
# ax3.grid(True) # 画网格
 
# # 绘制KDJ
# K, D, J = matix[:, 9], matix[:, 10], matix[:, 11] # 取出KDJ值
# ax4.axhline(0, ls='-', c='g', lw=0.5) # 水平线
# ax4.yaxis.set_tickers_position('right') # y轴显示在右边
# ax4.plot(xdates, K, c='y', label='K') # 绘制K线
# ax4.plot(xdates, D, c='c', label='D') # 绘制D线
# ax4.plot(xdates, J, c='m', label='J') # 绘制J线
# ax4.legend(loc='upper right') # 图例放置于右上角
# ax4.grid(True) # 画网格
 
# set useblit = True on gtkagg for enhanced performance
from matplotlib.widgets import Cursor # 处理鼠标
cursor = Cursor(ax1, useblit=True, color='w', linewidth=0.5, linestyle='--')
 
plt.show()
