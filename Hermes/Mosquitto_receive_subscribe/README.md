Le programme python « MqttReceiveTinker.py »
 a pour objet de recevoir les messages Mqtt émis par l'ESP32 pilotant un robot roulant et de les écrire dans un fichier CSV.
 Il est nécessite que Mosquitto soit installé sur le PC sur lequel est installé le programme ou sur un PC appartenant au même réseau. L'Esp32 doit être aussi sur le même réseau.

 
Prérequis
1. Matériel
 - Esp2 pour le robot roulant
 - Un Pc windows 11
2. Logiciels
- Python 3.13+
- Arduino IDE 2.x
- Broker MQTT (Mosquitto.)
3.Installation
1.  Récupérer le fichier python
De préférence créer un environnement virtuel avec la version 3.13 de python
2. Installer les dépendances Python
- pip install paho-mqtt

- pip install tinker    // inteface graphique pour Python

- Les autres dépendances (socket, csv, time et datetimesont inclues dans la version 


3. Installer le broker MQTT Windows (Mosquitto)
   - Télécharger depuis mosquitto.org
   - Installer et démarrer le service
   - Éditer C:\Program Files\mosquitto\mosquitto.conf :listener 1883 0.0.0.0 allow_anonymous true
   - Redémarrer le service Mosquitto
