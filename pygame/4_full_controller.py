"""
by ced with claude
"""
# ==================== IMPORTS ====================
import time

from sympy import re
import pygame
import math
import sys
import paho.mqtt.client as mqtt
from servo_timeline import *
import yaml
import os
from pathlib import Path
import re


"""
LOGICIEL DE CINEMATIQUE EMBARQUEE - JAMBE DE ROBOT

Configuration du repere cartesien :
- Modifiez REPERE_ORIGIN_X et REPERE_ORIGIN_Y pour deplacer l'origine du repere
- Modifiez REPERE_SCALE pour changer l'echelle (1.0 = 1 unite = 1 pixel)
- Utilisez place_leg_at_cartesian(x, y) pour placer la hanche dans le repere

Exemple : leg = RobotLeg(*place_leg_at_cartesian(0, 150))
Place la hanche a X=0, Y=150 dans le repere cartesien
"""
# ==================== CONFIGURATION FICHIER SAUVEGARDE DE LA TIMELINE ====================
CONFIG_FILE = "robot_leg_config.yaml"

# ==================== SAUVEGARDE/CHARGEMENT CONFIGURATION ====================
def save_config(timeline_yaw_left, timeline_yaw_right, leg_left):
    """Sauvegarde la configuration dans un fichier YAML"""
    config = {
        'timeline_yaw_left': {
            'keyframes': [
                {'time': kf.time, 'angle': kf.angle} 
                for kf in timeline_yaw_left.keyframes
            ]
        },
        'timeline_yaw_right': {
            'keyframes': [
                {'time': kf.time, 'angle': kf.angle} 
                for kf in timeline_yaw_right.keyframes
            ]
        },
        'animation': {
            'duration': leg_left.animation_duration
        },
        'ellipse': {
            'center_x': leg_left.ellipse_center_x,
            'center_y': leg_left.ellipse_center_y,
            'radius_x': leg_left.ellipse_radius_x,
            'radius_y': leg_left.ellipse_radius_y
        }
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"✅ Configuration sauvegardée dans '{CONFIG_FILE}'")
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

def load_config(timeline_yaw_left, timeline_yaw_right, leg_left, leg_right):
    """Charge la configuration depuis un fichier YAML"""
    if not os.path.exists(CONFIG_FILE):
        print(f"ℹ️  Pas de fichier de config trouvé, utilisation des valeurs par défaut")
        return False
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Charger timeline GAUCHE
        if 'timeline_yaw_left' in config:
            timeline_yaw_left.keyframes = [
                Keyframe(kf['time'], kf['angle']) 
                for kf in config['timeline_yaw_left']['keyframes']
            ]
        
        # Charger timeline DROITE
        if 'timeline_yaw_right' in config:
            timeline_yaw_right.keyframes = [
                Keyframe(kf['time'], kf['angle']) 
                for kf in config['timeline_yaw_right']['keyframes']
            ]
        
        # Charger durée animation
        if 'animation' in config:
            duration = config['animation']['duration']
            leg_left.animation_duration = duration
            leg_right.animation_duration = duration
            timeline_yaw_left.duration = duration
            timeline_yaw_right.duration = duration
        
        # Charger paramètres ellipse
        if 'ellipse' in config:
            leg_left.ellipse_center_x = config['ellipse']['center_x']
            leg_left.ellipse_center_y = config['ellipse']['center_y']
            leg_left.ellipse_radius_x = config['ellipse']['radius_x']
            leg_left.ellipse_radius_y = config['ellipse']['radius_y']
            
            leg_right.ellipse_center_x = config['ellipse']['center_x']
            leg_right.ellipse_center_y = config['ellipse']['center_y']
            leg_right.ellipse_radius_x = config['ellipse']['radius_x']
            leg_right.ellipse_radius_y = config['ellipse']['radius_y']
        
        print(f"✅ Configuration chargée depuis '{CONFIG_FILE}'")
        return True
        
    except Exception as e:
        print(f"❌ Erreur chargement: {e}")
        return False

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
FPS = 28
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)

# ==================== CONFIGURATION MQTT ====================
MQTT_BROKER = "localhost"  # Pour les tests locaux
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

# ==================== PARAMETRES DE LA JAMBE ====================
L1 = 54  # Longueur segment 1 (mm)
L2 = 59.5  # Longueur segment 2 (mm)
L3 = 62  # Longueur segment 3 (mm)

# Facteur de zoom pour la visualisation (3x pour mieux voir)
ZOOM_FACTOR = 1.5

# Longueurs pour l'affichage
L1_DISPLAY = L1 * ZOOM_FACTOR
L2_DISPLAY = L2 * ZOOM_FACTOR
L3_DISPLAY = L3 * ZOOM_FACTOR

# ==================== REPERE CARTESIEN ====================
REPERE_ORIGIN_X = 900  # Position X de l'origine du repere (en pixels ecran)
REPERE_ORIGIN_Y = 400  # Position Y de l'origine du repere (en pixels ecran)
REPERE_SCALE = ZOOM_FACTOR    # Echelle : 1.0 = 1 pixel ecran = 1 unite du repere
# Note : En pygame, Y augmente vers le bas. Le repere cartesien aura Y vers le haut

# ==================== FONCTIONS DE CONVERSION COORDONNEES ====================
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

# ==================== FONCTION DE DESSIN GRILLE ====================
def draw_cartesian_grid(screen):
    """Dessine le repere cartesien avec grille"""
    # Axes principaux
    # Axe X (horizontal, rouge)
    pygame.draw.line(screen, RED, (600, REPERE_ORIGIN_Y), (1200, REPERE_ORIGIN_Y), 2)
    # Axe Y (vertical, vert)
    pygame.draw.line(screen, GREEN, (REPERE_ORIGIN_X, 0), (REPERE_ORIGIN_X, HEIGHT/2), 2)
    
    # Origine
    pygame.draw.circle(screen, YELLOW, (REPERE_ORIGIN_X, REPERE_ORIGIN_Y), 8, 2)
    
    # Labels des axes
    font_small = pygame.font.Font(None, 20)
    label_x = font_small.render("X+", True, RED)
    label_y = font_small.render("Y+", True, GREEN)
    screen.blit(label_x, (1200, REPERE_ORIGIN_Y - 20))
    screen.blit(label_y, (REPERE_ORIGIN_X + 10, 10))
    
    # Origine (0,0)
    label_origin = font_small.render("(0,0)", True, YELLOW)
    screen.blit(label_origin, (REPERE_ORIGIN_X + 10, REPERE_ORIGIN_Y + 5))

# ==================== CLASSE ROBOT LEG ====================
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
        self.ellipse_center_y = 40.0       # Centre Y
        self.ellipse_radius_x = 75.0     # Grand rayon (horizontal) - plus grand
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
        

    def get_cycloid_position(self, t):
        t = t % 1.0

        if t <= 0.5:
            phase = t / 0.5
            x = self.ellipse_center_x + self.ellipse_radius_x * (1.0 - 2.0 * phase)
            y = self.ellipse_center_y  # même plancher que draw

        else:
            phase = (t - 0.5) / 0.5
            angle = math.pi + math.pi * phase
            x = self.ellipse_center_x + self.ellipse_radius_x * math.cos(angle)
            y = self.ellipse_center_y - self.ellipse_radius_y * math.sin(angle)  # même signe que draw

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
        """Dessine la trajectoire cycloid en D (sol droit + air en arc)"""
        color = YELLOW if self.animation_active else (100, 100, 100)
        points = []
        num_points = 100

        for i in range(num_points + 1):
            t = i / num_points

            if t <= 0.5:
                # Phase sol : ligne droite au plancher
                phase = t / 0.5
                x = self.ellipse_center_x + self.ellipse_radius_x * (1.0 - 2.0 * phase)
                y = self.ellipse_center_y  # plancher fixe

            else:
                # Phase air : demi-ellipse vers le haut
                phase = (t - 0.5) / 0.5
                angle = math.pi + math.pi * phase  # π → 2π
                x = self.ellipse_center_x + self.ellipse_radius_x * math.cos(angle)
                y = self.ellipse_center_y - self.ellipse_radius_y * math.sin(angle)

            points.append(cartesian_to_screen(x, y))

        pygame.draw.lines(screen, color, True, points, 2)

        # Centre
        screen_center = cartesian_to_screen(self.ellipse_center_x, self.ellipse_center_y)
        pygame.draw.circle(screen, color, (int(screen_center[0]), int(screen_center[1])), 4)

# ==================== FONCTION INTERFACE UTILISATEUR ====================
def draw_ui(screen, leg_left, leg_right, timeline_yaw_left, timeline_yaw_right, font):
    """Affiche l'interface utilisateur"""
    joints = leg_left.forward_kinematics()
    foot_pos = joints[3]

    joints_right = leg_right.forward_kinematics()
    foot_pos_right = joints_right[3]

    center_y = leg_left.ellipse_center_y

    # Convertir en coordonnees cartesiennes
    cart_x, cart_y = screen_to_cartesian(foot_pos[0], foot_pos[1])
    cart_x_right, cart_y_right = screen_to_cartesian(foot_pos_right[0], foot_pos_right[1])
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
        "F : Flip jambe gauche/jambe droite pour déplacement avec flèches", 
        "",
        f"{'jambe DROITE' if toggle else 'jambe GAUCHE'} activé",
        f"MQTT: {mqtt_status}",
        
 
        "",
        f"Hanche (repere): X={hip_cart_x:.1f}mm  Y={hip_cart_y:.1f}mm  /  L1={L1}mm, L2={L2}mm, L3={L3}mm",
        f"Pied Gauche (repere): X={cart_x:.1f}mm  Y={(cart_y - center_y):.1f}mm",
        f"Pied Droit (repere): X={cart_x_right:.1f}mm  Y={(cart_y_right - center_y) :.1f}  mm",
        "",
        f"jambe DROITE",
        f"θ1 (Segment 1): {math.degrees(leg_right.theta1):7.1f}° ",
        f"θ2 (Segment 2): {math.degrees(leg_right.theta2):7.1f}° ",
        f"θ3 (Segment 3): {math.degrees(leg_right.theta3):7.1f}°",
        f"roll_right: {timeline_yaw_right.get_current_angle():7.1f}°",
        "",
        f"jambe GAUCHE",
        f"θ1 (Segment 1): {math.degrees(leg_left.theta1):7.1f}° ",
        f"θ2 (Segment 2): {math.degrees(leg_left.theta2):7.1f}° ",
        f"θ3 (Segment 3): {math.degrees(leg_left.theta3):7.1f}°",
        f"roll_left: {timeline_yaw_left.get_current_angle():7.1f}°",
        "",
        # f"Dimensions reelles: L1={L1}mm | L2={L2}mm | L3={L3}mm",
    ]
    
    # Ajouter les contrôles angulaires si en mode angulaire
    if leg_left.control_mode == "cartesian":
        texts.insert(8, "MODE CARTESIEN: FLECHES GAUCHE/DROITE & FLECHES HAUT/BAS")
    
    if leg_left.control_mode == "angular":
        texts.insert(8, "MODE ANGULAIRE: Q/W (theta1), A/S (theta2), Z/X (theta3)")
    for i, text in enumerate(texts):
        if i == 0:
            color = YELLOW
        elif "Mode:" in text or "Contraintes:" in text:
            color = YELLOW if leg_left.control_mode == "cartesian" else YELLOW

        elif "MQTT:" in text:
            if re.search(r'\bACTIF\b', text):  # Match "ACTIF" mais pas "INACTIF"
                color = GREEN
            elif re.search(r'\bCONNECTE\b', text):  # Match "CONNECTE" mais pas "DECONNECTE"
                color = YELLOW
            
            elif re.search(r'\bDECONNECTE\b', text):  # Match "DESACTIF" mais pas "ACTIF"
                color = RED
            
            
            else:
                color = GRAY
        elif "Point VERT" in text or "Point ROUGE" in text:
            color = YELLOW
        elif "jambe GAUCHE" in text:
            color = GREEN
        elif "jambe DROITE" in text:
            color = RED
        elif "Note:" in text:
            color = GRAY
        elif re.search(r'\bMODE ANGULAIRE\b|\bMODE CARTESIEN\b', text):
            color = BLUE
        else:
            color = BLACK
        surface = font.render(text, True, color)
        screen.blit(surface, (10, y_offset + i * 25))


def save_ellipse_trajectory(leg_left, leg_right, timeline_yaw_left, timeline_yaw_right, filename="trajectory.h"):
    """
    Précalcule 800 points de la trajectoire cycloid + cinématique inverse
    et sauvegarde un tableau (800, 8) en fichier .h pour ESP32
    Colonnes : [θ1_G, θ2_G, θ3_G, roll_G, θ1_D, θ2_D, θ3_D, roll_D]
    """
    num_points = 800
    trajectory = []

    for i in range(num_points):
        t = i / num_points  # t dans [0, 1[

        # ── JAMBE GAUCHE (phase t) ────────────────────────────
        tx_left, ty_left = leg_left.get_cycloid_position(t)
        leg_left.inverse_kinematics_foot(tx_left, ty_left)
        t1_G = math.degrees(leg_left.theta1)
        t2_G = math.degrees(leg_left.theta2)
        t3_G = math.degrees(leg_left.theta3)
        roll_G = timeline_yaw_left.interpolate_angle(t)

        # ── JAMBE DROITE (opposition de phase +0.5) ───────────
        t_right = (t + 0.5) % 1.0
        tx_right, ty_right = leg_right.get_cycloid_position(t_right)
        leg_right.inverse_kinematics_foot(tx_right, ty_right)
        t1_D = math.degrees(leg_right.theta1)
        t2_D = math.degrees(leg_right.theta2)
        t3_D = math.degrees(leg_right.theta3)
        roll_D = timeline_yaw_right.interpolate_angle(t_right)

        trajectory.append([t1_G, t2_G, t3_G, roll_G, t1_D, t2_D, t3_D, roll_D])

    # ── SAUVEGARDE fichier .h pour ESP32 ──────────────────────
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("// Trajectoire précalculée - généré automatiquement\n")
            f.write("// Colonnes : [θ1_G, θ2_G, θ3_G, roll_G, θ1_D, θ2_D, θ3_D, roll_D]\n")
            f.write(f"// {num_points} points, 8 servos\n\n")
            f.write("#pragma once\n\n")
            f.write(f"#define TRAJECTORY_SIZE {num_points}\n")
            f.write(f"#define SERVO_COUNT 8\n\n")
            f.write("const float trajectory[TRAJECTORY_SIZE][SERVO_COUNT] = {\n")

            for i, row in enumerate(trajectory):
                vals = ", ".join(f"{v:8.3f}" for v in row)
                comma = "," if i < num_points - 1 else ""
                f.write(f"    {{{vals}}}{comma}  // t={i/num_points:.4f}\n")

            f.write("};\n")

        print(f"✅ Trajectoire sauvegardée dans '{filename}' ({num_points} points x 8 servos)")

    except Exception as e:
        print(f"❌ Erreur sauvegarde trajectoire: {e}")

# ==================== FONCTION PRINCIPALE ====================
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cinematique Jambe de Robot - IK + MQTT + Timeline Synchronisée")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Initialiser MQTT
    init_mqtt()
    
    # ========== CREATION DES JAMBES ==========
    # Jambe GAUCHE (visible, centrée, phase 0)
    leg_left = RobotLeg(*place_leg_at_cartesian(0, L1 +L2 + L3))
    
    # Jambe DROITE (virtuelle, décalée, phase +0.5) - Pour calculs MQTT uniquement
    leg_right = RobotLeg(*place_leg_at_cartesian(0, L1 +L2 + L3))
    
    # ========== CREATION TIMELINE ==========
    timeline_yaw_right = ServoTimeline(
        position=(600, 550),
        size=(600, 300),
        angle_range=(-25, 25),
        duration=leg_left.animation_duration,
        colorSPline=RED,
    )
    timeline_yaw_right.keyframes = [
        Keyframe(0.0, 0),
        Keyframe(0.5, 0),
        Keyframe(1.0, 0)
    ]
    
    timeline_yaw_left = ServoTimeline(
        position=(600, 550),
        size=(600, 300),
        angle_range=(-25, 25),
        duration=leg_left.animation_duration,
        colorSPline=GREEN,
    )
    timeline_yaw_left.keyframes = [
        Keyframe(0.0, 20),
        Keyframe(0.5, 20),
        Keyframe(1.0, 20)
    ]



   # ========== CHARGEMENT CONFIGURATION ==========
    load_config(timeline_yaw_left, timeline_yaw_right, leg_left, leg_right)
    

    # ========== CREATION BOUTONS UI ==========
    pos_boutton= 750  # position verticale des bouttons




    # Boutons durée
    btn_decrease = pygame.Rect(20, pos_boutton + 55, 40, 40)
    btn_increase = pygame.Rect(70, pos_boutton + 55, 40, 40)
    
    # Boutons rayon ellipse
    btn_radius_decrease = pygame.Rect(140, pos_boutton + 55, 40, 40)
    btn_radius_increase = pygame.Rect(190, pos_boutton + 55, 40, 40)







    # ========== PRÉCALCUL TRAJECTOIRE ESP32 ==========
    save_ellipse_trajectory(leg_left, leg_right, timeline_yaw_left, timeline_yaw_right)

    # Reset position après précalcul
    leg_left.theta1 = leg_left.theta2 = leg_left.theta3 = 0.0
    leg_right.theta1 = leg_right.theta2 = leg_right.theta3 = 0.0
    joints_left = leg_left.forward_kinematics()
    leg_left.foot_x, leg_left.foot_y = joints_left[3]
    joints_right = leg_right.forward_kinematics()
    leg_right.foot_x, leg_right.foot_y = joints_right[3]




    # ========== VARIABLES DE CONTROLE ==========
    msg_count = 0
    last_report = pygame.time.get_ticks()
    global toggle
    toggle = False
    running = True
    

    # ==================== BOUCLE PRINCIPALE ====================
    while running:
        # ========== GESTION DES ÉVÉNEMENTS ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Flag pour savoir si on doit passer l'événement à la timeline
            pass_to_timeline = True
            
            # ========== GESTION CLAVIER ==========
            if event.type == pygame.KEYDOWN:
                # ESPACE : Lancer/Arrêter les animations synchronisées
                if event.key == pygame.K_SPACE:
                    timeline_yaw_left.is_playing = not timeline_yaw_left.is_playing
                    timeline_yaw_right.is_playing = not timeline_yaw_right.is_playing
                    leg_left.animation_active = timeline_yaw_left.is_playing
                    leg_right.animation_active = timeline_yaw_left.is_playing
                    
                    if timeline_yaw_left.is_playing:
                        timeline_yaw_left.start_time = pygame.time.get_ticks() - timeline_yaw_left.current_time * timeline_yaw_left.duration * 1000
                        timeline_yaw_right.start_time = pygame.time.get_ticks() - timeline_yaw_left.current_time * timeline_yaw_left.duration * 1000

                        leg_left.control_mode = "cartesian"
                        leg_right.control_mode = "cartesian"
                        print(f"Animations synchronisées: REPRISES à t={timeline_yaw_left.current_time:.2f}")
                    else:
                        print(f"Animations synchronisées: ARRÊTÉES à t={timeline_yaw_left.current_time:.2f}")
                    
                    pass_to_timeline = False
                
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
                    
                    # Reset animations
                    timeline_yaw_left.current_time = 0.0
                    timeline_yaw_left.is_playing = False
                    timeline_yaw_right.current_time = 0.0
                    timeline_yaw_right.is_playing = False
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
                    
                    pass_to_timeline = False
                
                # M : MQTT
                elif event.key == pygame.K_m:
                    global MQTT_ENABLED
                    MQTT_ENABLED = not MQTT_ENABLED
                    print(f"MQTT: {'ACTIVE' if MQTT_ENABLED else 'INACTIVE'}")
                    pass_to_timeline = False
            
            # Gestion des événements de la timeline
            if pass_to_timeline:

                # ========== GESTION TIMELINES AVEC MODIFICATEURS ==========
                # CTRL + clic/drag = Éditer timeline VERTE (jambe gauche)
                timeline_yaw_left.handle_event(event, required_modifier=pygame.KMOD_CTRL)
                
                # ALT + clic/drag = Éditer timeline ROUGE (jambe droite)
                timeline_yaw_right.handle_event(event, required_modifier=pygame.KMOD_ALT)
            
            # ========== GESTION SOURIS ==========
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Boutons durée
                if btn_decrease.collidepoint(mouse_pos):
                    new_duration = max(1.0, leg_left.animation_duration - 0.25)
                    leg_left.animation_duration = new_duration
                    leg_right.animation_duration = new_duration
                    timeline_yaw_left.duration = new_duration
                    timeline_yaw_right.duration = new_duration
                    print(f"Durée: {new_duration:.2f}s")
                
                elif btn_increase.collidepoint(mouse_pos):
                    new_duration = min(30.0, leg_left.animation_duration + 0.25)
                    leg_left.animation_duration = new_duration
                    leg_right.animation_duration = new_duration
                    timeline_yaw_left.duration = new_duration
                    timeline_yaw_right.duration = new_duration
                    print(f"Durée: {new_duration:.2f}s")

                # Boutons rayon
                elif btn_radius_decrease.collidepoint(mouse_pos):
                    new_radius = max(20, leg_left.ellipse_radius_x - 1)
                    leg_left.ellipse_radius_x = new_radius
                    leg_right.ellipse_radius_x = new_radius
                    print(f"Rayon X: {new_radius}mm")
                
                elif btn_radius_increase.collidepoint(mouse_pos):
                    new_radius = min(200, leg_left.ellipse_radius_x + 1)
                    leg_left.ellipse_radius_x = new_radius
                    leg_right.ellipse_radius_x = new_radius
                    print(f"Rayon X: {new_radius}mm")

                # Drag & Drop du pied
                elif leg_left.control_mode == "cartesian":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if leg_left.is_near_foot(mouse_x, mouse_y):
                        leg_left.dragging = True
                    
                    elif leg_right.is_near_foot(mouse_x, mouse_y):
                        leg_right.dragging = True          
                    #else:
                    #    leg_left.inverse_kinematics_foot(mouse_x, mouse_y)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                leg_left.dragging = False
                leg_right.dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if leg_left.dragging and leg_left.control_mode == "cartesian":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    leg_left.inverse_kinematics_foot(mouse_x, mouse_y)

                elif leg_right.dragging and leg_left.control_mode == "cartesian":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    leg_right.inverse_kinematics_foot(mouse_x, mouse_y)
        
        # ========== MISE À JOUR ==========
        timeline_yaw_left.update()
        timeline_yaw_right.update()
        
        # Synchroniser le temps de l'ellipse avec la timeline
        if leg_left.animation_active and timeline_yaw_left.is_playing:
            leg_left.animation_time = timeline_yaw_left.current_time * leg_left.animation_duration
            leg_right.animation_time = leg_left.animation_time
        
        # Récupérer les angles des servos yaw
        yaw_left = timeline_yaw_left.get_current_angle()
        yaw_right = timeline_yaw_right.get_current_angle()
        
        # ========== CONTROLES CLAVIER CONTINUS ==========
        keys = pygame.key.get_pressed()
        
        # Animation ellipse (synchronisée avec la timeline)
        if leg_left.animation_active:
            t = leg_left.animation_time / leg_left.animation_duration
            
            # JAMBE GAUCHE
            target_x_left, target_y_left = leg_left.get_cycloid_position(t)
            leg_left.inverse_kinematics_foot(target_x_left, target_y_left)
            
            # JAMBE DROITE (opposition de phase)
            t_right = (t + 0.5) % 1.0
            target_x_right, target_y_right = leg_right.get_cycloid_position(t_right)
            leg_right.inverse_kinematics_foot(target_x_right, target_y_right)
        
        # Mode cartésien : contrôle avec flèches
        elif leg_left.control_mode == "cartesian":        
            speed = 1.0 
            
            leg = leg_left
            if keys[pygame.K_f]:
                toggle = not toggle
                time.sleep(0.2)  # Anti-rebond pour éviter les basculements rapides

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
            
            leg.inverse_kinematics_foot(leg.foot_x, leg.foot_y)
        
        # Mode angulaire : contrôle direct des angles
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
        
        # ========== PUBLICATION MQTT ==========
        # Jambe GAUCHE
        t1_deg_left = math.degrees(leg_left.theta1)
        t2_deg_left = math.degrees(leg_left.theta2)
        t3_deg_left = math.degrees(leg_left.theta3)
        roll_left = timeline_yaw_left.get_current_angle()
        message_left = f"{t1_deg_left:.1f},{t2_deg_left:.1f},{t3_deg_left:.1f},{roll_left:.1f}"
        pub("jambe_G", message_left)

        # Jambe DROITE
        t1_deg_right = math.degrees(leg_right.theta1)
        t2_deg_right = math.degrees(leg_right.theta2)
        t3_deg_right = math.degrees(leg_right.theta3)
        roll_right = timeline_yaw_right.get_current_angle()
        message_right = f"{t1_deg_right:.1f},{t2_deg_right:.1f},{t3_deg_right:.1f},{roll_right:.1f}"
        pub("jambe_D", message_right)

        msg_count += 1
        
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
        cart_x, cart_y = screen_to_cartesian(mouse_x, mouse_y)
        mouse_text = font.render(f"({mouse_x}, {mouse_y})" , True, BLUE)
        screen.blit(mouse_text, (WIDTH - 230, 10))

        # ========== DESSIN GRILLE ET WORKSPACE ==========
        draw_cartesian_grid(screen)
        leg_left.draw_workspace(screen)
        leg_left.draw_ellipse_trajectory(screen)
        
        # ========== DESSIN POINTS SUR ELLIPSE ==========
        if leg_left.animation_active:
            t = leg_left.animation_time / leg_left.animation_duration
            
            # Point ROUGE (jambe droite, opposition)
            t_right = (t + 0.5) % 1.0
            target_x_right, target_y_right = leg_right.get_cycloid_position(t_right)
            pygame.draw.circle(screen, GREEN, (int(target_x_right), int(target_y_right)), 12, 3)
            pygame.draw.circle(screen, GREEN, (int(target_x_right), int(target_y_right)), 6)
            
            # Point VERT (jambe gauche, principale)
            target_x_left, target_y_left = leg_left.get_cycloid_position(t)
            pygame.draw.circle(screen, RED, (int(target_x_left), int(target_y_left)), 12, 3)
            pygame.draw.circle(screen, RED, (int(target_x_left), int(target_y_left)), 6)
        



        # ========== DESSIN JAMBES ==========
        leg_left.draw(screen)
        leg_right.draw(screen)

        # ========== GESTION CURSEUR ==========
        if leg_left.control_mode == "cartesian":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if leg_left.is_near_foot(mouse_x, mouse_y):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            
        if leg_left.control_mode == "cartesian":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if leg_right.is_near_foot(mouse_x, mouse_y):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        
        # ========== DESSIN INDICATEURS PIED ==========
        if leg_left.control_mode == "cartesian":
            joints_left = leg_left.forward_kinematics()
            foot_pos_left = joints_left[3]
            joints_right = leg_right.forward_kinematics()
            foot_pos_right = joints_right[3]

            if leg_left.dragging:
                pygame.draw.circle(screen, YELLOW, (int(foot_pos_left[0]), int(foot_pos_left[1])), 25, 3)
                pygame.draw.circle(screen, YELLOW, (int(foot_pos_left[0]), int(foot_pos_left[1])), 18, 2)
            else:
                pygame.draw.circle(screen, GREEN, (int(foot_pos_left[0]), int(foot_pos_left[1])), 15, 2)
                pygame.draw.circle(screen, GREEN, (int(foot_pos_left[0]), int(foot_pos_left[1])), 20, 1)


            if leg_right.dragging:
                pygame.draw.circle(screen, YELLOW, (int(foot_pos_right[0]), int(foot_pos_right[1])), 25, 3)
                pygame.draw.circle(screen, YELLOW, (int(foot_pos_right[0]), int(foot_pos_right[1])), 18, 2)
            else:
                pygame.draw.circle(screen, RED, (int(foot_pos_right[0]), int(foot_pos_right[1])), 15, 2)
                pygame.draw.circle(screen, RED, (int(foot_pos_right[0]), int(foot_pos_right [1])), 20, 1)
        

        # ========== DESSIN INTERFACE UTILISATEUR ==========
        draw_ui(screen, leg_left, leg_right, timeline_yaw_left,timeline_yaw_right, font)
        
        # ========== DESSIN TIMELINE ==========
        # Dessiner la grille + courbe VERTE (jambe gauche)
        timeline_yaw_left.draw(screen, draw_background=True)

        # Dessiner SEULEMENT la courbe ROUGE par-dessus (jambe droite)
        timeline_yaw_right.draw(screen, draw_background=True)

        # Légende
        legend_y = 520
        pygame.draw.circle(screen, RED, (800, legend_y), 8)
        legend_left = font.render("Jambe droite (alt)", True, RED)
        screen.blit(legend_left, (820, legend_y - 10))

        pygame.draw.circle(screen, GREEN, (600, legend_y), 8)
        legend_right = font.render("Jambe gauche (ctrl)", True, GREEN)
        screen.blit(legend_right, (620, legend_y - 10))
        
        # ========== DESSIN CONTROLES DURATION TIME ==========
        # Titre
        title_text = font.render("Duration time", True, BLACK)
        screen.blit(title_text, (10, pos_boutton))

        # Fond
        duration_bg = pygame.Rect(10, pos_boutton + 20, 110, 90)
        pygame.draw.rect(screen, WHITE, duration_bg)
        pygame.draw.rect(screen, BLACK, duration_bg, 2)

        # Texte durée
        duration_text = font.render(f"{leg_left.animation_duration:.2f}s", True, BLACK)
        screen.blit(duration_text, (25, pos_boutton + 30))

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

        # ========== DESSIN CONTROLES ELLIPSE RADIUS X ==========
        # Titre
        radius_title_text = font.render("Ellipse Radius X", True, BLACK)
        screen.blit(radius_title_text, (130, pos_boutton))

        # Fond
        radius_bg = pygame.Rect(130, pos_boutton + 20, 110, 90)
        pygame.draw.rect(screen, WHITE, radius_bg)
        pygame.draw.rect(screen, BLACK, radius_bg, 2)

        # Texte rayon
        radius_text = font.render(f"{leg_left.ellipse_radius_x:.0f}mm", True, BLACK)
        screen.blit(radius_text, (145, pos_boutton + 30))

        # Bouton diminuer (-)
        pygame.draw.rect(screen, (200, 100, 100), btn_radius_decrease)
        pygame.draw.rect(screen, BLACK, btn_radius_decrease, 2)
        minus_radius = font.render("-", True, WHITE)
        screen.blit(minus_radius, (btn_radius_decrease.centerx - 4, btn_radius_decrease.centery - 9))

        # Bouton augmenter (+)
        pygame.draw.rect(screen, (100, 200, 100), btn_radius_increase)
        pygame.draw.rect(screen, BLACK, btn_radius_increase, 2)
        plus_radius = font.render("+", True, WHITE)
        screen.blit(plus_radius, (btn_radius_increase.centerx - 4, btn_radius_increase.centery - 9))

        # ========== RAFRAICHISSEMENT ECRAN ==========
        pygame.display.flip()
        clock.tick(FPS)
    

    # ========== ARRET PROPRE ==========
    # 💾 SAUVEGARDE AVANT DE QUITTER
    save_config(timeline_yaw_left, timeline_yaw_right, leg_left)


    # ========== ARRET PROPRE ==========
    stop_mqtt()
    pygame.quit()
    sys.exit()

# ==================== POINT D'ENTREE ====================
if __name__ == "__main__":
    main()