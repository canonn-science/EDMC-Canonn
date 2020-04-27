import threading
from .playsound import playsound
import os, sys

class Player(threading.Thread):
    def __init__(self, plugin_dir,sounds):
        threading.Thread.__init__(self)
        self.sounds = sounds
        self.plugin_dir = plugin_dir

    def run(self):
        
        try:
            for soundfile in self.sounds:
        
                playsound(os.path.join(self.plugin_dir,soundfile))
        except:
            print("Issue playing sound " + str(sys.exc_info()[0]))    