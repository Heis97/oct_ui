"""printhead_gui.py  —  Improved diameter detection & clean camera thread teardown
=================================================================
Touch-friendly control panel for a filament print-head (BTT Octopus, Marlin 2.1.2.5).

Install:
    pip install pyqt5 opencv-python numpy pyserial
Run:
    python printhead_gui.py
"""
import sys
import cv2
import numpy as np
import serial
import serial.tools.list_ports as ports
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPixmap

# Constants
CAM_W, CAM_H = 640, 480
FPS_DELAY    = 33
PX2MM        = 0.05
BTN_W, BTN_H = 300, 68
SLIDER_W     = 420

class CameraThread(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(QPixmap, float)

    def __init__(self, index: int = 0) -> None:
        super().__init__()
        self.index = index

    def run(self) -> None:
        cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            blank = QPixmap(CAM_W, CAM_H)
            blank.fill(Qt.black)
            while not self.isInterruptionRequested():
                self.frame_ready.emit(blank, -1.0)
                self.msleep(1000)
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        while not self.isInterruptionRequested():
            ret, frame = cap.read()
            if not ret:
                break
            dia = self._estimate_diameter(frame)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(rgb.data, CAM_W, CAM_H, rgb.strides[0], QImage.Format_RGB888)
            self.frame_ready.emit(QPixmap.fromImage(img), dia)
            self.msleep(FPS_DELAY)
        cap.release()

    @staticmethod
    def _estimate_diameter(frame: np.ndarray) -> float:
        """
        Точный подсчёт диаметра нити:
        1. Берём 100-px полосу вокруг середины кадра.
        2. Блюр + Canny → карта границ.
        3. Для каждой строки ищем первую и последнюю ненулевую точку
           (левый и правый край нити) → ширина строки.
        4. Убираем выбросы по правилу 2.5·MAD.
        5. Средняя оставшихся ширин * PX_TO_MM → диаметр в мм.
        """
        # ---------------- ROI & пре-обработка ----------------
        roi = frame[CAM_H // 2 - 50: CAM_H // 2 + 50]          # 100-px вертикальное окно
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 30, 100)

        # ---------------- поиск краёв построчно ---------------
        widths = []
        for row in edges:                                       # перебираем строки ROI
            xs = np.flatnonzero(row)
            if xs.size >= 2:
                widths.append(xs[-1] - xs[0])                  # первый и последний индекс

        if not widths:
            return -1.0                                         # нет уверенных краёв

        # ---------------- фильтр выбросов ---------------------
        w = np.asarray(widths, dtype=np.float32)
        med = np.median(w)
        mad = np.median(np.abs(w - med)) or 1.0                # защита от деления на 0
        good = w[np.abs(w - med) < 2.5 * mad]                  # 2.5*MAD ≈ 99% доверия
        if good.size == 0:
            return -1.0

        width_px = good.mean()                                  # можно взять median(good) для ещё большей робастности
        return width_px * PX_TO_MM


class MainGUI(QtWidgets.QWidget):
    FONT = QFont("Arial", 15)

    def __init__(self) -> None:
        super().__init__(None, QtCore.Qt.Window)
        self.setWindowTitle("Printhead Controller – Touch UI")
        self.resize(1054,700)
        self.serial: serial.Serial|None = None
        self._apply_style()
        self._build_ui()
        self._start_camera()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            "QWidget{background:#2b2b2b;color:#eee;}"+
            "QLabel{font:15px Arial;}"+
            "QGroupBox{font:16px Arial;border:1px solid #777;margin-top:30px;}"+
            "QGroupBox::title{left:15px;top:-14px;padding:0 6px;background:#2b2b2b;}"+
            "QTabBar::tab{min-width:220px;padding:14px 36px;font:16px Arial;background:#3b3b3b;border:0;}"+
            "QTabBar::tab:selected{background:#505050;}"
        )

    def _build_ui(self) -> None:
        tabs = QtWidgets.QTabWidget(self)
        tabs.tabBar().setExpanding(True)
        QtWidgets.QVBoxLayout(self).addWidget(tabs)
        # Camera Tab
        tab_cam = QtWidgets.QWidget(); tabs.addTab(tab_cam,"Камера")
        vcam = QtWidgets.QVBoxLayout(tab_cam); vcam.setAlignment(Qt.AlignCenter)
        self.lbl_img = QtWidgets.QLabel(); self.lbl_img.setFixedSize(CAM_W,CAM_H)
        self.lbl_img.setStyleSheet("background:#000;border:2px solid #444;")
        self.lbl_dia = QtWidgets.QLabel("Диаметр: -- мм"); self.lbl_dia.setAlignment(Qt.AlignCenter)
        vcam.addWidget(self.lbl_img); vcam.addWidget(self.lbl_dia)
        # Control Tab
        tab_ctl = QtWidgets.QWidget(); tabs.addTab(tab_ctl,"Управление")
        h = QtWidgets.QHBoxLayout(tab_ctl); h.setSpacing(28); h.setContentsMargins(25,25,25,25)
        # Params
        grp_p = QtWidgets.QGroupBox("Параметры"); h.addWidget(grp_p)
        vp = QtWidgets.QVBoxLayout(grp_p); vp.setSpacing(24)
        for lbl,unit,mn,mx,val,code in [
            ("Температура","°C",20,200,37,"M579 S{}"),
            ("Давление","kPa",0,300,50,"M578 P{}"),
            ("Скорость","мм/с",0,120,20,"M576 S{}"),
            ("Шлюз","об/мин",0,10,0,"M578 G{}")]:
            self._add_slider(vp,lbl,unit,mn,mx,val,lambda v,c=code:self._send_gcode(c.format(v)))
        vp.addStretch()
        # Actions
        grp_a = QtWidgets.QGroupBox("Действия"); h.addWidget(grp_a)
        va = QtWidgets.QVBoxLayout(grp_a); va.setSpacing(22)
        row = QtWidgets.QHBoxLayout(); va.addLayout(row)
        row.addWidget(QtWidgets.QLabel("Порт:"))
        self.cmb = QtWidgets.QComboBox(); [self.cmb.addItem(p.device) for p in ports.comports()]; self.cmb.setFixedWidth(160)
        row.addWidget(self.cmb)
        self.btn_conn=self._big_btn("Подключиться",True,self._toggle_serial); row.addWidget(self.btn_conn); row.addStretch()
        for lbl,code in [("Высокое напряжение","M577 S{}"),("Давление","M578 V{}"),("Вентилятор","M580 S{}")]:
            va.addWidget(self._toggle_btn(lbl,code))
        va.addWidget(self._big_btn("Сброс длины нити",False,lambda:self._send_gcode("G92 E0")))
        va.addWidget(self._big_btn("Движение нити",False,lambda:self._send_gcode("G1 E50 F1200")))
        va.addWidget(self._toggle_btn("Рекуперация",lambda s:"M106" if s else "M107"))
        va.addStretch()

    def _start_camera(self) -> None:
        self.cam_thread = CameraThread(0)
        self.cam_thread.frame_ready.connect(self._update_frame,QtCore.Qt.QueuedConnection)
        self.cam_thread.start()

    def closeEvent(self,event) -> None:
        if hasattr(self,'cam_thread') and self.cam_thread.isRunning():
            self.cam_thread.requestInterruption(); self.cam_thread.wait()
        super().closeEvent(event)

    def _update_frame(self,pix:QPixmap,dia:float) -> None:
        self.lbl_img.setPixmap(pix)
        self.lbl_dia.setText(f"Диаметр: {dia:.1f} мм" if dia>=0 else "Диаметр: -- мм")

    def _toggle_serial(self,state:bool) -> None:
        if state:
            try: self.serial=serial.Serial(self.cmb.currentText(),115200,timeout=2); self.btn_conn.setText("Отключиться")
            except Exception as e: QtWidgets.QMessageBox.critical(self,"COM Error",str(e)); self.btn_conn.setChecked(False)
        else:
            if self.serial and self.serial.is_open: self.serial.close()
            self.serial=None; self.btn_conn.setText("Подключиться")

    def _send_gcode(self,cmd:str) -> None:
        if self.serial and self.serial.is_open:
            try: self.serial.write((cmd+"\n").encode())
            except Exception as e: QtWidgets.QMessageBox.warning(self,"G-code Error",str(e))

    def _big_btn(self,text:str,chk:bool=False,cb=None):
        b=QtWidgets.QPushButton(text); b.setCheckable(chk); b.setMinimumSize(BTN_W,BTN_H); b.setFont(QFont("Arial",15))
        b.setStyleSheet("QPushButton{background:#3a3a3a;border:1px solid #666;border-radius:7px;} QPushButton:pressed{background:#4d4d4d;} QPushButton:checked{background:#00796b;}")
        if cb: (b.toggled.connect(cb) if chk else b.clicked.connect(cb))
        return b

    def _toggle_btn(self, label, code_tpl) -> QtWidgets.QPushButton:
        # Creates a toggle button that sends a G-code on state change
        btn = self._big_btn(f"{label}: выкл", True)
        # Handler uses closure variables label, btn, code_tpl
        def handler(state, label=label, btn=btn, tpl=code_tpl):
            # Update button text
            btn.setText(f"{label}: {'вкл' if state else 'выкл'}")
            # Format command and send
            cmd = tpl.format(int(state)) if isinstance(tpl, str) else tpl(state)
            self._send_gcode(cmd)
        btn.toggled.connect(handler)
        return btn

    def _add_slider(self,lay,label,unit,mn,mx,val,cb):
        l=QtWidgets.QLabel(f"{label}: {val} {unit}"); s=QtWidgets.QSlider(Qt.Horizontal)
        s.setRange(mn,mx); s.setValue(val); s.setFixedWidth(SLIDER_W)
        s.setStyleSheet("QSlider::groove:horizontal{height:18px;background:#555;border-radius:9px;} QSlider::handle:horizontal{width:36px;margin:-14px 0;border-radius:18px;background:#e0e0e0;border:1px solid #888;} QSlider::sub-page:horizontal{background:#009688;border-radius:9px;}")
        s.valueChanged.connect(lambda v:(l.setText(f"{label}: {v} {unit}"), cb(v)))
        lay.addWidget(l); lay.addWidget(s)

if __name__=="__main__":
    app=QtWidgets.QApplication(sys.argv);
    gui=MainGUI(); gui.show(); sys.exit(app.exec_())
