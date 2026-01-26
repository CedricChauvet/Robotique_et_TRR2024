"""
Module Timeline pour Servomoteur - Contrôle de trajectoire
Par Ced avec Claude
Usage: from servo_timeline import ServoTimeline
"""

import pygame
import math
import numpy as np
from scipy.interpolate import CubicHermiteSpline

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
    """Timeline pour contrôler un servomoteur avec interpolation spline"""
    
    def __init__(self, position=(100, 450), size=(800, 200), angle_range=(-60, 60), duration=3.0):
        """
        Args:
            position: (x, y) Position de la timeline
            size: (width, height) Taille de la timeline
            angle_range: (min, max) Plage d'angles en degrés
            duration: Durée de l'animation en secondes
        """
        # Position et taille
        self.timeline_rect = pygame.Rect(position[0], position[1], size[0], size[1])
        
        # Paramètres du servo
        self.angle_min = angle_range[0]
        self.angle_max = angle_range[1]
        
        # Keyframes
        self.keyframes = [
            Keyframe(0.0, 0),
            Keyframe(1.0, 0)
        ]
        
        # Animation
        self.current_time = 0.0
        self.is_playing = False
        self.duration = duration
        self.start_time = 0
        self.loop_animation = True
        
        # Options d'affichage
        self.show_tangents = True
        
        # Interface
        self.selected_keyframe = None
        self.dragging = False
        
        # Font
        self.font_small = pygame.font.Font(None, 20)
    
    def get_current_angle(self):
        """Retourne l'angle actuel interpolé"""
        return self.interpolate_angle(self.current_time)
    
    def get_opposite_angle(self):
        """Retourne l'angle en opposition de phase (+0.5)"""
        opposite_time = (self.current_time + 0.5) % 1.0
        return self.interpolate_angle(opposite_time)
    
    def interpolate_angle(self, time):
        """Interpolation par spline cubique avec dérivées nulles aux keyframes"""
        sorted_kf = sorted(self.keyframes, key=lambda k: k.time)
        
        if len(sorted_kf) < 2:
            return sorted_kf[0].angle if sorted_kf else 0
        
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
    
    def draw(self, screen):
        """Dessine la timeline sur l'écran"""
        # Fond de la timeline
        #pygame.draw.rect(screen, WHITE, self.timeline_rect)
        #pygame.draw.rect(screen, BLACK, self.timeline_rect, 2)
        
        # Grille horizontale (angles)
        num_h_lines = 6
        for i in range(num_h_lines + 1):
            angle = self.angle_min + i * (self.angle_max - self.angle_min) / num_h_lines
            y = self.angle_to_y(angle)
            pygame.draw.line(screen, BLACK, 
                           (self.timeline_rect.left, y), 
                           (self.timeline_rect.right, y), 1)
            
            # Labels des angles
            label = self.font_small.render(f"{angle:.0f}°", True, BLACK)
            screen.blit(label, (self.timeline_rect.left - 40, y - 10))
        
        # Grille verticale (temps)
        num_v_lines = 10
        for i in range(num_v_lines + 1):
            time = i / num_v_lines
            x = self.time_to_x(time)
            pygame.draw.line(screen, BLACK,
                           (x, self.timeline_rect.top),
                           (x, self.timeline_rect.bottom), 1)
            
            # Labels du temps
            label = self.font_small.render(f"{time:.1f}", True, BLACK)
            screen.blit(label, (x - 15, self.timeline_rect.bottom + 5))
        
        # Courbe d'interpolation
        sorted_kf = sorted(self.keyframes, key=lambda k: k.time)
        if len(sorted_kf) >= 2:
            points = []
            for i in range(self.timeline_rect.width):
                t = i / self.timeline_rect.width
                angle = self.interpolate_angle(t)
                x = self.timeline_rect.left + i
                y = self.angle_to_y(angle)
                points.append((x, y))
            
            if len(points) > 1:
                pygame.draw.lines(screen, BLUE, False, points, 2)
        
        # Keyframes
        for i, kf in enumerate(self.keyframes):
            x = self.time_to_x(kf.time)
            y = self.angle_to_y(kf.angle)
            
            color = YELLOW if i == self.selected_keyframe else RED
            size = 10 if i == self.selected_keyframe else 8
            
            pygame.draw.circle(screen, color, (int(x), int(y)), size)
            pygame.draw.circle(screen, BLACK, (int(x), int(y)), size, 2)
        
        # Tangentes
        if self.show_tangents:
            for kf in sorted_kf:
                x = self.time_to_x(kf.time)
                y = self.angle_to_y(kf.angle)
                tangent_length = 30
                
                pygame.draw.line(screen, GREEN,
                                (int(x - tangent_length), int(y)),
                                (int(x + tangent_length), int(y)), 3)
        
        # Curseur de temps actuel (ligne verte)
        cursor_x = self.time_to_x(self.current_time)
        current_angle = self.interpolate_angle(self.current_time)
        pygame.draw.line(screen, GREEN,
                        (cursor_x, self.timeline_rect.top),
                        (cursor_x, self.timeline_rect.bottom), 3)
        
        # Affichage des infos ligne verte
        time_text = f"t={self.current_time:.2f}s"
        angle_text = f"{current_angle:.1f}°"
        time_surf = self.font_small.render(time_text, True, GREEN)
        angle_surf = self.font_small.render(angle_text, True, GREEN)
        screen.blit(time_surf, (cursor_x + 5, self.timeline_rect.top - 25))
        screen.blit(angle_surf, (cursor_x + 5, self.timeline_rect.top - 10))
        
        # Curseur en opposition de phase (ligne rouge, décalé de +0.5)
        opposite_time = (self.current_time + 0.5) % 1.0
        opposite_angle = self.interpolate_angle(opposite_time)
        opposite_x = self.time_to_x(opposite_time)
        pygame.draw.line(screen, RED,
                        (opposite_x, self.timeline_rect.top),
                        (opposite_x, self.timeline_rect.bottom), 3)
        
        # Affichage des infos ligne rouge
        opp_time_text = f"t={opposite_time:.2f}s"
        opp_angle_text = f"{opposite_angle:.1f}°"
        opp_time_surf = self.font_small.render(opp_time_text, True, RED)
        opp_angle_surf = self.font_small.render(opp_angle_text, True, RED)
        screen.blit(opp_time_surf, (opposite_x + 5, self.timeline_rect.top - 25))
        screen.blit(opp_angle_surf, (opposite_x + 5, self.timeline_rect.top - 10))
    
    def handle_event(self, event):
        """Gère un événement pygame. Retourne True si l'événement a été consommé"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.is_playing = not self.is_playing
                if self.is_playing:
                    self.start_time = pygame.time.get_ticks() - self.current_time * self.duration * 1000
                return True
            elif event.key == pygame.K_p:
                self.is_playing = False
                return True
            elif event.key == pygame.K_r:
                self.current_time = 0.0
                self.is_playing = False
                return True
            elif event.key == pygame.K_t:
                self.show_tangents = not self.show_tangents
                return True
            elif event.key == pygame.K_l:
                self.loop_animation = not self.loop_animation
                return True
            elif event.key == pygame.K_DELETE and self.selected_keyframe is not None:
                if len(self.keyframes) > 2:
                    del self.keyframes[self.selected_keyframe]
                    self.selected_keyframe = None
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                # Vérifier si c'est dans la timeline
                if self.timeline_rect.collidepoint(event.pos):
                    # Vérifier si c'est une keyframe
                    for i, kf in enumerate(self.keyframes):
                        x = self.time_to_x(kf.time)
                        y = self.angle_to_y(kf.angle)
                        dist = math.sqrt((event.pos[0] - x)**2 + (event.pos[1] - y)**2)
                        
                        if dist < 10:
                            self.selected_keyframe = i
                            self.dragging = True
                            return True
                    
                    # Ajouter une nouvelle keyframe
                    new_time = self.x_to_time(event.pos[0])
                    new_angle = self.y_to_angle(event.pos[1])
                    self.keyframes.append(Keyframe(new_time, new_angle))
                    self.selected_keyframe = len(self.keyframes) - 1
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and self.selected_keyframe is not None:
                if self.timeline_rect.collidepoint(event.pos):
                    new_time = self.x_to_time(event.pos[0])
                    new_angle = self.y_to_angle(event.pos[1])
                    self.keyframes[self.selected_keyframe].time = new_time
                    self.keyframes[self.selected_keyframe].angle = new_angle
                    return True
        
        return False
    
    def update(self):
        """Met à jour l'état de l'animation"""
        if self.is_playing:
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
            self.current_time = elapsed / self.duration
            
            if self.current_time >= 1.0:
                if self.loop_animation:
                    self.current_time = 0.0
                    self.start_time = pygame.time.get_ticks()
                else:
                    self.current_time = 1.0
                    self.is_playing = False


# Test standalone si exécuté directement
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("Servo Timeline - Test Module")
    clock = pygame.time.Clock()
    
    # Créer une timeline de test
    timeline = ServoTimeline(position=(100, 450), size=(800, 200))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            timeline.handle_event(event)
        
        timeline.update()
        
        screen.fill((50, 50, 50))
        timeline.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()