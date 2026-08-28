import socket
import sys
import time
import serial
import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit,
    QInputDialog, QApplication,QSlider)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPolygon
from PyQt5.QtCore import (pyqtProperty, pyqtSignal, pyqtSlot, QPoint, QSize,
        Qt, QTime, QTimer)

#from Devices.TensMash import TensMash
#from Devices.StringMash import PrinterMash
#from Devices.TensSens import TensSens

class CameraThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(QPixmap)
    def __init__(self, ind_cam:str, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.i= ind_cam
    def run(self):
            
        cap = cv2.VideoCapture(self.i, cv2.CAP_DSHOW)
        #640 480  1920 1080
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        while (cap.isOpened()):
            ret, frame = cap.read()
            if not ret:
                break   
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)          
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)     
            pix = QPixmap.fromImage(img)
            
            self.mysignal.emit(pix)  

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()

class App(QtWidgets.QWidget):
    def __init__(self, parent=None):
        # Передаём ссылку на родительский элемент и чтобы виджет
        # отображался как самостоятельное окно указываем тип окна
        super().__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle("Printhead")
        self.comport=["COM1", "COM2", "COM3", "COM4", "COM5", "COM6","COM7","COM8","COM9","COM10","COM11","COM12"]
        self.resize(1024, 1200)
        self.stringmash:PrinterMash = None
        
        self.build()
    def build(self):
        self.obrsleva=0
        self.obrsprava=0
        self.obrsverxy=0
        self.obrsnuzy=0
        self.but1 = QtWidgets.QPushButton('Подключиться', self)
        self.but1.setGeometry(QtCore.QRect(830, 20, 120, 40))
        #self.but1.clicked.connect(self.op)

        

        self.but3 = QtWidgets.QPushButton('Отключиться', self)
        self.but3.setGeometry(QtCore.QRect(830, 70, 120, 40))
        self.but3.clicked.connect(self.close)
        #-------------------------------

        self.but4 = QtWidgets.QPushButton('Включить насосы', self)
        self.but4.setGeometry(QtCore.QRect(100, 620, 120, 40))
        #self.but4.clicked.connect(self.close)

        self.but5 = QtWidgets.QPushButton('Напечатать сфероид', self)
        self.but5.setGeometry(QtCore.QRect(250, 620, 120, 40))
        #self.but5.clicked.connect(self.close)

        self.but6 = QtWidgets.QPushButton('Калибровка', self)
        self.but6.setGeometry(QtCore.QRect(400, 620, 120, 40))
        #self.but6.clicked.connect(self.close)

        self.but7 = QtWidgets.QPushButton('Выдвинуть поршень', self)
        self.but7.setGeometry(QtCore.QRect(550, 620, 120, 40))
        #self.but7.clicked.connect(self.close)

        

        self.butk = QtWidgets.QPushButton('Обрезать края', self)
        self.butk.setGeometry(QtCore.QRect(620, 20, 120, 40))
        self.butk.clicked.connect(self.kameraobr)

        self.link1 = QtWidgets.QLineEdit(self)
        self.link1.setGeometry(QtCore.QRect(120, 20, 80, 40))

        self.link2 = QtWidgets.QLineEdit(self)
        self.link2.setGeometry(QtCore.QRect(220, 20, 80, 40))

        self.link3 = QtWidgets.QLineEdit(self)
        self.link3.setGeometry(QtCore.QRect(320, 20, 80, 40))

        self.link4 = QtWidgets.QLineEdit(self)
        self.link4.setGeometry(QtCore.QRect(420, 20, 80, 40))

        
        self.lin1 = QtWidgets.QLineEdit(self)
        self.lin1.setGeometry(QtCore.QRect(930, 220, 120, 40))
        
        self.lin2 = QtWidgets.QLineEdit(self)
        self.lin2.setGeometry(QtCore.QRect(930, 320, 120, 40))

        self.lin3 = QtWidgets.QLineEdit(self)
        self.lin3.setGeometry(QtCore.QRect(930, 420, 120, 40))

        self.label1 = QtWidgets.QLabel(self)
        self.label1.setGeometry(QtCore.QRect(980, 16, 236, 50))
        self.label1.setText('Не подключено')

        self.label_cam1 = QtWidgets.QLabel(self)
        self.label_cam1.setGeometry(QtCore.QRect(100, 100, 640, 480))
        
        self.label_cam2 = QtWidgets.QLabel(self)
        self.label_cam2.setGeometry(QtCore.QRect(100, 600, 640, 480))

        self.label3 = QtWidgets.QLabel(self)
        self.label3.setGeometry(QtCore.QRect(830, 216, 236, 50))
        self.label3.setText('Объём вверх')

        self.label3 = QtWidgets.QLabel(self)
        self.label3.setGeometry(QtCore.QRect(830, 316, 236, 50))
        self.label3.setText('Объём вниз')

        self.label3 = QtWidgets.QLabel(self)
        self.label3.setGeometry(QtCore.QRect(830, 416, 236, 50))
        self.label3.setText('Время цикла')
        
        #self.thread_cam1 = CameraThread(2)
        #self.thread_cam1.mysignal.connect(self.cam1_sign, QtCore.Qt.QueuedConnection)
        #self.thread_cam1.start()
        #cam_dev = r'@device:pnp:\\?\usb#USB#VID_09DA&PID_2695&MI_00#7&26DAA0E0&3&0000#{65E8773D-8F56-11D0-A3B9-00A0C9223196}'
        cam_dev = 1
        self.thread_cam2 = CameraThread(cam_dev)
        self.thread_cam2.mysignal.connect(self.cam2_sign, QtCore.Qt.QueuedConnection)
        self.thread_cam2.start()
    def kameraobr(self):
        try:
            if self.link1.text()=='':
                self.link1.setText('0')
            if self.link2.text()=='':
                self.link2.setText('0')
            if self.link3.text()=='':
                self.link3.setText('0')
            if self.link4.text()=='':
                self.link4.setText('0')
            self.obrsleva=6.4*int(self.link1.text())
            self.obrsprava=6.4*int(self.link2.text())
            self.obrsverxy=4.8*int(self.link3.text())
            self.obrsnuzy=4.8*int(self.link4.text())
        except BaseException:
            pass
    def cam1_sign(self, pix):
        self.label_cam1.setPixmap(pix)  
    def cam2_sign(self, pix):
        self.label_cam2.setPixmap(pix)  
    
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
