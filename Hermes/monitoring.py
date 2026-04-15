import pygame
import paho.mqtt.client as mqtt
import re
import sys

# ==================== INITIALISATION PYGAME ====================
pygame.init()  # Important : initialiser avant get_desktop_sizes()
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Utiliser 90% de la taille d'écran avec marges
WIDTH = int(SCREEN_WIDTH * 0.9)
WIDTH = 1300
HEIGHT = int(SCREEN_HEIGHT * 0.85)  # 85% pour laisser place à la barre de tâches
HEIGHT = 900
print(f"📐 Résolution écran: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
print(f"📐 Fenêtre pygame: {WIDTH}x{HEIGHT}")
FPS = 50
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)

# ==================== DONNÉES REÇUES ====================
mqtt_topic  = "teensy/data"
data = {
    "FAV": 0, "FAR": 0, "FAF": 0, "FAFD": 0,
    "angleBraq": 0, "PwmVIT": 0, "deltaMicro": 0,
    "nb_tour_sec": 0.0, "nbPignon": 0,
    "cumDist": 0.0, "VIT": 0.0, "freq": 0
}


# ==================== CONFIGURATION MQTT ====================
MQTT_BROKER = "localhost"  # Pour les tests locaux
MQTT_PORT = 1883
MQTT_ENABLED = False  # Activer/Desactiver avec la touche 'M'

mqtt_client = None
mqtt_connected = False

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print("MQTT: Connecte!")
        # Subscribe au topic au moment de la connexion
        client.subscribe(mqtt_topic)
        print(f"MQTT: Subscrit à {mqtt_topic}")
    else:
        mqtt_connected = False
        print(f"MQTT: Echec connexion, code: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback deconnexion MQTT"""
    global mqtt_connected
    mqtt_connected = False
    print("MQTT: Deconnecte")

def init_mqtt():
    """Initialise MQTT"""
    global mqtt_client
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"MQTT: Connexion a {MQTT_BROKER}:{MQTT_PORT}...")
        return True
    except Exception as e:
        print(f"MQTT: Erreur: {e}")
        return False

def on_message(client, userdata, msg):
    """Callback reception message MQTT"""
    global data
    try:
        payload = msg.payload.decode("utf-8").strip()
        print(f"📥 Reçu : {payload}")

        # Nettoyage des marqueurs $ et # si présents
        payload = payload.replace("$", "").replace("#", "").strip()

        # Parsing des valeurs séparées par des espaces
        values = payload.split()
        if len(values) >= 10:
            data["FAV"]         = int(values[0])
            data["FAR"]         = int(values[1])
            data["FAF"]         = int(values[2])
            data["FAFD"]        = int(values[3])
            data["angleBraq"]   = int(values[4])
            data["PwmVIT"]      = int(values[5])
            data["deltaMicro"]  = int(values[6])
            data["nb_tour_sec"] = float(values[7])
            data["nbPignon"]    = int(values[8])
            data["cumDist"]     = float(values[9])
            data["VIT"]         = float(values[10])
        else:
            print(f"⚠️ Trame incomplète ({len(values)} valeurs) : {payload}")

    except Exception as e:
        print(f"⚠️ Erreur parsing: {e} — payload: {msg.payload}")

def sub(topic):
    """Subscribe à un topic MQTT"""
    global mqtt_client
    if mqtt_client:
        mqtt_client.subscribe(topic)
        print(f"MQTT: Subscrit à {topic}")

def pub(topic, value):
    """Publie une valeur sur un topic MQTT"""
    global mqtt_client, mqtt_connected
    if mqtt_client and mqtt_connected and MQTT_ENABLED:
        try:
          mqtt_client.publish(topic, value, qos=0, retain=False)
        except Exception as e:
            print(f"MQTT: Erreur publication: {e}")

def stop_mqtt():
    """Arrete MQTT"""
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


def draw_ui(screen, font):
    """Affiche l'interface utilisateur"""


    # Statut MQTT
    mqtt_status = "CONNECTE et ACTIF" if mqtt_connected and MQTT_ENABLED else \
                  "CONNECTE mais INACTIF" if mqtt_connected else \
                  "DECONNECTE" if MQTT_ENABLED else "DESACTIVE"
    
    y_offset = 20
    texts = [
        "=== Monitoring du robot HERMES + MQTT + 5 Lidars TFMiniPlus ===",
        "",
        f"MQTT: {mqtt_status}",
        "",
        # Affichage des données reçues
        f"FAV: {data['FAV']} cm      FAR: {data['FAR']} cm",
        f"FAF: {data['FAF']} cm      FAFD: {data['FAFD']} cm",
        f"Braquage: {data['angleBraq']}°      PWM: {data['PwmVIT']}",
        f"Vitesse: {data['VIT']:.2f} km/h      Dist: {data['cumDist']:.1f} cm",
        f"Pignons: {data['nbPignon']}      Tours/s: {data['nb_tour_sec']:.2f}",
        f"Freq loop: {data['freq']} Hz",    
    ]

    for i, text in enumerate(texts):
        if i == 0:
            color = RED
      
        elif "MQTT:" in text:
            if re.search(r'\bACTIF\b', text):  # Match "ACTIF" mais pas "INACTIF"
                color = GREEN
            elif re.search(r'\bCONNECTE\b', text):  # Match "CONNECTE" mais pas "DECONNECTE"
                color = YELLOW
            
            elif re.search(r'\bDECONNECTE\b', text):  # Match "DESACTIF" mais pas "ACTIF"
                color = RED
            
        surface = font.render(text, True, color)
        screen.blit(surface, (10, y_offset + i * 25))

# Charger l'image
image = pygame.image.load("vehicule_1.jpg")

# (Optionnel) Redimensionner l'image
image = pygame.transform.scale(image, (400, 300))
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Monitoring Hermes + MQTT")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Initialiser MQTT
    init_mqtt()


    # ========== VARIABLES DE CONTROLE ==========
    msg_count = 0
    last_report = pygame.time.get_ticks()

    running = True
    

    # ==================== BOUCLE PRINCIPALE ====================
    while running:
        # ========== GESTION DES ÉVÉNEMENTS ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            

            
            # ========== GESTION CLAVIER ==========
            if event.type == pygame.KEYDOWN:
                # M : MQTT
                if event.key == pygame.K_m:
                    global MQTT_ENABLED
                    MQTT_ENABLED = not MQTT_ENABLED
                    print(f"MQTT: {'ACTIVE' if MQTT_ENABLED else 'INACTIVE'}")
                    pass_to_timeline = False
            
   
        # ========== CONTROLES CLAVIER CONTINUS ==========
        keys = pygame.key.get_pressed()
        

        # Stats MQTT
        now = pygame.time.get_ticks()
        if now - last_report >= 1000:
            print(f"📤 Python publie {msg_count} msg/sec")
            msg_count = 0
            last_report = now
        
        # Limitation des publications 
        #time.sleep(0.02)
        
        # ========== AFFICHAGE ==========
        screen.fill([200, 200, 200])
        
        # ========== AFFICHAGE FPS ==========
        actual_fps = clock.get_fps()
        fps_text = font.render(f"FPS: {actual_fps:.1f}", True, RED)
        screen.blit(fps_text, (WIDTH - 120, 10))



        # ========== AFFICHAGE POSITION SOURIS ==========
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_text = font.render(f"({mouse_x}, {mouse_y})" , True, BLUE)
        screen.blit(mouse_text, (WIDTH - 230, 10))


        
        # ========== DESSIN INTERFACE UTILISATEUR ==========
        draw_ui(screen, font)
        
        # ========== RAFRAICHISSEMENT ECRAN ==========
        pygame.display.flip()
        clock.tick(FPS)
    

    # ========== ARRET PROPRE ==========
    stop_mqtt()
    pygame.quit()
    sys.exit()

# ==================== POINT D'ENTREE ====================
if __name__ == "__main__":
    main()