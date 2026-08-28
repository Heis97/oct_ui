import sys
import cv2
import numpy as np
import serial
import serial.tools.list_ports as ports
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QImage

"""
Stable GUI version (confirmed working):
 • Camera fixed at 640×480, QLabel same size – no scaling artefacts.
 • Diameter detection = largest contour → min(width, height) of minAreaRect.
 • Titles «Параметры / Действия» fully visible.
 • COM @115200, basic M-codes bound to sliders / toggles.
 • Requires: PyQt5, opencv-python, numpy, pyserial.
"""

CAM_W, CAM_H = 640, 480            # requested capture size & QLabel
MM_PER_PX    = 0.05                # calibrate once!
FPS_DELAY    = 33                  # ms between frames (~30 fps)

# ──────────────────────────────────────────────────────────────────────
class CamThread(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(QPixmap, float)  # QPixmap, diameter_mm

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        while not self.isInterruptionRequested():
            ok, frame = cap.read()
            if not ok:
                break
            d_mm = self._detect(frame)
            rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, CAM_W, CAM_H, rgb.strides[0], QImage.Format_RGB888)
            self.frame_ready.emit(QPixmap.fromImage(qimg), d_mm)
            self.msleep(FPS_DELAY)
        cap.release()

    def _detect(self, img: np.ndarray) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return -1.0
        cnt = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(cnt) < 200:
            return -1.0
        (_, _), (w, h), _ = cv2.minAreaRect(cnt)
        return min(w, h) * MM_PER_PX

# ──────────────────────────────────────────────────────────────────────
class GUI(QtWidgets.QWidget):
    FONT = QFont("Arial", 15)
    BTN_W, BTN_H = 300, 70
    SLIDER_W = 420

    def __init__(self):
        super().__init__(None, QtCore.Qt.Window)
        self.setWindowTitle("Printhead Controller – Stable")
        self.resize(1054, 700)
        self.ser = None
        self._style(); self._build(); self._start_cam()

    # ── style ──
    def _style(self):
        self.setStyleSheet(
            "QWidget{background:#2b2b2b;color:#eee;} QLabel{font:15px Arial;}"+
            "QGroupBox{font:16px Arial;border:1px solid #777;margin-top:30px;}"+
            "QGroupBox::title{left:15px;top:-14px;padding:0 6px;background:#2b2b2b;}"+
            "QTabBar::tab{min-width:220px;padding:14px 36px;font:16px Arial;background:#3b3b3b;border:0;}"+
            "QTabBar::tab:selected{background:#505050;}" )

    # ── UI ──
    def _build(self):
        tabs = QtWidgets.QTabWidget(self); tabs.tabBar().setExpanding(True)
        QtWidgets.QVBoxLayout(self).addWidget(tabs)

        # Camera tab
        tcam = QtWidgets.QWidget(); tabs.addTab(tcam, "Камера")
        vcam = QtWidgets.QVBoxLayout(tcam); vcam.setAlignment(Qt.AlignCenter)
        self.img_lbl = QtWidgets.QLabel(); self.img_lbl.setFixedSize(CAM_W, CAM_H)
        self.img_lbl.setStyleSheet("background:#000;border:2px solid #444;")
        self.diam_lbl= QtWidgets.QLabel("Толщина нити: -- мм"); self.diam_lbl.setAlignment(Qt.AlignCenter)
        vcam.addWidget(self.img_lbl); vcam.addWidget(self.diam_lbl)

        # Control tab
        tctl = QtWidgets.QWidget(); tabs.addTab(tctl, "Управление")
        h = QtWidgets.QHBoxLayout(tctl); h.setSpacing(26); h.setContentsMargins(25,25,25,25)

        # parameters
        gpar = QtWidgets.QGroupBox("Параметры"); h.addWidget(gpar)
        vpar = QtWidgets.QVBoxLayout(gpar)
        self._slider(vpar, "Температура", "°C", 20, 200, 37, lambda v:self._g(f"M579 S{v}"))
        self._slider(vpar, "Давление",   "kPa",0,300,50, lambda v:self._g(f"M578 P{v}"))
        self._slider(vpar, "Скорость",   "мм/с",0,120,20,lambda v:self._g(f"M576 S{v}"))
        self._slider(vpar, "Шлюз",       "об/мин",0,10,0,lambda v:self._g(f"M578 G{v}"))
        vpar.addStretch()

        # actions
        gact = QtWidgets.QGroupBox("Действия"); h.addWidget(gact)
        vact = QtWidgets.QVBoxLayout(gact)
        # COM
        row = QtWidgets.QHBoxLayout(); vact.addLayout(row)
        row.addWidget(QtWidgets.QLabel("Порт:"))
        self.cmb = QtWidgets.QComboBox(); [self.cmb.addItem(p.device) for p in ports.comports()]; self.cmb.setFixedWidth(160)
        row.addWidget(self.cmb)
        self.bconn = self._btn("Подключиться", True); self.bconn.toggled.connect(self._toggle_serial); row.addWidget(self.bconn); row.addStretch()

        self.bhv  = self._toggle("Высокое напряжение",   "M577 S{}")
        self.bps  = self._toggle("Давление",             "M578 V{}")
        self.bfan = self._toggle("Вентилятор",           "M580 S{}")
        self.bz   = self._btn("Сброс длины нити"); self.bz.clicked.connect(lambda:self._g("G92 E0"))
        self.bmv  = self._btn("Движение нити"); self.bmv.clicked.connect(lambda:self._g("G1 E50 F1200"))
        self.brec = self._toggle("Рекуперация",          lambda s: "M106" if s else "M107")
        for w in [self.bhv,self.bps,self.bfan,self.bz,self.bmv,self.brec]: vact.addWidget(w)
        vact.addStretch()

    # ── helpers ──
    def _btn(self,text,toggle=False):
        b=QtWidgets.QPushButton(text); b.setCheckable(toggle); b.setMinimumSize(self.BTN_W,self.BTN_H); b.setFont(self.FONT)
        b.setStyleSheet("QPushButton{background:#3a3a3a;border:1px solid #666;border-radius:7px;} QPushButton:pressed{background:#4d4d4d;} QPushButton:checked{background:#00695c;}")
        return b
    def _toggle(self,label,cmd_tpl):
        b=self._btn(f"{label}: выкл",True)
        def h(s):
            b.setText(f"{label}: {'вкл' if s else 'выкл'}");
            c=cmd_tpl.format(int(s)) if isinstance(cmd_tpl,str) else cmd_tpl(s); self._g(c)
        b.toggled.connect(h); return b
    def _slider(self,lbl,cap,unit,mn,mx,init,cb):
        lab=QtWidgets.QLabel(f"{cap}: {init} {unit}"); lbl.addWidget(lab)
        sl=QtWidgets.QSlider(Qt.Horizontal); sl.setRange(mn,mx); sl.setValue(init); sl.setFixedWidth(self.SLIDER_W)
        sl.setStyleSheet("QSlider::groove:horizontal{height:18px;background:#555;border-radius:9px;} QSlider::handle:horizontal{width:36px;margin:-14px 0;border-radius:18px;background:#e0e0e0;border:1px solid #888;} QSlider::sub-page:horizontal{background:#009688;border-radius:9px;}")
        sl.valueChanged.connect(lambda v:(lab.setText(f"{cap}: {v} {unit}"),cb(v)))
        lbl.addWidget(sl)

    # ── serial & gcode ──
    def _toggle_serial(self,state):
        if state:
            try:
                self.ser=serial.Serial(self.cmb.currentText(),115200,timeout=2); self.bconn.setText("Отключиться")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self,"COM",str(e)); self.bconn.setChecked(False)
        else:
            if self.ser and self.ser.is_open: self.ser.close(); self.ser=None; self.bconn.setText("Подключиться")
    def _g(self,cmd):
        if self.ser and self.ser.is_open:
            try:self.ser.write((cmd+"\n").encode())
            except Exception as e: QtWidgets.QMessageBox.warning(self,"G-code",str(e))

    # ── camera ──
    def _start_cam(self):
        self.ct=CamThread(); self.ct.frame