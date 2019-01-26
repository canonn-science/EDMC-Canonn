from emitter import codexEmitter


class fgReports(codexEmitter):
    types={}
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        codexEmitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="fgreports"
        self.modeltype="fgtypes"
            
'''
    
'''
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):

    if entry["event"] == "CodexEntry":
        fgReports(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client).start()   



