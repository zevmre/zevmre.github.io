'''
A python code calculating the solution to Problem 10.11 of [1]
Coded by zevmre
[1]Behzad Razavi. Design of analog CMOS integrated circuits[M]. 陈贵灿, 程军等, 译. 陈贵灿, 审. 2版. 西安: 西安交通大学出版社, 2019: 408
'''
from math import sqrt,log10,fabs,atan
epsSiO2=3.9
eps0=8.854187817e-12
tox=9e-9
Cox=epsSiO2*eps0/tox
VDD=3

class MOS:
    def __init__(self,W,L,mu,VTO,gamma,PHI,lam,I=0,VGS=0,VDS=0,VSB=0):
        self.W,self.L,self.WL=W,L,W/L
        self.k=mu*Cox
        self.VTO=VTO
        self.gamma,self.PHI,self.lam=gamma,PHI,lam
        self.I=I
        self.VGS,self.VDS,self.VSB=VGS,VDS,VSB
        self.VTH=0
        self.VGT=0
    def updateI(self):
        #Calc I_D given VGS (perhaps with VSB, VDS)
        self.VTH=self.VTO+self.gamma*(sqrt(fabs(self.PHI+self.VSB))-sqrt(self.PHI))
        self.VGT=self.VGS-self.VTH
        self.I=0.5*self.k*self.WL*(self.VGT)**2*(1+self.lam*self.VDS)
    def updateV(self):
        #Calc VGS given I_D (perhaps with VSB, VDS)
        self.VTH=self.VTO+self.gamma*(sqrt(fabs(self.PHI+self.VSB))-sqrt(self.PHI))
        self.VGT=sqrt((2*self.I)/(self.k*self.WL*(1+self.lam*self.VDS)))
        self.VGS=self.VGT+self.VTH
    def updateWL(self):
        #Calc W/L given I & V_GT (assuming critical saturation)
        self.WL=(2*self.I)/(self.k*self.VGT**2*(1+self.lam*self.VGT))
    @property
    def gm(self):
        return (2*self.I)/(self.VGT)
    @property
    def gmb(self):
        return (self.gamma/(2*sqrt(self.PB+self.VSB)))*self.gm()
    @property
    def ro(self):
        return 1/(self.lam*self.I)
    def init_cap(self,CJ,CJSW,CGDO,CGSO,MJ,MJSW,PB,VRS,VRD):
        self.CGD=self.W*1e-6*CGDO
        self.CGS=self.W*1e-6*CGSO+2/3*self.W*1e-6*self.L*1e-6*Cox
        LSD=1.5e-6
        self.CDB=(CJ*self.W*1e-6*LSD)/(1+VRD/PB)**MJ+(CJSW*(2*self.W+2*LSD)*1e-6)/(1+VRD/PB)**MJSW
        self.CSB=(CJ*self.W*1e-6*LSD)/(1+VRS/PB)**MJ+(CJSW*(2*self.W+2*LSD)*1e-6)/(1+VRS/PB)**MJSW

class NMOS(MOS):
    def __init__(self,W,L,I=0,VGS=0,VDS=0,VSB=0,gamma=0.45,lam=0.1,LD=0.08):
        MOS.__init__(self,W,L-2*LD,350e-4,0.7,gamma,0.9,lam,I,VGS,VDS,VSB)
    def init_cap(self,VRD=0,VRS=0):
        MOS.init_cap(self,0.56e-3,0.35e-11,0.4e-9,0.4e-9,0.45,0.2,0.9,VRS,VRD)

class PMOS(MOS):
    def __init__(self,W,L,I=0,VGS=0,VDS=0,VSB=0,gamma=0.4,lam=0.2,LD=0.09):
        MOS.__init__(self,W,L-2*LD,100e-4,0.8,gamma,0.8,lam,I,VGS,VDS,VSB)
    def init_cap(self,VRD=0,VRS=0):
        MOS.init_cap(self,0.94e-3,0.32e-11,0.3e-9,0.3e-9,0.5,0.3,0.9,VRS,VRD)

def PA(a,b):
    #Parallel
    return (a*b)/(a+b)

Iout=1e-3
M5=PMOS(60,0.5,Iout,gamma=0)
M5.updateV()
VX=VDD-M5.VGS
#print("%g"%(VX))

M7=NMOS(50,0.5,Iout,gamma=0)
M7.updateV()
Vout_max=VDD-M5.VGT
Vout_min=M7.VGT
#print(Vout_max-Vout_min)

Vout_cm=0.5*(Vout_max+Vout_min)
Iin=0.5*0.25e-3
M3=PMOS(50,0.5,Iin,gamma=0,VDS=VDD-VX)
M3.updateV()
M1=NMOS(50,0.5,Iin,gamma=0)
M1.updateV()
M1.init_cap(VX)
M3.init_cap(VDD-VX)
M5.init_cap(VDD-Vout_cm)
M7.init_cap(Vout_cm)
RX=PA(M3.ro,M1.ro)
Rout=PA(M5.ro,M7.ro)
Av1=M1.gm*RX
Av2=M5.gm*Rout
CX=M1.CGD+M1.CDB+M3.CGD+M3.CDB+M5.CGS+M5.CGD*(1+Av2)
CL=1e-12
Cout=M7.CGD+M7.CDB+M5.CDB+M5.CGD*(1+1/Av2)+CL
omega_X=1/(RX*CX)
omega_out=1/(Rout*Cout)
#print("Dominant:%g\nSecond:%g\n-------After-------"%(omega_X,omega_out))

omega_p2_after=M5.gm/(CX+Cout)
omega_GX_after=omega_p2_after*(1/sqrt(3))
omega_p1_after=omega_GX_after/(10**(20*log10(Av1*Av2)/20))
#print("%g"%(omega_p1_after))

CC=(1/(omega_p1_after*RX)-CX)/(1+Av2)
omega_z=M5.gm/(CC+M5.CGD)
#print("Dominant:%g\nSecond:%g\nZero:%g\n"%(omega_p1_after,omega_p2_after,omega_z))
#print(CC+M5.CGD,CX)

Rz=1/M5.gm+1/(omega_p2_after*CC)
#print(Rz)

SR=Iin/CC
print("%g"%(SR))
