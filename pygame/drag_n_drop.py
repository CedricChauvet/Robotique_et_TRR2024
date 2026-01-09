import pygame
import math
import sys
import paho.mqtt.client as mqtt

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
WIDTH, HEIGHT = 1000, 800
FPS = 60
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
MQTT_TOPIC_THETA1 = "robot/leg/theta1"
MQTT_TOPIC_THETA2 = "robot/leg/theta2"
MQTT_TOPIC_THETA3 = "robot/leg/theta3"
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
          mqtt_client.publish(topic, value)

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
REPERE_ORIGIN_X = 700  # Position X de l'origine du repere (en pixels ecran)
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
    pygame.draw.line(screen, RED, (0, REPERE_ORIGIN_Y), (WIDTH, REPERE_ORIGIN_Y), 2)
    # Axe Y (vertical, vert)
    pygame.draw.line(screen, GREEN, (REPERE_ORIGIN_X, 0), (REPERE_ORIGIN_X, HEIGHT), 2)
    
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
        self.animation_duration = 8.0  # Duree totale en secondes
        
        # Rectangle (en mm)
        self.rect_width = 60
        self.rect_height = 40
        self.rect_center_x = 0
        self.rect_center_y = 30
        
        self.update_rectangle_corners()
        
        # MQTT - dernier angles publies
        self.last_theta1 = None
        self.last_theta2 = None
        self.last_theta3 = None
    
    
    def publish_angles_mqtt(self):
        """Publie les 3 angles en un seul message"""
        # Convertir en degres
        t1_deg = math.degrees(self.theta1)
        t2_deg = math.degrees(self.theta2)
        t3_deg = math.degrees(self.theta3)
        
        # Publier seulement si changement significatif (>0.01 degre)
        if (self.last_theta1 is None or 
            abs(t1_deg - self.last_theta1) > 0.01 or
            abs(t2_deg - self.last_theta2) > 0.01 or
            abs(t3_deg - self.last_theta3) > 0.01):
            
            # Concatener les 3 angles: "45.2,90.5,-12.3"
            message = f"{t1_deg:.2f},{t2_deg:.2f},{t3_deg:.2f}"
            pub("jambe_G", message)
            
            self.last_theta1 = t1_deg
            self.last_theta2 = t2_deg
            self.last_theta3 = t3_deg

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
    
    def get_rectangle_position(self, t):
        """Position sur le rectangle (t entre 0 et 1)"""
        t = t % 1.0
        
        if t < 0.25:
            progress = t * 4
            x = self.rect_corners[0][0] + (self.rect_corners[1][0] - self.rect_corners[0][0]) * progress
            y = self.rect_corners[0][1]
        elif t < 0.5:
            progress = (t - 0.25) * 4
            x = self.rect_corners[1][0]
            y = self.rect_corners[1][1] + (self.rect_corners[2][1] - self.rect_corners[1][1]) * progress
        elif t < 0.75:
            progress = (t - 0.5) * 4
            x = self.rect_corners[2][0] + (self.rect_corners[3][0] - self.rect_corners[2][0]) * progress
            y = self.rect_corners[2][1]
        else:
            progress = (t - 0.75) * 4
            x = self.rect_corners[3][0]
            y = self.rect_corners[3][1] + (self.rect_corners[0][1] - self.rect_corners[3][1]) * progress
        
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
            
            # Publier les angles via MQTT
            self.publish_angles_mqtt()
            
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
        pygame.draw.circle(screen, GRAY, self.origin, int(L1_DISPLAY + L2_DISPLAY), 1)
        pygame.draw.circle(screen, GRAY, self.origin, int(abs(L1_DISPLAY - L2_DISPLAY)), 1)
    
    def draw_rectangle_trajectory(self, screen):
        """Dessine la trajectoire rectangulaire"""
        if len(self.rect_corners) == 4:
            screen_corners = [cartesian_to_screen(x, y) for x, y in self.rect_corners]
            color = YELLOW if self.animation_active else (100, 100, 100)
            
            for i in range(4):
                start = screen_corners[i]
                end = screen_corners[(i + 1) % 4]
                pygame.draw.line(screen, color, start, end, 2)
            
            for corner in screen_corners:
                pygame.draw.circle(screen, color, (int(corner[0]), int(corner[1])), 4)

def draw_ui(screen, leg, font):
    """Affiche l'interface utilisateur"""
    joints = leg.forward_kinematics()
    foot_pos = joints[3]
    
    # Convertir en coordonnees cartesiennes
    cart_x, cart_y = screen_to_cartesian(foot_pos[0], foot_pos[1])
    hip_cart_x, hip_cart_y = screen_to_cartesian(leg.origin[0], leg.origin[1])
    
    # Statut MQTT
    mqtt_status = "CONNECTE et ACTIF" if mqtt_connected and MQTT_ENABLED else \
                  "CONNECTE mais INACTIF" if mqtt_connected else \
                  "DECONNECTE" if MQTT_ENABLED else "DESACTIVE"
    
    y_offset = 20
    texts = [
        "=== CONTROLE CINEMATIQUE INVERSE ===",
        "",
        "FLECHES GAUCHE/DROITE : Deplacer le POINT ROUGE horizontalement",
        "FLECHES HAUT/BAS : Deplacer le POINT ROUGE verticalement",
        "SHIFT + FLECHES : Deplacement rapide (x2.5)",
        "",
        "CLIC + DRAG sur point rouge : Deplacer avec la souris",
        "CLIC ailleurs : Teleporter le point rouge",
        "ESPACE : Basculer mode controle",
        "R : Reinitialiser position (jambe verticale)",
        "P : Demarrer/Arreter animation rectangulaire",
        "M : Activer/Desactiver MQTT",
        "",
        f"Mode: {'CARTESIEN -> Controle position pied (X,Y)' if leg.control_mode == 'cartesian' else 'ANGULAIRE -> Controle angles (theta)'}",
        f"Animation: {'ACTIVE' if leg.animation_active else 'INACTIVE'}",
        f"MQTT: {mqtt_status}",
        "Contraintes: Pied VERTICAL | theta1 < 90° | theta2 > 0°",
        "",
        f"Hanche (repere): X={hip_cart_x:.1f}mm  Y={hip_cart_y:.1f}mm",
        f"Pied (repere): X={cart_x:.1f}mm  Y={cart_y:.1f}mm",
        "",
        f"theta1 (Segment 1): {math.degrees(leg.theta1):7.1f}° ",
        f"theta2 (Segment 2): {math.degrees(leg.theta2):7.1f}° ",
        f"theta3 (Segment 3): {math.degrees(leg.theta3):7.1f}°",
        "",
        f"Dimensions reelles: L1={L1}mm | L2={L2}mm | L3={L3}mm",
        f"Rectangle: {leg.rect_width}mm x {leg.rect_height}mm",
        "",
        "Note: theta=0° correspond a la position verticale"
    ]
    
    if leg.control_mode == "angular":
        texts[2] = "Q/W : Controle theta1 (segment 1)"
        texts[3] = "A/S : Controle theta2 (segment 2)"
        texts[4] = "Z/X : Controle theta3 (segment 3)"
    
    for i, text in enumerate(texts):
        if i == 0:
            color = YELLOW
        elif "Mode:" in text or "Contraintes:" in text:
            color = GREEN if leg.control_mode == "cartesian" else YELLOW
        elif "Animation:" in text:
            color = GREEN if leg.animation_active else GRAY
        elif "MQTT:" in text:
            if "ACTIF" in text:
                color = GREEN
            elif "CONNECTE" in text:
                color = YELLOW
            else:
                color = GRAY
        elif "POINT ROUGE" in text:
            color = RED
        elif "Note:" in text:
            color = GRAY
        else:
            color = WHITE
        surface = font.render(text, True, color)
        screen.blit(surface, (10, y_offset + i * 25))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cinematique Jambe de Robot - Controle IK + MQTT")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Initialiser MQTT
    init_mqtt()
    
    # Creer la jambe
    leg = RobotLeg(*place_leg_at_cartesian(0, 179))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if leg.control_mode == "cartesian":
                        leg.control_mode = "angular"
                    else:
                        leg.control_mode = "cartesian"
                        joints = leg.forward_kinematics()
                        leg.foot_x = joints[3][0]
                        leg.foot_y = joints[3][1]
                
                if event.key == pygame.K_r:
                    leg.theta1 = 0.0
                    leg.theta2 = 0.0
                    leg.theta3 = 0.0
                    joints = leg.forward_kinematics()
                    leg.foot_x = joints[3][0]
                    leg.foot_y = joints[3][1]
                    leg.publish_angles_mqtt()
                
                if event.key == pygame.K_p:
                    leg.animation_active = not leg.animation_active
                    if leg.animation_active:
                        leg.animation_time = 0.0
                        leg.control_mode = "cartesian"
                
                if event.key == pygame.K_m:
                    global MQTT_ENABLED
                    MQTT_ENABLED = not MQTT_ENABLED
                    print(f"MQTT: {'ACTIVE' if MQTT_ENABLED else 'INACTIVE'}")
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if leg.control_mode == "cartesian":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if leg.is_near_foot(mouse_x, mouse_y):
                        leg.dragging = True
                    else:
                        leg.inverse_kinematics_foot(mouse_x, mouse_y)
            
            if event.type == pygame.MOUSEBUTTONUP:
                leg.dragging = False
            
            if event.type == pygame.MOUSEMOTION:
                if leg.dragging and leg.control_mode == "cartesian":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    leg.inverse_kinematics_foot(mouse_x, mouse_y)
        
        # Controles
        keys = pygame.key.get_pressed()
        
        # Animation rectangulaire
        if leg.animation_active:
            leg.animation_time += 1.0 / FPS
            t = leg.animation_time / leg.animation_duration
            target_x, target_y = leg.get_rectangle_position(t)
            leg.inverse_kinematics_foot(target_x, target_y)
            
            if leg.animation_time >= leg.animation_duration:
                leg.animation_time = 0.0
        
        elif leg.control_mode == "cartesian":
            speed = 5.0 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 2.0
            
            if keys[pygame.K_LEFT]:
                leg.foot_x -= speed
            if keys[pygame.K_RIGHT]:
                leg.foot_x += speed
            if keys[pygame.K_UP]:
                leg.foot_y -= speed
            if keys[pygame.K_DOWN]:
                leg.foot_y += speed
            
            leg.inverse_kinematics_foot(leg.foot_x, leg.foot_y)
            
        else:
            angular_speed = 0.02
            
            if keys[pygame.K_q]:
                new_theta1 = leg.theta1 + angular_speed
                if new_theta1 < math.radians(90):
                    leg.theta1 = new_theta1
                    leg.publish_angles_mqtt()
            if keys[pygame.K_w]:
                leg.theta1 -= angular_speed
                leg.publish_angles_mqtt()
            
            if keys[pygame.K_a]:
                leg.theta2 += angular_speed
                leg.publish_angles_mqtt()
            if keys[pygame.K_s]:
                new_theta2 = leg.theta2 - angular_speed
                if new_theta2 > 0:
                    leg.theta2 = new_theta2
                    leg.publish_angles_mqtt()
            
            if keys[pygame.K_z]:
                leg.theta3 += angular_speed
                leg.publish_angles_mqtt()
            if keys[pygame.K_x]:
                leg.theta3 -= angular_speed
                leg.publish_angles_mqtt()
        
        # Affichage
        screen.fill(BLACK)
        
        draw_cartesian_grid(screen)
        
        if leg.control_mode == "cartesian":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if leg.is_near_foot(mouse_x, mouse_y):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        leg.draw_workspace(screen)
        leg.draw_rectangle_trajectory(screen)
        leg.draw(screen)
        
        if leg.control_mode == "cartesian":
            joints = leg.forward_kinematics()
            foot_pos = joints[3]
            if leg.dragging:
                pygame.draw.circle(screen, YELLOW, (int(foot_pos[0]), int(foot_pos[1])), 25, 3)
                pygame.draw.circle(screen, YELLOW, (int(foot_pos[0]), int(foot_pos[1])), 18, 2)
            else:
                pygame.draw.circle(screen, GREEN, (int(foot_pos[0]), int(foot_pos[1])), 15, 2)
                pygame.draw.circle(screen, GREEN, (int(foot_pos[0]), int(foot_pos[1])), 20, 1)
        
        draw_ui(screen, leg, font)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    stop_mqtt()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()