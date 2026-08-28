from time import sleep
import serial
import sys
from PyQt5 import QtCore,  QtWidgets
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import ( QPoint, QSize,Qt)
import gc
from Util.TensEnum import WaveForm
from Devices.TensMash import TensMash
from Devices.StringMash import PrinterMash
from Devices.TensSens import TensSens





class TensApp(QtWidgets.QWidget):

    def __init__(self, parent=None):
        # Передаём ссылку на родительский элемент и чтобы виджет
        # отображался как самостоятельное окно указываем тип окна
        super().__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle("Отправка на Fishman")
        self.comport=["COM1", "COM2", "COM3", "COM4", "COM5", "COM6","COM7","COM8","COM9","COM10","COM11","COM12"]
        self.cyctypes=["triangle","sinus","meandr"]
        self.bauds=["250000","9600", "57600", "115200"]
        self.zValues = [10,1,0.1,0.01,0.001,-0.001,-0.01,-0.1,-1,-10]
        self.tens_mash:TensMash =  None
        self.force_mash:PrinterMash = None
        self.force_sens:TensSens = None
        self.openPorts =[]
        self.baud = 250000
        self.resize(1750, 800)
        self.build()  
        self.checkPorts()   
        self.countdelim = 0
        self.coords:"list[list[float]]" = []

        self.initSens()
    
    def build(self):


        self.but_force = QtWidgets.QPushButton('Включить давление', self)
        self.but_force.setGeometry(QtCore.QRect(520, 190, 140, 30))
        self.but_force.clicked.connect(self.startForce)

        self.but_Cycleforce = QtWidgets.QPushButton('Включить цикл', self)
        self.but_Cycleforce.setGeometry(QtCore.QRect(520, 130, 140, 30))
        self.but_Cycleforce.clicked.connect(self.startCycleForm)

        self.but_stopforce = QtWidgets.QPushButton('Остановить цикл', self)
        self.but_stopforce.setGeometry(QtCore.QRect(520, 100, 140, 30))
        self.but_stopforce.clicked.connect(self.stopCycle)

        self.but_stopforce = QtWidgets.QPushButton('Относ', self)
        self.but_stopforce.setGeometry(QtCore.QRect(520, 160, 140, 30))
        self.but_stopforce.clicked.connect(self.setRel)

        self.but_savetxt = QtWidgets.QPushButton('Сохранить координаты', self)
        self.but_savetxt.setGeometry(QtCore.QRect(520, 70, 140, 30))
        self.but_savetxt.clicked.connect(self.saveCoords)

        self.but3 = QtWidgets.QPushButton('Найти порты', self)
        self.but3.setGeometry(QtCore.QRect(30, 170, 120, 40))
        self.but3.clicked.connect(self.checkPorts)

        self.lines_axis:list[QLineEdit]=[]

        self.lin_force = QtWidgets.QLineEdit(self)
        self.lin_force.setGeometry(QtCore.QRect(520, 220, 140, 30))
        self.lin_force.setText("0")

        self.lin_in = QtWidgets.QLineEdit(self)
        self.lin_in.setGeometry(QtCore.QRect(30, 220, 250, 30))
        
        self.lin_out = QtWidgets.QLineEdit(self)
        self.lin_out.setGeometry(QtCore.QRect(30, 270, 420, 30))

        self.lin_out = QtWidgets.QLineEdit(self)
        self.lin_out.setGeometry(QtCore.QRect(30, 270, 420, 30))

        self.lin3 = QtWidgets.QLineEdit(self)
        self.lin3.setGeometry(QtCore.QRect(30, 320, 120, 30))

        self.tex_out = QtWidgets.QTextEdit(self)
        self.tex_out.setGeometry(QtCore.QRect(30, 320, 620, 800))
        self.tex_out.setVisible(False)

        self.tex_out2 = QtWidgets.QTextEdit(self)
        self.tex_out2.setGeometry(QtCore.QRect(360, 320, 620, 800))
        self.tex_out2.setVisible(False)

        self.label1 = QtWidgets.QLabel(self)
        self.label1.setGeometry(QtCore.QRect(350, 16, 236, 50))
        self.label1.setText('Не подключено')

        self.label1 = QtWidgets.QLabel(self)
        self.label1.setGeometry(QtCore.QRect(300, 36, 236, 50))
        self.label1.setText('Циклическая нагрузка')

        self.label1 = QtWidgets.QLabel(self)
        self.label1.setGeometry(QtCore.QRect(300, 70-4, 236, 50))
        self.label1.setText(' Максимальная сила')

        self.label1 = QtWidgets.QLabel(self)
        self.label1.setGeometry(QtCore.QRect(300, 100-4, 236, 50))
        self.label1.setText('Время цикла')
        
        self.label1 = QtWidgets.QLabel(self)
        self.label1.setGeometry(QtCore.QRect(300, 130-4, 236, 50))
        self.label1.setText('Время релаксации')

        self.lin_cycl_force = QtWidgets.QLineEdit(self)
        self.lin_cycl_force.setGeometry(QtCore.QRect(450, 80, 60, 20))
        self.lin_cycl_force.setText("500")

        self.lin_cycl_timeF = QtWidgets.QLineEdit(self)
        self.lin_cycl_timeF.setGeometry(QtCore.QRect(450, 110, 60, 20))
        self.lin_cycl_timeF.setText("20")

        self.lin_cycl_timeR = QtWidgets.QLineEdit(self)
        self.lin_cycl_timeR.setGeometry(QtCore.QRect(450, 140, 60, 20))
        self.lin_cycl_timeR.setText("1")      



        self.cBauds_printer = QtWidgets.QComboBox(self)
        self.cBauds_printer.setGeometry(QtCore.QRect(0, 70, 120, 30))
        self.cBauds_printer.addItems(self.bauds)
        self.cBauds_printer.setCurrentText = self.cBauds_printer.itemText(-1)

        self.cBauds_sens = QtWidgets.QComboBox(self)
        self.cBauds_sens.setGeometry(QtCore.QRect(160, 70, 120, 30))
        self.cBauds_sens.addItems(self.bauds)
        self.cBauds_sens.setCurrentText = self.cBauds_sens.itemText(-1)
        #self.cBauds.activated[str].connect(self.onChBauds) 

        self.cPorts_printer = QtWidgets.QComboBox(self)
        self.cPorts_printer.setGeometry(QtCore.QRect(0, 120, 120, 30))
        self.cPorts_printer.addItems(self.comport)
        self.cPorts_printer.setCurrentText = self.cPorts_printer.itemText(-1)

        self.cPorts_sens = QtWidgets.QComboBox(self)
        self.cPorts_sens.setGeometry(QtCore.QRect(160, 120, 120, 30))
        self.cPorts_sens.addItems(self.comport)
        self.cPorts_sens.setCurrentText = self.cPorts_sens.itemText(-1)

        self.cCycTp = QtWidgets.QComboBox(self)
        self.cCycTp.setGeometry(QtCore.QRect(360, 20, 120, 30))
        self.cCycTp.addItems(self.cyctypes)
        self.cCycTp.setCurrentText = self.cCycTp.itemText(-1)

        self.moveButtons(QPoint(700,20),QSize(120,30),self.zValues,"Z")

    def initSens(self):
        self.cPorts_sens.setCurrentIndex(1)
        
        self.cPorts_printer.setCurrentIndex(0)
        self.open_tens()
        print("ready")
    
    def sendGcom(self):
        but:QtWidgets.QPushButton = self.sender()
        self.tens_mash.move(float(but.accessibleName()))

    def moveButtons(self, startpoint: QPoint, butsize:QSize, values:"list[float]",axis:str):
        axis_vel = QtWidgets.QLineEdit(self)
        axis_vel.setGeometry(QtCore.QRect(startpoint, butsize))
        axis_vel.setAccessibleName(axis)
        axis_vel.setText("100")
        self.lines_axis.append(axis_vel)
        startpoint.setY(startpoint.y()+butsize.height())       

        for i in range(len(values)):
            but = QtWidgets.QPushButton(axis+str(values[i]), self)
            but.setGeometry(QtCore.QRect(startpoint, butsize))
            startpoint.setY(startpoint.y()+butsize.height())
            but.setAccessibleName(str(values[i]))
            but.clicked.connect(self.sendGcom)

    def getVelAxis(self,axis:str):
        line = self.takeLine(axis)
        vel = ""
        if line!=None:
            vel = line.text()
        return vel

    def takeLine(self,axis:str):
        if len(self.lines_axis)>0:
            for i in range(len(self.lines_axis)):
                if self.lines_axis[i].accessibleName()==axis:
                    return self.lines_axis[i]
        return None


#----------------------------------------------
    def curPort_printer(self)->str:
        print("printer "+self.cPorts_printer.currentText())
        return self.cPorts_printer.currentText()

    def curBaud_printer(self)->int:
        return int(self.cBauds_printer.currentText())

    def curPort_sens(self)->str:
        return self.cPorts_sens.currentText()

    def curBaud_sens(self)->int:
        return int(self.cBauds_sens.currentText())

    def curCycleType(self)->WaveForm:
        return WaveForm(self.cCycTp.currentIndex())

    def checkPorts(self):
        self.cPorts_printer.clear()
        self.cPorts_sens.clear()
        self.comport = []
        for i in range(10):
            try:
                port = "COM"+str(i)
                ser = serial.Serial( port,int(self.baud))
                self.comport.append(port)
                ser.close()
            except BaseException:
                pass
        self.cPorts_printer.addItems(self.comport)
        self.cPorts_sens.addItems(self.comport)
    
    def open_tens(self):
        printer = PrinterMash(self.curPort_printer(), int(self.curBaud_printer()))
        sleep(0.5)
        sensor = TensSens(self.curPort_sens(), int(self.curBaud_sens()))
        self.tens_mash = TensMash(printer,sensor)
        if self.tens_mash!=None:
            print("open_tensom")

#----------------------------------------------
    def startCycleForm(self):
        try:
            fmax = float(self.lin_cycl_force.text())
            time_f = 1000*float(self.lin_cycl_timeF.text())
            time_r = 1000*float(self.lin_cycl_timeR.text())
            self.tens_mash.startCycle(fmax,time_f,time_r, self.curCycleType())
        except BaseException:
            print("parse error")

    def stopCycle(self):
        try:
            self.tens_mash.stopCycle()
        except BaseException:
            print("tens_mash not exist")

    def startForce(self):
        try:
            self.tens_mash.startForce(float(self.lin_force.text()))
            print("force started "+self.lin_force.text())
        except BaseException:
            print("tens_mash not exist")

    def stopForce(self):
        try:
            self.tens_mash.stopForce()
        except BaseException:
            print("tens_mash not exist")

    def setRel(self):
        self.tens_mash.force_mash.setRelP()

#----------------------------------------------
    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        #print("1")
        qp.setRenderHint(QPainter.Antialiasing)
        try:
            self.drawLines(qp)
            self.update()
        except BaseException:
            print("paint err")

    def saveCoords(self):
        f = open("coords.txt",'w')
        f.write("#___t_ms_____f_gr______________\n")
        for i in range(len(self.coords)):
            f.write(str(round(self.coords[i][0],3))+" "+str(self.coords[i][1])+"\n")

    def drawLines(self, qp:QPainter):
        gc.collect()
        pen = QPen(Qt.blue, 1, Qt.SolidLine)
        qp.setPen(pen)
        #print(str(self.koord_2))
        if self.tens_mash!=None:
            paint_koords:"list[list[float]]" = self.tens_mash.coords
        
        Xmin=100000000000000
        Ymin=100000000000000
        Xmax=-100000000000000
        Ymax=-100000000000000
        Xq1=700
        Xq2= Xq1+1000
        Yq1=20
        Yq2=Yq1+700
        #print("2")
        if len(paint_koords)==0:
            return
        #print("_______________")
        
        if(len(paint_koords)>120):
            self.coords = paint_koords[-100:-1]
        #if(len(paint_koords)>110):
            #start_i = int(len(paint_koords)-100)
        for i in range(len(paint_koords)-1): 
            #print(paint_koords[i])           
            if paint_koords[i][0]>Xmax:
                Xmax=paint_koords[i][0]
            if paint_koords[i][0]<Xmin:
                Xmin=paint_koords[i][0]
            if paint_koords[i][1]>Ymax:
                Ymax=paint_koords[i][1]
            if paint_koords[i][1]<Ymin:
                Ymin=paint_koords[i][1]
        kx=abs(Xq1-Xq2)/abs(Xmax-Xmin)  
        ky=abs(Yq1-Yq2)/abs(Ymax-Ymin)  
        offX=Xmin*kx-Xq1
        offY=Ymin*ky-Yq1
        pen = QPen(Qt.blue, 1, Qt.SolidLine)
        qp.setPen(pen)
        #print("3")
        for i in range(int(len(paint_koords))-1):   
            x1=paint_koords[i][0]
            y1=paint_koords[i][1]
            x2=paint_koords[i+1][0]
            y2=paint_koords[i+1][1]
            qp.drawLine(int(x1*kx-offX),int(y1*ky-offY),int(x2*kx-offX),int(y2*ky-offY))



if __name__ == '__main__':    
    app = QApplication(sys.argv)
    tensom = TensApp()
    tensom.show()
    sys.exit(app.exec_())
