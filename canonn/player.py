import threading
from winsound import *

class Player(threading.Thread):
    def __init__(self, plugin_dir,sounds):
        threading.Thread.__init__(self)
        self.sounds = sounds
        self.plugin_dir = plugin_dir

    def run(self):
        
        try:
            for soundfile in self.sounds:
        
                PlaySound("{}\\{}".format(self.plugin_dir,soundfile),SND_FILENAME)
        except:
            print("Issue playing sound " + str(sys.exc_info()[0]))    