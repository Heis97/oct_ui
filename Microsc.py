from enum import Enum
import math

def round_s(val:float,prec:int):
    v = round(val,prec)
    return str(v)

class Microcop_type(Enum):
    e = 0
    d = 1

class Microcop(object):
    mirror_axis = ''
    camera_axis = ''
    mirror_coord:float = 0.0
    camera_coord:float  = 0.0

    mirror_h_off = 0.0
    camera_h_off = 0.0
    camera_v_off = 0.0
    microsc_type = None
    homed:bool = False
    limit_mirror = 40
    limit_camera = 40


    mirror_cur = 0
    camera_cur = 0
    offset_mirror = 10
    pos_mirror = [8.1,12.3,15.8]#e
    pos_camera = [10.3,14.5,18]#e

    def __init__(self,_mirror_axis:str,_camera_axis:str, _microsc_type:Microcop_type, _pos_mirror:list, _pos_camera:list) -> None:
        self.mirror_axis = _mirror_axis
        self.camera_axis = _camera_axis
        self.microsc_type = _microsc_type

        self.pos_mirror = _pos_mirror
        self.pos_camera = _pos_camera
    

    """def move_mirror_rel(self, dist)->str:
        self.mirror_coord+=dist
        self.apply_limits()
        cmd = "G1 "+self.mirror_axis+self.mirror_coord
        return cmd
    
    def move_camera_rel(self, dist)->str:
        dest_camera = self.camera_coord+dist
        self.apply_limits(dest_camera,self.mirror_cur)
        cmd = "G1 "+self.camera_axis+dest_camera
        return cmd"""
    
    def move_depth(self, dist)->str:
        self.camera_v_off = dist
        cam_x = self.camera_coord + self.camera_v_off  + self.camera_h_off
        cam_x,self.mirror_cur = self.apply_limits(cam_x,self.mirror_cur)
        cmd = "G1 "+ self.camera_axis + round_s(cam_x,2)
        return cmd
    
    def move_betw_string(self, dist)->str:
        self.camera_h_off = dist
        self.mirror_h_off = dist
        cam_x = self.camera_coord + self.camera_v_off + self.camera_h_off
        mir_x = self.mirror_coord +self.mirror_h_off
        cam_x,mir_x = self.apply_limits(cam_x, mir_x)
        cmd = "G1 "+self.mirror_axis+round_s(mir_x,2) + " " + self.camera_axis + round_s(cam_x,2)
        return cmd
    
    def move_to_pos(self, num:int )->str:
        '''num = 1, 2, 3'''
        self.camera_coord = self.pos_camera[num-1]
        self.mirror_coord = self.pos_mirror[num-1]
        self.camera_coord,self.mirror_coord = self.apply_limits(self.camera_coord,self.mirror_coord)
        cmd = "G1 "+self.mirror_axis+round_s(self.mirror_coord,2)+" "+self.camera_axis+round_s(self.camera_coord,2)
        return cmd
    
    def apply_limits(self, _camera_coord_in: float = 0.0, _mirror_coord_in: float = 0.0)-> tuple[float,float]:
        _camera_coord = _camera_coord_in
        _mirror_coord = _mirror_coord_in
        #if not self.homed: return print("not homed")
        
        if _mirror_coord < 0: _mirror_coord = 0
        if _camera_coord < 0: _camera_coord = 0

        if _mirror_coord > self.limit_mirror: _mirror_coord = self.limit_mirror
        if _camera_coord > self.limit_camera: _camera_coord = self.limit_camera

        if _mirror_coord + self.offset_mirror < _camera_coord: _camera_coord =_mirror_coord + self.offset_mirror

        self.mirror_cur = _mirror_coord
        self.camera_cur = _camera_coord
        return _camera_coord, _mirror_coord


    def home(self)->str:
        cmd = "G28 "+ self.camera_axis+self.mirror_axis
        #cmd += "G28 "+ self.mirror_axis+''
        self.homed = True
        return cmd
    
    
