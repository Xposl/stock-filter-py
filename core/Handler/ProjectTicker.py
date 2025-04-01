
from core.API import APIHelper

from core.utils import UtilsHelper

class ProjectTicker:
    APIHelper = APIHelper()

    def addProjectTicker(self,projectId,code):
        ticker= self.APIHelper.ticker().getItemByCode(code)
        self.APIHelper.projectTicker().updateItem(projectId,ticker['id'])
    
    def delProjectTicker(self,projectId,code):
        ticker= self.APIHelper.ticker().getItemByCode(code)
        self.APIHelper.projectTicker().updateItem(projectId,ticker['id'],1)

    def getProjectTickers(self,projectId):
        return self.APIHelper.projectTicker().getTickersByProjectId(projectId)

    def updateProjectTickers(self,projectId,codeList):
        self.APIHelper.projectTicker().delItemsByProjectId(projectId)
        total = len(codeList)
        for i in range(total):
            code = codeList[i]

            UtilsHelper().runProcess(i,total,"project","[total:{total}]{code}".format(
                code = ticker['code'],
                total = total
            ))
            ticker= self.APIHelper.ticker().getItemByCode(code)
            self.APIHelper.projectTicker().updateItem(projectId,ticker['id'])

