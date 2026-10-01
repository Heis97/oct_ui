#from Util.ArduinoPort import ArduinoPort,serial
from Util.TcpPort import *
from Util.UdpPort import *
from Util.Gcomand import gcodeCom
import time
import copy

TEST_PROG = True
MAKET = True
TENS_NUM = 5

if MAKET:
    TENS_NUM = 5

class StringStatePrimary(object):
    axis_names = ["X","Y","Z","I","J","K","U","E"]
    cur_pos: "list[int]" = 8*[0]
    cur_end: "list[int]" = 8*[0]
    steps: "list[int]" = 8*[0]
    debug: "list[int]" = 8*[0]

    cur_counter:int = 0
    cur_buf:int = 0
    delta_calib:int = 0
    ring_buf_go:int = 0
    homing_done:int = 0
    temp_cur:int = 0
    prog_done:int = 0

    tool_recogn:int = 0
    

    x:float = 0.0
    y:float = 0.0
    z:float = 0.0

    board_num:int = 0

    

    def __init__(self, data:str,state:"StringStatePrimary"=None):    
        self.parsed = False
        if "st" not in data: return

        #print(data)
        data = data.replace("'",'')
        data = data.replace("b",'')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.split("s")[1]


        self.board_num:int = int(data[1])
        #print(self.board_num)

        data = data.replace('t'+str(self.board_num),'')
        data = data.replace('  ',' ')
        data = data.replace('  ',' ')
        data = data.strip()
        
        values = data.split(" ")
        if state is not None:
            self.clone(state)
        #print(values)
        if len(values) > 13: 

            try:
                self.cur_buf:int = int(values[1])
                cur_send = int(values[2])
                if cur_send == 0:
                   
                    self.cur_counter:int = int(values[3])                   
                    self.delta_calib:int = int(values[4])
                    self.ring_buf_go:int = int(values[5])
                    self.homing_done:int = int(values[6])
                    self.temp_cur:int = int(values[7])
                    self.prog_done:int = int(values[8])
                    self.tool_recogn:int = int(values[10])

                elif cur_send == 1:
                    for i in range(8):
                        self.cur_pos[i] = int(values[3+i]) 

                    self.x = float(values[11])
                    self.y = float(values[12])
                    self.z = float(values[13])

                elif cur_send == 2:
                    for i in range(8):
                        self.cur_end[i] = int(values[3+i]) 

                elif cur_send == 3:
                    for i in range(8):
                        self.steps[i] = int(values[3+i]) 

                elif cur_send == 4:
                    for i in range(8):
                        self.debug[i] = int(values[3+i]) 

                    


                self.parsed = True
            except :
                pass
                #print("parse_exc")
        else:
            pass
            #print(len(values))
        #print(self)

    def clone(self,state:"StringStatePrimary"):
        self.cur_pos = copy.deepcopy(state.cur_pos)
        self.cur_end = copy.deepcopy(state.cur_end)
        self.steps = copy.deepcopy(state.steps)
        self.debug = copy.deepcopy(state.debug)

    
        self.cur_counter:int = state.cur_counter
        self.cur_buf:int = state.cur_buf
        self.delta_calib:int = state.delta_calib
        self.ring_buf_go:int = state.ring_buf_go
        self.homing_done:int = state.homing_done
        self.temp_cur:int = state.temp_cur
        self.prog_done:int = state.prog_done
        self.tool_recogn:int = state.tool_recogn
        
        
        self.x:float = state.x
        self.y:float = state.y
        self.z:float = state.z

        self.board_num:float = state.board_num

        pass

    def __str__(self):
        #print("out ",self.temp_val_ext)
        outp = ""+str(self.cur_counter)+\
                "\ndelta_calib: "+str(self.delta_calib)+"\nring_buf_go: "+str(self.ring_buf_go)+"\nhoming_done: "+str(self.homing_done)+"\ntemp: "+str(self.temp_cur)+"\n "+"\nprog_done: "+str(self.prog_done)+"\n "+\
                "\ntools: "+str(self.tool_recogn)+"\nx: "+str(round( self.x,2))+"\ny: "+str(round( self.y,2))+"\nz: "+str(round( self.z,2))
        
        outp += "\n"
        for i in range(8):
            outp += "\n"+self.axis_names[i]+"pos: "+str(self.cur_pos[i])
        outp += "\n"
        for i in range(8):
            outp += "\n"+self.axis_names[i]+"end: "+str(self.cur_end[i])
        outp += "\n"
        for i in range(8):
            outp += "\ndeb: "+str(self.debug[i])
        outp += "\n"
        for i in range(8):
            outp += "\n"+self.axis_names[i]+"steps: "+str(self.steps[i])

        

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
    
        
        



    
            



