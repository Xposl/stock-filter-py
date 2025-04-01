from decimal import Decimal
from futu import *

class FutuClient:

    def getTickers(self,groupName):
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        ret, data = quote_ctx.get_user_security(groupName)
        if ret == RET_OK:
            quote_ctx.close()
            return data['code'].values
        else:
            raise Exception('error:', data)

    def modifyUserGroup(self,groupName,op,code_list):
        operation = ModifyUserSecurityOp.NONE
        if op == 'add':
            operation = ModifyUserSecurityOp.ADD
        if op == 'del':
            operation = ModifyUserSecurityOp.DEL
        if op == 'out':
            operation = ModifyUserSecurityOp.MOVE_OUT
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        ret, data = quote_ctx.modify_user_security(groupName, operation, code_list)
        if ret == RET_OK:
            print(data) # 返回 success
        else:
            print('error:', data)
        quote_ctx.close()
    

    def updateWatchList(self,myGroups,codeList):
        watchList = []
        recommendGroup = '推荐'
        groups = ['港股','沪深','美股']
        # 获取特殊列表，保留观察项目
        # for groupName in myGroups:
        #     tickers = self.getTickers(groupName)
        #     for code in tickers:
        #         watchList.append(code)
        
        # # 移除非关注项目
        # for groupName in groups:
        #     code_list = []
        #     out_list = []
        #     tickers = self.getTickers(groupName)
        #     for code in tickers:
        #         if code not in watchList:
        #             code_list.append(code)
        #         else:
        #             out_list.append(code)
        #     self.modifyUserGroup(recommendGroup,'del',code_list)
        #     self.modifyUserGroup(recommendGroup,'out',out_list)
        
        if len(codeList) > 0:
            print('一共获取推荐项目：'+str(len(codeList)))
            self.modifyUserGroup(recommendGroup,'add',codeList)
