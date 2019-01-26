from emitter import surfaceEmitter


class btReports(surfaceEmitter):
    types={}
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        surfaceEmitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="btreports"
        self.modeltype="bttypes"
            
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
    btReports(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client).start()   


