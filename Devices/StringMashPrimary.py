#from Util.ArduinoPort import ArduinoPort,serial
from Util.TcpPort import *
from Util.UdpPort import *
from Util.Gcomand import gcodeCom
import time

TEST_PROG = True
MAKET = True
TENS_NUM = 5

if MAKET:
    TENS_NUM = 5

class StringStatePrimary(object):

    
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
    string_move_second:list = [0.0,0.0,0.0,0.0,0.0]
    force_string1:list = [0.0,0.0,0.0,0.0,0.0]
    len_string1:list = [0,0,0,0,0]
    step_s:list = [0.0,0.0,0.0,0.0,0.0]
    f_dest_s:list = [0.0,0.0,0.0,0.0,0.0]
    tens_num = TENS_NUM
    cur_speed_tens_com = 0
    parsed:bool = False

    motors_free_state = 0
    homing_karet = 0 
    karet_in_work_pos = 0
    reley_24_out = 0
    tare_tens = 0

    ind_sensor = 0
    temp_dest = 0
    pressure_dest = 0

    heater_en = 0

    string_ended = 0

    def __init__(self, data:str,state:"StringStatePrimary"=None):    
        self.parsed = False
        if "st1" not in data: return

        
        data = data.replace("'",'')
        data = data.replace("b",'')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.split("s")[1]

        data = data.replace('t1','')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.strip()
        #print(data)
        values = data.split(" ")
        if state is not None:
            self.clone(state)
        #print(len(values))
        if len(values) > 6: 
            cur_send = int(values[1])     

            #print(self.tens_num,cur_send,cur_send == self.tens_num)
            try:
                if cur_send<self.tens_num:
                    i = cur_send
                    self.string_move_second[i] = round(  float(values[2]),1)
                    self.force_string1[i] = round(  float(values[3]),1)
                    self.len_string1[i] = int(values[4])
                    self.step_s[i] = round(float(values[5]),4)
                    self.f_dest_s[i] = round(float(values[6]),2)

                elif cur_send == self.tens_num:
                    self.temp_val_ext = round( float(values[2]),2) 
                    self.temp_val_int2 = round( float(values[3]))
                    self.temp_val_int1 = round( float(values[4]))
                    self.reley_24_out = int(values[5])#reley_24_out                
                    self.reley_HV = int(values[6])
                    #print("parse",self.temp_val_ext)

                elif cur_send == self.tens_num+1:
                    self.reley_press = int(values[2])
                    self.pressure = float(values[3])
                    if self.pressure > 60000: self.pressure = 0.0
                    self.pressure = round( (self.pressure-237)/10)
                    if self.pressure < 0: self.pressure = 0.0
                    self.HV= float(values[4])
                    #self.HV = round( 40 *( self.HV/1610))
                    self.motors_free_state= int(values[5])
                    self.time_measure = int(values[6])

                elif cur_send == self.tens_num+2:
                    self.homing_karet = int(values[2]) #homing karet
                    self.ind_sensor = int(values[3]) 
                    self.tare_tens = int(values[4]) #karet in work pos
                    self.pressure_dest = int(values[5]) #karet in work pos
                    self.temp_dest = float(values[6]) #karet in work pos      
                         
                elif cur_send == self.tens_num+3:
                    self.heater_en = int(values[2]) #
                    self.duty_1 = int(values[3]) #
                    self.duty_2 = int(values[4]) #
                    self.string_ended = int(values[5]) #

                if TEST_PROG:
                    self.time_measure = int(values[1])
                    self.temp_val_ext = int(values[2])
                    self.temp_val_int2 =int(values[3])
                    self.temp_val_int1 = int(values[4])
                    self.cur_speed_tens_com = int(values[5])#reley_24_out                
                    self.reley_24_out= int(values[6])
                    self.duty_1= int(values[7])

                self.parsed = True
            except :
                pass
                #print("parse_exc")
        else:
            pass
            #print(len(values))
        #print(self)

    def clone(self,state:"StringStatePrimary"):
        self.temp_val_int1:float = state.temp_val_int1
        self.temp_val_int2:float= state.temp_val_int2
        self.temp_val_ext:float= state.temp_val_ext
        self.reley_1:int= state.reley_1
        self.reley_2:int= state.reley_2
        self.reley_HV:int= state.reley_HV
        self.reley_press:int= state.reley_press
        self.string_lenght:int= state.string_lenght
        self.pressure:int= state.pressure
        self.HV:int= state.HV
        self.turbo:int= state.turbo
        self.moves_planned:int= state.moves_planned
        self.time_measure:int= state.time_measure
        self.duty_1:int = state.duty_1
        self.duty_2:int = state.duty_2
        self.string_move_second:list = state.string_move_second
        self.force_string1:list = state.force_string1
        self.len_string1:list = state.len_string1
        self.step_s:list = state.step_s
        self.f_dest_s:list = state.f_dest_s
        self.cur_speed_tens_com = state.cur_speed_tens_com

        self.motors_free_state = state.motors_free_state
        self.homing_karet = state.homing_karet
        self.karet_in_work_pos = state.karet_in_work_pos
        self.reley_24_out = state.reley_24_out
        self.tare_tens = state.tare_tens

        self.ind_sensor = state.ind_sensor
        self.temp_dest = state.temp_dest
        self.pressure_dest = state.pressure_dest

        self.heater_en = state.heater_en

        pass

    def __str__(self):
        #print("out ",self.temp_val_ext)
        outp = "\nT_e: "+\
            str(self.temp_val_ext)+"\n "+str(self.temp_val_int2)+"\n"+str(self.temp_val_int1)+"\n "+str(self.cur_speed_tens_com)+"\n"+str(self.reley_24_out)+"\n"+str(self.time_measure)+"\n "+str(self.duty_1)+"\n "+str(self.duty_2)+"\n "
        """outp = "\nT1:"+str(self.temp_val_int1) +"\nT2: "+str(self.temp_val_int2)+"\nT_e: "+\
            str(self.temp_val_ext)+"\n "+str(self.reley_1)+"\n "+str(self.reley_2)+\
                "\n "+str(self.reley_HV)+"\n "+str(self.reley_press)+"\n L:"+str(round(self.string_lenght*0.00651922607,1))+"\n P:"+str(self.pressure)+\
                    "\n HV:"+str(self.HV)+"\n "+str(self.turbo)+"\n "+str(self.moves_planned)+"\n "+str(self.time_measure)+"\n "+str(self.duty_1)+"\n "+str(self.duty_2)+"\n"""
        len = self.tens_num
        if MAKET: len =3
        for i in range(len):
            outp +="F"+str(i+1)+":"+str(self.force_string1[i])+"\n Len"+str(i+1)+":"+str(self.len_string1[i])+"\n v"+str(i+1)+":"+str(self.step_s[i])+"\n f_dest"+str(i+1)+":"+str(self.f_dest_s[i])+"\n"
        return outp
                        

#class StringMashPrimary(UdpPort):
class StringMashPrimary(TcpPort):
    string_vel_force = 5
    def __init__(self, tcp_ip:str,tcp_port:int,tcp_port_self:int):        
        super().__init__(tcp_ip, tcp_port,tcp_port_self)
        self.string_vel = 0
        self.curCom = 0
        self.all_data:list[StringStatePrimary] = []
        self.err = 0
        self.gateway_move = 0
        self.recuperator_move = 0
        self.string_move = 0

        self.second_string_0 = 0
        self.second_string_1 = 0
        self.second_string_2 = 0

        self.karet_move_up = 0
        self.karet_move_down = 0
        self.feed_pound_move = 0

        self.gateway_vel = 0.0
        self.recuperator_vel = 0.0
        self.string_vel = 0.0


        self.working = True
        self.ind_err = 0

    def close(self):
        return super().close()


    """def sendGcom(self, command:str):
        if self.port is None: return
        #print(command)
        if len(command)<2: return
        self.curCom+=1
        com = gcodeCom(self.curCom,command)
        #print("str",com)
        self.send(com)

        if self.check_err_line(): 
            self.sendGcom(command)"""

    def sendGcom(self, command:str):
        if self.port is None: return
        #print("sec")
        self.curCom+=1
        com = gcodeCom(self.curCom,command)
        #print("str",com)
        self.send(com)

        if self.check_err_line(): 
            self.sendGcom(command)
            
            

    
    def parse_resp(self):
        #try:
        if self.port is None: return
        #try:
        data = self.responce()
        #except BaseException:
            #print("tcp ex")
            #return
        if data is None: return
        new_data = str(data)
        print(new_data)
        self.buff += new_data
        vals = self.buff.split("\\n")
        added = False
        for val in vals:
            #print(val)
            if "string" in val:
                #print("string")
                state = StringStatePrimary(val.strip())
                if state.parsed:
                    self.all_data.append(state)

                #if len(self.buff)>2500:
                self.buff = ""
            #self.check_err_line()
        #except BaseException:
            #pass



    def comp_lin_speed(self)->float:
        v = 0.0
        if len(self.all_data)>100:
            x1 = float(self.all_data[-1].len_string1[0])
            t1 = float(self.all_data[-1].time_measure)
            x2 = float(self.all_data[-99].len_string1[0])
            t2 = float(self.all_data[-99].time_measure)
            if t1-t2>0.1:
                v = (x1-x2)/(t1-t2)#imp/ms
                v*=6.51922607
            self.all_data = self.all_data[-99:-1]
        self.string_vel-=0.01*(self.string_vel-v)
        return self.string_vel
    


    #rev/min to steps
    def convert_gateway()->float:
        rev = 1600

    def set_working(self,state:bool):
        self.working = state
        if self.working: self.sendGcom("G91")

    def setup_gcode(self):
        return
        f_off_0 = -201.5
        f_off_1 = 6.1
        f_off_2 = -140#120

        f_dest_0 = -50
        f_dest_1 = -50
        f_dest_2 = -50


        k_decr = 0.00001

        self.sendGcom(f"M584 A O{f_off_0} J{f_dest_0} K{k_decr:.6f}")

        self.sendGcom(f"M584 B O{f_off_1} J{f_dest_1} K{k_decr:.6f}")

        self.sendGcom(f"M584 C O{f_off_2} J{f_dest_2} K{k_decr:.6f}")


        pass
        #self.string_mash.sendGcom("M576 I")
        #self.sendGcom("G91")
        #self.sendGcom("M92 X550 Y200 Z50 E6 A50 B800 C6")
        #self.sendGcom("M579 K0.2 P0.2")

    def clear_tens_settings(self):
        return
        f_off_0 = 0
        f_off_1 = 0
        f_off_2 = 0#120

        f_dest_0 = -50
        f_dest_1 = -50
        f_dest_2 = -50


        k_decr = 0.00001


        #time.sleep(2)
        #time.sleep(0.01)
        self.sendGcom(f"M584 I0 O{f_off_0} F{f_dest_0} K{k_decr:.6f} ")
        #time.sleep(0.01)
        self.sendGcom(f"M584 I1 O{f_off_1} F{f_dest_1} K{k_decr:.6f}")
        #time.sleep(0.01)
        self.sendGcom(f"M584 I2 O{f_off_2} F{f_dest_2} K{k_decr:.6f}")
        #time.sleep(0.01)
        self.sendGcom(f"M584 O{f_off_0} F{f_dest_0} K{k_decr:.6f}")
        #time.sleep(0.01)
        #self.sendGcom(f"M119")
        pass
        #self.string_mash.sendGcom("M576 I")
        #self.sendGcom("G91")
        #self.sendGcom("M92 X550 Y200 Z50 E6 A50 B800 C6")
        #self.sendGcom("M579 K0.2 P0.2")

    def check_err_line(self)->bool:
        have_ok = False
        #time.sleep(0.01)
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
        """if not "ok" in self.buff:
            print("not ok")
            return True"""
        
        self.buff = ""
        return False
    

"""    def check_err_line(self)->bool:
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
        #print(self.buff)
        if len(self.buff)>1000: self.buff = ""
        return False"""
    
        
        



    
            



