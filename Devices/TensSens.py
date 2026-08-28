
from Util.ArduinoPort import ArduinoPort

class TensSens(ArduinoPort):
    def __init__(self,port:str,baud:int):
        super().__init__(port,baud)
        self.value = 0

    def getValue(self):
        return self.parseArduino()

    def getValueIn(self):
        return self.value

    def parseArduino(self):
        vals = self.responceAll().split("\\r\\n")
        if len(vals)>3:
            vals = vals[1:-1]
        valsP = []
        for i in range(len(vals)):
            preval = vals[i].replace("b","")
            preval = preval.replace("\\n","")
            preval = preval.replace("\\r","")
            preval = preval.replace("'","")
            preval = preval.replace(" ","")   
            #print(preval)         
            try:
                val = int(preval)                    
                valsP.append(val) 
            except BaseException:
                pass

        if len(valsP)>0:
            self.force = valsP[-1]
            self.value = self.force
            return valsP[-1]
        return None