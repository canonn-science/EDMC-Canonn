from emitter import surfaceEmitter


class csReports(surfaceEmitter):
    types={}
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        surfaceEmitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="csreports"
        self.modeltype="cstypes"
            
'''
    
'''
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):

    if entry["event"] == "CodexEntry":
        csReports(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client).start()   

