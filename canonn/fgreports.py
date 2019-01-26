from emitter import surfaceEmitter


class fgReports(surfaceEmitter):
    types={}
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        surfaceEmitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="fgreports"
        self.modeltype="fgtypes"
            
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):

    if entry["event"] == "CodexEntry":
        fgReports(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client).start()   



