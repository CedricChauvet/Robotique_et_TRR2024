"""
by ced with claude
"""
import time
import pygame
import math
import sys
import paho.mqtt.client as mqtt
from servo_timeline import *

"""
LOGICIEL DE CINEMATIQUE EMBARQUEE - JAMBE DE ROBOT

Configuration du repere cartesien :
- Modifiez REPERE_ORIGIN_X et REPERE_ORIGIN_Y pour deplacer l'origine du repere
- Modifiez REPERE_SCALE pour changer l'echelle (1.0 = 1 unite = 1 pixel)
- Utilisez place_leg_at_cartesian(x, y) pour placer la hanche dans le repere

Exemple : leg = RobotLeg(*place_leg_at_cartesian(0, 150))
Place la hanche a X=0, Y=150 dans le repere cartesien
"""

# Initialisation de Pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 1300, 1000
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)

# ==================== CONFIGURATION MQTT ====================
MQTT_BROKER = "192.168.1.192"  # Pour les tests locaux
MQTT_PORT = 1883

MQTT_ENABLED = False  # Activer/Desactiver avec la touche 'M'

mqtt_client = None
mqtt_connected = False

def on_connect(client, userdata, flags, rc):
    """Callback connexion MQTT"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print("MQTT: Connecte!")
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
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"MQTT: Connexion a {MQTT_BROKER}:{MQTT_PORT}...")
        return True
    except Exception as e:
        print(f"MQTT: Erreur: {e}")
        return False

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

# Parametres de la jambe de robot
L1 = 54  # Longueur segment 1 (mm)
L2 = 54  # Longueur segment 2 (mm)
L3 = 71  # Longueur segment 3 (mm)

# Facteur de zoom pour la visualisation (3x pour mieux voir)
ZOOM_FACTOR = 1.5

# Longueurs pour l'affichage
L1_DISPLAY = L1 * ZOOM_FACTOR
L2_DISPLAY = L2 * ZOOM_FACTOR
L3_DISPLAY = L3 * ZOOM_FACTOR

# REPERE CARTESIEN (a configurer selon vos besoins)
REPERE_ORIGIN_X = 900  # Position X de l'origine du repere (en pixels ecran)
REPERE_ORIGIN_Y = 400  # Position Y de l'origine du repere (en pixels ecran)
REPERE_SCALE = ZOOM_FACTOR    # Echelle : 1.0 = 1 pixel ecran = 1 unite du repere
# Note : En pygame, Y augmente vers le bas. Le repere cartesien aura Y vers le haut


def screen_to_cartesian(screen_x, screen_y):
    """Convertit coordonnees ecran pygame vers coordonnees du repere cartesien (en mm)"""
    cart_x = (screen_x - REPERE_ORIGIN_X) / REPERE_SCALE  # en mm
    cart_y = (REPERE_ORIGIN_Y - screen_y) / REPERE_SCALE  # en mm, inverser Y
    return cart_x, cart_y

def cartesian_to_screen(cart_x, cart_y):
    """Convertit coordonnees du repere cartesien (en mm) vers coordonnees ecran pygame"""
    screen_x = REPERE_ORIGIN_X + cart_x * REPERE_SCALE
    screen_y = REPERE_ORIGIN_Y - cart_y * REPERE_SCALE  # Inverser Y
    return screen_x, screen_y

def place_leg_at_cartesian(cart_x, cart_y):
    """Calcule la position ecran de la hanche a partir de coordonnees cartesiennes
    Usage : leg = RobotLeg(*place_leg_at_cartesian(0, 100))
    Cela place la hanche a (0, 100) dans le repere cartesien
    """
    return cartesian_to_screen(cart_x, cart_y)

def draw_cartesian_grid(screen):
    """Dessine le repere cartesien avec grille"""
    # Axes principaux
    # Axe X (horizontal, rouge)
    pygame.draw.line(screen, RED, (WIDTH/2, REPERE_ORIGIN_Y), (WIDTH, REPERE_ORIGIN_Y), 2)
    # Axe Y (vertical, vert)
    pygame.draw.line(screen, GREEN, (REPERE_ORIGIN_X, 0), (REPERE_ORIGIN_X, HEIGHT/2), 2)
    
    # Origine
    pygame.draw.circle(screen, YELLOW, (REPERE_ORIGIN_X, REPERE_ORIGIN_Y), 8, 2)
    
    # Labels des axes
    font_small = pygame.font.Font(None, 20)
    label_x = font_small.render("X+", True, RED)
    label_y = font_small.render("Y+", True, GREEN)
    screen.blit(label_x, (WIDTH - 30, REPERE_ORIGIN_Y - 20))
    screen.blit(label_y, (REPERE_ORIGIN_X + 10, 10))
    
    # Origine (0,0)
    label_origin = font_small.render("(0,0)", True, YELLOW)
    screen.blit(label_origin, (REPERE_ORIGIN_X + 10, REPERE_ORIGIN_Y + 5))

class RobotLeg:
    def __init__(self, origin_x, origin_y):
        self.origin = [origin_x, origin_y]
        
        # Position initiale : tous les segments verticaux, tous les angles a 0
        self.theta1 = 0.0  # Angle segment 1 (par rapport a la verticale)
        self.theta2 = 0.0  # Angle segment 2 (par rapport au segment 1)
        self.theta3 = 0.0  # Angle segment 3 (par rapport au segment 2)
        
        # Position cible du pied
        joints = self.forward_kinematics()
        self.foot_x = joints[3][0]
        self.foot_y = joints[3][1]
        
        self.control_mode = "cartesian"  # "cartesian" ou "angular"
        self.dragging = False  # Etat du drag and drop
        
        # Animation rectangulaire
        self.animation_active = False
        self.animation_time = 0.0
        self.animation_duration = 4.0  # Duree totale en secondes
        
        # Paramètres de l'ellipse horizontale
        self.ellipse_center_x = 0       # Centre X
        self.ellipse_center_y = 40       # Centre Y
        self.ellipse_radius_x = 100     # Grand rayon (horizontal) - plus grand
        self.ellipse_radius_y = 20      # Petit rayon (vertical) - plus petit


    def update_rectangle_corners(self):
        """Calcule les 4 coins du rectangle en mm"""
        half_w = self.rect_width / 2
        half_h = self.rect_height / 2
        
        self.rect_corners = [
            (self.rect_center_x - half_w, self.rect_center_y + half_h),
            (self.rect_center_x + half_w, self.rect_center_y + half_h),
            (self.rect_center_x + half_w, self.rect_center_y - half_h),
            (self.rect_center_x - half_w, self.rect_center_y - half_h),
        ]
    

    def get_ellipse_position(self, t):
        """Position sur l'ellipse (t entre 0 et 1)"""
        t = t % 1.0
        
        # Convertir t en angle (0 à 2π) - SENS INVERSE
        angle = -2 * math.pi * t  # Négatif pour inverser le sens
        
        # Équations paramétriques de l'ellipse
        x = self.ellipse_center_x + self.ellipse_radius_x * math.cos(angle)
        y = self.ellipse_center_y + self.ellipse_radius_y * math.sin(angle)
        
        return cartesian_to_screen(x, y)
    
        
    def forward_kinematics(self):
        """Calcule la position de chaque articulation (cinematique directe)
        Convention : theta = 0 correspond a la verticale vers le bas
        """
        x0, y0 = self.origin
        
        # Angle absolu segment 1 (90° = vertical vers le bas)
        angle1_abs = math.pi/2 + self.theta1
        
        # Position articulation 1 (genou)
        x1 = x0 + L1_DISPLAY * math.cos(angle1_abs)
        y1 = y0 + L1_DISPLAY * math.sin(angle1_abs)
        
        # Angle absolu segment 2
        angle2_abs = angle1_abs + self.theta2
        
        # Position articulation 2 (cheville)
        x2 = x1 + L2_DISPLAY * math.cos(angle2_abs)
        y2 = y1 + L2_DISPLAY * math.sin(angle2_abs)
        
        # Angle absolu segment 3
        angle3_abs = angle2_abs + self.theta3
        
        # Position bout du pied
        x3 = x2 + L3_DISPLAY * math.cos(angle3_abs)
        y3 = y2 + L3_DISPLAY * math.sin(angle3_abs)
        
        return [(x0, y0), (x1, y1), (x2, y2), (x3, y3)]
    
    def inverse_kinematics_foot(self, foot_target_x, foot_target_y):
        """Cinematique inverse pour positionner le bout du pied avec pied vertical
        Contraintes : theta1 < 90°, theta2 > 0°, pied vertical
        """
        # Le pied doit rester vertical (segment 3 vertical)
        # La cheville est L3_DISPLAY pixels au-dessus du bout du pied
        ankle_x = foot_target_x
        ankle_y = foot_target_y - L3_DISPLAY
        
        dx = ankle_x - self.origin[0]
        dy = ankle_y - self.origin[1]
        
        # Distance hanche -> cheville
        distance = math.sqrt(dx**2 + dy**2)
        
        # Verifier si la cheville est atteignable
        max_reach = L1_DISPLAY + L2_DISPLAY
        min_reach = abs(L1_DISPLAY - L2_DISPLAY)
        
        # Limiter la distance si necessaire
        if distance > max_reach:
            distance = max_reach - 1
            if dx != 0 or dy != 0:
                scale = distance / math.sqrt(dx**2 + dy**2)
                ankle_x = self.origin[0] + dx * scale
                ankle_y = self.origin[1] + dy * scale
                foot_target_x = ankle_x
                foot_target_y = ankle_y + L3_DISPLAY
                dx = ankle_x - self.origin[0]
                dy = ankle_y - self.origin[1]
                distance = math.sqrt(dx**2 + dy**2)
        
        if distance < min_reach:
            distance = min_reach + 1
        
        # Angle de la direction hanche -> cheville
        angle_to_ankle = math.atan2(dy, dx)
        
        try:
            # Loi des cosinus pour trouver l'angle du genou
            cos_angle = (distance**2 - L1_DISPLAY**2 - L2_DISPLAY**2) / (2 * L1_DISPLAY * L2_DISPLAY)
            cos_angle = max(-1, min(1, cos_angle))
            angle_genou = math.acos(cos_angle)
            
            # Calculer l'angle du premier segment
            k1 = L1_DISPLAY + L2_DISPLAY * math.cos(angle_genou)
            k2 = L2_DISPLAY * math.sin(angle_genou)
            angle1_abs = angle_to_ankle - math.atan2(k2, k1)
            
            # Convertir en theta1 (par rapport a la verticale)
            theta1 = angle1_abs - math.pi/2
            
            # theta2 est l'angle entre segment 1 et segment 2
            theta2 = angle_genou
            
            # CONTRAINTES
            # Contrainte 1 : theta1 < 90°
            if theta1 >= math.radians(90):
                theta1 = math.radians(89.9)
            
            # Contrainte 2 : theta2 > 0°
            if theta2 <= 0:
                theta2 = math.radians(0.1)
            
            # Mise a jour des angles
            self.theta1 = theta1
            self.theta2 = theta2
            
            # theta3 pour garder le pied vertical
            angle1_abs_final = math.pi/2 + self.theta1
            angle2_abs_final = angle1_abs_final + self.theta2
            self.theta3 = math.pi/2 - angle2_abs_final
            
            # Mettre a jour la position cible
            self.foot_x = foot_target_x
            self.foot_y = foot_target_y
            
            return True
        except Exception as e:
            return False
    
    def is_near_foot(self, mouse_x, mouse_y, threshold=20):
        """Verifie si la souris est pres du point rouge (bout du pied)"""
        joints = self.forward_kinematics()
        foot_pos = joints[3]
        distance = math.sqrt((mouse_x - foot_pos[0])**2 + (mouse_y - foot_pos[1])**2)
        return distance < threshold
    
    def draw(self, screen):
        """Dessine la jambe du robot"""
        joints = self.forward_kinematics()
        
        # Dessiner les segments
        pygame.draw.line(screen, BLUE, joints[0], joints[1], 12)   # Segment 1
        pygame.draw.line(screen, GREEN, joints[1], joints[2], 12)  # Segment 2
        pygame.draw.line(screen, RED, joints[2], joints[3], 10)    # Segment 3
        
        # Dessiner les articulations
        pygame.draw.circle(screen, YELLOW, (int(joints[0][0]), int(joints[0][1])), 15)  # Hanche
        pygame.draw.circle(screen, YELLOW, (int(joints[1][0]), int(joints[1][1])), 12)  # Genou
        pygame.draw.circle(screen, YELLOW, (int(joints[2][0]), int(joints[2][1])), 12)  # Cheville
        pygame.draw.circle(screen, RED, (int(joints[3][0]), int(joints[3][1])), 10)     # Bout pied
    
    def draw_workspace(self, screen):
        """Dessine l'espace de travail de la jambe"""

        # Nouveau centre en coordonnées cartésienne
        center_x = 0  # ou self.origin en coordonnées cartésiennes si différent
        center_y = L1 + L2  # vers le bas (y négatif en cartésien)

        # Convertir en coordonnées écran
        screen_center = cartesian_to_screen(center_x, center_y)
        
        # Dessiner les cercles avec le nouveau centre
        pygame.draw.circle(screen, GRAY, screen_center, int(L1_DISPLAY + L2_DISPLAY), 1)
   
    
    def draw_ellipse_trajectory(self, screen):
        """Dessine la trajectoire elliptique horizontale"""
        color = YELLOW if self.animation_active else (100, 100, 100)
        
        # Générer des points sur l'ellipse en coordonnées cartésiennes
        points = []
        num_points = 100
        
        for i in range(num_points + 1):
            angle = 2 * math.pi * i / num_points
            x = self.ellipse_center_x + self.ellipse_radius_x * math.cos(angle)
            y = self.ellipse_center_y + self.ellipse_radius_y * math.sin(angle)
            screen_pos = cartesian_to_screen(x, y)
            points.append(screen_pos)
        
        # Dessiner l'ellipse
        pygame.draw.lines(screen, color, True, points, 2)
        
        # Dessiner le centre
        screen_center = cartesian_to_screen(self.ellipse_center_x, self.ellipse_center_y)
        pygame.draw.circle(screen, color, (int(screen_center[0]), int(screen_center[1])), 4)


def draw_ui(screen, leg_left, leg_right, timeline_yaw, font):
    """Affiche l'interface utilisateur"""
    joints = leg_left.forward_kinematics()
    joints_right = leg_right.forward_kinematics()
    foot_pos = joints[3]
    foot_right_pos = joints_right[3]
    
    # Convertir en coordonnees cartesiennes
    cart_x, cart_y = screen_to_cartesian(foot_pos[0], foot_pos[1])
    cart_right_x, cart_right_y = screen_to_cartesian(foot_right_pos[0], foot_right_pos[1])
    
    hip_cart_x, hip_cart_y = screen_to_cartesian(leg_left.origin[0], leg_left.origin[1])
    
    # Statut MQTT
    mqtt_status = "CONNECTE et ACTIF" if mqtt_connected and MQTT_ENABLED else \
                  "CONNECTE mais INACTIF" if mqtt_connected else \
                  "DECONNECTE" if MQTT_ENABLED else "DESACTIVE"
    
    y_offset = 20
    texts = [
        "=== CONTROLE CINEMATIQUE INVERSE + TIMELINE ===",
        "",
        "ESPACE : Play/Pause animations (Timeline + Ellipse) - Reprend là où arrêté",
        "R : Reset complet (position + animations à t=0)",
        "P : Basculer mode cartesien/angulaire",
        "M : Activer/Desactiver MQTT",
        "",
        "F : Flip jambe gauche/jambe droite pour déplacement avec flèches", 
        "FLECHES GAUCHE/DROITE : Deplacer le POINT ROUGE horizontalement",
        "FLECHES HAUT/BAS : Deplacer le POINT ROUGE verticalement",
        f"mode {'jambe DROITE' if toggle else 'jambes GAUCHE'} activé",
        "",
        f"Mode: {'CARTESIEN -> Controle position pied (X,Y)' if leg_left.control_mode == 'cartesian' else 'ANGULAIRE -> Controle angles (theta)'}",
        f"Animations: {'EN COURS (t={timeline_yaw.current_time:.2f})' if leg_left.animation_active else 'EN PAUSE'}",
        f"MQTT: {mqtt_status}",
        "Topics MQTT: jambe_G, jambe_D (opposition)",
        "Point VERT = Jambe principale | Point ROUGE = Jambe opposée",
        "",
        f"Hanche (repere): X={hip_cart_x:.1f}mm  Y={hip_cart_y:.1f}mm",
        f"Pied Gauche (repere): X={cart_x:.1f}mm  Y={cart_y:.1f}mm",
        f"Pied Droit (repere): X={cart_right_x:.1f}mm  Y={cart_right_y:.1f}mm",
        "",
        f"theta1 (Segment 1): {math.degrees(leg_left.theta1):7.1f}° ",
        f"theta2 (Segment 2): {math.degrees(leg_left.theta2):7.1f}° ",
        f"theta3 (Segment 3): {math.degrees(leg_left.theta3):7.1f}°",
        f"yaw_left: {timeline_yaw.get_current_angle():7.1f}°",
        "",

        f"Dtheta1 (Segment 1): {math.degrees(leg_right.theta1):7.1f}° ",
        f"Dtheta2 (Segment 2): {math.degrees(leg_right.theta2):7.1f}° ",
        f"Dtheta3 (Segment 3): {math.degrees(leg_right.theta3):7.1f}°",
        f"yaw_right: {timeline_yaw.get_opposite_angle():7.1f}°",
        "",



        f"Dimensions reelles: L1={L1}mm | L2={L2}mm | L3={L3}mm",
        
    ]
    
    # Ajouter les contrôles angulaires si en mode angulaire
    if leg_left.control_mode == "angular":
        texts.insert(7, "")
        texts.insert(8, "MODE ANGULAIRE: Q/W (theta1), A/S (theta2), Z/X (theta3)")
    
    for i, text in enumerate(texts):
        if i == 0:
            color = YELLOW
        elif "Mode:" in text or "Contraintes:" in text:
            color = GREEN if leg_left.control_mode == "cartesian" else YELLOW
        elif "Animations:" in text:
            color = GREEN if leg_left.animation_active else GRAY
        elif "MQTT:" in text:
            if "ACTIF" in text:
                color = GREEN
            elif "CONNECTE" in text:
                color = YELLOW
            else:
                color = GRAY
        elif "Point VERT" in text or "Point ROUGE" in text:
            color = YELLOW
        elif "POINT ROUGE" in text:
            color = RED
        elif "Note:" in text:
            color = GRAY
        else:
            color = BLACK
        surface = font.render(text, True, color)
        screen.blit(surface, (10, y_offset + i * 25))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cinematique Jambe de Robot - IK + MQTT + Timeline Synchronisée")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Initialiser MQTT
    init_mqtt()
    
    # Créer les DEUX jambes (calculs pour MQTT)
    # Jambe GAUCHE (visible, centrée, phase 0)
    leg_left = RobotLeg(*place_leg_at_cartesian(0, 179))
    
    # Jambe DROITE (virtuelle, décalée, phase +0.5) - Pour calculs MQTT uniquement
    leg_right = RobotLeg(*place_leg_at_cartesian(160, 179))
    
    # Créer UNE timeline pour 2 servos (yaw gauche et droite)
    timeline_yaw = ServoTimeline(
        position=(600, 600),     # En bas de l'écran
        size=(600, 300),        # Timeline horizontale
        angle_range=(-60, 60),  # Limites d'angle
        duration=leg_left.animation_duration,
      # Même durée que l'ellipse pour synchronisation
    )
    timeline_yaw.keyframes = [
            Keyframe(0.0, 0),
            Keyframe(0.5, 20),
            Keyframe(1.0, 0)
        ]   
    btn_decrease = pygame.Rect(20, HEIGHT - 80, 40, 40)
    btn_increase = pygame.Rect(70, HEIGHT - 80, 40, 40)

    btn_radius_decrease = pygame.Rect(140, HEIGHT - 80, 40, 40)
    btn_radius_increase = pygame.Rect(190, HEIGHT - 80, 40, 40)

    # Compteur pour debug
    msg_count = 0
    last_report = pygame.time.get_ticks()
    global toggle
    toggle = False
    running = True
    while running:
        # ========== GESTION DES ÉVÉNEMENTS ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Flag pour savoir si on doit passer l'événement à la timeline
            pass_to_timeline = True
            
            if event.type == pygame.KEYDOWN:
                # ESPACE : Lancer/Arrêter les animations synchronisées (Timeline + Ellipse)
                if event.key == pygame.K_SPACE:
                    # Toggle les deux animations ensemble
                    timeline_yaw.is_playing = not timeline_yaw.is_playing
                    leg_left.animation_active = timeline_yaw.is_playing
                    leg_left.animation_active = timeline_yaw.is_playing
                    leg_right.animation_active = timeline_yaw.is_playing
                    
                    if timeline_yaw.is_playing:
                        # Reprendre là où on s'est arrêté (ne pas remettre à 0)
                        timeline_yaw.start_time = pygame.time.get_ticks() - timeline_yaw.current_time * timeline_yaw.duration * 1000
                        leg_left.control_mode = "cartesian"
                        leg_left.control_mode = "cartesian"
                        leg_right.control_mode = "cartesian"
                        print(f"Animations synchronisées: REPRISES à t={timeline_yaw.current_time:.2f}")
                    else:
                        print(f"Animations synchronisées: ARRÊTÉES à t={timeline_yaw.current_time:.2f}")
                    
                    pass_to_timeline = False  # Ne pas passer ESPACE à la timeline
                
                # R : Reset tout
                elif event.key == pygame.K_r:
                    # Reset JAMBE GAUCHE
                    leg_left.theta1 = 0.0
                    leg_left.theta2 = 0.0
                    leg_left.theta3 = 0.0
                    joints_left = leg_left.forward_kinematics()
                    leg_left.foot_x = joints_left[3][0]
                    leg_left.foot_y = joints_left[3][1]
                    
                    # Reset JAMBE DROITE
                    leg_right.theta1 = 0.0
                    leg_right.theta2 = 0.0
                    leg_right.theta3 = 0.0
                    joints_right = leg_right.forward_kinematics()
                    leg_right.foot_x = joints_right[3][0]
                    leg_right.foot_y = joints_right[3][1]
                    
                    # Reset référence
                    leg = leg_left
                    
                    # Reset aussi les animations à 0
                    timeline_yaw.current_time = 0.0
                    timeline_yaw.is_playing = False
                    leg_left.animation_time = 0.0
                    leg_right.animation_time = 0.0
                    leg_left.animation_active = False
                    leg_right.animation_active = False
                    print("Reset complet : Position + Animations à t=0.0")
                    pass_to_timeline = False
                
                # P : Mode cartésien/angulaire
                elif event.key == pygame.K_p:
                    if leg_left.control_mode == "cartesian":
                        leg_left.control_mode = "angular"
                        leg_right.control_mode = "angular"
                    else:
                        leg_left.control_mode = "cartesian"
                        leg_right.control_mode = "cartesian"
                        joints_left = leg_left.forward_kinematics()
                        leg_left.foot_x = joints_left[3][0]
                        leg_left.foot_y = joints_left[3][1]
                        joints_right = leg_right.forward_kinematics()
                        leg_right.foot_x = joints_right[3][0]
                        leg_right.foot_y = joints_right[3][1]
                    
                    # Mettre à jour la référence
                    leg_left.control_mode = leg_left.control_mode
                    pass_to_timeline = False
                
                # M : MQTT
                elif event.key == pygame.K_m:
                    global MQTT_ENABLED
                    MQTT_ENABLED = not MQTT_ENABLED
                    print(f"MQTT: {'ACTIVE' if MQTT_ENABLED else 'INACTIVE'}")
                    pass_to_timeline = False
            
            # Gestion des événements de la timeline (sauf touches spéciales)
            if pass_to_timeline:
                timeline_yaw.handle_event(event)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Bouton diminuer durée
                if btn_decrease.collidepoint(mouse_pos):
                    new_duration = max(1.0, leg_left.animation_duration - 0.25)
                    leg_left.animation_duration = new_duration
                    leg_right.animation_duration = new_duration
                    timeline_yaw.duration = new_duration
                    print(f"Durée: {new_duration:.2f}s")
                
                # Bouton augmenter durée
                elif btn_increase.collidepoint(mouse_pos):
                    new_duration = min(30.0, leg_left.animation_duration + 0.25)
                    leg_left.animation_duration = new_duration
                    leg_right.animation_duration = new_duration
                    timeline_yaw.duration = new_duration
                    print(f"Durée: {new_duration:.2f}s")

                #  Bouton diminuer rayon X
                elif btn_radius_decrease.collidepoint(mouse_pos):
                    new_radius = max(20, leg_left.ellipse_radius_x - 1)
                    leg_left.ellipse_radius_x = new_radius
                    leg_right.ellipse_radius_x = new_radius
                    print(f"Rayon X: {new_radius}mm")
                
                #  Bouton augmenter rayon X
                elif btn_radius_increase.collidepoint(mouse_pos):
                    new_radius = min(200, leg_left.ellipse_radius_x + 1)
                    leg_left.ellipse_radius_x = new_radius
                    leg_right.ellipse_radius_x = new_radius
                    print(f"Rayon X: {new_radius}mm")


                if leg_left.control_mode == "cartesian":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if leg_left.is_near_foot(mouse_x, mouse_y):
                        leg_left.dragging = True
                    else:
                        leg_left.inverse_kinematics_foot(mouse_x, mouse_y)
            
            if event.type == pygame.MOUSEBUTTONUP:
                leg_left.dragging = False
            
            if event.type == pygame.MOUSEMOTION:
                if leg_left.dragging and leg_left.control_mode == "cartesian":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    leg_left.inverse_kinematics_foot(mouse_x, mouse_y)
        
        # ========== MISE À JOUR ==========
        # Mise à jour de la timeline
        timeline_yaw.update()
        
        # ✅ SYNCHRONISER le temps de l'ellipse avec la timeline
        if leg_left.animation_active and timeline_yaw.is_playing:
            leg_left.animation_time = timeline_yaw.current_time * leg_left.animation_duration
            leg_left.animation_time = leg_left.animation_time
            leg_right.animation_time = leg_left.animation_time
        
        # Récupérer les angles des servos yaw
        yaw_left = timeline_yaw.get_current_angle()
        yaw_right = timeline_yaw.get_opposite_angle()
        
        # Controles clavier
        keys = pygame.key.get_pressed()
        
        # Animation ellipse (synchronisée avec la timeline)
        if leg_left.animation_active:
            t = leg_left.animation_time / leg_left.animation_duration
            
            # JAMBE GAUCHE : suit l'ellipse au temps t
            target_x_left, target_y_left = leg_left.get_ellipse_position(t)
            leg_left.inverse_kinematics_foot(target_x_left, target_y_left)
            
            # JAMBE DROITE : suit l'ellipse au temps (t + 0.5) en OPPOSITION
            t_right = (t + 0.5) % 1.0
            target_x_right, target_y_right = leg_right.get_ellipse_position(t_right)
            leg_right.inverse_kinematics_foot(target_x_right, target_y_right)
        
        elif leg_left.control_mode == "cartesian":        
            speed = 1.0 
        
            leg = leg_left
            if keys[pygame.K_f]:
                toggle = not toggle

            if toggle:
                leg = leg_right
            else:
                leg = leg_left

            if keys[pygame.K_LEFT]:
                leg.foot_x -= speed
            if keys[pygame.K_RIGHT]:
                leg.foot_x += speed
            if keys[pygame.K_UP]:
                leg.foot_y -= speed
            if keys[pygame.K_DOWN]:
                leg.foot_y += speed
            
            leg.inverse_kinematics_foot(leg_left.foot_x, leg_left.foot_y)
            
        else:
            angular_speed = 0.02
            
            if keys[pygame.K_q]:
                new_theta1 = leg_left.theta1 + angular_speed
                if new_theta1 < math.radians(90):
                    leg_left.theta1 = new_theta1
            if keys[pygame.K_w]:
                leg_left.theta1 -= angular_speed
            
            if keys[pygame.K_a]:
                leg_left.theta2 += angular_speed
            if keys[pygame.K_s]:
                new_theta2 = leg_left.theta2 - angular_speed
                if new_theta2 > 0:
                    leg_left.theta2 = new_theta2
            
            if keys[pygame.K_z]:
                leg_left.theta3 += angular_speed
            if keys[pygame.K_x]:
                leg_left.theta3 -= angular_speed
        
        
        # Jambe GAUCHE
        t1_deg_left = math.degrees(leg_left.theta1)
        t2_deg_left = math.degrees(leg_left.theta2)
        t3_deg_left = math.degrees(leg_left.theta3)
        yaw_left = timeline_yaw.get_current_angle()
        message_left = f"{t1_deg_left:.1f},{t2_deg_left:.1f},{t3_deg_left:.1f},{yaw_left:.1f}"
        pub("jambe_G", message_left)

        # Jambe DROITE
        t1_deg_right = math.degrees(leg_right.theta1)
        t2_deg_right = math.degrees(leg_right.theta2)
        t3_deg_right = math.degrees(leg_right.theta3)
        yaw_right = timeline_yaw.get_opposite_angle()
        message_right = f"{t1_deg_right:.1f},{t2_deg_right:.1f},{t3_deg_right:.1f},{yaw_right:.1f}"
        pub("jambe_D", message_right)

        msg_count += 1
        
        # Afficher stats toutes les secondes
        now = pygame.time.get_ticks()
        if now - last_report >= 1000:
            print(f"📤 Python publie {msg_count} msg/sec")
            msg_count = 0
            last_report = now
        
        # Limitation des publications 
        time.sleep(0.02)
        
        # ========== AFFICHAGE ==========
        screen.fill([200, 200, 200])
        
        draw_cartesian_grid(screen)
        
        # Gestion du curseur
        if leg_left.control_mode == "cartesian":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if leg_left.is_near_foot(mouse_x, mouse_y):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        leg_left.draw_workspace(screen)
        leg_left.draw_ellipse_trajectory(screen)
        
        # Dessiner un POINT ROUGE sur l'ellipse en opposition (jambe droite virtuelle)
        if leg_left.animation_active:
            t = leg_left.animation_time / leg_left.animation_duration
            t_right = (t + 0.5) % 1.0
            target_x_right, target_y_right = leg_right.get_ellipse_position(t_right)
            pygame.draw.circle(screen, RED, (int(target_x_right), int(target_y_right)), 12, 3)
            pygame.draw.circle(screen, RED, (int(target_x_right), int(target_y_right)), 6)
            
            # Dessiner un POINT VERT sur l'ellipse pour la jambe principale
            target_x_left, target_y_left = leg_left.get_ellipse_position(t)
            pygame.draw.circle(screen, GREEN, (int(target_x_left), int(target_y_left)), 12, 3)
            pygame.draw.circle(screen, GREEN, (int(target_x_left), int(target_y_left)), 6)
        
        # Dessiner seulement la JAMBE GAUCHE
        leg_left.draw(screen)
        
        if leg_left.control_mode == "cartesian":
            # Dessiner les indicateurs pour la JAMBE (gauche visible)
            joints_left = leg_left.forward_kinematics()
            foot_pos_left = joints_left[3]
            if leg_left.dragging:
                pygame.draw.circle(screen, YELLOW, (int(foot_pos_left[0]), int(foot_pos_left[1])), 25, 3)
                pygame.draw.circle(screen, YELLOW, (int(foot_pos_left[0]), int(foot_pos_left[1])), 18, 2)
            else:
                pygame.draw.circle(screen, GREEN, (int(foot_pos_left[0]), int(foot_pos_left[1])), 15, 2)
                pygame.draw.circle(screen, GREEN, (int(foot_pos_left[0]), int(foot_pos_left[1])), 20, 1)
        
        draw_ui(screen, leg_left, leg_right, timeline_yaw, font)
        
        # ✅ FOND BLANC POUR LA TIMELINE (évite le clignotement)
        timeline_bg = pygame.Rect(40, 590, 620, 170)  # Un peu plus grand que la timeline
        #pygame.draw.rect(screen, WHITE, timeline_bg)
        #pygame.draw.rect(screen, BLACK, timeline_bg, 2)  # Bordure noire
        
        # Dessiner la timeline
        timeline_yaw.draw(screen)
        

        # Titre au-dessus du rectangle
        title_text = font.render("Duration time", True, BLACK)
        screen.blit(title_text, (10, HEIGHT - 110))

        # Fond
        duration_bg = pygame.Rect(10, HEIGHT - 90, 110, 90)
        pygame.draw.rect(screen, WHITE, duration_bg)
        pygame.draw.rect(screen, BLACK, duration_bg, 2)

        # Texte durée
        duration_text = font.render(f"{leg_left.animation_duration:.2f}s", True, BLACK)
        screen.blit(duration_text, (25, HEIGHT - 30))

        # Bouton diminuer (-)
        pygame.draw.rect(screen, (200, 100, 100), btn_decrease)
        pygame.draw.rect(screen, BLACK, btn_decrease, 2)
        minus_text = font.render("-", True, WHITE)
        screen.blit(minus_text, (btn_decrease.centerx - 4, btn_decrease.centery - 9))

        # Bouton augmenter (+)
        pygame.draw.rect(screen, (100, 200, 100), btn_increase)
        pygame.draw.rect(screen, BLACK, btn_increase, 2)
        plus_text = font.render("+", True, WHITE)
        screen.blit(plus_text, (btn_increase.centerx - 4, btn_increase.centery - 9))



        # Titre Ellipse Radius X
        radius_title_text = font.render("Ellipse Radius X", True, BLACK)
        screen.blit(radius_title_text, (130, HEIGHT - 110))

        # Fond du rectangle rayon
        radius_bg = pygame.Rect(130, HEIGHT - 90, 110, 90)
        pygame.draw.rect(screen, WHITE, radius_bg)
        pygame.draw.rect(screen, BLACK, radius_bg, 2)

        # Texte rayon
        radius_text = font.render(f"{leg_left.ellipse_radius_x:.0f}mm", True, BLACK)
        screen.blit(radius_text, (145, HEIGHT - 30))

        # Bouton diminuer rayon (-)
        pygame.draw.rect(screen, (200, 100, 100), btn_radius_decrease)
        pygame.draw.rect(screen, BLACK, btn_radius_decrease, 2)
        minus_radius = font.render("-", True, WHITE)
        screen.blit(minus_radius, (btn_radius_decrease.centerx - 4, btn_radius_decrease.centery - 9))

        # Bouton augmenter rayon (+)
        pygame.draw.rect(screen, (100, 200, 100), btn_radius_increase)
        pygame.draw.rect(screen, BLACK, btn_radius_increase, 2)
        plus_radius = font.render("+", True, WHITE)
        screen.blit(plus_radius, (btn_radius_increase.centerx - 4, btn_radius_increase.centery - 9))



        pygame.display.flip()

        clock.tick(FPS)
    
    stop_mqtt()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()