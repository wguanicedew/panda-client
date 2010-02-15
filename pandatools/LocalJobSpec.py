"""
local job specification

"""

import re
import urllib
import datetime

class LocalJobSpec(object):
    # attributes
    _attributes = ('id','JobID','PandaID','jobStatus','site','cloud','jobType',
                   'jobName','inDS','outDS','libDS','provenanceID','creationTime',
                   'lastUpdate','jobParams','dbStatus','buildStatus','retryID',
                   'commandToPilot')
    # appended attributes
    appended = {
        'groupID'    :'INTEGER',
        'releaseVar' :'VARCHAR(128)',
        'cacheVar'   :'VARCHAR(128)',
        }
    
    _attributes += tuple(appended.keys())
    # slots
    __slots__ = _attributes


    # constructor
    def __init__(self):
        # install attributes
        for attr in self._attributes:
            setattr(self,attr,None)


    # string format
    def __str__(self):
        # job status
        statusMap = {}
        for item in self.jobStatus.split(','):
            match = re.search('^(\w+)\*(\d+)$',item)
            if match == None:
                # non compact
                if not statusMap.has_key(item):
                    statusMap[item] = 0
                statusMap[item] += 1
            else:
                # compact
                tmpStatus = match.group(1)
                tmpCount  = int(match.group(2))
                if not statusMap.has_key(tmpStatus):
                    statusMap[tmpStatus] = 0
                statusMap[tmpStatus] += tmpCount
        statusStr = self.dbStatus
        for tmpStatus,tmpCount in statusMap.iteritems():
            statusStr += '\n%8s   %8s : %s' % ('',tmpStatus,tmpCount)
        # number of jobs
        nJobs = len(self.PandaID.split(','))
        if self.buildStatus != '':
            # including buildJob
            nJobsStr = "%d + 1(build)" % (nJobs-1)
        else:
            nJobsStr = "%d" % nJobs
        # remove duplication in inDS and outDS
        strInDS = ''
        try:
            tmpInDSList = []
            for tmpItem in str(self.inDS).split(','):
                if not tmpItem in tmpInDSList:
                    tmpInDSList.append(tmpItem)
                    strInDS += '%s,' % tmpItem
            strInDS = strInDS[:-1]
        except:
            pass
        strOutDS = ''
        try:
            tmpOutDSList = []
            for tmpItem in str(self.outDS).split(','):
                if not tmpItem in tmpOutDSList:
                    tmpOutDSList.append(tmpItem)
                    strOutDS += '%s,' % tmpItem
            strOutDS = strOutDS[:-1]
        except:
            pass
        # parse
        relStr = ''
        if not self.releaseVar in ['','NULL','None',None]:
            relStr = self.releaseVar
        # cache
        cacheStr = ''
        if not self.cacheVar in ['','NULL','None',None]:
            cacheStr = self.cacheVar
        # string representation
        strFormat = "%15s : %s\n"
        strOut =  ""
        strOut += strFormat % ("JobID",        self.JobID)
        strOut += strFormat % ("type",         self.jobType)
        strOut += strFormat % ("release",      relStr)
        strOut += strFormat % ("cache",        cacheStr)
        strOut += strFormat % ("PandaID",      self.encodeCompact()['PandaID'])
        strOut += strFormat % ("nJobs",        nJobsStr)
        strOut += strFormat % ("site",         self.site)
        strOut += strFormat % ("cloud",        self.cloud)                
        strOut += strFormat % ("inDS",         strInDS)
        strOut += strFormat % ("outDS",        strOutDS)
        strOut += strFormat % ("libDS",        str(self.libDS))
        strOut += strFormat % ("retryID",      self.retryID)        
        strOut += strFormat % ("provenanceID", self.provenanceID)
        strOut += strFormat % ("creationTime", self.creationTime.strftime('%Y-%m-%d %H:%M:%S'))
        strOut += strFormat % ("lastUpdate",   self.lastUpdate.strftime('%Y-%m-%d %H:%M:%S'))
        strOut += strFormat % ("params",       self.jobParams)
        strOut += strFormat % ("jobStatus",    statusStr)
        # return
        return strOut

    
    # override __getattribute__ for SQL
    def __getattribute__(self,name):
        ret = object.__getattribute__(self,name)
        if ret == None:
            return "NULL"
        return ret
        
    
    # pack tuple into JobSpec
    def pack(self,values):
        for i in range(len(self._attributes)):
            attr= self._attributes[i]
            val = values[i]
            setattr(self,attr,val)
        # expand compact values
        self.decodeCompact()


    # return a tuple of values
    def values(self,forUpdate=False):
        # make compact values
        encVal = self.encodeCompact()
        if forUpdate:
            # for UPDATE
            retS = ""
        else:
            # for INSERT
            retS = "("
        # loop over all attributes     
        for attr in self._attributes:
            if encVal.has_key(attr):
                val = encVal[attr]
            else:
                val = getattr(self,attr)
            # convert datetime to str
            if type(val) == datetime.datetime:
                val = val.strftime('%Y-%m-%d %H:%M:%S')
            # add colum name for UPDATE
            if forUpdate:
                if attr == 'id':
                    continue
                retS += '%s=' % attr
            # value    
            if val == 'NULL':
                retS += 'NULL,'
            else:
                retS += "'%s'," % str(val)
        retS  = retS[:-1]
        if not forUpdate:
            retS += ')'
        return retS

    
    # expand compact values
    def decodeCompact(self):
        # PandaID
        pStr = ''
        for item in self.PandaID.split(','):
            match = re.search('^(\d+)-(\d+)$',item)
            if match == None:
                # non compact
                pStr += (item+',')
            else:
                # compact
                sID = long(match.group(1))
                eID = long(match.group(2))
                for tmpID in range(sID,eID+1):
                    pStr += "%s," % tmpID
        self.PandaID = pStr[:-1]
        # status
        sStr = ''
        for item in self.jobStatus.split(','):
            match = re.search('^(\w+)\*(\d+)$',item)
            if match == None:
                # non compact
                sStr += (item+',')
            else:
                # compact
                tmpStatus = match.group(1)
                tmpCount  = int(match.group(2))
                for tmpN in range(tmpCount):
                    sStr += "%s," % tmpStatus
        self.jobStatus = sStr[:-1]
        # job parameters
        self.jobParams = urllib.unquote(self.jobParams)
        # datetime
        for attr in self._attributes:
            val = getattr(self,attr)
            # convert str to datetime
            match = re.search('^(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)$',val)
            if match != None:
                tmpDate = datetime.datetime(year   = int(match.group(1)),
                                            month  = int(match.group(2)),
                                            day    = int(match.group(3)),
                                            hour   = int(match.group(4)),
                                            minute = int(match.group(5)),
                                            second = int(match.group(6)))
                setattr(self,attr,tmpDate)


    # make compact values
    def encodeCompact(self):
        ret = {}
        # PandaID
        pStr = ''
        sID = None
        eID = None
        for item in self.PandaID.split(','):
            # convert to long
            tmpID = long(item)
            # set start/end ID
            if sID == None:
                sID = tmpID
                eID = tmpID
                continue
            # successive number
            if eID+1 == tmpID:
                eID = tmpID
                continue
            # jump
            if sID == eID:
                pStr += '%s,' % sID
            else:
                pStr += '%s-%s,' % (sID,eID)
            # reset
            sID = tmpID
            eID = tmpID
        # last bunch
        if sID == eID:
            pStr += '%s,' % sID
        else:
            pStr += '%s-%s,' % (sID,eID)
        ret['PandaID'] = pStr[:-1]
        # job status
        sStr = ''
        sStatus = None
        nStatus = 0
        toBeFrozen = True
        for tmpStatus in self.jobStatus.split(','):
            # check if is should be frozen
            if toBeFrozen and not tmpStatus in ['finished','failed','partial','canceled']:
                toBeFrozen = False
            # set start status
            if sStatus == None:
                sStatus = tmpStatus
                nStatus += 1
                continue
            # same status
            if sStatus == tmpStatus:
                nStatus += 1
                continue
            # jump
            if nStatus == 1:
                sStr += '%s,' % sStatus
            else:
                sStr += '%s*%s,' % (sStatus,nStatus)
            # reset
            sStatus = tmpStatus
            nStatus = 1
        # last bunch
        if nStatus == 1:
            sStr += '%s,' % sStatus
        else:
            sStr += '%s*%s,' % (sStatus,nStatus)
        ret['jobStatus'] = sStr[:-1]
        # job parameters
        ret['jobParams'] = urllib.quote(self.jobParams)
        # set dbStatus
        if toBeFrozen:
            self.dbStatus = 'frozen'
        else:
            if self.commandToPilot=='tobekilled':
                self.dbStatus = 'killing'
            else:
                self.dbStatus = 'running'
        # return
        return ret

        
    # return column names for INSERT or full SELECT
    def columnNames(cls):
        ret = ""
        for attr in cls._attributes:
            if ret != "":
                ret += ','
            ret += attr
        return ret
    columnNames = classmethod(columnNames)
