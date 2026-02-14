# 🦾 Robot Leg Kinematics - MQTT Control

Simulation de cinématique inverse pour jambe de robot avec contrôle MQTT temps réel vers Arduino R4 WiFi.







https://github.com/user-attachments/assets/7e486a98-69d9-4aa1-a991-552a9fedccd1







<img width="1461" height="471" alt="image" src="https://github.com/user-attachments/assets/2a956893-493f-47fc-bf98-6607d1e15ea5" />






## 📋 Table des matières

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Contribuer](#contribuer)
- [License](#license)

## 🎯 Aperçu

Ce projet permet de simuler et contrôler une jambe de robot à 3 segments avec cinématique inverse. La simulation se fait en Python/Pygame et les angles calculés sont envoyés en temps réel via MQTT vers une Arduino R4 WiFi qui contrôle 3 servomoteurs.

### Caractéristiques de la jambe

- **Segment 1 (Cuisse)** : L1 = 54mm
- **Segment 2 (Tibia)** : L2 = 54mm  
- **Segment 3 (Pied)** : L3 = 71mm
- **Contraintes** : θ1 < 90°, θ2 > 0°, pied toujours vertical

## ✨ Fonctionnalités

### Simulation Python (drag_n_drop.py)

- 🎮 **Contrôle cartésien** : Déplacer le pied avec les flèches ou la souris (drag & drop)
- 🔄 **Contrôle angulaire** : Contrôle direct des angles θ1, θ2, θ3
- 📐 **Cinématique inverse** : Calcul automatique des angles pour atteindre une position
- 🎬 **Animation rectangulaire** : Trajectoire prédéfinie en boucle
- 📡 **Publication MQTT** : Envoi des angles en temps réel (format: "θ1,θ2,θ3")
- 📊 **Repère cartésien** : Visualisation avec axes X/Y en millimètres
- ⚙️ **Contraintes physiques** : Respect des limites articulaires

### Contrôle Arduino

- 📶 **Connexion WiFi** : Arduino R4 WiFi
- 📡 **Client MQTT** : Réception des angles via topic `jambe_G`
- 🔧 **Contrôle servos** : Pilotage de 3 servomoteurs
- 📈 **Serial Plotter** : Visualisation temps réel des angles

## 🔧 Prérequis

### Matériel

- Arduino R4 WiFi (ou autre carte WiFi compatible)
- 3 servomoteurs (ex: SG90, MG90S)
- Alimentation externe 5V pour les servos (recommandé)
- Câbles de connexion

### Logiciels

- Python 3.8+
- Arduino IDE 2.x
- Broker MQTT (Mosquitto, HiveMQ, etc.)

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-username/robot-leg-kinematics.git
cd robot-leg-kinematics
```

### 2. Installer les dépendances Python

```bash
pip install pygame paho-mqtt
```

### 3. Installer le broker MQTT

#### Windows (Mosquitto)

1. Télécharger depuis [mosquitto.org](https://mosquitto.org/download/)
2. Installer et démarrer le service
3. Éditer `C:\Program Files\mosquitto\mosquitto.conf` :
   ```
   listener 1883 0.0.0.0
   allow_anonymous true
   ```
4. Redémarrer le service Mosquitto

#### Linux/Mac

```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

### 4. Librairies Arduino

Dans l'Arduino IDE, installer :
- **WiFiS3** (incluse pour R4 WiFi)
- **ArduinoMqttClient** (via le gestionnaire de bibliothèques)
- **Servo** (incluse)

## ⚙️ Configuration

### Python (drag_n_drop.py)

Modifier les paramètres MQTT (lignes 38-44) :

```python
MQTT_BROKER = "192.168.1.192"  # IP de votre broker
MQTT_PORT = 1883
MQTT_ENABLED = False  # Activer avec la touche 'M'
```

Ajuster la position du repère (ligne 50) :

```python
REPERE_ORIGIN_X = 700  # Position X de l'origine (pixels)
REPERE_ORIGIN_Y = 400  # Position Y de l'origine (pixels)
```

### Arduino (robot_leg_mqtt.ino)

Modifier les informations WiFi et MQTT (lignes 5-11) :

```cpp
const char* ssid = "VOTRE_SSID";
const char* password = "VOTRE_PASSWORD";
const char* broker = "192.168.1.192";  // IP du broker
```

Définir les pins des servos (si différent) :

```cpp
const int SERVO1_PIN = 9;   // Pin pour θ1
const int SERVO2_PIN = 10;  // Pin pour θ2
const int SERVO3_PIN = 11;  // Pin pour θ3
```

## 🚀 Utilisation

### 1. Démarrer le broker MQTT

```bash
# Vérifier que Mosquitto écoute sur 0.0.0.0:1883
netstat -an | findstr 1883
```

### 2. Téléverser le code Arduino

1. Ouvrir `robot_leg_mqtt.ino` dans l'IDE Arduino
2. Sélectionner la carte "Arduino UNO R4 WiFi"
3. Téléverser le code
4. Ouvrir le **Serial Monitor** (115200 baud) pour vérifier la connexion

### 3. Lancer la simulation Python

```bash
python drag_n_drop.py
```

### 4. Activer MQTT

Appuyer sur **M** dans la simulation → Statut doit passer à "CONNECTE et ACTIF" (vert)

### 5. Contrôler la jambe

| Touche | Action |
|--------|--------|
| **M** | Activer/Désactiver MQTT |
| **P** | Démarrer/Arrêter animation rectangulaire |
| **ESPACE** | Basculer mode cartésien ↔ angulaire |
| **Flèches** | Déplacer le pied (mode cartésien) |
| **SHIFT + Flèches** | Déplacement rapide |
| **R** | Réinitialiser (position verticale) |
| **Q/W** | Contrôle θ1 (mode angulaire) |
| **A/S** | Contrôle θ2 (mode angulaire) |
| **Z/X** | Contrôle θ3 (mode angulaire) |
| **Clic + Drag** | Déplacer le pied avec la souris |

## 🏗️ Architecture

```
┌─────────────────┐
│  Python/Pygame  │
│  Simulation IK  │
│  drag_n_drop.py │
└────────┬────────┘
         │ MQTT
         │ Topic: jambe_G
         │ Format: "θ1,θ2,θ3"
         ▼
┌─────────────────┐
│  Broker MQTT    │
│  Mosquitto      │
│  192.168.1.X    │
└────────┬────────┘
         │ MQTT
         ▼
┌─────────────────┐
│  Arduino R4     │
│  WiFi + MQTT    │
│  robot_leg.ino  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3 Servomoteurs │
│  θ1, θ2, θ3     │
└─────────────────┘
```

### Format du message MQTT

**Topic** : `jambe_G`  
**Payload** : `"45.23,90.56,-12.45"`  
- θ1 en degrés (Segment 1)
- θ2 en degrés (Segment 2)  
- θ3 en degrés (Segment 3)

### Système de coordonnées

```
      Y+
      │
      │   Hanche (0,0)
      │      ●
      │     ╱ │
      │    ╱  │ θ1
      │   ╱   │
      │  ●────┘ Genou
      │   \
      │    \ θ2
      │     \
      │      ● Cheville
      │      │
      │      │ θ3 (vertical)
      │      │
      │      ● Pied
──────┼──────────────── X+
      │
```

## 🛠️ Troubleshooting

### Python : "MQTT: DECONNECTE"

1. Vérifier que Mosquitto tourne :
   ```bash
   netstat -an | findstr 1883
   ```
2. Vérifier `MQTT_BROKER` dans le code
3. Tester avec MQTT Explorer

### Arduino : Erreur -2 (timeout)

1. Vérifier la connexion WiFi (Serial Monitor)
2. Vérifier l'IP du broker dans le code
3. Tester avec `ping 192.168.1.X`
4. Augmenter le timeout :
   ```cpp
   mqttClient.setConnectionTimeout(10000);
   ```

### Lag / Latence importante

1. Utiliser un broker local (pas test.mosquitto.org)
2. Vérifier le réseau WiFi (signal fort)
3. Réduire le seuil de publication (ligne Python) :
   ```python
   abs(t1_deg - self.last_theta1) > 0.1  # Au lieu de 0.01
   ```

### Servos ne bougent pas

1. Vérifier l'alimentation externe (5V suffisant)
2. Vérifier les pins (D9, D10, D11)
3. Vérifier la réception MQTT (Serial Monitor)
4. Tester avec :
   ```cpp
   servo1.write(90);  // Position neutre
   ```

## 📊 Visualisation

### Serial Plotter Arduino

Ouvrir **Outils → Traceur série** pour visualiser les 3 courbes d'angles en temps réel.

### MQTT Explorer

Connectez-vous à votre broker pour surveiller les messages :
- Topic : `jambe_G`
- Messages : `"45.23,90.56,-12.45"`

## 🎓 Ressources

- [Cinématique inverse](https://en.wikipedia.org/wiki/Inverse_kinematics)
- [Protocole MQTT](https://mqtt.org/)
- [Arduino R4 WiFi](https://docs.arduino.cc/hardware/uno-r4-wifi/)
- [Pygame Documentation](https://www.pygame.org/docs/)

## 🤝 Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 TODO

- [ ] Ajouter support pour plusieurs jambes
- [ ] Enregistrement/replay de trajectoires
- [ ] Export des angles en CSV
- [ ] Interface web de contrôle
- [ ] Support d'autres types de servos (dynamixel)
- [ ] Trajectoires personnalisées (cercle, spirale, marche)

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👤 Auteur

Votre Nom - [@votre-twitter](https://twitter.com/votre-twitter)

Lien du projet : [https://github.com/votre-username/robot-leg-kinematics](https://github.com/votre-username/robot-leg-kinematics)

## 🙏 Remerciements

- [Pygame](https://www.pygame.org/) pour la simulation graphique
- [Eclipse Paho](https://www.eclipse.org/paho/) pour le client MQTT Python
- [Arduino](https://www.arduino.cc/) pour la plateforme de prototypage
- [Mosquitto](https://mosquitto.org/) pour le broker MQTT

---

⭐ Si ce projet vous a été utile, n'hésitez pas à lui donner une étoile !
