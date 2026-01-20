import pygame
import math
import sys
import numpy as np
from scipy.interpolate import CubicHermiteSpline

# Initialisation de pygame
pygame.init()

# Constantes
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
FPS = 60

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (70, 130, 255)
RED = (255, 70, 70)
GREEN = (70, 255, 130)
YELLOW = (255, 220, 70)

class Keyframe:
    def __init__(self, time, angle):
        self.time = time  # [0, 1]
        self.angle = angle
        
class ServoTimeline:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Timeline Servomoteur Cheville")
        self.clock = pygame.time.Clock()
        
        # Paramètres du servo
        self.angle_min = 0
        self.angle_max = 180
        
        # Keyframes
        self.keyframes = [
            Keyframe(0.0, 90),
            Keyframe(1.0, 90)
        ]
        
        # Animation
        self.current_time = 0.0
        self.is_playing = False
        self.duration = 3.0  # secondes
        self.start_time = 0
        
        # Options d'interpolation
        self.use_spline = True
        self.show_tangents = True
        self.loop_animation = True
        
        # Interface
        self.timeline_rect = pygame.Rect(100, 450, 800, 200)
        self.selected_keyframe = None
        self.dragging = False
        
        # Zone de texte active
        self.active_input = None
        self.input_texts = {
            'angle_min': str(self.angle_min),
            'angle_max': str(self.angle_max),
            'duration': str(self.duration)
        }
        
        # Font
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        
    def interpolate_angle_linear(self, time):
        """Interpolation linéaire entre les keyframes"""
        sorted_kf = sorted(self.keyframes, key=lambda k: k.time)
        
        if time <= sorted_kf[0].time:
            return sorted_kf[0].angle
        if time >= sorted_kf[-1].time:
            return sorted_kf[-1].angle
        
        for i in range(len(sorted_kf) - 1):
            k1 = sorted_kf[i]
            k2 = sorted_kf[i + 1]
            
            if k1.time <= time <= k2.time:
                t = (time - k1.time) / (k2.time - k1.time)
                return k1.angle + (k2.angle - k1.angle) * t
        
        return sorted_kf[0].angle
    
    def interpolate_angle(self, time):
        """Interpolation par spline cubique avec dérivées nulles aux keyframes"""
        if not self.use_spline:
            return self.interpolate_angle_linear(time)
        
        sorted_kf = sorted(self.keyframes, key=lambda k: k.time)
        
        if len(sorted_kf) < 2:
            return sorted_kf[0].angle if sorted_kf else 90
        
        if time <= sorted_kf[0].time:
            return sorted_kf[0].angle
        if time >= sorted_kf[-1].time:
            return sorted_kf[-1].angle
        
        # Extraire les temps et angles
        times = np.array([kf.time for kf in sorted_kf])
        angles = np.array([kf.angle for kf in sorted_kf])
        
        # Dérivées nulles à tous les keyframes
        derivatives = np.zeros(len(times))
        
        # Créer la spline cubique de Hermite
        spline = CubicHermiteSpline(times, angles, derivatives)
        
        # Évaluer la spline au temps donné
        return float(spline(time))
    
    def time_to_x(self, time):
        """Convertit un temps [0,1] en coordonnée X"""
        return self.timeline_rect.left + time * self.timeline_rect.width
    
    def angle_to_y(self, angle):
        """Convertit un angle en coordonnée Y"""
        normalized = (angle - self.angle_min) / (self.angle_max - self.angle_min)
        return self.timeline_rect.bottom - normalized * self.timeline_rect.height
    
    def x_to_time(self, x):
        """Convertit une coordonnée X en temps [0,1]"""
        time = (x - self.timeline_rect.left) / self.timeline_rect.width
        return max(0.0, min(1.0, time))
    
    def y_to_angle(self, y):
        """Convertit une coordonnée Y en angle"""
        normalized = (self.timeline_rect.bottom - y) / self.timeline_rect.height
        angle = self.angle_min + normalized * (self.angle_max - self.angle_min)
        return max(self.angle_min, min(self.angle_max, angle))
    
    def draw_servo_visualization(self):
        """Dessine la visualisation du servomoteur"""
        center_x = 500
        center_y = 200
        radius = 100
        
        # Cercle du servo
        pygame.draw.circle(self.screen, DARK_GRAY, (center_x, center_y), radius, 3)
        
        # Angle actuel
        current_angle = self.interpolate_angle(self.current_time)
        
        # Convertir l'angle servo en radians (0° = droite, sens horaire)
        angle_rad = math.radians(current_angle - 90)
        
        # Bras du servo
        end_x = center_x + radius * 0.8 * math.cos(angle_rad)
        end_y = center_y + radius * 0.8 * math.sin(angle_rad)
        pygame.draw.line(self.screen, RED, (center_x, center_y), (end_x, end_y), 5)
        pygame.draw.circle(self.screen, RED, (int(end_x), int(end_y)), 8)
        
        # Centre
        pygame.draw.circle(self.screen, BLACK, (center_x, center_y), 10)
        
        # Affichage de l'angle
        angle_text = self.font.render(f"Angle: {current_angle:.1f}°", True, BLACK)
        self.screen.blit(angle_text, (center_x - 60, center_y + radius + 20))
        
        # Indicateurs min/max
        min_rad = math.radians(self.angle_min - 90)
        max_rad = math.radians(self.angle_max - 90)
        
        min_x = center_x + radius * 0.9 * math.cos(min_rad)
        min_y = center_y + radius * 0.9 * math.sin(min_rad)
        max_x = center_x + radius * 0.9 * math.cos(max_rad)
        max_y = center_y + radius * 0.9 * math.sin(max_rad)
        
        pygame.draw.line(self.screen, BLUE, (center_x, center_y), (min_x, min_y), 2)
        pygame.draw.line(self.screen, BLUE, (center_x, center_y), (max_x, max_y), 2)
        
    def draw_timeline(self):
        """Dessine la timeline"""
        # Fond de la timeline
        pygame.draw.rect(self.screen, WHITE, self.timeline_rect)
        pygame.draw.rect(self.screen, BLACK, self.timeline_rect, 2)
        
        # Grille horizontale (angles)
        num_h_lines = 5
        for i in range(num_h_lines + 1):
            angle = self.angle_min + i * (self.angle_max - self.angle_min) / num_h_lines
            y = self.angle_to_y(angle)
            pygame.draw.line(self.screen, GRAY, 
                           (self.timeline_rect.left, y), 
                           (self.timeline_rect.right, y), 1)
            
            # Labels des angles
            label = self.font_small.render(f"{angle:.0f}°", True, BLACK)
            self.screen.blit(label, (self.timeline_rect.left - 40, y - 10))
        
        # Grille verticale (temps)
        num_v_lines = 10
        for i in range(num_v_lines + 1):
            time = i / num_v_lines
            x = self.time_to_x(time)
            pygame.draw.line(self.screen, GRAY,
                           (x, self.timeline_rect.top),
                           (x, self.timeline_rect.bottom), 1)
            
            # Labels du temps
            label = self.font_small.render(f"{time:.1f}", True, BLACK)
            self.screen.blit(label, (x - 15, self.timeline_rect.bottom + 5))
        
        # Courbe interpolée
        sorted_kf = sorted(self.keyframes, key=lambda k: k.time)
        points = []
        for t in range(0, 101):
            time = t / 100.0
            angle = self.interpolate_angle(time)
            x = self.time_to_x(time)
            y = self.angle_to_y(angle)
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(self.screen, BLUE, False, points, 2)
        
        # Keyframes
        for i, kf in enumerate(self.keyframes):
            x = self.time_to_x(kf.time)
            y = self.angle_to_y(kf.angle)
            
            color = YELLOW if i == self.selected_keyframe else RED
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 8)
            pygame.draw.circle(self.screen, BLACK, (int(x), int(y)), 8, 2)
            
            # Visualisation des tangentes (lignes horizontales)
            if self.show_tangents and self.use_spline:
                tangent_length = 30
                pygame.draw.line(self.screen, (255, 150, 0),
                               (int(x - tangent_length), int(y)),
                               (int(x + tangent_length), int(y)), 2)
                # Petites flèches pour indiquer la direction
                pygame.draw.circle(self.screen, (255, 150, 0), 
                                 (int(x - tangent_length), int(y)), 3)
                pygame.draw.circle(self.screen, (255, 150, 0), 
                                 (int(x + tangent_length), int(y)), 3)
        
        # Curseur de temps actuel
        cursor_x = self.time_to_x(self.current_time)
        pygame.draw.line(self.screen, GREEN,
                        (cursor_x, self.timeline_rect.top),
                        (cursor_x, self.timeline_rect.bottom), 3)
        
    def draw_controls(self):
        """Dessine les contrôles"""
        y_offset = 20
        x_offset = 50
        
        # Titre
        title = self.font.render("TIMELINE SERVOMOTEUR CHEVILLE", True, BLACK)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, y_offset))
        
        y_offset += 350
        
        # Inputs
        input_fields = [
            ('Angle Min:', 'angle_min', 50),
            ('Angle Max:', 'angle_max', 250),
            ('Durée (s):', 'duration', 450)
        ]
        
        for label, key, x_pos in input_fields:
            label_surf = self.font_small.render(label, True, BLACK)
            self.screen.blit(label_surf, (x_pos, y_offset))
            
            input_rect = pygame.Rect(x_pos + 100, y_offset - 5, 80, 30)
            color = YELLOW if self.active_input == key else WHITE
            pygame.draw.rect(self.screen, color, input_rect)
            pygame.draw.rect(self.screen, BLACK, input_rect, 2)
            
            text_surf = self.font_small.render(self.input_texts[key], True, BLACK)
            self.screen.blit(text_surf, (input_rect.x + 5, input_rect.y + 5))
        
        # Boutons
        y_offset += 50
        button_texts = [
            "Play (SPACE)", 
            "Pause (P)", 
            "Reset (R)", 
            "Boucle (L)",
            "Spline/Lin (S)"
        ]
        for i, text in enumerate(button_texts):
            btn_surf = self.font_small.render(text, True, BLACK)
            self.screen.blit(btn_surf, (50 + i * 180, y_offset))
        
        # Infos mode
        y_offset += 30
        mode_text = "Mode: " + ("SPLINE (dérivées nulles)" if self.use_spline else "LINÉAIRE")
        mode_surf = self.font_small.render(mode_text, True, BLUE if self.use_spline else RED)
        self.screen.blit(mode_surf, (50, y_offset))
        
        loop_text = "Boucle: " + ("ON ∞" if self.loop_animation else "OFF")
        loop_surf = self.font_small.render(loop_text, True, GREEN if self.loop_animation else RED)
        self.screen.blit(loop_surf, (350, y_offset))
        
        tangent_text = "Tangentes: " + ("ON" if self.show_tangents else "OFF")
        tangent_surf = self.font_small.render(tangent_text, True, BLACK)
        self.screen.blit(tangent_surf, (550, y_offset))
        
        # Temps actuel
        time_text = self.font.render(f"Temps: {self.current_time:.2f} / 1.00", True, BLACK)
        self.screen.blit(time_text, (750, y_offset))
        
    def handle_input_click(self, pos):
        """Gère les clics sur les champs de texte"""
        y = 370
        input_fields = [
            ('angle_min', 150, y),
            ('angle_max', 350, y),
            ('duration', 550, y)
        ]
        
        for key, x, y_pos in input_fields:
            rect = pygame.Rect(x, y_pos - 5, 80, 30)
            if rect.collidepoint(pos):
                self.active_input = key
                return True
        
        self.active_input = None
        return False
    
    def apply_input_changes(self):
        """Applique les changements des champs de texte"""
        try:
            self.angle_min = float(self.input_texts['angle_min'])
            self.angle_max = float(self.input_texts['angle_max'])
            self.duration = float(self.input_texts['duration'])
        except ValueError:
            pass
    
    def handle_events(self):
        """Gère les événements pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if self.active_input:
                    if event.key == pygame.K_RETURN:
                        self.apply_input_changes()
                        self.active_input = None
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_texts[self.active_input] = self.input_texts[self.active_input][:-1]
                    elif event.unicode.isprintable():
                        self.input_texts[self.active_input] += event.unicode
                else:
                    if event.key == pygame.K_SPACE:
                        self.is_playing = not self.is_playing
                        if self.is_playing:
                            self.start_time = pygame.time.get_ticks() - self.current_time * self.duration * 1000
                    elif event.key == pygame.K_p:
                        self.is_playing = False
                    elif event.key == pygame.K_r:
                        self.current_time = 0.0
                        self.is_playing = False
                    elif event.key == pygame.K_s:
                        self.use_spline = not self.use_spline
                    elif event.key == pygame.K_t:
                        self.show_tangents = not self.show_tangents
                    elif event.key == pygame.K_l:
                        self.loop_animation = not self.loop_animation
                    elif event.key == pygame.K_DELETE and self.selected_keyframe is not None:
                        if len(self.keyframes) > 2:
                            del self.keyframes[self.selected_keyframe]
                            self.selected_keyframe = None
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    # Vérifier si c'est un champ de texte
                    if self.handle_input_click(event.pos):
                        continue
                    
                    # Vérifier si c'est une keyframe
                    for i, kf in enumerate(self.keyframes):
                        x = self.time_to_x(kf.time)
                        y = self.angle_to_y(kf.angle)
                        dist = math.sqrt((event.pos[0] - x)**2 + (event.pos[1] - y)**2)
                        
                        if dist < 10:
                            self.selected_keyframe = i
                            self.dragging = True
                            break
                    else:
                        # Ajouter une nouvelle keyframe si clic dans la timeline
                        if self.timeline_rect.collidepoint(event.pos):
                            new_time = self.x_to_time(event.pos[0])
                            new_angle = self.y_to_angle(event.pos[1])
                            self.keyframes.append(Keyframe(new_time, new_angle))
                            self.selected_keyframe = len(self.keyframes) - 1
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging and self.selected_keyframe is not None:
                    new_time = self.x_to_time(event.pos[0])
                    new_angle = self.y_to_angle(event.pos[1])
                    self.keyframes[self.selected_keyframe].time = new_time
                    self.keyframes[self.selected_keyframe].angle = new_angle
        
        return True
    
    def update(self):
        """Met à jour l'état de l'animation"""
        if self.is_playing:
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
            self.current_time = elapsed / self.duration
            
            if self.current_time >= 1.0:
                if self.loop_animation:
                    # Boucler l'animation
                    self.current_time = 0.0
                    self.start_time = pygame.time.get_ticks()
                else:
                    # Arrêter à la fin
                    self.current_time = 1.0
                    self.is_playing = False
    
    def draw(self):
        """Dessine tout"""
        self.screen.fill(WHITE)
        self.draw_servo_visualization()
        self.draw_timeline()
        self.draw_controls()
        pygame.display.flip()
    
    def run(self):
        """Boucle principale"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = ServoTimeline()
    app.run()