# -*- coding: utf-8 -*-
import tkinter as tk
import time
import datetime
import paho.mqtt.client as mqtt  # import library
import socket
import csv

MQTT_BROKER = "127.0.0.1"  # specify the broker address, it can be IP of raspberry pi or simply localhost
MQTT_TOPIC = "test"  # this is the name of topic

global vari
vari=0
global fichier
global objetFichier
global okFic

global messageReceived
messageReceived = False
global messageString

def InitMqtt():
    global MQTT_BROKER
    global MQTT_TOPIC

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER)

    #client.loop_forever()  # use this line if you don't want to write any further code. It blocks the code forever to check for data
    client.loop_start()

# callback called when client receives a CONNACK response
def on_connect(client, userdata, flags, rc):
    global fichier
    global okFic
    global objetFichier

    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        print("subscribe to {}".format(MQTT_TOPIC))
        if okFic == True:
            objetFichier = open(fichier, 'w')
    else:
        print("bad connection {}".format(rc))


# callback called when a PUBLISH message is received
def on_message(client, userdata, msg):
    global vari
    global messageString
    global fichier
    global okFic
    global objetFichier

    vari +=1
    print(msg.topic + " " + str(msg.payload.decode("utf-8")) + " " + str(vari))
    messageString = str(msg.payload.decode("utf-8"))
    messageList = messageString.split()
    if okFic == True:
        writer = csv.writer(objetFichier, delimiter=';')
        writer.writerow(messageList)

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
        self.champs['procedure'].set('  ')
        self._create_gui()
        self.pack()


    def _create_gui(self):

        label = tk.Label(self, text="Adresse IP Broker : ")
        label.grid(column=0, row=1)

        text = tk.Entry(self, textvariable=self.champs['message'])
        text.grid(column=1, row=1, columnspan=2)

        text = tk.Entry(self, textvariable=self.champs['procedure'])
        text.grid(column=0, row=2, columnspan=3)

        button = tk.Button(self, text="Test subscribe", command=self.test)
        button.grid(column=0, row=100)

        button = tk.Button(self, text="Ecriture ficher", command=self.CreerFic)
        button.grid(column=2, row=100)

        button = tk.Button(self, text="Fermer", command=app.quit)
        button.grid(column=3, row=100)

    def test(self):
        global okFic
        okFic = False
        InitMqtt()

    def CreerFic(self):
        global okFic
        global fichier
        global objetFichier
        d = datetime.datetime.now()
        unixtime = int(time.mktime(d.timetuple()))  # récupération de la date et temps unix pour suffixe noms fichiers
        fichier = 'logs/log'+ str(unixtime) + '.csv'  # initialisation nom du flux video en sortie

        print('creation fichier' , fichier)
        okFic =True
        InitMqtt()

app = tk.Tk()
app.title("Subscribe Mqtt")
DemoWidget(app)
app.mainloop()

