#!/usr/bin/env python
VERSION='1.02'
import os,sys,array
import coral
from RecoLuminosity.LumiDB import argparse,idDealer,CommonUtil


class newSchemaNames():
    def __init__(self):
        self.revisiontable='REVISIONS'
        self.luminormtable='LUMINORMS'
        self.lumidatatable='LUMIDATA'
        self.lumisummarytable='LUMISUMMARY'
        self.runsummarytable='CMSRUNSUMMARY'
        self.lumidetailtable='LUMIDETAIL'
        self.trgdatatable='TRGDATA'
        self.lstrgtable='LSTRG'
        self.hltdatatable='HLTDATA'
        self.lshlttable='LSHLT'
        self.trghltmaptable='TRGHLTMAP'
        self.validationtable='LUMIVALIDATION'
    def idtablename(self,datatablename):
        return datatablename.upper()+'_ID'
    def entrytablename(self,datatablename):
        return datatablename.upper()+'_ENTRIES'
    def revtablename(self,datatablename):
        return datatablename.upper()+'_REV'
    
class oldSchemaNames(object):
    def __init__(self):
        self.lumisummarytable='LUMISUMMARY'
        self.lumidetailtable='LUMIDETAIL'
        self.runsummarytable='CMSRUNSUMMARY'
        self.trgtable='TRG'
        self.hlttable='HLT'
        self.trghltmaptable='TRGHLTMAP'

def createNewTable(dbsession):
    pass

def modifyOldTables():
    pass

def createEntry():
    pass
def createRevision():
    pass
def createBranch():
    pass

def getOldTrgData(dbsession,runnum):
    '''
    generate new trgdata_id for trgdata
    select cmslsnum,deadtime,bitname,trgcount,prescale from trg where runnum=:runnum and bitnum=0 order by cmslsnum;
    select cmslsnum,bitnum,bitname,trgcount,deadtime,prescale from trg where runnum=:runnum order by cmslsnum
    single out trgcount[0],bitname[0],prescale[0]
    pack into blob bitname,trgcount,prescale
    insert into trgdata trgdata_id,runnum,source,bitzeroname,bitnameblob
    insert into lstrg trgdata_id,runnum,cmslsnum,deadtime,bitzerocount,bitzeroprescale,prescaleblob,trgcountblob
    '''
    databuffer={} #{cmslsnum:[deadtime,bizeroname,bitzerocount,bitzeroprescale,bitnames,trgcountBlob,trgprescaleBlob]}
    dbsession.typeConverter().setCppTypeForSqlType('unsigned int','NUMBER(10)')
    dbsession.typeConverter().setCppTypeForSqlType('unsigned long long','NUMBER(20)')
    try:
        dbsession.transaction().start(True)
        qHandle=dbsession.nominalSchema().newQuery()
        n=oldSchemaNames()
        qHandle.addToTableList(n.trgtable)
        qHandle.addToOutputList('CMSLSNUM','cmslsnum')
        qHandle.addToOutputList('DEADTIME','deadtime')
        qHandle.addToOutputList('BITNAME','bitname')
        qHandle.addToOutputList('TRGCOUNT','trgcount')
        qHandle.addToOutputList('PRESCALE','prescale')
        qCondition=coral.AttributeList()
        qCondition.extend('runnum','unsigned int')
        qCondition.extend('bitnum','unsigned int')
        qCondition['runnum'].setData(int(runnum))
        qCondition['bitnum'].setData(int(0))
        qResult=coral.AttributeList()
        qResult.extend('cmslsnum','unsigned int')
        qResult.extend('deadtime','unsigned long long')
        qResult.extend('bitname','string')
        qResult.extend('trgcount','unsigned int')
        qResult.extend('prescale','unsigned int')
        qHandle.defineOutput(qResult)
        qHandle.setCondition('RUNNUM=:runnum AND BITNUM=:bitnum',qCondition)
        cursor=qHandle.execute()
        while cursor.next():
            cmslsnum=cursor.currentRow()['cmslsnum'].data()
            deadtime=cursor.currentRow()['deadtime'].data()
            bitname=cursor.currentRow()['bitname'].data()
            bitcount=cursor.currentRow()['trgcount'].data()
            prescale=cursor.currentRow()['prescale'].data()
            if not databuffer.has_key(cmslsnum):
                databuffer[cmslsnum]=[]
            databuffer[cmslsnum].append(deadtime)
            databuffer[cmslsnum].append(bitname)
            databuffer[cmslsnum].append(bitcount)
            databuffer[cmslsnum].append(prescale)
        del qHandle
        qHandle=dbsession.nominalSchema().newQuery()
        qHandle.addToTableList(n.trgtable)
        qHandle.addToOutputList('CMSLSNUM','cmslsnum')
        qHandle.addToOutputList('BITNUM','bitnum')
        qHandle.addToOutputList('BITNAME','bitname')
        qHandle.addToOutputList('TRGCOUNT','trgcount')
        qHandle.addToOutputList('PRESCALE','prescale')
        qCondition=coral.AttributeList()
        qCondition.extend('runnum','unsigned int')
        qCondition['runnum'].setData(int(runnum))
        qHandle.setCondition('RUNNUM=:runnum',qCondition)
        qHandle.addToOrderList('cmslsnum')
        qHandle.addToOrderList('bitnum')
        qResult=coral.AttributeList()
        qResult.extend('cmslsnum','unsigned int')
        qResult.extend('bitnum','unsigned int')
        qResult.extend('bitname','string')
        qResult.extend('trgcount','unsigned int')
        qResult.extend('prescale','unsigned int')
        qHandle.defineOutput(qResult)
        cursor=qHandle.execute()
        bitnameList=[]
        trgcountArray=array.array('l')
        prescaleArray=array.array('l')
        counter=0
        previouscmslsnum=0
        while cursor.next():
            cmslsnum=cursor.currentRow()['cmslsnum'].data()
            bitnum=cursor.currentRow()['bitnum'].data()
            bitname=cursor.currentRow()['bitname'].data()
            trgcount=cursor.currentRow()['trgcount'].data()        
            prescale=cursor.currentRow()['prescale'].data()
            if bitnum==0 and counter!=0:
                bitnames=','.join(bitnameList)
                trgcountBlob=CommonUtil.packArraytoBlob(trgcountArray)
                prescaleBlob=CommonUtil.packArraytoBlob(prescaleArray)
                databuffer[previouslsnum].append(bitnames)
                databuffer[previouslsnum].append(trgcountBlob)
                databuffer[previouslsnum].append(prescaleBlob)
                bitnameList=[]
                trgcountArray=array.array('l')
                prescaleArray=array.array('l')
            else:
                previouslsnum=cmslsnum
            bitnameList.append(bitname)
            trgcountArray.append(trgcount)
            prescaleArray.append(prescale)
            counter+=1
        bitnames=','.join(bitnameList)
        trgcountBlob=CommonUtil.packArraytoBlob(trgcountArray)
        prescaleBlob=CommonUtil.packArraytoBlob(prescaleArray)
        databuffer[cmslsnum].append(bitnames)
        databuffer[cmslsnum].append(trgcountBlob)
        databuffer[cmslsnum].append(prescaleBlob)
        print CommonUtil.unpackBlobtoArray(databuffer[377][5],'l')
        del qHandle
        dbsession.transaction().commit()
    except Exception,e :
        dbsession.transaction().rollback()
        del dbsession
        raise Exception,'migrateSchema.getOldTrgData:'+str(e)
    return databuffer

    #coral.transaction().start(False)
    #idgen=idDealer.idDealer(schema)
    #trgid=idgen.generateNextIDForTable(trgtable) 
    #coral.transaction().commit()
    
def transferLumiData(dbsession,runnum):
    '''
    generate new lumidata_id for lumidata
    insert into lumidata_id , runnum into lumidata
    insert into lumidata_id into lumisummary
    insert into lumidata_id into lumidetail
    '''
    pass

def getOldHLTData(dbsession,runnum):
    '''
    generate new hltdata_id for hltdata
    select cmslsnum,pathname,inputcount,acceptcount,prescale from hlt where runnum=:runnum order by cmslsnum
    find npath
    pack for the first cmslsnum into blob pathname
    pack for each cmslsnum into blob inputcount,acceptcount,prescale,
    insert into hlt_data hltdata_id, runnum,npath,pathnameblob
    insert into lshlt hltdata_id,runnum,cmslsnum,prescaleblob,hltcountblob,acceptblob
    '''
    pass
    

def main():
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),description="migrate lumidb schema",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c',dest='connect',action='store',required=False,default='oracle://cms_orcoff_prep/CMS_LUMI_DEV_OFFLINE',help='connect string to trigger DB(required)')
    parser.add_argument('-P',dest='authpath',action='store',required=False,default='/afs/cern.ch/user/x/xiezhen',help='path to authentication file')
    parser.add_argument('-r',dest='runnumber',action='store',required=True,help='run number')
    parser.add_argument('--debug',dest='debug',action='store_true',help='debug')
    args=parser.parse_args()
    runnumber=int(args.runnumber)
    os.environ['CORAL_AUTH_PATH']=args.authpath
    svc=coral.ConnectionService()
    dbsession=svc.connect(args.connect,accessMode=coral.access_Update)
    if args.debug:
        msg=coral.MessageStream('')
        msg.setMsgVerbosity(coral.message_Level_Debug)
    result=getOldTrgData(dbsession,runnumber)
    del dbsession
    del svc
    #print result
if __name__=='__main__':
    main()
    
