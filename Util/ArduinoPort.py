import serial
from PyQt5 import QtWidgets

class ArduinoPort(object):
    def __init__(self, port:str,baud:int):
        self.port:serial.Serial = self.tryOpen(port,baud)
        self.buff = ""

    def tryOpen(self,port,baud):
        try:
            ser = serial.Serial(port,baud, timeout=0)
            if ser!=None:
                print("open "+str(port)+" "+str(baud))
            return ser
        except BaseException:
            print("Cannot open "+str(port)+" "+str(baud))
            return None

    def sendMes(self, box:QtWidgets.QLineEdit): 
        msg = box.text()       
        self.send(msg)

    def send(self,mes:str):
        if self.port!=None and len(mes)>0:
            if not self.port.is_open: return
            try:   
                bData = bytes(bytes(mes, encoding='ascii')+bytes('\n\r', encoding='ascii'))
                self.port.write(bData)            
            except BaseException:
                print("self.port!=None and len(mes)>0")
    
    def close(self):
        if self.port!=None:
            self.port.close()

    def responceAll(self):
        if self.port.is_open:
            self.buff+=self.port.read_all()

    def responce(self):
        allResp = ""
        if self.port!=None and self.port.is_open:
            resp:bytes = self.port.readline() 
            if len(resp)>2:                
                return str(resp)
        else:
            pass      
        return allResp

    
