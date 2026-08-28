from operator import contains
from time import sleep
from Devices.TensSens import TensSens
from Devices.StringMash import PrinterMash
from Util.TensEnum import WaveForm
from Util.CurTime import ProgTime
import numpy as np
from PyQt5 import QtCore


class TensMash(object):
    def __init__(self,force_mash:PrinterMash,force_sens:TensSens):
        self.data = None
        self.force_mash:PrinterMash = force_mash
        self.force_sens:TensSens = force_sens

        self.cycle_time = 0
        self.prog_time = ProgTime()

        self.timeDelt = 0.02
        self.timeDeltCycl = self.timeDelt *2

        self.threadMoveToForce = CurForceThread(self,self.timeDelt)
        self.threadCycleForce = CurCycleThread(self,self.timeDeltCycl)

        
        self.kp = 0.00005
        self.dest_force = 0
        
        self.VelPr = 0.8

        self.Fmax = None
        self.timeF = None
        self.tRelax = None
        self.waveForm = None

        self.run_force = False
        self.run_cycle = False
        
        self.delim = int(2/self.timeDelt)

        self.countdelim = 0
        self.coords:"list[list[float]]" = []

    def move(self,dist:float):
        self.force_mash.move(dist,self.VelPr)

    def moveToForceIntern(self):
        if self.force_sens!=None:           
            force = self.force_sens.getValueIn()
        if force!=None:
            move = self.compMove(force,self.dest_force)
            if abs(move)>0:    
                if self.force_mash!=None:
                    self.force_mash.move(move,self.VelPr)

    def compMove(self,cur_force:float,dest_force:float)->float:
        df = dest_force - cur_force
        s = 0
        if abs(df)>5:
            s = self.kp*df
        return s

    def startCycle(self,Fmax:float,timeF:float,tRelax:float,waveForm:WaveForm):
        if Fmax!=None and timeF!=None and tRelax!=None and waveForm!=None :
            self.Fmax = Fmax
            self.timeF = timeF
            self.tRelax = tRelax
            self.waveForm = waveForm
            self.prog_time.startNew()
            self.run_cycle = True
            self.run_force = True

    def resumeCycle(self):
        self.run_cycle = True

    def startForce(self, force:float):        
        self.dest_force = force
        self.run_force = True

    def stopForce(self):
        self.run_force = False

    def stopCycle(self):
        self.run_cycle = False
        self.run_force = False

    def compCycle(self):
        if self.prog_time!=None and self.timeF!=None and  self.Fmax!=None and self.waveForm!=None and self.tRelax!=None:
            dt = self.prog_time.getCurrentTime()
            fi = float(dt)/float(self.timeF)
            ampl_F = self.Fmax * self.compCurForce(fi,self.waveForm)
            if dt > self.timeF:
                ampl_F = self.Fmax*0.1
            if dt > self.timeF + self.tRelax:
                ampl_F = self.Fmax*0.1
                self.prog_time.startNew()
            self.dest_force = ampl_F

    def compCurForce(self,fi:float,waveForm:WaveForm)->float:
        ampl = 0
        if waveForm == WaveForm.meandr:
            ampl = 1
        elif waveForm == WaveForm.triangle:
            if(fi<0.5):
                ampl = 2*fi
            else:
                ampl = 1-2*(fi-0.5)
        elif waveForm == WaveForm.sinus:        
            ampl = np.sin(np.pi*fi)
        
        return ampl

    def moveToForce(self,dest_force:float,vel:float):
        if dest_force!=None and vel!=None:
            force = self.force_sens.getValueIn()
            if force!=None:
                move = self.compMove(force,dest_force)
                if abs(move)>0:    
                    self.force_mash.move(move,vel)


class CurForceThread(QtCore.QThread):
    def __init__(self,tens_mash:TensMash,timeDelt:float):
        QtCore.QThread.__init__(self)   
        self.tens_mash:TensMash = tens_mash
        self.timeDelt = timeDelt
        self.delim = 10
        self.ind = 0
        self.start()   
    def run(self):
        while True:
            self.ind +=1
            self.tens_mash.force_sens.getValue()
            
            if self.ind%self.delim==0:
                #print(self.tens_mash.dest_force)
                cur_force = self.tens_mash.force_sens.getValueIn()
                print(cur_force)
                self.tens_mash.coords.append([self.ind,cur_force])
            
                
            resp = str(self.tens_mash.force_mash.responce())
            if "Error" in resp:
                self.tens_mash.force_mash.curCom-=1

            if self.tens_mash!=None:
                if self.tens_mash.run_force==True:
                    self.tens_mash.moveToForceIntern()
                sleep(self.timeDelt)

class CurCycleThread(QtCore.QThread):
    def __init__(self,tens_mash:TensMash,timeDelt:float):
        QtCore.QThread.__init__(self)   
        self.tens_mash:TensMash = tens_mash
        self.timeDelt = timeDelt
        self.start()
    def run(self):
        while True:            
            if self.tens_mash!=None:
                if self.tens_mash.run_cycle==True:
                    self.tens_mash.compCycle()
                sleep(self.timeDelt)