#CODE issu de Truggy_asservi_30_07_4.py,opérationnel, testé plusieurs fois en mars 2022,
#simplifié au max. Calage nouvelle caméra PICAM (2) à 2 m avec  AC=30 cm
# champs caméra mesurés 60° et 53,396°, d'où radpix=0,0032 et epsilon=0,00388 en rd

import matplotlib.pyplot as plt             # librairie de tracage de graphique
import cv2
import sys
import numpy as np
import os.path
import time
from time import perf_counter as pc         # méthode mesure des performances en secondes
import datetime
import math
from threading import Thread
import Adafruit_PCA9685
import RPi.GPIO as GPIO

"""Constantes et variables de traitement video
Attention seuls les formats 320x240 et 160x120 sont possibles.
tout autre format générera une erreur """
largeur = 320 # largeur de la frame
hauteur = 240  # hauteur de la frame
AC = 30.00  # Altitude caméra en cm
deltaY = 53.396  #   Champ vertical caméra en °
deltaX = 60.0 # Champ horizontal caméra en °
alpha = 28.0724867     # angle ° plan vertical caméra / plan inférieur champ de vision caméra
epsilon = 0.22248333333      #angle en ° qui sous tend un pixel vers avant/en hauteur image
coeflarg = 0.0036084   # coef pour largeur pixel 

offset=0                                    # décalage en cm ou mm entre l'axe central et l'axe du véhicule
azyc=lastazyc=deltaAzyc=0.0                  # angle entre le vecteur trajectoire du véhicule et le vecteur
                                         # entre caméra et coordonnées du mileu de la piste la plus éloignée
kpa=1.0                                       # coefficient proportionnel
kda=0                                       # coefficient dérivée

f = 0  # compteur de frames

# table des numéros de lignes et largeur en pixel ligne blanche
# pour taille 320x240 colonne 0 et 1 pour taille 640 x 480 colonne 2 et 3
yl = np.array([[80, 24],
                    [100, 29],
                    [130, 38]], int)

"""yl = np.array([[10, 9],
                    [20,11],
                    [30,13],
                    [40,15],
                    [50,17],
                    [60,20],
                    [80,24],
                    [110,32],
                    [140,41],
                    [170,52],
                    [200,71]], int)"""


if largeur == 320:
    iL = 0                      #indice de la hauteur de ligne table numéro de ligne analysée
    iP = 1                      #indice nbre pixel ligne blanche table numéro de ligne analysée
elif largeur == 640:
    iL = 2                      #indice de la hauteur de ligne table numéro de ligne analysée
    iP = 3                      #indice de la hauteur de ligne table numéro de ligne analysée

bright = 50                 # valeur du brightness
contrast = 50                 # valeur du contraste

debY=0                  # début boucle extraction des lignes
finY=np.size(yl,0)      # fin boucle  extraction des lignes
lg = 1                  # nbre de pixel à comparer
pas = 2                 # pas entre les groupes de pixels à comparer
saut = 60               # valeur du saut
seuil = 0  # valeur du seuil mini de blanc
coefl=0.70  # coefficient d'approximation nombre pixel ligne blanche

vSaut=0    # valeur saut pour affichage video
vSeuil=0   # valeur du pixel milieu de ligne pour affichage video

"""array de 5 lignes de 320 colonnes pour l'analyse de 5 lignes"""
graySingleLine = np.zeros((5, largeur))
milieu = largeur / 2                # initialisation variable valeur x du centre de la piste
xdeb=0                              # initialisation variable début de segment à analyser

okCroix = False  # flag indiquant si le centre de la ligne blanche a été localisé

""" Variables PCA9685"""

escCh = 3  # canal ESc 3 pour le truggy
servoCh = 7  # canal servo 7 pour le truggy

#Initialisation objets esc et servo
esc = Adafruit_PCA9685.PCA9685()
servo = Adafruit_PCA9685.PCA9685()
esc.set_pwm_freq(50)
servo.set_pwm_freq(50)
servo.set_pwm(servoCh, 4096, 0)         # ajout 30/07/2021 nettoyage PCA
esc.set_pwm(escCh,4096, 0)              # servo et esc


"""Variables de Pilotage Truggy"""
angleDefaut = 307.6   # Valeur neutre de l'angle de braquage'
angleBraq = angleDefaut  # cde angle de braquage
angleBraqDroit = 297  # cd angle maxi droite
angleBraqgauch = 315  # angle maxi gauche
#coefAngle = 0.25 # pente fonction transfert PWM=f(angle braquage)

EscStop = 307 # Valeur cde ESC pour arrêt moteur
EscMaxAv = 370  # Valeur cde ESC pour vitesse avant maxi
EscFrein = 250  # Valeur de blocage des roues
EsxMaxAr = 270  # valeur cde ESC pour vitesse arrière maxi
coefVit = 0.0 # coefficient de vitesse  pour Donkey
Vit = EscStop+10  # vitesse cible +10 pour le démarrage manuel
sTop=False

corr=0          # correction pour assservissement vitesse
PwmVIT=0        # commande pwm calculé par l'asservissement

"""variables de débogages à supprimer dans la version ope"""
deTect = np.zeros(finY, int)

"""Variables GPIO"""
pinBout = 37                        # GPIO 26
pinOdo = 22                         # GPIO 25
"""Initialisation pin GPIO"""
GPIO.setmode(GPIO.BOARD)  # numérotation  sérigraphie du connecteur de la carte
GPIO.setup(pinBout, GPIO.IN)
GPIO.setup(pinOdo, GPIO.IN)
Go=False                    # etat du bouton Go

"""Variables odométrie"""
tachy =0.0
nbPignon=0
lastval = 0
cumDist = 0
t=0.00
stopThread=False

lastTime = 0.00
perimetreRoue = 34

# table des tronçon : indice 0 = dsitance en cm, indice 1 = vitesse en km, indice 2 = angle par défaut servo,
# indice 3 = borne gauche servo, indice 4 = borne droite servo. Les angle servo sont exprimés en pwm.
tronCon=np.array([[0,3,307.6,420,180],                # ligne droite
    [300,1.5,307.6,420,180],                          # courbe à droite environ 10°
    [1000,0,307.6,420,180],                           # ligne droite
    [3482,0,307.6,315,297],
    [4282,0,307.6,274,282],
    [5000,0,307.6,315,297],
    [6000,0,307,315,297],
    [7000,0,307,315,297],
    [8000,0,307,315,297],
    [9000,0,307,315,297]],float)

finT=np.size(tronCon,0)         # Nbre d'éléments de la table troncon
""" Variables asservissemnt vitesse 'PID) """
conSi=0.0                                   # consigne de vitesse
lastconSi=conSi                             # consigne précédente
deltaconSi=conSi-lastconSi                  # Ecart entre consigne de vitesse
freinconSi=100                                # valeur ecart déclenchant le freinage
erreur_precedente = 0                       # erreur précédente
frein=False                                 # indicateur de freinage
kp = 0.8                                   # Coefficient proportionnel
ki = 0                                      # Coefficient intégrateur
kd = 0                                      # Coefficient dérivateur
corr = 0                                    # correction pid
def timer(deb):
    """ Debug fonction de calcul du temps passé par une boucle de programme """
    global cum_time
    total_time = time.time() - deb
    cum_time += total_time

def compteur():
    global lastval
    global lastTime
    global nbPignon
    global perimetreRoue
    global tachy
    global t
    global stopThread
    print(" thread", stopThread," taille tableau troncon : ",finT)
    while stopThread == False:
        time.sleep(0.001)
        val = GPIO.input(pinOdo)
        if val == 1 and lastval == 0:
            lastval = 1
        elif val == 0 and lastval == 1:
            lastval = 0
            t = time.time() - lastTime
            lastTime = time.time()
            nbPignon = nbPignon + 1
            nb_tour_par_sec = 1 / t
            tachy = (nb_tour_par_sec * 3600 * 0.3 * perimetreRoue) / 100000

    print(" Stop thread ",stopThread)

def plotGraph():
    """  Debug Fonction d'affichage histogramme ligne extraite"""
    graySingleLineP = Ligne.get_ligne(yl[y, iL], 0, largeur)
    plt.plot(graySingleLineP[0, 1:largeur])
    text="y: "+str(yl[y, iL])
    plt.text(10, 65, text)
    plt.show()
    plt.pause(0.001)
    plt.clf()

class infoFlux:
    """ Debug Récupere infos sur flux video"""

    def get_info(self):
        fps = cap.get(cv2.CAP_PROP_FPS)
        largeur = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        hauteur = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        bright = cap.get(cv2.CAP_PROP_BRIGHTNESS)
        contrast = cap.get(cv2.CAP_PROP_CONTRAST)
        codec = cap.get(cv2.CAP_PROP_FOURCC)
        nbFrame = 0
        print('largeur : ', largeur, ' hauteur : ', hauteur, ' brightness : ', bright, ' contrast ', contrast,
              ' nbFrame : ', nbFrame, ' fps : ', fps)


class Croix:
    """trace une croix à partir des positions y et x
    par la méthode dess_croix"""

    def dess_croix(y, x):                                                  # dessine la croix centre de la ligne blanche
        cv2.line(frame, (x - 10, y - 10), (x + 10, y + 10), (255, 0, 255))
        cv2.line(frame, (x - 10, y + 10), (x + 10, y - 10), (255, 0, 255))

    def dess_maxLoc(y, x):                                                 # dessine la croix localisant la valeur la
        cv2.line(frame, (x - 10, y - 10), (x + 10, y + 10), (0, 255, 255)) # plus blanche
        cv2.line(frame, (x - 10, y + 10), (x + 10, y - 10), (0, 255, 255))

    def ligne_vert(self):                                                 # Ligne verticale mileu de l'image
        cv2.line(frame, (int(largeur / 2), 0), (int(largeur / 2), hauteur), (255, 0, 0))

    def ligne_hori(self):                                                 # lignes horizontales
        cv2.line(frame, (0, int(hauteur / 2)), (largeur, int(hauteur / 2)),
                 (255, 0, 0))  # ligne mileu image# lignes horizontales

        for i in range(debY, finY):  # visualisation des positions des lignes table yl
            cv2.line(frame, (0, int(yl[i, iL])), (largeur, int(yl[i, iL])), (0, 0, 0))  # lignes analysée

class text:
    """Affiche du texte sur le flux video en sortie
       offset et azimut """

    def affiche(self):
        numf = int(cap.get(cv2.CAP_PROP_POS_FRAMES))                # numéro de frame
        #numft = 'F: ' + str(f) + ' O: ' + str(round(offset, 2))     # chaine caractère frame + offset
        numft = 'F: ' + str(f) + ' Hz: ' + str(freqK)+' V: '+ str(round(tachy, 2))  # chaine caractère frame + offset
        azyt = ''
        azyt = 'Az '+str(round(azyc,2)) + 'Offs '+str(round(offset,2))+' Angbraq '+str(round(angleBraq,2))  # Chaine azimut et distance croix
        cv2.putText(frame, numft, (1, 200), cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 0), 2)
        cv2.putText(frame, azyt, (1, 160), cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 0), 2)

    def cR(self):
        numf = int(cap.get(cv2.CAP_PROP_POS_FRAMES))                # numéro de frame
        #numft = 'F: ' + str(f) + ' O: ' + str(round(offset, 2))     # chaine caractère frame + offset
        numft = 'F: ' + str(f) + ' Freq: ' + str(round(f/cum_time),2)  # chaine caractère frame + offset
        azyt = ''
        azyt = 'Az: ' + str(round(azyc, 2)) + ' AH: ' + str(round(AH, 2))  # Chaine azimut et distance croix
        cv2.putText(frame, numft, (5, 200), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 0), 2)
        cv2.putText(frame, azyt, (5, 160), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 0), 2)

class Ligne:
    """ Classe ligne : extrait une ligne à la hauteur Y par la méthode get_ligne et la converti en niveaux de gris"""

    def get_ligne(y, xd, xl):
        return (cv2.cvtColor(frame[y:y + 1, xd:xl], cv2.COLOR_BGR2GRAY))

class findCentre:
    """Voir note """

    def Saut(y, xdeb, centre):  # méthode de recherche des sauts
        global oKroix  # variables globales
        global graySingleLine
        global vSaut
        global vSeuil
        xG = xD = 0  # position x des sauts
        # extraction de la ligne à analyser
        graySingleLine[0:1] = Ligne.get_ligne(yl[y, iL], xdeb, largeur)
        for i in range(0, int(largeur - lg * 2 - pas)):  # boucle lecture segment de gauche à droite
            dipsG = graySingleLine[0:1, i + lg + pas:i + lg * 2 + pas] - graySingleLine[0:1,
                                                                         i:i + lg]  # Ecart valeurs pixel
            if int(np.mean(dipsG)) >= saut:  # valeur saut gauche  supérieure au seuil paramétré
                vSaut = np.mean(dipsG)
                xG = i + lg  # position du saut gauche
                for i2 in range(xG, xG + int((yl[y, iP]/coefl) * 1)):  # recherche du saut sur 2 fois la largeur théorique
                    if i2 >= largeur-(lg*2 + pas):
                        break
                    dipsD = graySingleLine[0:1, i2:i2 + lg] - graySingleLine[0:1, i2 + lg+pas: i2 + lg*2 + pas]
                    if int(np.mean(dipsD)) >= saut and (i2 - xG) > int((yl[y, iP]) * coefl and np.mean(graySingleLine[0:1, i:i2 ]) >=seuil):
                    #if int(np.mean(dipsD)) >= saut and (i2 - xG) > int((yl[y, iP]) * coefl) and (np.mean(graySingleLine[0:1, i:i2 ]) >=seuil):
                        vSeuil = np.mean(graySingleLine[0:1, i:i2 ])
                        oKroix = True
                        xD = i2 + lg
                        break
            if oKroix == True:
                centre = xG + int((xD - xG) / 2)  # le centre de la piste est égal à xG +1/2 largeur ligne blanche
                break
        return (centre)

class calcT:
    """ Classe de calcul de l'offset et de l'azimit à partir des formules du
        document ANNEXE calage caméra TRUGGY.docx mais uniquement
        à partir du nombre de pixels
        la méthode calcAH calcule la distance AH entre la base du plan vertical
        de la caméra et la base du plan inférieur du champ de vision vertical
        la méthode largp estime la largeur d'un pixel en fonction de la hauteur de ligne
        la méthode offset calcule l'écart entre la droite véhicule centre
        de la piste identifié et la droite passant par l'axe central horizontal de la frame en cm
        la méthode azy calcule l'azimut, angle entre l'axe du véhicule et la droite"""

    def calcAh(y):          # calcul de AH
        return (AC * (math.tan(math.radians((alpha) + ((hauteur + 1) - y) * epsilon))))

    def largp(y):   # calcul largeur pixel fonction AH                                      # formule truggy
        return (coeflarg * calcT.calcAh(y))

    def offset(x, y):                   # calcul de l'offset
        return (calcT.largp(y) * (x - (largeur / 2)))

    def azy(y, x):                      # calcul de l'azimut
        return (math.atan2(y, x) * 180 / np.pi)

    def freqK(self):                    # fréquence détection croix
        global cptK
        global tk0
        global fk
        if pc()-tk0 >=1:
            fk=cptK
            cptK=0
            tk0=pc()
        return(fk)



class pilot:

    def calcBraq(a):                      # calcul de la commande de  braquage, par conversion de la correction angulaire
        return (angleDefaut - (3*a))      # droite étalonnage PWM=f(braquage)  
    def calcVit(a, b, c):                   # calcul de la vitesse  en pourcentage (coefvit) du pwm vitesse maxi
        # Méthode pour Donkey sans odométrie et tronçon
        return (coefVit * (EscMaxAv - EscStop) + EscStop)

    def loiA(a,da, kp,kd):                  # loi de braquage sur azimut a= azimut, da = delta azimut
        return(kp*a+kd*da)                  # kp = coefficient prportionnel, kd = coefficient dérivée.

    def etatBout(self):
        retour=False
        val = GPIO.input(pinBout)
        if val:
            retour=True
        return(retour)

    def asservissement_T(self):
        global conSi
        global tachy
        global erreur_precedente
        global corr
        global PwmVIT
        erreur = conSi - tachy
        #if erreur >= 5.0:
            #erreur= 5.0
        corr = kp * (erreur)
        PwmVIT = ((2.0) * (conSi + corr)) + 325.00
        print("conSi",conSi,"tachy",tachy,"erreur",erreur," corr: ",corr,"     pwm : ",PwmVIT)
        return(PwmVIT)

    def frein(self):
        Esc.pwm(0, EscStop)
        Esc.pwm(0, EscFrein)
        print("FREIN")

class odo:
    """méthodes d'odométrie :
       vitesse et distance parcourue
       """
    def ouEstil(self):
        global cumDist
        global deltaconSi
        global lastconSi
        global frein
        global conSi
        global angleDefaut
        global angleBraqgauch
        global angleBraqDroit
        cumDist =nbPignon * 0.3 * perimetreRoue
        for i in range(0,finT-1):
            if (cumDist >= tronCon[i,0] and cumDist < tronCon[i + 1,0]):
                conSi = tronCon[i,1]
                angleDefaut=tronCon[i,2]
                angleBraqgauch=tronCon[i,3]
                angleBraqDroit=tronCon[i,4]

        deltaconSi = lastconSi - conSi
        lastconSi = conSi
        """if deltaconSi >= freinconSi and (tachy>conSi*1.1):
            frein=True"""

class Servo:
    def _init_(self, a=0, b=0):
        self.a, self.a = a, b

    def braque(a, b):                       # commande servo de direction
        if b < angleBraqDroit:              # contrôle que l'angle braquage dans les bornes du servo
            b = angleBraqDroit
        if b > angleBraqgauch:
            b = angleBraqgauch
        servo.set_pwm(servoCh, a, int(b))

class Esc:
    def _init_(self, ton=0, toff=0):
        self.ton, self.toff = ton, toff

    def pwm(ton, toff):                     # commande ESC
        if toff < EsxMaxAr:
            toff = EsxMaxAr
        if toff > EscMaxAv:
            toff = EscMaxAv
        esc.set_pwm(escCh, ton, int(toff))

affV = True  # affichage video vrai ou faux
ecrV = True # écriture video
affC = True  # affichage croix sur video
affT = True  # affichage texte sur video
affL = True   # affichage lignes horizontales
affPlot =False # affichage histogramme ligne

# Création d'un objet VideoCapture à partir de la  picaméra
cap = cv2.VideoCapture(0)
# Ajustement de la résolution uniquement pour flux caméra
cap.set(cv2.CAP_PROP_BRIGHTNESS, bright)                          # paramétrage de la luminosité
cap.set(cv2.CAP_PROP_CONTRAST, contrast)                               # paramétrage du contraste
cap.set(3, largeur)
cap.set(4, hauteur)
# Debug : appel methode info sur le flux en entrée
infoFlux.get_info(0)
if affPlot ==True:                                      # pour affichage histogramme
    plt.ion()

start = time.time()  # initialisation chrono
cum_time = 0  # initialisation compteur temps passés
tk0=pc()            # initialisation compteur temps     pour calcul fréquence seconde détection croix
cptK=0              # compteur de détection de croix
fk=0                # fréquence détection croix
d = datetime.datetime.now()
unixtime = int(time.mktime(d.timetuple()))  # récupération de la date et temps unix pour suffice noms fichiers

if ecrV == True:            # paramétrage du flux vidéo en sortie
    vid = '../Videos/out' + str(unixtime) + '.avi'  # initialisation nom du flux video en sortie
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(vid, fourcc, 30.0, (largeur, hauteur))

# Test si la caméra ou le flux vidéo est ouvert
if (cap.isOpened() == False):
    print("Error opening video stream or file")

# mise en position neutre des roues
Servo.braque(0, angleDefaut)
# Armement ESC
Esc.pwm(0, EscStop)
time.sleep(0.5)

mythread = Thread(target=compteur, args = ())
mythread.start()

print('bouton go et Thread OK')

# Lecture du flux
while (cap.isOpened()):
    # Capture du flux video frame par frame
    ret, frame = cap.read()
    if ret == True:
        f = f + 1  # compteur de frames
        timer(start)
        start = time.time()
        odo.ouEstil(0)
        Vit=pilot.asservissement_T(0)
        #Vit=conSi
        oKroix = False
        for y in range(debY, finY):
            if affPlot == True:  # appel fonction histogramme ligne analysée
                plotGraph()

            milieu = findCentre.Saut(int(y), 0, int(milieu))
            if oKroix == True:
                AH = calcT.calcAh(yl[y,iL])
                offset = calcT.offset(milieu, yl[y,iL])
                lastazyc=azyc
                azyc = calcT.azy(offset, AH)
                deltaAzyc=azyc-lastazyc
                azyc=pilot.loiA(azyc,deltaAzyc,kpa,kda)
                angleBraq = pilot.calcBraq(azyc)
                #angleBraq=307
                Servo.braque(0, angleBraq)
                if Go==False:
                    Go=pilot.etatBout(0)
                else:
                    Esc.pwm(0, Vit)
                deTect[y] += 1
                cptK +=1
                freqK=calcT.freqK(0)                          # calcul fréquence détection croix
                print(' cumdist ',cumDist,' consi ',conSi, ' angleDefaut ',angleDefaut, ' borne gauche ',angleBraqgauch,'borne droite ',angleBraqDroit)
                if affV == True and affC == True:
                    Croix.dess_croix(int(yl[y,iL]), milieu)
                    if affL == True:
                        Croix.ligne_vert(0)
                        Croix.ligne_hori(0)
                if affV == True:
                    if affT == True:
                        text.affiche(0)  # appel methode affichage sur video
                break

        # affichage video

        cv2.imshow('img', frame)
        if ecrV == True:
            out.write(frame)

        # Appuyez sur  Q  du clavier pour quitter le script
        # la valeur tempo de cv2.waitKey(tempo) détermine la vitesse d'affichage
        if cv2.waitKey(20) & 0xFF == ord('q'):
            stopThread =True
            print(" cv2key : ", stopThread)
            mythread.join()
            break         # Break the loop
    else:
        break
    
Esc.pwm(0,EscStop)
Servo.braque(0,angleDefaut)

# Libération de la vidéo

cap.release()
if ecrV == True:
    out.release()
# Affichage compte rendu
print('Temps de traitement : ', cum_time,' frames lues ',f, ' fps ',int(f/cum_time))

for i in range(debY, finY):
    print('Milieu détecté ligne ', i, ' : ', deTect[i])

# Fermeture des fenêtres
servo.set_pwm(servoCh, 0,4096)
esc.set_pwm(escCh, 0, 4096)
GPIO.cleanup()
cv2.destroyAllWindows()
