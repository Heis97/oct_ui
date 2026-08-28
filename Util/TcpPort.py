import socket
from PyQt5 import QtWidgets

class TcpPort(object):
    def __init__(self, tcp_ip:str,tcp_port:int,tcp_port_self:int):
        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.port:socket.socket = self.tryOpen()
        self.buff = ""
        
        #self.port.bind(('192.168.10.3', tcp_port_self))

    def tryOpen(self):
        try:
            ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#socket.AF_INET, socket.SOCK_DGRAM
            ser.connect((self.tcp_ip,self.tcp_port))
            if ser!=None:
                
                print("open")
            return ser
        except BaseException:
            print("Cannot open",self.tcp_ip,self.tcp_port)
            return None

    def sendMes(self, box:QtWidgets.QLineEdit): 
        msg = box.text()       
        self.send(msg)

    def send(self,mes:str):
        if self.port!=None and len(mes)>0:
            #if not self.port.connect(): return
            #try:   
            bData = bytes(mes+'\n\r', encoding='ascii')
            self.port.send(bData)            
            #except BaseException:
                #print("self.port.sendto")
    
    def close(self):
        if self.port!=None:
            self.port.close()

    def responceAll(self):
        #if self.port.is_open:
        resp =self.port.recv(1024)
        self.buff+=resp

    def responce(self):
        try:
            allResp = ""
            if self.port!=None:
                resp= self.port.recv(1024)
                if len(resp)>2:                
                    return str(resp)
            else:
                pass      
            return allResp
        except BaseException:
            pass
            #print("responce")

    
