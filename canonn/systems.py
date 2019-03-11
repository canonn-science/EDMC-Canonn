from urllib import quote_plus
import requests
import json
from debug import Debug
from debug import debug,error

class Systems():

    '''
        Caching all the Canonn Systems because we don't want to hit them up every time 
        we start the plugin
    '''
    systemCache={
        "HIP 89478":[-166.6875,96.46875,-62.90625],
        "Col 285 Sector RE-P c6-5":[-178.46875,31.28125,-72.75],
        "Varati":[-178.65625,77.125,-87.125],
        "Rodentia":[-9530.53125,-907.25,19787.375],
        "Bactrimpox":[-123.25,82,-84],
        "Col 285 Sector RE-P c6-8":[-184.15625,25,-78.4375],
        "Amatsuboshi":[-9516.03125,-908.25,19802.71875],
        "34 Omicron Cephei":[-183.15625,24.65625,-84.25],
        "Ngundjedes":[-167.6875,69.6875,-64.90625],
        "Masai":[-138.90625,52.75,-85.75],
        "HIP 112970":[-176.25,26.125,-72.6875],
        "Ix Chodharr":[-163.3125,51.71875,-96.34375],
        "Col 285 Sector TP-N c7-12":[-149.6875,84.9375,-52.28125],
        "Carlota":[-9531.40625,-874.96875,19797.53125],
        "Njoere":[-118.59375,64.03125,-92.25],
        "Col 285 Sector KJ-E b13-5":[-137.6875,53.1875,-78.90625],
        "Hementrim":[-160.4375,13.90625,-70.125],
        "Mahatrents":[-149.3125,81.78125,-51.40625],
        "Popon":[-156.78125,20.84375,-76.75],
        "Col 285 Sector KS-T d3-78":[-174.0625,7.96875,-101.71875],
        "Col 285 Sector EI-G b12-2":[-135.0625,66.84375,-90.28125],
        "HIP 2293":[-142.96875,56,-89.96875],
        "Canonnia":[-9522.9375,-894.0625,19791.875],
        "Jarildekald":[-164.9375,23.21875,-62.875],
        "Chacobog":[-161.15625,27.375,-72.75],
        "Col 285 Sector KS-T d3-124":[-168.21875,40.28125,-100.375],
        "Evenses":[-133.875,54.03125,-80.5625],
        "Aknango":[-155.40625,30,-76.4375],
        "Elboongzi":[-122.5,48.34375,-95],
        "Aymarahuara":[-151.5,39.40625,-74.1875],
        "Col 285 Sector IX-T d3-43":[-174.75,73.375,-92.84375],
        "Othelkan":[-162.84375,51.59375,-84.5],
        "Khun":[-171.59375,19.96875,-56.96875],
        "Undalibaluf":[-178.6875,19.4375,-93.40625],
        "HIP 114099":[-153.28125,26.65625,-69.34375],
        "31 Cephei":[-159.25,41.625,-70.40625],
        "Diabozo":[-159.34375,28.9375,-89.03125],
        "Chematja":[-136.40625,60.53125,-84.75],
        "Cauan Tzu":[-172.5,48.34375,-100.9375],
        "Dubbuennel":[-9521.40625,-913.5625,19786.53125],
        "Kopernik":[-9504.75,-901.75,19801.875],
        "HIP 94126":[-164.21875,81.59375,-52.5625],
        "Col 285 Sector XF-N c7-20":[-163.0625,14.03125,-64.5625],
        "Col 285 Sector JJ-E b13-4":[-162.96875,40.75,-72.5],
        "Col 285 Sector QJ-P c6-18":[-136.25,78.0625,-90.125],
        "Col 285 Sector KS-T d3-82":[-169.21875,35.3125,-71.84375],
        "HIP 110094":[-188.59375,12.5625,-53.3125],
        "Col 285 Sector KS-T d3-88":[-173.40625,11.78125,-62.15625],
        "Arine":[-143.6875,40.6875,-77.5],
        "Potilo":[-133.09375,57.9375,-98.5625],
        "Lumaragro":[-162.28125,33.0625,-92],
    }

    @classmethod
    def edsmGetSystem(cls,system):
        
        if cls.systemCache.has_key(system):
        
            return cls.systemCache[system]
            
        else:
            url = 'https://www.edsm.net/api-v1/system?systemName='+quote_plus(system)+'&showCoordinates=1'      
            r = requests.get(url)
            s =  r.json()
        
            cls.systemCache[system]=(s["coords"]["x"],s["coords"]["y"],s["coords"]["z"])
            return s["coords"]["x"],s["coords"]["y"],s["coords"]["z"]    
            
    @classmethod      
    def dump(cls):
        for x in cls.systemCache.keys():
            debug('"{}":[{},{},{}],'.format(x, cls.systemCache.get(x)[0],cls.systemCache.get(x)[1],cls.systemCache.get(x)[2]))

def edsmGetSystem(system):
    Systems.edsmGetSystem(system)
    
def dumpSystemCache():
    Systems.dump()