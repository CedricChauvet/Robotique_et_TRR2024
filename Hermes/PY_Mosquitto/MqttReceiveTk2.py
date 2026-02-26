# -*- coding: utf-8 -*-

"""
Programme MqttReceiveTk.py
Dernière version au 23/02/2026
du programme de réception des messages Mqtt
émis par un robot.
ajout creation de l,objet cCsv
et suppression du test Subscribe

procédure à suivre :
lancer le programme et cliquer le bouton
Ecrit fichier avant de lancer le programme du robot.
Ne pas oublier de cliquer sur le bouton Fermer
pour arrêter le programme et fermer le fichier
et écrire les données sur le disque
"""

import tkinter as tk
import time
import datetime
import paho.mqtt.client as mqtt  # import library
import socket
import csv

MQTT_BROKER = "127.0.0.1"  # specify the broker address, it can be IP of raspberry pi or simply localhost
MQTT_TOPIC = "test"  # this is the name of topic

global okFic
okFic = False
global objetFichier

global messageReceived
messageReceived = False
global messageString

class myCsv:
    def __init__(self):
        self.data = []

    def majsuffixe(self):
        d = datetime.datetime.now()
        suffixes = int(time.mktime(d.timetuple()))  # récupération de la date et temps unix pour suffixe noms fichiers
        return suffixes

    def nomFichier(self):
        fichier: str = 'logs/log' + str(cCsv.majsuffixe()) + '.csv'
        if fichier == None:
            print("Fichier n'existe pas")
        else:
            print("Creation du fichier : " + fichier)
            return fichier

    def creerFichier(self):
        global objetFichier
        fichier = cCsv.nomFichier()
        objetFichier = open(fichier, 'w')
        return objetFichier

    def ecritFichier(self,messageString):
        messageList = messageString.split()
        #objetFichier = cCsv.creerFichier()
        writer = csv.writer(objetFichier, delimiter=';')
        writer.writerow(messageList)


def InitMqtt():
    global MQTT_BROKER
    global MQTT_TOPIC
    global okFic

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER)

    #client.loop_forever()  # use this line if you don't want to write any further code. It blocks the code forever to check for data
    client.loop_start()

# callback called when client receives a CONNACK response
def on_connect(client, userdata, flags, rc, self=None):
    global okFic

    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        print("subscribe to Topic {}".format(MQTT_TOPIC)+ " OK")
        if okFic == True:
            myCsv.creerFichier(self)
    else:
        print("bad connection {}".format(rc))


# callback called when a PUBLISH message is received
def on_message(client, userdata, msg, self=None):
    global okFic

    print(msg.topic + " " + str(msg.payload.decode("utf-8")))
    messageString = str(msg.payload.decode("utf-8"))
    if okFic == True:
        cCsv.ecritFichier(messageString)
    global messageReceived
    messageReceived = True

class DemoWidget(tk.Frame):
    def __init__(self, root):
        super().__init__(root)

        self.master.configure(bg='Gray10', bd=40)
        self.configure(bg='Gray26', bd=2 ,relief='groove')
        self.champs = {
            'message': tk.StringVar(),
            'procedure': tk.StringVar(),
        }
        # récupère l'adresse ip du pc hote
        adresse = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][0]
        self.champs['message'].set(adresse)
        self.champs['procedure'].set('Fermer valide le fichier ')
        self._create_gui()
        self.pack()


    def _create_gui(self):

        label = tk.Label(self, text="Adresse IP Broker : ")
        label.grid(column=0, row=1)

        text = tk.Entry(self, textvariable=self.champs['message'])
        text.grid(column=1, row=1, columnspan=2)

        text = tk.Entry(self, textvariable=self.champs['procedure'])
        text.grid(column=0, row=2, columnspan=3)

        button = tk.Button(self, text="Ecrit ficher", command=self.CreerFic)
        button.grid(column=0, row=100)

        button = tk.Button(self, text="Fermer", command=app.quit)
        button.grid(column=3, row=100)

    def CreerFic(self):
        global okFic
        okFic =True
        InitMqtt()

app = tk.Tk()
app.title("Subscribe Mqtt")
DemoWidget(app)
cCsv = myCsv()
app.mainloop()
