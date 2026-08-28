import socket
from PyQt5 import QtWidgets

class UdpPort(object):
    def __init__(self, udp_ip:str,udp_port:int,udp_port_self:int):
        self.port:socket.socket = self.tryOpen()
        self.buff = ""
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.port.bind(('192.168.10.3', udp_port_self))

    def tryOpen(self):
        try:
            ser = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if ser!=None:
                print("open")
            return ser
        except BaseException:
            print("Cannot open")
            return None

    def sendMes(self, box:QtWidgets.QLineEdit): 
        msg = box.text()       
        self.send(msg)

    def send(self,mes:str):
        if self.port!=None and len(mes)>0:
            #if not self.port.connect(): return
            try:   
                bData = bytes(bytes(mes, encoding='ascii')+bytes('\n\r', encoding='ascii'))
                self.port.sendto(bData,(self.udp_ip,self.udp_port))            
            except BaseException:
                print("self.port!=None and len(mes)>0")
    
    def close(self):
        if self.port!=None:
            self.port.close()

    def responceAll(self):
        #if self.port.is_open:
        resp,addr= self.port.recvfrom(1024)
        self.buff+=resp

    def responce(self):
        allResp = ""
        if self.port!=None:
            resp,addr= self.port.recvfrom(1024)
            if len(resp)>2:                
                return str(resp)
        else:
            pass      
        return allResp

    
