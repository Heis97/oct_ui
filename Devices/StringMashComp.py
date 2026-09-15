#from Util.ArduinoPort import ArduinoPort,serial
from Util.TcpPort import *
from Util.UdpPort import *
from Util.Gcomand import gcodeCom
import time


from Devices.StringMashPrimary import *

        

#class StringMashSecondary(UdpPort):
class StringMashComp(TcpPort):
    string_vel_force = 5
    def __init__(self, tcp_ip:str,tcp_port:int,tcp_port_self:int):        
        super().__init__(tcp_ip,tcp_port,tcp_port_self)
        self.string_vel = 0
        self.curCom = 0
        self.err = 0
        self.gateway_move = 0
        self.recuperator_move = 0
        self.string_move = 0

        self.all_data:list[StringStatePrimary] = [StringStatePrimary("")]
        self.all_data_sec:list[StringStatePrimary] = [StringStatePrimary("")]

        self.gateway_vel = 0.0
        self.recuperator_vel = 0.0
        self.string_vel = 0.0


        self.working = True
        self.ind_err = 0

    def close(self):
        return super().close()


    def sendGcom(self, command:str):
        if self.port is None: return
        #print("sec")
        self.curCom+=1
        #com = gcodeCom(self.curCom,command)
        com = command
        print(self.curCom," str",com)
        self.send(com)

        #if self.check_err_line(): 
        #self.sendGcom(command)

            
            

    
    def parse_resp(self)->int:
        #try:
        if self.port is None: return -1
        #try:
        data = self.responce()
        #except BaseException:
            #print("tcp ex")
            #return
        if data is None: return -1
        new_data = str(data)
        #print(new_data)
        self.buff += new_data
        vals = self.buff.split("\\n")
        added = False
        for val in vals:
            #print(val)
            if "st1" in val:
                #print("string1")
                state = StringStatePrimary(val.strip(),self.all_data[-1])
                if state.parsed:
                    self.all_data.append(state)
                    #print(str(state))
                    if len(self.all_data)>1000:
                        self.all_data = [self.all_data[-1]]


            if "st2" in val:
                #print("string2")
                state = StringStatePrimary(val.strip(),self.all_data_sec[-1])
                if state.parsed:
                    self.all_data_sec.append(state)
                    #print(str(state))
                    if len(self.all_data_sec)>1000:
                        self.all_data_sec = [self.all_data_sec[-1]]

                #if len(self.buff)>2500:
        self.buff = ""

        return 1
            #self.check_err_line()
        #except BaseException:
            #pass

    def comp_lin_speed(self)->float:
        if len(self.all_data)>100:
            self.all_data = self.all_data[-99:-1]
        return 0.0


    def set_working(self,state:bool):
        self.working = state
        #if self.working: self.sendGcom("G91")

    def setup_gcode(self):
        pass

    def check_err_line(self)->bool:
        have_ok = False
        #time.sleep(0.01)
        if "Error" in self.buff:
            #print("error")
            lines = self.buff.split('\\n')
            for line in lines:
                if "Resend" in line:
                    num = int(line.split(":")[1])
            
                    #print(self.buff)
                    self.curCom = num-1
                    self.buff = ""
                    return True
        """if not "ok" in self.buff:
            print("not ok")
            return True"""
        
        self.buff = ""
        return False
    
        
        



    
            



