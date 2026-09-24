"""printhead_gui.py  —  Awesome Touch GUI (Fresh rebuild)
=================================================================
Control interface for a custom print-head on BTT Octopus (Marlin 2.1.2.5).
Designed for a 10" capacitive panel, resolution 1054×700.

Features:
  • Two tabs: "Камера" (live 640×480; shows filament diameter)
              "Управление" (big sliders & toggles for G-codes)
  • Big touch-friendly widgets (buttons ≥300×68 px, sliders long)
  • Works standalone: if no camera/COM-port, UI still opens (black video placeholder)
  • M-code bindings:
      M579 (temperature), M578 P/V/G (pressure/value/valve/gate),
      M576 (filament speed), M577 (HV), M580 (fan), M106/107 (recuperation),
      G92 E0 (zero length), G1 E50 F1200 (move filament)

Usage:
  pip install pyqt5 opencv-python numpy pyserial
  python printhead_gui.py
"""

import subprocess
from enum import Enum
import sys
import os
from typing import Tuple
import cv2
import numpy as np
import serial
import serial.tools.list_ports as ports
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt,QDateTime
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QComboBox,QMessageBox
from Devices.StringMashComp import *
from Devices.StringMash import *
from Microsc import *
import threading

from Viewer3D_GL import GLWidget
#press 237 to 640
#hv 1610 max
TEST_PROG = True
RELE_UI = False
CAMERAS_OPEN = False
# ─────────────────────────── CONSTANTS ───────────────────────────
CAM_W_string, CAM_H_string =  1920, 1080
CAM_W_pound, CAM_H_pound =  640 , 480        # camera capture & display size || 1280, 720 || 1920, 1080|| 640, 480|| 800, 600
FPS_DELAY    = 33                 # ms between frames (~30 FPS)
PX_TO_MM     = 0.5/1920               # mm per pixel, calibrate!
BTN_W, BTN_H = 400, 50            # touch-friendly button size 400,100
SLIDER_W     = 420                # slider width

CAM_W_disp, CAM_H_disp = 1280, 960           # camera capture & display size
#CAM_W_disp, CAM_H_disp = 640, 480           # camera capture & display size
captures = []

MAKET = True


class SliderLabel(object):

    def __init__(self, slider:QtWidgets.QSlider, label:QtWidgets.QLabel ,k = 1.0 ) -> None:
        super().__init__()
        self.slider = slider
        self.label = label
        self.k = k

    def setValue(self,v):
        if self.k != 0:
            self.slider.setValue(int(v/self.k))

    def setValueSilent(self, v):
        self.slider.blockSignals(True)
        self.setValue(v)
        self.slider.blockSignals(False)

target_ip = "192.168.1.81"
#device self "127.0.0.1"
#device 2 "192.168.1.81"
#device 10 "192.168.1.80"

CAMERAS = [
    {"ip": target_ip, "port": 5000, "name": "Камера 1"},
    {"ip": target_ip, "port": 5001, "name": "Камера 2"},
    {"ip": target_ip, "port": 5002, "name": "Камера 3"},
]
threads = []


class CameraThreadUDP(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(QPixmap)  # (image, info)
    type_cam:"CameraType" = 0 #0 - string, #1 - powuder
    cap = None
    ip = None
    port = None
    _running = True
    
    def __init__(self, index, ip,port) -> None:
        super().__init__()
        self.index = index
        self.ip = ip
        self.port = port

    def run(self,) -> None:
        """Поток для приёма видео с одной камеры"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.ip = '0.0.0.0'
        print("prebind")
        
        sock.bind(('0.0.0.0', self.port))
        #sock.bind((self.ip, self.port))
        print("postbind")
        sock.settimeout(1.0)
        
        print(f"{self.port}: ожидание потока на порту {self.port}...")
        
        while True:
            try:
                data, addr = sock.recvfrom(65536)
                #print("adddr1",str(addr[0]),str(self.ip),"_________\n")
                if str(addr[0]) in str(self.ip):
                    #print("adddr",str(addr),"_________\n")

                    # Декодирование JPEG
                    nparr = np.frombuffer(data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    res = cv2.resize(frame,(CAM_W_disp, CAM_H_disp))
                    res = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
                    img = QImage(res.data, CAM_W_disp, CAM_H_disp, res.strides[0], QImage.Format_RGB888)
                    pix = QPixmap.fromImage(img)
                    self.frame_ready.emit(pix)

                #if frame is not None:
                    # Отображение с именем камеры
                    #cv2.imshow(self.camera_config["name"], frame)
                
            except socket.timeout:
                continue

    def stop(self):
        self._running = False

    def set_type(self,cam_type:"CameraType"):
        pass
        #self.type_cam = cam_type

    def set_expo(self,exp:int):

        pass
        #self.cap.set(cv2.CAP_PROP_EXPOSURE,  exp)




# ─────────────────────────── CAMERA THREAD ───────────────────────────
class CameraThread(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(QPixmap)  # (image, info)
    type_cam:"CameraType" = 0 #0 - string, #1 - powuder
    bin_lvl = 140
    pound_lvl = 100
    cap = None
    buffer = []
    buffer_size = 5
    buffer_size_diff = 300
    last_sums = []
    buffer_diffs = []
    _running = True
    def __init__(self, index ) -> None:
        super().__init__()
        self.index = index

    def run(self) -> None:
        if self._running:
            try:

                self.cap = cv2.VideoCapture(self.index,cv2.CAP_DSHOW)

                
            except Exception as e:
                QMessageBox.information(self, "Information", f"{e}")
            CAM_W = CAM_W_pound
            CAM_H = CAM_H_pound
            
            if not self.cap.isOpened():
                # no camera: emit black frame periodically
                blank = QPixmap(CAM_W, CAM_H)
                blank.fill(Qt.black)
                while not self.isInterruptionRequested():
                    self.frame_ready.emit(blank)
                    self.msleep(1000)
                return
            if self.type_cam == 0:
                CAM_W = CAM_W_string
                CAM_H = CAM_H_string
                #self.cap.set(cv2.CAP_PROP_EXPOSURE,  -7)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
            codec = 0x47504A4D
            self.cap.set(cv2.CAP_PROP_FOURCC, codec)
            print(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            while not self.isInterruptionRequested():
                ret, frame = self.cap.read()
                frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                if not ret:
                    break
                # estimate diameter
                if (self.type_cam == CameraType.string_after) or (self.type_cam == CameraType.string_before) or (self.type_cam == CameraType.not_cam):
                    
                    #frame = self._estimate_diameter(frame)
                    res = cv2.resize(frame,(CAM_W_disp, CAM_H_disp))
                    img = QImage(res.data, CAM_W_disp, CAM_H_disp, res.strides[0], QImage.Format_RGB888)
                    pix = QPixmap.fromImage(img)
                    self.frame_ready.emit(pix)
                    #self.msleep(FPS_DELAY)
                elif self.type_cam == CameraType.pound:
                    #frame = self._estimate_powder_level(frame)
                    res = cv2.resize(frame,(CAM_W_disp, CAM_H_disp))
                    img = QImage(res.data, CAM_W_disp, CAM_H_disp, res.strides[0], QImage.Format_RGB888)
                    pix = QPixmap.fromImage(img)                
                    self.frame_ready.emit(pix)
                    #self.msleep(FPS_DELAY)
                #cv2.imshow("asd",bin)
                #cv2.waitKey()
                #if res is not None:
                
                

        self.cap.release()

    def stop(self):
        self._running = False

    def set_type(self,cam_type:"CameraType"):
        self.type_cam = cam_type

    def set_expo(self,exp:int):
        self.cap.set(cv2.CAP_PROP_EXPOSURE,  exp)

    def _estimate_diameter(self,frame: np.ndarray):
        gray = cv2.cvtColor(frame , cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray,(7,7),-1)
        _,bin = cv2.threshold(gray,self.bin_lvl,255,cv2.THRESH_BINARY)
        #_,bin = cv2.threshold(gray,self.bin_lvl,255,cv2.THRESH_BINARY_INV)
        #laplacian = cv2.Laplacian(frame,cv2.CV_64F,None,9)
        #sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=5)
        #bin = cv2.threshold(frame,160,255,cv2.THRESH_BINARY)
        diametrs = []
        rows,cols = bin.shape
        j = int(rows/2)
        start_i = 0
        stop_i = 0

        for i in range(1,cols-1):            
            if bin[j,i] == 0 and bin[j, i+1] > 0:
                start_i = i
            if bin[j,i] > 0 and bin[j, i+1] == 0:
                stop_i = i
                diametrs.append([start_i,stop_i])
            #print(p)
        #print(diametrs)
        #print("_____________________________")
        #1280 pix = 12.8 mm //*10 for um
        up_down = 1
        for diametr in diametrs:
            
            diam = round((diametr[1] - diametr[0])*9.2)
            #if diam>1400:
            len = str(diam)+" mkm"

            cv2.line(frame,(diametr[0],j),(diametr[1],j),(255,0,0),6)
            cv2.putText(frame,len,(diametr[1]+10,j+10),cv2.FONT_HERSHEY_SIMPLEX,2,(255,0,0),2)
            #up_down*=-1

        #bin2 = cv2.cvtColor(bin,cv2.COLOR_GRAY2RGB)
        #return bin2
        return frame
    

    def _estimate_powder_level(self,orig: np.ndarray):
        frame = cv2.cvtColor(orig , cv2.COLOR_BGR2GRAY)
        self.buffer.append(frame)
        ret = frame
        if len(self.buffer)>self.buffer_size:           
            self.buffer = self.buffer[1:]
            ret = cv2.subtract( self.buffer[-1], self.buffer[-2])
            #ret = cv2.convertScaleAbs(ret, alpha = 5, beta = 1)
            
            rows,cols = ret.shape
            sums = []
            for i in range(cols):  
                sum_i = 0.0
                for j in range(rows):
                    sum_i += float(ret[j,i] )
                #sum_i = sum_i/10
                if sum_i > rows -1: sum_i = rows - 1
                sums.append(sum_i)
            diffs = []
            for i in range(len(sums)):
                if len(self.last_sums)==len(sums):
                    diff = abs(self.last_sums[i] - sums[i])
                    diffs.append(diff)
                    #cv2.line(orig,(i,0),(i,int(diff)),(0,255,0),1)
                    self.last_sums[i] = sums[i]
                else:
                    self.last_sums.append(sums[i])
            
            self.buffer_diffs.append(diffs.copy())
            
            if len(self.buffer_diffs)>self.buffer_size_diff:
                self.buffer_diffs = self.buffer_diffs[1:]
                diff_aver = []
                for i in range(len(self.buffer_diffs[0])):
                    val = 0.0
                    for j in range(len(self.buffer_diffs)):
                        val+=self.buffer_diffs[j][i]
                    aver = float(val)/(1*len(self.buffer_diffs))
                    diff_aver.append(aver)
                    cv2.line(orig,(i,0),(i,int(aver)),(0,255,0),1)


                #print(self.buffer_diffs)

                i_lvl = self.get_i_from_mass(diff_aver,self.pound_lvl)
                cv2.line(orig,(i_lvl,0),(i_lvl,rows-1),(255,0,0),3)

        #laplacian = cv2.Laplacian(frame,cv2.CV_64F,None,9)
        #sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=5)
        #bin = cv2.threshold(frame,160,255,cv2.THRESH_BINARY)
        #orig = cv2.rotate(orig,cv2.ROTATE_90_CLOCKWISE)
        return orig
    
    def get_i_from_mass(self,arr,x):
        for i in range(1,len(arr)):
            if x>arr[i-1] and x <=arr[i]:
                return i
        return -1


def save(file_name,data):    
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def load(file_name)->"list[StringStatePrimary]":
    with open(file_name, "r", encoding="utf-8") as file:
        loaded_dict = json.load(file)


#_____________________________MARLIN THREAD____________________________________

class SaveThread(QtCore.QThread):
   
    def __init__(self,filename,file):
        QtCore.QThread.__init__(self)
        self._file  = file 
        self._filename  = filename

    def run(self):
        save(self._filename,self._file)


class PosThreadAll(QtCore.QThread):
    cur_state = QtCore.pyqtSignal(StringStatePrimary,StringStatePrimary)  # ()
    

    def __init__(self,target_ip):
        QtCore.QThread.__init__(self)   
        
        #tcp_ip = [target_ip,"127.0.0.1"]#["192.168.10.212","192.168.10.211"]  // ["127.0.0.1","127.0.0.1"]  // ["192.168.1.80","127.0.0.1"]
        self.string_mash = StringMashComp(target_ip, 62000,50000)

        self.timeDelt = 5  
        self._running = True
        self.data_main = []
        self.data_sup = []
        self.start()   
        self.couter = 0
        self.couter_f = 0.0
        self.couter_f2 = 0.0
        self.couter_save = 0
        self.lock = threading.Lock()



    def run(self):
        if self._running:
            while self._running:
                ret = self.string_mash.parse_resp()
                if ret>0 and len(self.string_mash.all_data)>0 and len(self.string_mash.all_data_sec)>0:  
                    self.cur_state.emit(self.string_mash.all_data[-1],self.string_mash.all_data_sec[-1])    
                    """self.send_g_code("M584 U E"+str(round(self.couter_f,3)))    
                    self.send_g_code("M585 F"+str(self.couter_f))      
                    self.couter_f+=1    
                    if self.couter_f>4000:
                        self.couter_f = 0"""
                #self.msleep(self.timeDelt)

    def stop(self):
        self._running = False

    def send_g_code(self,command:str):
        #with self.lock:
        self.string_mash.sendGcom(command)

    

class StringMashType(Enum):
    primary = 0
    secondary = 1   
    rele = 2      

class CameraType(Enum):
    string_before = 0
    string_after = 1   
    pound = 2  
    not_cam = 3 


pos_mirror_e = [8.1,12.3,15.8]#e
pos_camera_e = [10.3,14.5,18]#e

pos_mirror_d = [14.1,12.3,15.8]#d
pos_camera_d = [14.3,14.5,18]#d

# ────────────────────────────── MAIN GUI ──────────────────────────────
class StringGUI(QtWidgets.QWidget):
    # Define font for widgets
    FONT = QFont("Arial", 22)
    BTN_W, BTN_H = BTN_W, BTN_H
    SLIDER_W = SLIDER_W
    string_mash:StringMashPrimary
    string_mash_sec:StringStatePrimary

    threads_cams:"list[CameraThread]" = [None,None,None]
    monitor_nums = [-1,-1,-1]

    turbo_power = 0

    move_a = False
    move_b = False
    move_c = False

    move_d = False
    move_e = False

    tared = False
    
    def __init__(self) -> None:
        super().__init__(None, QtCore.Qt.Window)
        self.setWindowTitle("Printhead Controller – Touch UI")
        self._apply_style()        
        self._build_ui()
        self.resize(1920, 1080)


    # ------------------------- STYLE -------------------------
    def _apply_style(self) -> None:
        self.setStyleSheet(
            "QWidget{background:#2b2b2b;color:#f0f0f0;}" +
            "QLabel{font:22px 'Arial';}" +
            "QGroupBox{font:22px 'Arial';border:2px solid #666;margin-top:20px;}" +
            "QGroupBox::title{left:22px;top:-22px;padding:2 10px;background:#2b2b2b;}" +
            "QTabBar::tab{min-width:250px;min-height:30px;padding:30px 50px;font:22px 'Arial';background:#3b3b3b;border:0;}" +
            "QTabBar::tab:selected{background:#505050;}"
        )

    # ------------------------- BUILD UI -------------------------
    def _build_ui(self) -> None:
        self.string_inv = False
        self.pos_thread_all = None
        #print("2")
        tabs = QtWidgets.QTabWidget(self)
        tabs.tabBar().setExpanding(True)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(tabs)
        spacing = 12   #32


        


        # --- Prog Control Tab ---


        
        tab_ctrl = QtWidgets.QWidget()
        tabs.addTab(tab_ctrl, "Программа")
        hctrl = QtWidgets.QHBoxLayout(tab_ctrl)
        hctrl.setSpacing(spacing)
        hctrl.setContentsMargins(25, 25, 25, 25)

        # Parameters
        grp_par = QtWidgets.QGroupBox("Печать")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)

        #self.slab_vibr_ampl_shkiv = self._add_slider_na(vpar, "Подача", "", 1, 255, 10,  lambda v: self._send_gcode(StringMashType.secondary,f"M581 C{int(v)}"))
        self.textbox:QtWidgets.QTextEdit = self._add_textbox_na(vpar,1.0)
        
        self.textbox.setText("G1 X0 Y0 F600\n")
        self.textbox.setText(self.textbox.toPlainText()+"G1 X10 E0.1\n")
        self.textbox.setText(self.textbox.toPlainText()+"G1 X10 Y10 E0.2\n")
        self.textbox.setText(self.textbox.toPlainText()+"G1 X0 Y10 E0.3\n")
        self.textbox.setText(self.textbox.toPlainText()+"G1 X0 Y0 Z0 E0.5 F600\n")

        self.lbl_state_main =  QtWidgets.QLabel()
        self.lbl_state_main.setAlignment(Qt.AlignTop)
        self.lbl_state_main.setText('\n\n\n\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\n')
        hctrl.addWidget(self.lbl_state_main)

        self.lbl_state_sec =  QtWidgets.QLabel()
        self.lbl_state_sec.setAlignment(Qt.AlignTop)
        self.lbl_state_sec.setText('\n\n\n\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\n')
        hctrl.addWidget(self.lbl_state_sec)

        grp_par = QtWidgets.QGroupBox("Авто")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Запуск прогр", lambda v: self._start_prog(v,self.textbox))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Пауза", lambda v: self._start_prog(v,self.textbox))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Home", lambda v: self._set_home(v))
        
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Уст. т. 0", lambda v: self._set_zero_p(v))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Передвиж в т. 0", lambda v: self._move_zero_p(v))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Загрузить настройки", lambda v: self._set_settings(v))

        vpar.addStretch()

        grp_par = QtWidgets.QGroupBox("Ручн")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+X", lambda v: self._jog_bool(v,0))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-X", lambda v: self._jog_bool(v,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+Y", lambda v: self._jog_bool(v,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-Y", lambda v: self._jog_bool(v,3))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+Z", lambda v: self._jog_bool(v,4))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-Z", lambda v: self._jog_bool(v,5))

        """self.but_feed_pound = self._momentary_button_common_a(vpar,"+Z", lambda v: self._jog_direct_steps_vel(v,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-Z", lambda v: self._jog_direct_steps_vel(v,-1))"""
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+E", lambda v: self._jog_periph(v,7, 1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-E", lambda v: self._jog_periph(v,7,-1,1))
        

        vpar.addStretch()

        # --- Periph Control Tab ---
        tab_ctrl = QtWidgets.QWidget()
        tabs.addTab(tab_ctrl, "Перифирия")
        hctrl = QtWidgets.QHBoxLayout(tab_ctrl)
        hctrl.setSpacing(spacing)
        hctrl.setContentsMargins(25, 25, 25, 25)

        self.lbl_state_main2 =  QtWidgets.QLabel()
        self.lbl_state_main2.setAlignment(Qt.AlignTop)
        self.lbl_state_main2.setText('\n\n\n\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\n')
        hctrl.addWidget(self.lbl_state_main2)

        self.lbl_state_sec2 =  QtWidgets.QLabel()
        self.lbl_state_sec2.setAlignment(Qt.AlignTop)
        self.lbl_state_sec2.setText('\n\n\n\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\nОбъём вверх\n')
        hctrl.addWidget(self.lbl_state_sec2)

        # Parameters
        grp_par = QtWidgets.QGroupBox("Осцилляторы")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)
        self.lbl =  QtWidgets.QLabel()
        self.lbl.setAlignment(Qt.AlignTop)
        self.lbl.setText('\nОсциллятор 1\n')
        vpar.addWidget(self.lbl)

        self.but_feed_pound = self._momentary_button_common_a(vpar,"+rot", lambda v: self._jog_periph(v,4,1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-rot", lambda v: self._jog_periph(v,4,-1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+up", lambda v: self._jog_periph(v,3,1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-down", lambda v: self._jog_periph(v,3,-1,1))
        self._add_slider_na(vpar,"serv_1","",40,240,120, lambda v: self._servo_rot(v,0))

        self.but_feed_pound = self._momentary_button_common_a(vpar,"home rot", lambda v: self._home_ax(v,4,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"home lift", lambda v: self._home_ax(v,3,1))

        self.lbl2 =  QtWidgets.QLabel()
        self.lbl2.setAlignment(Qt.AlignTop)
        self.lbl2.setText('\nОсциллятор 2\n')
        vpar.addWidget(self.lbl2)
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+rot", lambda v: self._jog_periph(v,6,1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-rot", lambda v: self._jog_periph(v,6,-1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+up", lambda v: self._jog_periph(v,5,1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-down", lambda v: self._jog_periph(v,5,-1,1))
        self._add_slider_na(vpar,"serv_2","",40,240,120, lambda v: self._servo_rot(v,1))

        self.but_feed_pound = self._momentary_button_common_a(vpar,"home rot", lambda v: self._home_ax(v,6,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"home lift", lambda v: self._home_ax(v,5,1))
        vpar.addStretch()


        grp_par = QtWidgets.QGroupBox("Манипулятор")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)

        self.lbl3 =  QtWidgets.QLabel()
        self.lbl3.setAlignment(Qt.AlignTop)
        self.lbl3.setText('\nМанипулятор 1\n')
        vpar.addWidget(self.lbl3)
        
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+rot", lambda v: self._jog_periph(v,4,1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-rot", lambda v: self._jog_periph(v,4,-1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+up", lambda v: self._jog_periph(v,3,1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-down", lambda v: self._jog_periph(v,3,-1,2))

        self.but_feed_pound = self._momentary_button_common_a(vpar,"home rot", lambda v: self._home_ax(v,4,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"home lift", lambda v: self._home_ax(v,3,2))

        self.lbl4 =  QtWidgets.QLabel()
        self.lbl4.setAlignment(Qt.AlignTop)
        self.lbl4.setText('\nМанипулятор 2\n')
        vpar.addWidget(self.lbl4)
        
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+rot", lambda v: self._jog_periph(v,6,1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-rot", lambda v: self._jog_periph(v,6,-1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+up", lambda v: self._jog_periph(v,5,1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-down", lambda v: self._jog_periph(v,5,-1,2))

        self.but_feed_pound = self._momentary_button_common_a(vpar,"home rot", lambda v: self._home_ax(v,6,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"home lift", lambda v: self._home_ax(v,5,2))
        vpar.addStretch()

        grp_par = QtWidgets.QGroupBox("Система подачи")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)
        self.but_feed_pound = self._momentary_button_common_a(vpar,"table out", lambda v: self._jog_periph(v,0,1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"table in", lambda v: self._jog_periph(v,0,-1,2))

        self.but_feed_pound = self._momentary_button_common_a(vpar,"up", lambda v: self._jog_periph(v,2,1,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"down", lambda v: self._jog_periph(v,2,-1,2))

        self.but_feed_pound = self._momentary_button_common_a(vpar,"table home", lambda v: self._home_ax(v,0,2))
        
        self._add_slider_na(vpar,"Temp: ","C",20,50,37, lambda v: self._set_heater_val(v))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Нагрев", lambda v: self._set_heater_en(v))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Насос", lambda v: self._set_reley(v,0))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Стол", lambda v: self._set_reley(v,1))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Крышка", lambda v: self._set_reley(v,2))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Сброс", lambda v: self._set_reley(v,3))

        vpar.addStretch()

        grp_par = QtWidgets.QGroupBox("Ручн")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+X", lambda v: self._jog_bool(v,0))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-X", lambda v: self._jog_bool(v,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+Y", lambda v: self._jog_bool(v,2))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-Y", lambda v: self._jog_bool(v,3))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+Z", lambda v: self._jog_direct_steps_vel(v,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-Z", lambda v: self._jog_direct_steps_vel(v,-1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"+E", lambda v: self._jog_periph(v,7, 1,1))
        self.but_feed_pound = self._momentary_button_common_a(vpar,"-E", lambda v: self._jog_periph(v,7,-1,1))
        vpar.addStretch()

        # ---  Prog Control Tab ---
        tab_ctrl = QtWidgets.QWidget()
        tabs.addTab(tab_ctrl, "Программа")
        hctrl = QtWidgets.QHBoxLayout(tab_ctrl)
        hctrl.setSpacing(spacing)
        hctrl.setContentsMargins(25, 25, 25, 25)

        
        grp_par = QtWidgets.QGroupBox("Траектория")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)        
        vpar.setSpacing(spacing)        

        self.viewer3d = GLWidget(self)
        #self.viewer3d.setGeometry(QtCore.QRect(10, 10, 600, 600))
        self.viewer3d.draw_start_frame(10.)
        vpar.addWidget(self.viewer3d)

        vpar.addStretch()


        grp_par = QtWidgets.QGroupBox("Программа")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)        
        vpar.setSpacing(spacing)     

        self.textbox2:QtWidgets.QTextEdit = self._add_textbox_na(vpar,1.0)
        
        self.textbox2.setText("G1 X0 Y0 F600\n")
        self.textbox2.setText(self.textbox.toPlainText()+"G1 X10 E4\n")
        self.textbox2.setText(self.textbox.toPlainText()+"G1 X10 Y10 E8\n")
        self.textbox2.setText(self.textbox.toPlainText()+"G1 X0 Y10 E12\n")
        self.textbox2.setText(self.textbox.toPlainText()+"G1 X0 Y0 Z0 E12 F600\n")

        self.but_feed_pound = self._momentary_button_common_a(vpar,"Загрузить прогр", lambda v: self._open_prog(v,self.textbox2))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Запуск прогр", lambda v: self._start_prog(v,self.textbox2))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Пауза", lambda v: self._start_prog(v))
           
        vpar.addStretch()


        
        #vpar.addStretch()

        # --- Setup 1 Control Tab ---
        tab_ctrl = QtWidgets.QWidget()
        tabs.addTab(tab_ctrl, "Настройки")
        hctrl = QtWidgets.QHBoxLayout(tab_ctrl)
        hctrl.setSpacing(spacing)
        hctrl.setContentsMargins(25, 25, 25, 25)


        grp_par = QtWidgets.QGroupBox("Настройка двигателей 1")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)

        self.but_feed_pound = self._toggle_button_common_a(vpar,"Пауза", lambda v: self._start_prog(v))

        self.but_feed_pound = self._toggle_button_common_a(vpar,"Home_test", lambda v: self._set_home_test(v))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Delta calibrate", lambda v: self._set_delta_calibr(v))
        
        vpar.addStretch()


        grp_par = QtWidgets.QGroupBox("Калибровка стола")
        hctrl.addWidget(grp_par)
        vpar = QtWidgets.QVBoxLayout(grp_par)
        vpar.setSpacing(spacing)

        self.but_feed_pound = self._toggle_button_common_a(vpar,"Точка 1", lambda v: self.remember_point(v,0))        
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Точка 2", lambda v: self.remember_point(v,1))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Точка 3", lambda v: self.remember_point(v,2))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Калибровка стола", lambda v: self.bed_vec_comp(v))
        self.but_feed_pound = self._toggle_button_common_a(vpar,"Сбросить калибровку стола", lambda v: self.bed_vec_reset(v))
        
        vpar.addStretch()
        #-----------------------------------------------------------

        self.connect_serial()
        #self.btn_conn.setChecked(True)
        
        #self.init_ui()
        
        #print(bool(1), bool(0))
        #self.start_code()

    #------------PROG FUNC-----------------------------------------

    def remember_point(self,val, num):
        if val:
            self._send_gcode(StringMashType.primary,f"main M616 {int(num)}")

    def bed_vec_reset(self,val):
        if val:
            self._send_gcode(StringMashType.primary,f"main M616 -1")

    def bed_vec_comp(self,val):
        if val:
            self._send_gcode(StringMashType.primary,f"main M616 5")

    def _open_prog(self, val, textbox):
        if val:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Выберите файл программы",
                "", 
                "G-code files (*.gcode *.nc *.txt);;All files (*)"
            )

            if not file_path:
                return

            try:
                content = None
                for enc in ("utf-8", "cp1251", "latin-1"):
                    try:
                        with open(file_path, "r", encoding=enc) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue

                if content is None:
                    raise IOError("Не удалось определить кодировку файла")

                # Записываем содержимое в textbox
                if content is not None:
                    textbox.setPlainText(content)
                    traj = self.viewer3d.parse_g_code(content)
                    self.viewer3d.addLines(traj,1,0,0,1)

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Ошибка открытия файла",
                    f"Не удалось прочитать файл:\n{file_path}\n\n{e}"
                )
        else:
            pass
        

    def _set_reley(self, val,ind):
        self._send_gcode(StringMashType.primary,f"num2 M579 I{int(ind)} S{int(val)}")

    def _set_heater_en(self, val):
        if val:
            self._send_gcode(StringMashType.primary,f"num2 M579 E1")
        else:
            self._send_gcode(StringMashType.primary,f"num2 M579 E0")


    def _set_heater_val(self, val):
        self._send_gcode(StringMashType.primary,f"num2 M579 T{int(val)}")

    def _servo_rot(self, val,ind):
        self._send_gcode(StringMashType.primary,f"num1 M577 I{ind} V{int(val)}")


    def _jog_bool(self, val, type):
        if val:
            self._send_gcode(StringMashType.primary,f"main M611 {int(type)}")
        else:
            self._send_gcode(StringMashType.primary,f"main M597 2")


    def _jog_direct_steps_vel(self, val, type):
        if val:
            self._send_gcode(StringMashType.primary,f"num1 M589 Z10.0 E{int(type)}")
        else:
            self._send_gcode(StringMashType.primary,f"num1 M589 Z0 E0")

    def _jog_periph(self, val, type, dir, num):
        if val:
            self._send_gcode(StringMashType.primary,f"num{str(num)} M587 I{int(type)} S{int(100000*dir)}")
        else:
            self._send_gcode(StringMashType.primary,f"num{str(num)} M587 I{int(type)} S0")



    def _home_ax(self, val, type, num):
        if val:
            self._send_gcode(StringMashType.primary,f"num{str(num)} M587 I{int(type)} H")
        else:
            pass

    def _start_prog(self, val,textbox):
        if val:
            self._send_gcode(StringMashType.primary,f"num1 M587 I7 C0")
            self._send_gcode(StringMashType.primary,f"main M598 0")

            text_code = textbox.toPlainText()
            lines = text_code.split('\n')
            for line in lines:
                self._send_gcode(StringMashType.primary,f"main M596 "+line)


            self._send_gcode(StringMashType.primary,f"main M597 0")
        else:
            self._send_gcode(StringMashType.primary,f"main M597 2")

    def _set_zero_p(self, val):
        if val:
            self._send_gcode(StringMashType.primary,f"main M612")
        else:
            pass

    def _move_zero_p(self, val):
        if val:
            self._send_gcode(StringMashType.primary,f"main M615")
        else:
            pass

    def _set_settings(self, val):
        if val:
            self._send_gcode(StringMashType.primary,f"main M614")
        else:
            pass

    def _set_home(self, val):
        if val:
            self._send_gcode(StringMashType.primary,f"num1 M589 X10")
        else:
            pass
                #self._send_gcode(StringMashType.primary,f"M597 2")

    def _set_home_test(self, val):
        if val:
            self._send_gcode(StringMashType.primary,f"num1 M589 Y40")
        else:
            pass

    def _set_delta_calibr(self, val):
        if val:
            self._send_gcode(StringMashType.primary,f"main M613 18")
        else:
            pass



    def init_ui(self):
        if self.pos_thread_all is None: return
        if self.pos_thread_all.string_mash is None: return
        if self.pos_thread_all.string_mash.all_data is None or self.pos_thread_all.string_mash.all_data_sec is None: return
        if len(self.pos_thread_all.string_mash.all_data)<2 or len(self.pos_thread_all.string_mash.all_data_sec)<2: return

        state_prim = self.pos_thread_all.string_mash.all_data[-1]
        state_sec = self.pos_thread_all.string_mash.all_data_sec[-1]


        widgets_to_silence = [
        self.but_string_move_a, self.but_string_move_b, self.but_string_move_c,
        self.but_string_move_d, self.but_string_move_e,
        self.but_home_microsc_d, self.but_led_microsc_d,
        self.but_gateway,self.but_temp_rele,self.but_hv_rele,
        self.but_24out_rele,self.but_press_rele,self.but_temp_sens, self.but_motors_free,
        self.but_gateway,self.but_tare_string,self.but_recuperat,
        self.but_karet_home,self.but_feed_pound,self.but_vibro_main
        ]

        self.but_string_move_a.setChecked(bool(state_prim.string_move_second[0]))
        self.but_string_move_b.setChecked(bool(state_prim.string_move_second[1]))
        self.but_string_move_c.setChecked(bool(state_prim.string_move_second[2]))
        self.but_string_move_d.setChecked(bool(state_prim.string_move_second[3]))
        self.but_string_move_e.setChecked(bool(state_prim.string_move_second[4]))
        for widget in widgets_to_silence:
            widget.blockSignals(True)
        
        

        #self.slider_turbo.set
        

        self.but_home_microsc_d.setChecked(bool(state_sec.homed_d))
        self.but_led_microsc_d.setChecked(bool(state_prim.heater_en))


        self.slab_turbo.setValueSilent(state_sec.turbo_val)
        self.but_gateway.setChecked(bool(state_sec.gateway_move))
        


        self.slab_temp.setValueSilent(state_prim.temp_dest)
        self.slab_hv.setValueSilent(state_prim.HV)
        self.slab_press.setValueSilent(state_prim.pressure_dest)
        self.slab_vel_tens.setValueSilent(state_prim.cur_speed_tens_com)
        self.slab_force_tens.setValueSilent(state_prim.f_dest_s[0])


        self.but_temp_rele.setChecked(bool(state_prim.heater_en))
        self.but_hv_rele.setChecked(bool(state_prim.reley_HV))
        self.but_24out_rele.setChecked(bool(state_prim.reley_24_out))
        self.but_press_rele.setChecked(bool(state_prim.reley_press))
        self.but_temp_sens.setChecked(bool(state_prim.ind_sensor))

        self.but_motors_free.setChecked(bool(state_prim.motors_free_state))
        self.but_gateway.setChecked(bool(state_sec.gateway_move))
        self.but_tare_string.setChecked(bool(state_prim.tare_tens))

        self.but_recuperat.setChecked(bool(state_sec.recuperator_move))
        self.but_karet_home.setChecked(bool(state_prim.homing_karet))
        self.but_feed_pound.setChecked(bool(state_sec.feed_pound_move))

        self.slab_vibr_ampl_shkiv.setValueSilent(state_sec.vibro_loop_high)
        self.slab_vibr_cycle_time.setValueSilent(state_sec.vibro_loop_ampl)

        self.but_vibro_main.setChecked(bool(state_sec.vibro_main))

        for widget in widgets_to_silence:
            widget.blockSignals(False)

        return 
    


    # ---------------------- CAMERA CONTROL ----------------------
    def _start_camera(self,num_cam:int,ip,port) -> None:
        thread_cam = CameraThreadUDP(num_cam,ip,port)
        thread_cam.start()
        self.threads_cams[num_cam] = thread_cam

    def set_expo(self,expo,monit):
        cmd = "M590 "
        cmd+= str(int(monit))+" "
        cmd+= str(int(expo))
        self._send_gcode(StringMashType.primary,cmd)
        #self.threads_cams[self.monitor_nums[monit]].set_expo(expo)

    def _set_monitor(self,num_cam:int,num_monit:int) -> None:
        
        """if self.monitor_nums[num_monit]>=0:
            try:
                self.threads_cams[self.monitor_nums[num_monit]].disconnect()
                self.threads_cams[self.monitor_nums[num_monit]].set_type(CameraType.not_cam)
            except BaseException as e:
                print(e)
        

            #print("self.monitor_nums[num_monit]",self.monitor_nums[num_monit])
        self.monitor_nums[num_monit] = num_cam"""
        if num_monit == 0:            
            self.threads_cams[num_cam].frame_ready.connect(self._update_frame_control_before, QtCore.Qt.QueuedConnection)
            self.threads_cams[num_cam].set_type(CameraType.string_before)

        elif num_monit == 1:
            self.threads_cams[num_cam].frame_ready.connect(self._update_frame_control, QtCore.Qt.QueuedConnection)
            self.threads_cams[num_cam].set_type(CameraType.string_after)

        elif num_monit == 2:
            self.threads_cams[num_cam].frame_ready.connect(self._update_frame_pound, QtCore.Qt.QueuedConnection)
            self.threads_cams[num_cam].set_type(CameraType.pound)


    def microscope_camera_set(self, state, num, monit,but_off_1:  QtWidgets.QPushButton,but_off_2:  QtWidgets.QPushButton):
        if state:
            but_off_1.setChecked(False)
            but_off_2.setChecked(False)
            self._set_monitor(num, monit)
            
        pass        


    def _update_frame_control(self, pix: QPixmap) -> None:
        self.lbl_img.setPixmap(pix)
        #self.lbl_dia.setText(f"Диаметр: {dia[0]:.1f} мм" if dia[0] >= 0 else "Диаметр: -- мм")


    
    def _update_frame_pound(self, pix: QPixmap) -> None:
        self.lbl_img_pound.setPixmap(pix)
        #self.lbl_dia.setText(f"Диаметр: {dia[0]:.1f} мм" if dia[0] >= 0 else "Диаметр: -- мм")

        # ---------------------- CAMERA CONTROL2 ----------------------
    


    def _update_frame_control_before(self, pix: QPixmap) -> None:
        self.lbl_img_before.setPixmap(pix)
        #self.lbl_dia.setText(f"Диаметр: {dia[0]:.1f} мм" if dia[0] >= 0 else "Диаметр: -- мм")


    
    def _update_frame_pound_before(self, pix: QPixmap) -> None:
        self.lbl_img_pound_before.setPixmap(pix)
        #self.lbl_dia.setText(f"Диаметр: {dia[0]:.1f} мм" if dia[0] >= 0 else "Диаметр: -- мм")


 

    def _update_state(self, state1: StringStatePrimary, state2: StringStatePrimary) -> None: 
        #self.lbl_state.setText("_____________Состояние\n"+str(state1)+"\n")
        self.lbl_state_main.setText("\n\n\n\nСостояние\n"+str(state1))
        self.lbl_state_main2.setText("\n\n\n\nСостояние\n"+str(state1))
        self.lbl_state_sec.setText("\n\n\n\nСостояние\n"+str(state2))
        self.lbl_state_sec2.setText("\n\n\n\nСостояние\n"+str(state2))


    def update_serial_ports(self):
        self.cmb_port.clear()
        #for p in ports.comports():
        for p in reversed(ports.comports()):
            self.cmb_port.addItem(p.device)
        

    def _pound_lvl(self, val):
        if  self.cam_thread_pound is not None:
            self.cam_thread_pound.pound_lvl = val
            
    def _bin_lvl(self, val):
        if  self.cam_thread_control is not None:
            self.cam_thread_control.bin_lvl = val

    def _cam_exp(self, val):
        if  self.cam_thread_control is not None:
            self.cam_thread_control.cap.set(cv2.CAP_PROP_EXPOSURE, val)

    def _cam_exp_bef(self, val):
        if  self.cam_thread_control_before is not None:
            self.cam_thread_control_before.cap.set(cv2.CAP_PROP_EXPOSURE, val)

    def _gateway_move(self, val):        
        self._send_gcode(StringMashType.secondary,   f"M585 Y{int(val)}")

    def _recuperator_move(self, val):
        
        #self._send_gcode(StringMashType.secondary, f"M585 Z{int(val)} D-1")#макет
        self._send_gcode(StringMashType.secondary, f"M585 Z{int(val)} D1")
        self._send_gcode(StringMashType.secondary,   f"M585 Y{int(val)}")

    def _recuperator_move_inv(self, val):
        
        self._send_gcode(StringMashType.secondary, f"M585 Z{int(val)} D1") #макет
        #self._send_gcode(StringMashType.secondary, f"M585 Z{int(val)} D-1")

    def move_string_a(self,val):
        self.move_a = val

    def move_string_b(self,val):
        self.move_b = val

    def move_string_c(self,val):
        self.move_c = val

    def move_string_d(self,val):
        self.move_d = val

    def move_string_e(self,val):
        self.move_e = val

    

    def _string_move_inv(self, val):
        self.string_inv = val

    def _string_set_zero_len(self):
        
        com = "M584 "
        if self.move_a: com+= f" A1"
        if self.move_b: com+= f" B1"
        if self.move_c: com+= f" C1"
        if self.move_d: com+= f" D1"
        if self.move_e: com+= f" F1"
        if self.move_a or self.move_b or self.move_c or self.move_d or self.move_e:
            com+= f" W J0.0 "
            self._send_gcode(StringMashType.primary,com)


    def _string_move(self, val, suffix):
        
        if val == True:
            com = "M584 "
            print(self.string_inv)
            move_string =  int(val)*(int(val)+int(self.string_inv))
            if self.move_a: com+= f" A{move_string}"
            if self.move_b: com+= f" B{move_string}"
            if self.move_c: com+= f" C{move_string}"
            if self.move_d: com+= f" D{move_string}"
            if self.move_e: com+= f" F{move_string}"
            if self.move_a or self.move_b or self.move_c or self.move_d or self.move_e:
                com+= f" U{move_string} "+suffix
                self._send_gcode(StringMashType.primary,com)

        if val == False:
            self._send_gcode(StringMashType.primary,f"M584 A0 B0 C0 D0 F0 U0 "+suffix)

    def _relax_motors(self, val):
        self._send_gcode(StringMashType.primary,f"M578 F{int(val)}")
        self._send_gcode(StringMashType.primary,f"M585 B{int(val)}")


    def _string_pull(self, val):

        if val == True:
            com = "M584 K1"
            
            if self.move_a: com+= f" A{int(val)}"
            if self.move_b: com+= f" B{int(val)}"
            if self.move_c: com+= f" C{int(val)}"
            if self.move_d: com+= f" D{int(val)}"
            if self.move_e: com+= f" F{int(val)}"
            if self.move_a or self.move_b or self.move_c or self.move_d or self.move_e:
                self._send_gcode(StringMashType.primary,com)

        if val == False:
            self._send_gcode(StringMashType.primary,f"M584 K0 A0 B0 C0 D0 F0")
        

    def _feed_pound(self, val):
        
        self._send_gcode(StringMashType.secondary,f"M585 X{int(val)}")

    def _karet_move_up(self, val):
        
        self._send_gcode(StringMashType.primary,f"M580 Z{int(val)} D1")

    def _karet_move_down(self, val):
        
        self._send_gcode(StringMashType.primary,f"M580 Z{int(val)} D-1")

    def _karet_home(self, val):
        self._send_gcode(StringMashType.primary,f"M587 I0 H")


    def _toggle_serial(self, state: bool) -> None:
        if state:
            self.connect_serial()
        else:
            pass
            #self.disconnect_serial()

    def _send_command(self,state):
        self._send_gcode(StringMashType.secondary,self.command_line.text())
        
    def connect_serial(self):
        #try:
            target_ip = '127.0.0.1'

            port_cam0 = 5000
            port_cam1 = 5001
            port_cam2 = 5002
            self.pos_thread_all = PosThreadAll(target_ip)
            self.pos_thread_all.cur_state.connect(self._update_state, QtCore.Qt.QueuedConnection)
            self.pos_thread_all.start()

            
            #device self "127.0.0.1"
            #device 10 "192.168.1.80"
            if CAMERAS_OPEN:
                self._start_camera(0,target_ip ,port_cam0)
                ##time.sleep(2)
                self._start_camera(1,target_ip ,port_cam1)
                #time.sleep(2)
                self._start_camera(2,target_ip ,port_cam2)


                self._set_monitor(0,0)
                self._set_monitor(1,1)
                self._set_monitor(2,2)

            """time.sleep(0.5)
            self._send_gcode(StringMashType.primary,f"M584 U W-1")
            self._send_gcode(StringMashType.primary,f"M584 U W-1")
            self._send_gcode(StringMashType.primary,f"M584 U W-1")"""
            
        #except Exception as e:
            #QtWidgets.QMessageBox.critical(self, "COM Error", str(e))
            #self.btn_conn.setChecked(False)
            #self._update_state(StringStatePrimary(""), 0)

    def disconnect_serial(self,args):
        self.pos_thread_all.stop()
        self.pos_thread_all.string_mash.close()
        QApplication.instance().quit()

    def _send_gcode(self,_string_mash_type:StringMashType, cmd: str) -> None: 
        #print(cmd)
        self.pos_thread_all.send_g_code(cmd)
        #time.sleep(1)
        #self.init_ui()

    # ---------------------- WIDGET HELPERS ----------------------
    def _big_button(self, text: str, checkable: bool=False, callback=None) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(text)
        btn.setCheckable(checkable)
        btn.setMinimumSize(BTN_W, BTN_H)
        btn.setFont(self.FONT)
        btn.setStyleSheet(
            "QPushButton{background:#3a3a3a;border:2px solid #666;border-radius:14px;}"
            "QPushButton:pressed{background:#4d4d4d;}"
            "QPushButton:checked{background:#00796b;}"
        )
        if callback:
            if checkable:
                btn.toggled.connect(callback)
            else:
                btn.clicked.connect(callback)
        return btn

    def _toggle_button(self, label: str, cmd_tpl, mash:StringMashType) -> QtWidgets.QPushButton:
        btn = self._big_button(f"{label}: выкл", checkable=True)
        def on_toggle(state: bool) -> None:
            btn.setText(f"{label}: {'вкл' if state else 'выкл'}")
            cmd = cmd_tpl.format(int(state)) if isinstance(cmd_tpl, str) else cmd_tpl(state)
            if state is False: 
                cmd = cmd.upper()
            self._send_gcode(mash,cmd)
        btn.toggled.connect(on_toggle)
        return btn

    def _big_momentary_button(self, text: str, callback=None) -> QtWidgets.QPushButton:
        """Создаёт кнопку без фиксации состояния, активный цвет – при нажатии."""
        btn = QtWidgets.QPushButton(text)
        btn.setCheckable(False)          # не переключается
        btn.setMinimumSize(BTN_W, BTN_H)
        btn.setFont(self.FONT)
        btn.setStyleSheet(
            "QPushButton{background:#3a3a3a;border:2px solid #666;border-radius:14px;}"
            "QPushButton:pressed{background:#00796b;}"   # цвет «включено»
        )
        if callback:
            # При нажатии – True, при отпускании – False
            btn.pressed.connect(lambda: callback(True))
            btn.released.connect(lambda: callback(False))
        return btn

    def _momentary_button_common_a(self, layout: QtWidgets.QLayout, label: str, callback) -> QtWidgets.QPushButton:
        """Создаёт кнопку с текстом, меняющимся при нажатии/отпускании."""
        btn = self._big_momentary_button(f"{label}: выкл")

        def on_pressed():
            btn.setText(f"{label}: вкл")
            callback(True)

        def on_released():
            btn.setText(f"{label}: выкл")
            callback(False)

        btn.pressed.connect(on_pressed)
        btn.released.connect(on_released)
        layout.addWidget(btn)
        return btn
    


    def _toggle_button_common(self, label: str, callback) -> QtWidgets.QPushButton:
        btn = self._big_button(f"{label}: выкл", checkable=True)
        def on_toggle(state: bool) -> None:
            btn.setText(f"{label}: {'вкл' if state else 'выкл'}")
            callback(state)
        btn.toggled.connect(on_toggle)
        return btn
    
    def _toggle_button_common_a(self,layout:QtWidgets.QLayout, label: str, callback) -> QtWidgets.QPushButton:
        btn = self._big_button(f"{label}: выкл", checkable=True)
        def on_toggle(state: bool) -> None:
            btn.setText(f"{label}: {'вкл' if state else 'выкл'}")
            callback(state)
        btn.toggled.connect(on_toggle)
        layout.addWidget(btn)
        return btn

    def _add_slider(self, layout, label: str, unit: str, mn: int, mx: int, val: int, callback, k_v:float = 1.0) -> None:
        lbl = QtWidgets.QLabel(f"{label}: {val} {unit}")
        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setRange(mn, mx)
        slider.setValue(val)
        slider.setFixedWidth(SLIDER_W)
        slider.setStyleSheet(
            "QSlider::groove:horizontal{height:20px;background:#555;border-radius:14px;}"
            "QSlider::handle:horizontal{width:50px;margin:0px 0;border-radius:30px;background:#e0e0e0;border:2px solid #888;}"
            "QSlider::sub-page:horizontal{background:#009688;border-radius:14px;}"
        )

        slider.valueChanged.connect(lambda v: (lbl.setText(f"{label}: {round(k_v*v,3)} {unit}"), callback(k_v*v)))

        #slider.valueChanged.connect(lambda v: (lbl.setText(f"{label}: {k_v*v} {unit}"), callback(v)))
        layout.addWidget(lbl)
        layout.addWidget(slider)
        return slider
    
    def _add_textbox_na(self, layout: QtWidgets.QLayout, val: float) -> None:
        """
        Добавляет в layout текстовое поле с подписью.
        При изменении текста (если он является числом) обновляет метку и вызывает callback.
        """

        # Текстовое поле
        textbox = QtWidgets.QTextEdit()
        textbox.setText(str(val))
        #textbox.setFixedWidth(400)
        #textbox.setFixedHeight(400)
        textbox.setAlignment(Qt.AlignCenter) 
        textbox.setStyleSheet(
            "QLineEdit {"
            "   background: #333;"
            "   color: white;"
            "   border: 1px solid #555;"
            "   border-radius: 4px;"
            "   padding: 4px;"
            "}"
        )

        layout.addWidget(textbox)

        return textbox 

    def _add_slider_na(self,layout:QtWidgets.QLayout,label: str, unit: str, mn: int, mx: int, val: int, callback, k_v:float = 1.0) -> SliderLabel:
            lbl = QtWidgets.QLabel(f"{label}: {val} {unit}")
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setRange(mn, mx)
            slider.setValue(val)
            slider.setFixedWidth(SLIDER_W)
            slider.setStyleSheet(
                "QSlider::groove:horizontal{height:20px;background:#555;border-radius:14px;}"
                "QSlider::handle:horizontal{width:50px;margin:0px 0;border-radius:30px;background:#e0e0e0;border:2px solid #888;}"
                "QSlider::sub-page:horizontal{background:#009688;border-radius:14px;}"
            )
    
            slider.valueChanged.connect(lambda v: (lbl.setText(f"{label}: {round(k_v*v,3)} {unit}"), callback(k_v*v)))
            layout.addWidget(lbl)
            layout.addWidget(slider)
            return SliderLabel(slider,lbl,k_v)

    def disconnect_tcp(self):
        
        pass
    def closeEvent(self, event):
        
        pass
        #self.disconnect_serial()

    

def process_exists_windows(process_name):
    # Use tasklist command and capture output
    progs = str(subprocess.check_output('tasklist'))
    if process_name in progs:
        return True
    else:
        return False

# ──────────────────────── MAIN BLOCK ────────────────────────
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #gui = MainGUI()
    #gui.show()
    """if not process_exists_windows('tcp_to_udp.exe'):
        proc = subprocess.Popen("serv\\tcp_to_udp.exe")
        time.sleep(0.5)"""
    dialog = StringGUI()
    #dialog.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowType_Mask)
    dialog.show()
    #dialog.showFullScreen()

    sys.exit(app.exec_())



