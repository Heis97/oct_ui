from Util.ArduinoPort import ArduinoPort,serial
from Util.Gcomand import gcodeCom
import time


class StringState(object):

    
    temp_val_int1:float = 0
    temp_val_int2:float= 0
    temp_val_ext:float= 0
    reley_1:int= 0
    reley_2:int= 0
    reley_HV:int= 0
    reley_press:int= 0
    string_lenght:int= 0
    pressure:int= 0
    HV:int= 0
    turbo:int= 0
    moves_planned:int= 0
    time_measure:int= 0
    duty_1:int = 0
    duty_2:int = 0
    force_string1:int = 0
    len_string1:int = 0
    force_string2:int = 0
    len_string2:int = 0
    force_string3:int = 0
    len_string3:int = 0

    parsed:bool = False
    

    def __init__(self, data:str):    
        if "string" not in data: return
        data = data.replace("'b'",'')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        #print(data)
        values = data.split(" ")
        #print(len(values))
        if len(values) > 15:            
            try:
                values = values[1:]
                self.temp_val_int1 = round( float(values[0]))
                self.temp_val_int2 = round( float(values[1]))
                self.temp_val_ext = round( float(values[2]))
                self.reley_1 = int(values[3])
                self.reley_2 = int(values[4])
                self.reley_HV = int(values[5])
                self.reley_press = int(values[6])
                self.string_lenght = int(values[7])
                self.pressure = float(values[8])
                if self.pressure > 60000: self.pressure = 0.0
                self.pressure = round( (self.pressure-237)/10)
                if self.pressure < 0: self.pressure = 0.0
                self.HV= float(values[9])
                self.HV = round( 40 *( self.HV/1610))
                self.turbo= int(values[10])
                self.moves_planned = int(values[11])
                self.time_measure = int(values[12])
                self.duty_1 = float(values[13])
                self.duty_2 = float(values[14])

                self.force_string1 = int(values[15])
                self.len_string1 = int(values[16])

                self.force_string2 = int(values[17])
                self.len_string2 = int(values[18])

                self.force_string3 = int(values[19])
                self.len_string3 = int(values[20])
                self.parsed = True
            except :
                pass
                #print("parse_exc")
        else:
            print(len(values))
        #print(self)

    def __str__(self):
        return "\nT1:"+str(self.temp_val_int1) +"\nT2: "+str(self.temp_val_int2)+"\nT_e: "+str(self.temp_val_ext)+"\n "+str(self.reley_1)+"\n "+str(self.reley_2)+"\n "+str(self.reley_HV)+"\n "+str(self.reley_press)+"\n L:"+str(round(self.string_lenght*0.00651922607,1))+"\n P:"+str(self.pressure)+"\n HV:"+str(self.HV)+"\n "+str(self.turbo)+"\n "+str(self.moves_planned)+"\n "+str(self.time_measure)+"\n "+str(self.duty_1)+"\n "+str(self.duty_2)+"\n F1:"+str(self.force_string1)+"\n L1:"+str(self.len_string1)+"\n F1:"+str(self.force_string2)+"\n L1:"+str(self.len_string2)+"\n F1:"+str(self.force_string3)+"\n L1:"+str(self.len_string3)+" "



class StringMash(ArduinoPort):
    string_vel_force = 5
    def __init__(self, port:str,baud:int):        
        super().__init__(port,baud)
        self.string_vel = 0
        self.curCom = 0
        self.all_data:list[StringState] = []
        self.err = 0
        self.gateway_move = 0
        self.recuperator_move = 0
        self.string_move = 0
        self.karet_move_up = 0
        self.karet_move_down = 0
        self.feed_pound_move = 0
        self.recuperation = 0

        self.gateway_vel = 0.0
        self.recuperator_vel = 0.0
        self.string_vel = 0.0


        self.working = True
        
        self.koef_c = 1
        self.ind_err = 0

    def close(self):
        return super().close()


    def sendGcom(self, command:str):
        if self.port is None: return
        if not self.port.is_open: return
        print(command)
        """self.curCom+=1
        com = gcodeCom(self.curCom,command)
        self.send(com)

        if self.check_err_line(): 
            self.sendGcom(command)"""

        self.send(command)

            
            

    
    def parse_resp(self):
        #try:
        if self.port is None: return
        if not self.port.is_open: return
        try:
            data = self.port.read_all()
        except serial.SerialException:
            print("ser ex")
            return
        if data is None: return
        new_data = str(data)
        #print(new_data)
        self.buff += new_data
        vals = self.buff.split("\\n")
        added = False
        for val in vals:
            #print(val)
            if "string" in val:
                #print("string")
                state = StringState(val.strip())
                if state.parsed:
                    self.all_data.append(state)
            #self.check_err_line()
        #except BaseException:
            #pass


    def gen_move_mash(self):
        if not self.working: return
        dist = 0.8
        if self.gateway_move + self.recuperator_move + self.string_move+ self.karet_move_down+ self.karet_move_up+self.feed_pound_move > 0:
            com_text = "G"+str(dist)+" "
            if self.gateway_move > 0:
                com_text+="Z"+str(dist)+" "
            if self.recuperator_move > 0:
                com_text+="X-"+str(dist)+" "
            if self.karet_move_down > 0:
                com_text+="Y"+str(dist)+" "
            if self.karet_move_up > 0:
                com_text+="Y-"+str(dist)+" "
            if self.string_move > 0:
                com_text+="E-"+str(dist)+" "

            if self.feed_pound_move>0:
                com_text+="A"+str(dist)+" "

            com_text += "F600"
            #print("send_gcom")
            self.sendGcom(com_text)


    def comp_lin_speed(self)->float:
        v = 0.0
        if len(self.all_data)>100:
            x1 = float(self.all_data[-1].string_lenght)
            t1 = float(self.all_data[-1].time_measure)
            x2 = float(self.all_data[-99].string_lenght)
            t2 = float(self.all_data[-99].time_measure)
            if t1-t2>0.1:
                v = (x1-x2)/(t1-t2)#imp/ms
                v*=6.51922607
        self.string_vel-=0.01*(self.string_vel-v)
        return self.string_vel
    


    #rev/min to steps
    def convert_gateway()->float:
        rev = 1600

    def set_working(self,state:bool):
        self.working = state
        if self.working: self.sendGcom("G91")

    def setup_gcode(self):
        #self.string_mash.sendGcom("M576 I")
        self.sendGcom("G91")
        self.sendGcom("M92 X550 Y200 Z50 E6 A50 B800 C6")
        self.sendGcom("M579 K0.2 P0.2")

    def check_err_line(self)->bool:
        if "Error" in self.buff:
            print("error")
            lines = self.buff.split('\\n')
            for line in lines:
                if "Resend" in line:
                    num = int(line.split(":")[1])
            
                    #print(self.buff)
                    self.curCom = num-1
                    self.buff = ""
                    return True
        if len(self.buff)>1000: self.buff = ""
        return False
    
        
        



    
            



