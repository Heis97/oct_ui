#from Util.ArduinoPort import ArduinoPort,serial
from Util.TcpPort import *
from Util.UdpPort import *
from Util.Gcomand import gcodeCom
import time


class StringStateSecondary(object):

    
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
    force_string1:list = [0.0,0.0,0.0,0.0,0.0]
    len_string1:list = [0,0,0,0,0]
    step_s:list = [0.0,0.0,0.0,0.0,0.0]
    f_dest_s:list = [0.0,0.0,0.0,0.0,0.0]
    tens_num = 3

    parsed:bool = False


    turbo_val = 0
    motor1 = 0
    motor2 = 0

    mir_pos_e = 0
    cam_pos_e = 0

    mir_pos_d = 0
    cam_pos_d = 0

    gateway_move = 0
    feed_pound_move = 0
    recuperator_move= 0

    vibro_main = 0
    vibro_loop_high = 0
    vibro_loop_ampl = 0

    homed_e = 0
    homed_d = 0

    led_micro_d = 0
    led_micro_e = 0

    def __init__(self, data:str,state:"StringStateSecondary"=None):  
        self.parsed = False  
        if "st2" not in data: return

        #print(data)
        data = data.replace("'",'')
        data = data.replace("b",'')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.split("s")[1]

        data = data.replace('t2','')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.strip()
        
        values = data.split(" ")

        if state is not None:
            self.clone(state)
        #print(len(values))
        if len(values) > 6:   
                cur_send = int(values[1])   
            #try:
                if cur_send == 0:
                    self.turbo_val = int(values[2])
                    self.time_measure = int(values[3])
                    self.gateway_move = int(values[4])
                    self.feed_pound_move =int(values[5])
                    self.recuperator_move= int(values[6])

                elif cur_send == 1:
                    self.vibro_main = int(values[2])
                    self.vibro_loop_high = int(values[3])
                    self.vibro_loop_ampl = int(values[4])
                    self.homed_d = int(values[5])
                    self.homed_e = int(values[6])

                elif cur_send == 2:
                    self.mir_pos_d = round(float(values[2]),2)
                    self.cam_pos_d = round(float(values[3]),2)
                    self.mir_pos_e = round(float(values[4]),2)
                    self.cam_pos_e = round(float(values[5]),2)
                    self.led_micro_d = int(values[6])

                elif cur_send == 3:
                    self.led_micro_e = int(values[2])

                self.parsed = True
            #except :
                #pass
                #print("parse_exc")
        else:
            pass
            #print(len(values))
        #print(self)

    def clone(self,state:"StringStateSecondary"):
        self.turbo_val = state.turbo_val 
        self.time_measure = state.time_measure

        self.gateway_move = state.gateway_move
        self.feed_pound_move =state.feed_pound_move
        self.recuperator_move= state.recuperator_move

        self.vibro_main = state.vibro_main
        self.vibro_loop_high = state.vibro_loop_high
        self.vibro_loop_ampl = state.vibro_loop_ampl

        self.homed_d = state.homed_d
        self.homed_e = state.homed_e

        self.mir_pos_d = state.mir_pos_d
        self.cam_pos_d = state.cam_pos_d
        self.mir_pos_e = state.mir_pos_e 
        self.cam_pos_e = state.cam_pos_e

        self.led_micro_d = state.led_micro_d
        self.led_micro_e = state.led_micro_e

    def __str__(self):
        outp = "\nturb:"+str(self.turbo_val) +"\ntime: "+str(self.time_measure)+\
            "\nm1: "+str(self.motor1)+"\nm2: "+str(self.motor2)+\
            "\nhm1: "+str(self.homed_d)+"\nhm2: "+str(self.homed_e)+\
            "\nmir_pos_e: "+str(self.mir_pos_e)+"\ncam_pos_e: "+str(self.cam_pos_e)+\
            "\nmir_pos_d: "+str(self.mir_pos_d)+"\ncam_pos_d: "+str(self.cam_pos_d)+\
                "\n "

        return outp
                        

#class StringMashSecondary(UdpPort):
class StringMashSecondary(TcpPort):
    string_vel_force = 5
    def __init__(self, tcp_ip:str,tcp_port:int,tcp_port_self:int):        
        super().__init__(tcp_ip,tcp_port,tcp_port_self)
        self.string_vel = 0
        self.curCom = 0
        self.err = 0
        self.gateway_move = 0
        self.recuperator_move = 0
        self.string_move = 0

        self.all_data:list[StringStateSecondary] = []

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
        #print(new_data)
        self.buff += new_data
        vals = self.buff.split("\\n")
        added = False
        for val in vals:
            #print(val)
            if "str2ing" in val:
                #print("string")
                state = StringStateSecondary(val.strip())
                if state.parsed:
                    self.all_data.append(state)

                #if len(self.buff)>2500:
                self.buff = ""
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
    
        
        



    
            



