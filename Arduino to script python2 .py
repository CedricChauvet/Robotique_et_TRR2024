#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Reception des données émise par un Arduino branché
à un port USB.    
D'abord lancez le programme copyfile to serial.ino
rebootez l'arduino puis lancez le script. devrait retourner les données de cours sous la forme de plot
'''
import sys
import serial
import serial.tools.list_ports
import time
import pandas as pd
import re
import matplotlib.pyplot as plt
Start = False
A=[]
B=[]
C=[]
D=[]
E=[]
F=[]
G=[]
H=[]
I=[]
J=[]
K=[]
L=[]
M=[]
N=[]
O=[]
P=[]
Q=[]
R=[]
K1=[]
K2=[]

load_a_file=False
if(load_a_file):
    df = pd.read_csv("./TEST.csv")
    # print the data.
    print(df.index)

    fig,ax = plt.subplots(nrows=2)
    ax[0].plot(pd.to_numeric(df.index),pd.to_numeric(df.y1))
    ax[0].plot(pd.to_numeric(df.Time),pd.to_numeric(df.y2))
    ax[1].plot(pd.to_numeric(df.Time),pd.to_numeric(df.y3))
    plt.show()
    sys.exit(0)


portArduino = "COM14"   
baudrate=9600

t0 = time.time()  # initialisation chronometre
print('Connexion a '+ portArduino+" a un baud rate de "+ str(baudrate))

try :
    arduino = serial.Serial(portArduino, baudrate, timeout=0.01)      # on établit la communication série
except serial.serialutil.SerialException:
    print("Attention!!! port non reconnu, choisissez parmi les ports branchés ci dessous")
    ports = serial.tools.list_ports.comports()
    for port, _,_ in sorted(ports):
        print("{} ".format(port))
    sys.exit(0)






while True:
    data = arduino.readline()[:-2]  # le [:-2] enleve les caracteres "\n" 
    data = data.decode("utf-8")
    #if (re.search("CSV",data) or re.search("TXT",data)) :
    #    print("\n we gata fil' " + data+ "\n")
    #elif re.search("Start",data):
    #     Start = True     # debut de la capture. le fichier commence avec "Start"
    
    series=data.split(",") # désencapsule les données
    
    
    
    if Start == True:
        if series[0] != "":
            try:
                
                A.append(series[0])
                B.append(series[1])
                C.append(series[2])
                D.append(series[3])
                E.append(series[4])
                F.append(series[5])
                G.append(series[6])
                H.append(series[7])
                I.append(series[8])
                J.append(series[9])
                K.append(series[10])
                L.append(series[11])
                M.append(series[12])
                N.append(series[13])
                O.append(series[14])
                P.append(series[15])
                Q.append(series[16])
                R.append(series[17])
                
            except:
                print("données corrompues")
                sys.exit(0)
        else:
            break    
        
    if re.search("temps",series[0]):     # premiere ligne avec les titles
        Start = True     # debut de la capture. le fichier commence avec "Start"
        #print(series[:])
    

print(A[0:5])
print("isokay?")

# Initialize data to Dicts of series.
d = {'Time': pd.Series(A),
     'freqLoop': pd.Series(B),
    'valeurAvant': pd.Series(C),
    'valeurArriere': pd.Series(D),
    'Alpha': pd.Series(E),
    'Distance': pd.Series(F),
    'Erreur1': pd.Series(G),
    'Erreur2': pd.Series(H),
    'Erreur3': pd.Series(I),
    'SommmeErreurs': pd.Series(J),
    'K1': pd.Series(K),
    'K2': pd.Series(L),
    'K3': pd.Series(M),
    'pwmGauche': pd.Series(N),
    'pwmdroit': pd.Series(O),
    'vitesseG': pd.Series(P),
    'vitesseD': pd.Series(Q),
    'gyro': pd.Series(R),
    }
 
# creates Dataframe.
df = pd.DataFrame(d)
df.to_csv("./test.csv", index=True)






# print the data.
print(df.valeurAvant)

fig,ax = plt.subplots(nrows=3,ncols=2)
ax[0].plot(df.index,pd.to_numeric(df.valeurAvant))
#ax[0].plot(pd.to_numeric(df.index),pd.to_numeric(df.valeurArriere))
#ax[1].plot(pd.to_numeric(df.index),pd.to_numeric(df.Alpha))
#ax[1].plot(pd.to_numeric(df.index),pd.to_numeric(df.Distance))
#ax[2].plot(pd.to_numeric(df.index),pd.to_numeric(df.Erreur1))
#ax[2].plot(pd.to_numeric(df.index),pd.to_numeric(df.Erreur2))
#ax[2].plot(pd.to_numeric(df.index),pd.to_numeric(df.SommeErreurs))
#ax[3].plot(pd.to_numeric(df.index),pd.to_numeric(df.pwmGauche))
#ax[3].plot(pd.to_numeric(df.index),pd.to_numeric(df.pwmDroit))
#ax[4].plot(pd.to_numeric(df.index),pd.to_numeric(df.VitesseG))
#ax[4].plot(pd.to_numeric(df.index),pd.to_numeric(df.VitesseD))
#ax[5].plot(pd.to_numeric(df.index),pd.to_numeric(df.gyro))
plt.show()

