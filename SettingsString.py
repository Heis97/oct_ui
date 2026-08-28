import json

FILE_NAME = "settings_string.json"

class SettingsString:
    #common settings
    com_primary = "COM4"
    com_secondary = "COM8"

    #string settings

    string_vel = 4.0
    string_koef = 100.0

    #----------A------------
    f_dest_a = 10.0
    f_off_a = 255000.0
    f_sign_a = 1
    k_v_tens_a = 0.0001
    def_steps_a = 120.0
    dir_a = 1

    en_a = 0


    #----------B------------
    f_dest_b = 10.0
    f_off_b = 255000.0
    f_sign_b = 1
    k_v_tens_b = 0.0001
    def_steps_b = 120.0
    dir_b = 1

    en_b = 0

    #----------C------------

    f_dest_c = 10.0
    f_off_c = 255000.0
    f_sign_c = 1
    k_v_tens_c = 0.0001
    def_steps_c = 120.0
    dir_c = 1

    en_c = 0

    #microscope settings

    #----------E------------
    pos_mirror_e = [8.1,   12.3,  15.8]#e
    pos_camera_e = [10.3,   14.5,  18]#e
    expos_e = -7


    #----------D------------
    pos_mirror_d = [14.1,  12.3,  15.8]#d
    pos_camera_d = [14.3,  14.5  ,18]#d
    expos_d = -7


    #--------pound cam-----------

    level = 100
    #perepheri settings

    hv = 0.0
    pressure = 0.0
    turbo = 0.0


    #--------thermal---------
    sensor_type = 1

    k_th1 = 0.1
    k_th2 = 0.1
    time_cycle_th = 10.0

    #bunker settings
    recup_vel = 1.0
    gateway_vel = 1.0
    pound_vel = 1.0

    vibro_freq = 1.0

    #-------------------------

    cam_num_e = 0,
    cam_num_d = 1,
    cam_num_pound = 2

    string_move_a = 0
    string_move_b = 0
    string_move_c = 0
    string_move_d = 0
    string_move_e = 0



    def __init__(self,
            _com_primary = "COM4",
            _com_secondary = "COM8",
            _string_vel = 4.0,
            _string_koef = 100,
            _f_dest_a = 10,
            _f_off_a = 255000,
            _f_sign_a = 1,
            _k_v_tens_a = 0.0001,
            _def_steps_a = 120,
            _dir_a = 1,
            _en_a = 0,
            _f_dest_b = 10,
            _f_off_b = 255000,
            _f_sign_b = 1,
            _k_v_tens_b = 0.0001,
            _def_steps_b = 120,
            _dir_b = 1,
            _n_b = 0,
            _f_dest_c = 10,
            _f_off_c = 255000,
            _f_sign_c = 1,
            _k_v_tens_c = 0.0001,
            _def_steps_c = 120,
            _dir_c = 1,
            _en_c = 0,
            _pos_mirror_e = [8.1,   12.3,  15.8],
            _pos_camera_e = [10.3,   14.5,  18],
            _expos_e = -7,
            _pos_mirror_d = [14.1,  12.3,  15.8],
            _pos_camera_d = [14.3,  14.5  ,18],
            _expos_d = -7,
            _level = 100,
            _hv = 0,
            _pressure = 0,
            _turbo = 0,
            _sensor_type = 1,
            _k_th1 = 0.1,
            _k_th2 = 0.1,
            _time_cycle_th = 10,
            _recup_vel = 1,
            _gateway_vel = 1,
            _pound_vel = 1,
            _vibro_freq = 1,
            
            _cam_num_e = 0,
            _cam_num_d = 1,
            _cam_num_pound = 2,
            _string_move_a = 1,
            _string_move_b = 0,
            _string_move_c = 0,
            _string_move_d = 0,
            _string_move_e = 0):
        #common settings
        self.com_primary = _com_primary
        self.com_secondary = _com_secondary

        #string settings

        self.string_vel = _string_vel
        self.string_koef = _string_koef

        #----------A------------
        self.f_dest_a = _f_dest_a
        self.f_off_a =_f_off_a
        self.f_sign_a = _f_sign_a
        self.k_v_tens_a = _k_v_tens_a
        self.def_steps_a = _def_steps_a
        self.dir_a = _dir_a

        self.en_a = _en_a


        #----------B------------
        self.f_dest_b = _f_dest_b
        self.f_off_b = _f_off_b
        self.f_sign_b = _f_sign_b
        self.k_v_tens_b = _k_v_tens_b
        self.def_steps_b = _def_steps_b
        self.dir_b = _dir_b 

        self.n_b = _n_b

        #----------C------------

        self.f_dest_c = _f_dest_c
        self.f_off_c = _f_off_c
        self.f_sign_c = _f_sign_c 
        self.k_v_tens_c = _k_v_tens_c
        self.def_steps_c = _def_steps_c
        self.dir_c =_dir_c 

        self.en_c = _en_c

        #microscope settings

        #----------E------------
        self.pos_mirror_e = _pos_mirror_e
        self.pos_camera_e = _pos_camera_e
        self.expos_e = _expos_e


        #----------D------------
        self.pos_mirror_d = _pos_mirror_d
        self.pos_camera_d = _pos_camera_d
        self.expos_d = _expos_d


        #--------pound cam-----------

        self.level = _level
        #perepheri settings

        self.hv = _hv
        self.pressure = _pressure
        self.turbo = _turbo


        #--------thermal---------
        self.sensor_type = _sensor_type

        self.k_th1 = _k_th1
        self.k_th2 = _k_th2
        self.time_cycle_th = _time_cycle_th

        #bunker settings
        self.recup_vel = _recup_vel
        self.gateway_vel = _gateway_vel
        self.pound_vel = _pound_vel

        self.vibro_freq = _vibro_freq

        self.cam_num_e  = _cam_num_e 
        self.cam_num_d  =   _cam_num_d 
        self.cam_num_pound =  _cam_num_pound 

        self.string_move_a = _string_move_a
        self.string_move_b = _string_move_b
        self.string_move_c = _string_move_c
        self.string_move_d = _string_move_d
        self.string_move_e = _string_move_e

    def save(self):    
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(self.__dict__, file, indent=4)

    def load()->"SettingsString":
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            loaded_dict = json.load(file)
        return SettingsString(_com_primary = loaded_dict["com_primary"],
            _com_secondary = loaded_dict["com_secondary"],
            _string_vel = loaded_dict["string_vel"],
            _string_koef = loaded_dict["string_koef"],
            _f_dest_a = loaded_dict["f_dest_a"],
            _f_off_a = loaded_dict["f_off_a"],
            _f_sign_a = loaded_dict["f_sign_a"],
            _k_v_tens_a = loaded_dict["k_v_tens_a"],
            _def_steps_a = loaded_dict["def_steps_a"],
            _dir_a = loaded_dict["dir_a"],
            _en_a = loaded_dict["en_a"],
            _f_dest_b = loaded_dict["f_dest_b"],
            _f_off_b = loaded_dict["f_off_b"],
            _f_sign_b = loaded_dict["f_sign_b"],
            _k_v_tens_b = loaded_dict["k_v_tens_b"],
            _def_steps_b = loaded_dict["def_steps_b"],
            _dir_b = loaded_dict["dir_b"],
            _n_b = loaded_dict["n_b"],
            _f_dest_c = loaded_dict["f_dest_c"],
            _f_off_c = loaded_dict["f_off_c"],
            _f_sign_c = loaded_dict["f_sign_c"],
            _k_v_tens_c = loaded_dict["k_v_tens_c"],
            _def_steps_c = loaded_dict["def_steps_c"],
            _dir_c = loaded_dict["dir_c"],
            _en_c = loaded_dict["en_c"],
            _pos_mirror_e = loaded_dict["pos_mirror_e"],
            _pos_camera_e = loaded_dict["pos_camera_e"],
            _expos_e = loaded_dict["expos_e"],
            _pos_mirror_d = loaded_dict["pos_mirror_d"],
            _pos_camera_d = loaded_dict["pos_camera_d"],
            _expos_d = loaded_dict["expos_d"],
            _level = loaded_dict["level"],
            _hv = loaded_dict["hv"],
            _pressure = loaded_dict["pressure"],
            _turbo = loaded_dict["turbo"],
            _sensor_type = loaded_dict["sensor_type"],
            _k_th1 = loaded_dict["k_th1"],
            _k_th2 = loaded_dict["k_th2"],
            _time_cycle_th = loaded_dict["time_cycle_th"],
            _recup_vel = loaded_dict["recup_vel"],
            _gateway_vel = loaded_dict["gateway_vel"],
            _pound_vel = loaded_dict["pound_vel"],
            _vibro_freq = loaded_dict["vibro_freq"],
            _cam_num_e = loaded_dict["cam_num_e"],
            _cam_num_d = loaded_dict["cam_num_d"],
            _cam_num_pound = loaded_dict["cam_num_pound"],
            _string_move_a = loaded_dict["string_move_a"],
            _string_move_b = loaded_dict["string_move_b"],
            _string_move_c = loaded_dict["string_move_c"],
            _string_move_d = loaded_dict["string_move_d"],
            _string_move_e = loaded_dict["string_move_e"])

        #print(f"Имя: {self.name}, Значение: {self.value}")

#setings = SettingsString()
#setings.save()

#setings:SettingsString = SettingsString.load()
#setings.save()