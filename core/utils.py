
import math
import sys

class UtilsHelper:

    def runProcess(self,index,total,title,message):
        print("\r\033[K", end="")  # \r移回行首，\033[K清除从光标到行尾的内容
        process = int(index/(total-1) * 100) if total > 1 else 100
        print("{title}: {process}%: ".format(
            title = title,
            process= process
        ), "▋" * (process // 2), message, end="")
        sys.stdout.flush()

    def calcuPercent(self,dividend,divisor):
        return round(dividend/divisor * 100,2) if divisor > 0 else 0
    
    def calcuInteger(self,dividend,divisor):
        return math.floor(dividend/divisor) if divisor > 0 else 0

    def keepUpTrend(self,data,sign,day,length):
        result = True
        start = day - length if day - length > 0 else 0
        for i in range(start, day):
            if data[i] < sign:
                result = False
        return result

    # 通道交易点计算函数
    def doubleLinePos(self,priceData,adjustBaseData,adjustData):
        stopData = []
        posData = []
        for i in range(len(priceData)):
            price = priceData[i]
            adjustBasse = adjustBaseData[i]
            adjust = adjustData[i]
            if i == 0:
                stopData.append(adjustBasse - adjust)
                continue
            lastPrice = priceData[i-1]
            lastStopData = stopData[i-1]
            v1 = adjustBasse - adjust if price > lastStopData else adjustBasse + adjust
            v2 = min(adjustBasse + adjust, lastStopData) if price < lastStopData and lastPrice < lastStopData else v1
            v3 = max(adjustBasse - adjust, lastStopData) if price > lastStopData and lastPrice > lastStopData else v2
            stopData.append(v3)

        for i in range(len(priceData)):
            if i == 0:
                posData.append(0)
                continue
            price = priceData[i]
            lastPrice = priceData[i-1]
            lastStopData = stopData[i-1]
            lastPosData = posData[i-1]
            v1 = -1 if lastPrice > lastStopData and price < lastStopData else lastPosData
            v2 = 1 if lastPrice < lastStopData and price > lastStopData else v1
            posData.append(v2)
        return posData

    def keepDownTrend(self,data,sign,day,length):
        result = True
        start = day - length if day - length > 0 else 0
        for i in range(start, day):
            if data[i] > sign:
                result = False
        return result


    def SUM(self,data,dayCount):
        result = []
        length = len(data)
        for i in range(length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            sum = 0
            for j in range(calcuDay):
                sum += data[i-j]
            result.append(sum)
        return result
    
    def AVEDEV(self,data,dayCount):
        result = [0]
        length = len(data)
        smaData = self.SMA(data,dayCount)
        for i in range(1,length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            sum = 0
            for j in range(calcuDay):
                sum += abs(data[i-j] - smaData[i])
            result.append(sum/calcuDay)
        return result

    def STDDEV(self,data,dayCount):
        result = [0]
        length = len(data)
        smaData = self.SMA(data,dayCount)
        for i in range(1,length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            sum = 0
            for j in range(calcuDay):
                sum += abs(data[i-j] - smaData[i]) * abs(data[i-j] - smaData[i])
            result.append(math.sqrt(sum/calcuDay))
        return result

    def HIGHEST(self,data,dayCount):
        result = []
        length = len(data)
        for i in range(length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            subArr = data[i-calcuDay+1:i+1]
            result.append(max(subArr))
        return result

    def LOWEST(self,data,dayCount):
        result = []
        length = len(data)
        for i in range(length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            subArr = data[i - calcuDay + 1:i+1]
            result.append(min(subArr))
        return result

    def RMA(self, data, dayCount):
        result = []
        length = len(data)
        for i in range(length):
            if(i == 0):
                result.append(0)
                continue
            alpha = dayCount
            res = (data[i] + (alpha - 1) * result[i-1])/alpha
            result.append(res)
        return result
    
    def SMA(self, data, dayCount):
        result = [data[0]]
        length = len(data)
        for i in range(1,length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            sum = 0
            for j in range(calcuDay):
                sum += data[i-j]
            result.append(sum/calcuDay)
        return result

    def EMA(self, data, dayCount):
        result = [data[0]]
        length = len(data)
        for i in range(1,length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            res = (2 * data[i] + (calcuDay - 1) * result[i-1])/(calcuDay + 1)
            result.append(res)
        return result
    
    def WMA(self,data,dayCount):
        result = [data[0]]
        length = len(data)
        for i in range(1, length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            norm = 0
            sum = 0
            for j in range(calcuDay):
                weight = (calcuDay - j) * calcuDay
                norm = norm + weight
                sum = sum + data[i-j] * weight
            result.append(sum/norm)
        return result

    def MA(self, data, dayCount, weight):
        result = [data[0]]
        length = len(data)
        for i in range(1,length):
            calcuDay = dayCount
            if i < dayCount - 1:
                calcuDay = i + 1
            res = (weight * data[i] + (calcuDay - weight) * result[i-1])/calcuDay
            result.append(res)
        return result
    
    def HMA(self, data, dayCount):
        length = len(data)
        alphaData = []
        halfDay = int(round(dayCount/2,0))
        sqrtDay = int(round(math.sqrt(dayCount),0))
        halfData = self.WMA(data,halfDay)
        wmaData = self.WMA(data,dayCount)
        for i in range(length):
            alpha = 2 * halfData[i] - wmaData[i]
            alphaData.append(alpha)
        return self.WMA(alphaData,sqrtDay)
            
            
    def VWMA(self, kLineData, dayCount):
        result = []
        data = []
        volumeData = []
        length = len(kLineData)
        for klItem in kLineData:
            volumeData.append(klItem['volume'])
            data.append(klItem['close'] * klItem['volume'])
        maData = self.SMA(data,dayCount)
        maVolume = self.SMA(volumeData,dayCount)
        for i in range(length):
            vwma = maData[i]/maVolume[i] if maVolume[i] > 0 else 0
            result.append(vwma)

        return result

    def TR(self,kLineData):
        result = []
        length = len(kLineData)
        for i in range(length):
            dayVal = kLineData[i]
            lastDayVal = kLineData[i-1]
            high = dayVal['high']
            low = dayVal['low']
            lastClose = lastDayVal['close']
            res = max(max((high-low),abs(lastClose - high)),abs(lastClose-low))
            result.append(res)
        return result
    
    def RATR(self,kLineData,dayCount):
        trData = self.TR(kLineData)
        return self.RMA(trData,dayCount)
    
    def TYP(self,kLineData):
        result = []
        length = len(kLineData)
        for i in range(length):
            dayValue = kLineData[i]
            high = dayValue['high']
            low = dayValue['low']
            close = dayValue['close']
            result.append((high + low + close)/3)
        return result

    def CCI(self,kLineData,dayCount):
        result = [0]
        length = len(kLineData)
        typData = self.TYP(kLineData)
        typMaData = self.SMA(typData,dayCount)
        typeAveData = self.AVEDEV(typData,dayCount)
        for i in range(1,length):
            cci = (typData[i] - typMaData[i])/(0.015 * typeAveData[i]) if typeAveData[i] > 0 else 0
            result.append(cci)
        return result

    def getWeekLine(self,kLineData):
        result = []
        data = {
            'time_key': '',
            'high': 0,
            'low': 0,
            'open': 0,
            'close': 0,
            'volume': 0
        }
        curWeek = ''
        index = -1
        for kdata in kLineData:
            week = kdata['time_key'].strftime('%Y-%W')
            if curWeek != week:
                data = {
                    'time_key': kdata['time_key'],
                    'high': kdata['high'],
                    'low': kdata['low'],
                    'open': kdata['open'],
                    'close': kdata['close'],
                    'volume': kdata['volume']
                }
                index += 1
                curWeek = week
                result.append(data)
            else:
                data['high'] = data['high'] if data['high'] > kdata['high'] else kdata['high']
                data['low'] = data['low'] if data['low'] < kdata['low'] else kdata['low']
                data['close'] = kdata['close']
                data['volume'] += kdata['volume']
                result[index] = data
        return result
