import time
class ProgTime(object):
    def __init__(self):

        self.progStart = self.startNew()   
        
    def getCurrentTime(self):
        cur_time:float = time.time_ns()*0.000001 - self.progStart  #ms
        return cur_time

    def getAbsTime(self):
        return time.time_ns()*0.000001
    def startNew(self):
        self.progStart = time.time_ns()*0.000001
    