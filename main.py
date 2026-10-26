import sys
import random
import math
import pygame
import os
import wave
import struct

# Configurações do jogo
class Config:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    
    GRAVITY = 0.6
    MAX_FALL_SPEED = 12
    MOVE_SPEED = 5
    JUMP_FORCE = -13
    
    WORLD_WIDTH = 3000
    
    SKY_TOP = (8, 8, 20)
    SKY_BOTTOM = (24, 15, 38)
    MOON_COLOR = (245, 245, 235)
    MOON_GLOW = (30, 25, 45)
    
    FOREST_GROUND = (12, 22, 14)
    FOREST_GRASS = (20, 42, 24)
    
    CASTLE_STONE = (45, 45, 52)
    CASTLE_BORDER = (22, 22, 26)
    
    KNIGHT_ARMOR = (110, 120, 130)
    KNIGHT_DARK = (55, 60, 68)
    KNIGHT_GOLD = (212, 175, 55)
    
    SKELETON_BONE = (225, 225, 215)
    SKELETON_SHADOW = (155, 155, 145)
    SKELETON_EYES = (255, 30, 30)
    
    SWORD_SLASH = (255, 225, 100)
    SWORD_SPARK = (255, 150, 30)
    
    TEXT_GOLD = (220, 180, 70)
    TEXT_RED = (190, 30, 30)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

# Efeitos visuais
class Particle:
    def __init__(self, x, y, dx, dy, color, size, lifetime, decay=0.95):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.decay = decay

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1
        self.size = max(0.5, self.size * self.decay)

    def draw(self, screen, camera_offset_x):
        rx = int(self.x - camera_offset_x)
        ry = int(self.y)
        if 0 <= rx <= Config.SCREEN_WIDTH and 0 <= ry <= Config.SCREEN_HEIGHT:
            pygame.draw.circle(screen, self.color, (rx, ry), int(self.size))

class TextParticle:
    def __init__(self, text, x, y, dx, dy, color, size, lifetime):
        self.text = text
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.lifetime -= 1

    def draw(self, screen, camera_offset_x, font_cache):
        if self.lifetime <= 0:
            return
            
        ratio = self.lifetime / self.max_lifetime
        r = int(self.color[0] * ratio + Config.SKY_BOTTOM[0] * (1 - ratio))
        g = int(self.color[1] * ratio + Config.SKY_BOTTOM[1] * (1 - ratio))
        b = int(self.color[2] * ratio + Config.SKY_BOTTOM[2] * (1 - ratio))
        
        current_size = max(6, int(self.size * ratio))
        font = font_cache.get(current_size)
        if not font:
            font = pygame.font.SysFont('georgia', current_size)
            font_cache[current_size] = font
            
        text_surf = font.render(self.text, True, (r, g, b))
        screen.blit(text_surf, (int(self.x - camera_offset_x), int(self.y)))

# Sintetizador de áudio (Gera WAVs com cabeçalhos corretos de contagem de frames)
def generate_medieval_wav(filepath):
    sample_rate = 22050
    notes_freq = {
        'A3': 220.00, 'A#3': 233.08, 'B3': 246.94,
        'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13, 'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00, 'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
        'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25, 'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99, 'G#5': 830.61, 'A5': 880.00,
        'P': 0.0
    }
    
    melody = [
        ('A4', 0.4), ('B4', 0.2), ('C5', 0.6), ('D5', 0.3), ('E5', 0.6), ('D5', 0.3),
        ('C5', 0.6), ('B4', 0.3), ('G4', 0.6), ('A4', 0.3), ('B4', 0.6), ('G4', 0.3),
        ('A4', 0.8), ('P', 0.2),
        
        ('A4', 0.4), ('B4', 0.2), ('C5', 0.6), ('D5', 0.3), ('E5', 0.6), ('D5', 0.3),
        ('C5', 0.6), ('B4', 0.3), ('G4', 0.6), ('G#4', 0.3), ('A4', 0.8), ('P', 0.4),
        
        ('E5', 0.6), ('F5', 0.3), ('G5', 0.6), ('F5', 0.3), ('E5', 0.6), ('D5', 0.3),
        ('C5', 0.6), ('B4', 0.3), ('G4', 0.6), ('A4', 0.3), ('B4', 0.6), ('G4', 0.3),
        
        ('E5', 0.6), ('F5', 0.3), ('G5', 0.6), ('F5', 0.3), ('E5', 0.6), ('D5', 0.3),
        ('C5', 0.6), ('B4', 0.3), ('G#4', 0.6), ('E4', 0.3), ('A4', 0.8), ('P', 0.4)
    ]
    
    bass = [
        ('A3', 1.8), ('A3', 1.8), ('C4', 1.8), ('G3', 1.8), 
        ('G3', 1.8), ('A3', 1.8), ('E3', 1.8), ('A3', 1.8)
    ]
    
    total_duration = sum(d for _, d in melody)
    num_samples = int(total_duration * sample_rate)
    
    melody_time = 0
    melody_events = []
    for note, dur in melody:
        melody_events.append((melody_time, melody_time + dur, note))
        melody_time += dur
        
    bass_time = 0
    bass_events = []
    while bass_time < total_duration:
        for note, dur in bass:
            bass_events.append((bass_time, bass_time + dur, note))
            bass_time += dur
            
    frames = []
    for i in range(num_samples):
        t = float(i) / sample_rate
        
        val_m = 0.0
        m_freq = 0.0
        for start, end, note in melody_events:
            if start <= t < end:
                m_freq = notes_freq.get(note, 0.0)
                note_dur = end - start
                elapsed = t - start
                envelope = 1.0
                if elapsed < 0.04:
                    envelope = elapsed / 0.04
                elif note_dur - elapsed < 0.08:
                    envelope = (note_dur - elapsed) / 0.08
                break
        
        if m_freq > 0.0:
            period = 1.0 / m_freq
            phase = (t % period) / period
            if phase < 0.25:
                val_m = phase * 4.0
            elif phase < 0.75:
                val_m = 2.0 - phase * 4.0
            else:
                val_m = phase * 4.0 - 4.0
            val_m *= envelope * 0.20
            
        val_b = 0.0
        b_freq = 0.0
        for start, end, note in bass_events:
            if start <= t < end:
                b_freq = notes_freq.get(note, 0.0)
                note_dur = end - start
                elapsed = t - start
                b_envelope = 0.6
                if elapsed < 0.1:
                    b_envelope = (elapsed / 0.1) * 0.6
                elif note_dur - elapsed < 0.15:
                    b_envelope = ((note_dur - elapsed) / 0.15) * 0.6
                break
        
        if b_freq > 0.0:
            val_b = math.sin(2.0 * math.pi * b_freq * t)
            val_b *= b_envelope * 0.15
            
        val = val_m + val_b
        val = max(-1.0, min(1.0, val))
        
        sample = int(val * 32767)
        frames.append(struct.pack('<h', sample))
        
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(frames))

def generate_swing_wav(filepath):
    sample_rate = 22050
    duration = 0.12
    num_samples = int(duration * sample_rate)
    frames = []
    for i in range(num_samples):
        t = float(i) / sample_rate
        freq = 1700.0 * (1.0 - t / duration) + 250.0
        val = math.sin(2.0 * math.pi * freq * t)
        val = val * 0.5 + random.uniform(-0.5, 0.5) * 0.5
        envelope = (1.0 - t / duration)
        val *= envelope * 0.55
        
        sample = int(max(-1.0, min(1.0, val)) * 32767)
        frames.append(struct.pack('<h', sample))
        
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(frames))

def generate_hit_wav(filepath):
    sample_rate = 22050
    duration = 0.08
    num_samples = int(duration * sample_rate)
    frames = []
    for i in range(num_samples):
        t = float(i) / sample_rate
        freq = 110.0 + random.uniform(-30.0, 70.0)
        val = math.sin(2.0 * math.pi * freq * t)
        val = val * 0.25 + random.uniform(-0.75, 0.75) * 0.75
        envelope = (1.0 - t / duration)
        val *= envelope * 0.60
        
        sample = int(max(-1.0, min(1.0, val)) * 32767)
        frames.append(struct.pack('<h', sample))
        
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(frames))

# Blocos de cenário
class Platform:
    def __init__(self, x, y, width, height, plat_type='forest'):
        self.rect = pygame.Rect(x, y, width, height)
        self.type = plat_type

    def draw(self, screen, camera_offset_x):
        if self.rect.right - camera_offset_x < 0 or self.rect.left - camera_offset_x > Config.SCREEN_WIDTH:
            return

        draw_rect = pygame.Rect(self.rect.x - camera_offset_x, self.rect.y, self.rect.width, self.rect.height)
        
        if self.type == 'forest':
            pygame.draw.rect(screen, Config.FOREST_GROUND, draw_rect)
            pygame.draw.rect(screen, Config.FOREST_GRASS, (draw_rect.x, draw_rect.y, draw_rect.width, min(6, draw_rect.height)))
            
            for gx in range(draw_rect.left, draw_rect.right, 14):
                gh = 6 + ((gx + self.rect.y) % 6)
                pygame.draw.polygon(screen, Config.FOREST_GRASS, [
                    (gx, draw_rect.top),
                    (gx + 3, draw_rect.top - gh),
                    (gx + 6, draw_rect.top)
                ])
                if gx % 28 == 0:
                    pygame.draw.polygon(screen, (32, 65, 38), [
                        (gx + 2, draw_rect.top),
                        (gx + 4, draw_rect.top - gh + 2),
                        (gx + 6, draw_rect.top)
                    ])
        
        elif self.type == 'castle':
            pygame.draw.rect(screen, Config.CASTLE_STONE, draw_rect)
            pygame.draw.rect(screen, Config.CASTLE_BORDER, draw_rect, 3)
            
            brick_h = 20
            brick_w = 40
            
            row = 0
            for y_off in range(0, self.rect.height, brick_h):
                x_start = brick_w // 2 if row % 2 == 0 else 0
                for x_off in range(x_start - brick_w, self.rect.width + brick_w, brick_w):
                    bx = draw_rect.left + x_off
                    by = draw_rect.top + y_off
                    bw = min(brick_w, draw_rect.right - bx)
                    bh = min(brick_h, draw_rect.bottom - by)
                    
                    if bw <= 0 or bh <= 0 or bx > draw_rect.right or bx + bw < draw_rect.left:
                        continue
                        
                    tone_hash = (int(self.rect.x + x_off) * 17 + int(self.rect.y + y_off) * 31) % 4
                    if tone_hash == 0:
                        brick_color = (38, 38, 44)
                    elif tone_hash == 1:
                        brick_color = (52, 52, 60)
                    else:
                        brick_color = Config.CASTLE_STONE
                        
                    pygame.draw.rect(screen, brick_color, (bx, by, bw, bh))
                    pygame.draw.rect(screen, Config.CASTLE_BORDER, (bx, by, bw, bh), 1)
                    
                    pygame.draw.line(screen, (75, 75, 85), (bx + 1, by + 1), (bx + bw - 1, by + 1), 1)
                    pygame.draw.line(screen, (75, 75, 85), (bx + 1, by + 1), (bx + 1, by + bh - 1), 1)
                row += 1

            if self.rect.height > 100:
                ivy_x = draw_rect.left + 15
                pygame.draw.line(screen, (22, 52, 30), (ivy_x, draw_rect.top), (ivy_x + 8, draw_rect.bottom), 2)
                for iy in range(draw_rect.top + 10, draw_rect.bottom - 10, 15):
                    side = 4 if iy % 2 == 0 else -4
                    pygame.draw.circle(screen, (32, 75, 45), (ivy_x + 4 + side, iy), 3)

# Cavaleiro (Player)
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 50)
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False
        
        self.health = 5
        self.max_health = 5
        self.invulnerable_timer = 0
        self.facing_right = True
        
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.has_dealt_damage = False
        self.should_play_swing = False

        # Efeitos de corte pré-alocados
        self.slash_surf_right = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.arc(self.slash_surf_right, (Config.SWORD_SLASH[0], Config.SWORD_SLASH[1], Config.SWORD_SLASH[2], 180), (0, 5, 50, 50), -math.pi/3, math.pi/2, 6)
        pygame.draw.arc(self.slash_surf_right, (255, 130, 30, 120), (4, 9, 42, 42), -math.pi/3, math.pi/2, 4)
        
        self.slash_surf_left = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.arc(self.slash_surf_left, (Config.SWORD_SLASH[0], Config.SWORD_SLASH[1], Config.SWORD_SLASH[2], 180), (10, 5, 50, 50), math.pi/2, 4*math.pi/3, 6)
        pygame.draw.arc(self.slash_surf_left, (255, 130, 30, 120), (14, 9, 42, 42), math.pi/2, 4*math.pi/3, 4)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        self.velocity_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity_x = -Config.MOVE_SPEED
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity_x = Config.MOVE_SPEED
            self.facing_right = True
            
        if (keys[pygame.K_w] or keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.velocity_y = Config.JUMP_FORCE
            self.on_ground = False
            
        mouse_click = pygame.mouse.get_pressed()[0]
        attack_pressed = keys[pygame.K_e] or keys[pygame.K_f] or keys[pygame.K_j]
        
        if (attack_pressed or mouse_click) and self.attack_cooldown == 0 and not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 15
            self.attack_cooldown = 25
            self.has_dealt_damage = False
            self.should_play_swing = True

    def update(self, platforms, particles):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
            
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.is_attacking = False
                
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if not self.on_ground:
            self.velocity_y += Config.GRAVITY
            if self.velocity_y > Config.MAX_FALL_SPEED:
                self.velocity_y = Config.MAX_FALL_SPEED

        if self.velocity_x != 0 and self.on_ground and random.random() < 0.25:
            particles.append(Particle(
                self.rect.centerx, self.rect.bottom,
                -self.velocity_x * 0.2 + random.uniform(-0.4, 0.4),
                random.uniform(-0.8, -0.2),
                (95, 90, 85),
                random.uniform(2, 4),
                random.randint(10, 20),
                decay=0.92
            ))

        self.rect.x += self.velocity_x
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity_x < 0:
                    self.rect.left = platform.rect.right
                self.velocity_x = 0

        self.on_ground = False
        self.rect.y += self.velocity_y
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.on_ground = True
                    self.velocity_y = 0
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0

        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity_x = 0
            
        if self.rect.top > Config.SCREEN_HEIGHT:
            self.health = 0

    def draw(self, screen, camera_offset_x):
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 4) % 2 == 0:
            return

        rx = int(self.rect.x - camera_offset_x)
        ry = int(self.rect.y)
        ticks = pygame.time.get_ticks()
        visor_color = (60, 160, 240)  # Fenda brilhante azul no elmo

        # Capa ondulante
        wave = math.sin(ticks * 0.015 + rx * 0.03) * 3
        cape_shadow = (115, 12, 12)
        
        if self.facing_right:
            cape_pts = [
                (rx + 8, ry + 16),
                (rx - 6 - int(self.velocity_x * 1.5), ry + 22 + int(wave)),
                (rx - 10 - int(self.velocity_x * 1.5), ry + 38 + int(wave)),
                (rx - 2, ry + 44),
                (rx + 14, ry + 24)
            ]
        else:
            cape_pts = [
                (rx + 24, ry + 16),
                (rx + 38 - int(self.velocity_x * 1.5), ry + 22 + int(wave)),
                (rx + 42 - int(self.velocity_x * 1.5), ry + 38 + int(wave)),
                (rx + 34, ry + 44),
                (rx + 18, ry + 24)
            ]
        pygame.draw.polygon(screen, cape_shadow, cape_pts)
        pygame.draw.polygon(screen, Config.BLACK, cape_pts, 1)

        # Pernas e botas reforçadas de cavaleiro (Greaves)
        leg_offset = 2 if int(ticks / 120) % 2 == 0 and self.velocity_x != 0 else 0
        
        # Pernas (Grevas de metal cinza)
        pygame.draw.rect(screen, Config.KNIGHT_ARMOR, (rx + 6, ry + 36, 6, 11))
        pygame.draw.rect(screen, Config.KNIGHT_ARMOR, (rx + 20, ry + 36 - leg_offset, 6, 11))
        
        # Botas reforçadas (Sabatons escuros)
        pygame.draw.rect(screen, (35, 35, 40), (rx + 4, ry + 46, 9, 4))
        pygame.draw.rect(screen, (35, 35, 40), (rx + 18, ry + 46 - leg_offset, 9, 4))
        
        # Joelheiras
        pygame.draw.circle(screen, Config.KNIGHT_DARK, (rx + 9, ry + 36), 4)
        pygame.draw.circle(screen, Config.KNIGHT_DARK, (rx + 23, ry + 36 - leg_offset), 4)

        # Peitoral / Armadura de Placa (Breastplate)
        pygame.draw.rect(screen, Config.KNIGHT_ARMOR, (rx + 3, ry + 14, 26, 22))
        
        # Sombreamento 3D no peitoral (Reflexo de luz)
        pygame.draw.line(screen, (160, 175, 190), (rx + 4, ry + 15), (rx + 4, ry + 34), 2)
        pygame.draw.line(screen, (160, 175, 190), (rx + 4, ry + 15), (rx + 27, ry + 15), 2)
        pygame.draw.line(screen, Config.KNIGHT_DARK, (rx + 28, ry + 15), (rx + 28, ry + 34), 2)
        
        # Cinto de couro
        pygame.draw.rect(screen, (50, 30, 15), (rx + 3, ry + 31, 26, 4))
        pygame.draw.rect(screen, Config.KNIGHT_GOLD, (rx + 14, ry + 30, 4, 6))

        # Emblema heráldico no peitoral (Cruz de Malta vermelha)
        pygame.draw.line(screen, (190, 30, 30), (rx + 16, ry + 17), (rx + 16, ry + 25), 2)
        pygame.draw.line(screen, (190, 30, 30), (rx + 12, ry + 21), (rx + 20, ry + 21), 2)

        # Ombreiras (Pauldrons)
        pygame.draw.circle(screen, Config.KNIGHT_ARMOR, (rx + 3, ry + 17), 5)
        pygame.draw.circle(screen, Config.KNIGHT_DARK, (rx + 3, ry + 17), 5, 1)
        pygame.draw.circle(screen, Config.KNIGHT_ARMOR, (rx + 29, ry + 17), 5)
        pygame.draw.circle(screen, Config.KNIGHT_DARK, (rx + 29, ry + 17), 5, 1)

        # Bainha da Espada (Scabbard) no quadril
        scab_color = (80, 50, 25)
        if not self.is_attacking:
            if self.facing_right:
                pygame.draw.line(screen, scab_color, (rx + 6, ry + 26), (rx - 1, ry + 36), 3)
                pygame.draw.line(screen, Config.KNIGHT_GOLD, (rx + 5, ry + 26), (rx + 9, ry + 22), 2)
                pygame.draw.line(screen, (180, 180, 190), (rx + 7, ry + 24), (rx + 11, ry + 20), 2)
                pygame.draw.circle(screen, Config.KNIGHT_GOLD, (rx + 11, ry + 20), 2)
            else:
                pygame.draw.line(screen, scab_color, (rx + 26, ry + 26), (rx + 33, ry + 36), 3)
                pygame.draw.line(screen, Config.KNIGHT_GOLD, (rx + 27, ry + 26), (rx + 23, ry + 22), 2)
                pygame.draw.line(screen, (180, 180, 190), (rx + 25, ry + 24), (rx + 21, ry + 20), 2)
                pygame.draw.circle(screen, Config.KNIGHT_GOLD, (rx + 21, ry + 20), 2)

        # Elmo de Combate com fenda e crista (Great Helm / Sallet)
        pygame.draw.rect(screen, Config.KNIGHT_ARMOR, (rx + 6, ry + 2, 20, 14))
        pygame.draw.circle(screen, Config.KNIGHT_ARMOR, (rx + 16, ry + 4), 10)
        
        # Detalhe de Crista/Pluma Red
        plume_wave = math.sin(ticks * 0.02) * 2
        if self.facing_right:
            plume_pts = [
                (rx + 12, ry + 1),
                (rx + 3 + int(plume_wave), ry - 6),
                (rx - 2 + int(plume_wave), ry - 3),
                (rx + 9, ry + 5)
            ]
            pygame.draw.polygon(screen, (200, 30, 30), plume_pts)
            # Faceplate/Visor saliente
            pygame.draw.polygon(screen, Config.KNIGHT_DARK, [(rx + 13, ry + 4), (rx + 27, ry + 9), (rx + 13, ry + 15)])
            pygame.draw.rect(screen, (15, 15, 20), (rx + 15, ry + 7, 10, 3))
            pygame.draw.rect(screen, visor_color, (rx + 19, ry + 8, 3, 1)) # Olho brilhante
        else:
            plume_pts = [
                (rx + 20, ry + 1),
                (rx + 29 + int(plume_wave), ry - 6),
                (rx + 34 + int(plume_wave), ry - 3),
                (rx + 23, ry + 5)
            ]
            pygame.draw.polygon(screen, (200, 30, 30), plume_pts)
            # Faceplate/Visor saliente
            pygame.draw.polygon(screen, Config.KNIGHT_DARK, [(rx + 19, ry + 4), (rx + 5, ry + 9), (rx + 19, ry + 15)])
            pygame.draw.rect(screen, (15, 15, 20), (rx + 7, ry + 7, 10, 3))
            pygame.draw.rect(screen, visor_color, (rx + 10, ry + 8, 3, 1)) # Olho brilhante

        # Escudo Medieval (Heater Shield) na mão frontal
        shield_color = (25, 45, 115) # Azul medieval profundo
        if self.facing_right:
            sx, sy = rx - 5, ry + 14
        else:
            sx, sy = rx + 23, ry + 14
            
        shield_pts = [(sx, sy), (sx + 14, sy), (sx + 14, sy + 11), (sx + 7, sy + 20), (sx, sy + 11)]
        pygame.draw.polygon(screen, shield_color, shield_pts)
        pygame.draw.polygon(screen, Config.KNIGHT_GOLD, shield_pts, 2)
        pygame.draw.line(screen, Config.KNIGHT_GOLD, (sx + 7, sy), (sx + 7, sy + 19), 2)
        pygame.draw.line(screen, Config.KNIGHT_GOLD, (sx, sy + 7), (sx + 14, sy + 7), 2)

        # Desenho Físico da Espada (Sword) atacando ou em punho
        if self.is_attacking:
            # Calcula o progresso do ataque para rotacionar a lâmina
            p = (15 - self.attack_timer) / 15.0
            
            if self.facing_right:
                # Rotaciona de cima para baixo
                angle = -math.pi/3 + p * (5 * math.pi / 6)
                hx, hy = rx + 20, ry + 24
            else:
                # Rotaciona de cima para baixo (lado esquerdo)
                angle = math.pi + math.pi/3 - p * (5 * math.pi / 6)
                hx, hy = rx + 12, ry + 24
                
            tx = hx + math.cos(angle) * 32
            ty = hy + math.sin(angle) * 32
            
            # Posições da guarda (crossguard)
            glx = hx + math.cos(angle + math.pi/2) * 5
            gly = hy + math.sin(angle + math.pi/2) * 5
            grx = hx + math.cos(angle - math.pi/2) * 5
            gry = hy + math.sin(angle - math.pi/2) * 5
            
            # Posição do cabo/pomo
            px = hx - math.cos(angle) * 8
            py = hy - math.sin(angle) * 8
            
            # Desenha a espada física no espaço
            pygame.draw.line(screen, (80, 50, 20), (hx, hy), (int(px), int(py)), 3) # Cabo
            pygame.draw.circle(screen, Config.KNIGHT_GOLD, (int(px), int(py)), 3) # Pomo
            pygame.draw.line(screen, Config.KNIGHT_GOLD, (int(glx), int(gly)), (int(grx), int(gry)), 2) # Guarda
            pygame.draw.line(screen, (220, 220, 225), (hx, hy), (int(tx), int(ty)), 3) # Lâmina de aço
            pygame.draw.line(screen, Config.WHITE, (hx, hy), (int(tx), int(ty)), 1) # Fio da lâmina brilhante

            # Efeito de corte (Slash overlay)
            if self.facing_right:
                screen.blit(self.slash_surf_right, (rx + 22, ry - 5))
            else:
                screen.blit(self.slash_surf_left, (rx - 52, ry - 5))

# Esqueletos
class Enemy:
    def __init__(self, x, y, patrol_start, patrol_end):
        self.rect = pygame.Rect(x, y, 28, 48)
        self.patrol_start = patrol_start
        self.patrol_end = patrol_end
        
        self.direction = 1
        self.speed = 1.2
        self.health = 2
        
        self.velocity_y = 0
        self.hit_timer = 0
        self.stun_timer = 0
        self.knockback_x = 0

    def update(self, platforms):
        self.velocity_y += Config.GRAVITY
        if self.velocity_y > Config.MAX_FALL_SPEED:
            self.velocity_y = Config.MAX_FALL_SPEED

        self.rect.y += self.velocity_y
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0

        if self.hit_timer > 0:
            self.hit_timer -= 1
            
        if self.stun_timer > 0:
            self.stun_timer -= 1
            self.rect.x += self.knockback_x
            self.knockback_x *= 0.85
            
            for platform in platforms:
                if self.rect.colliderect(platform.rect):
                    if self.knockback_x > 0:
                        self.rect.right = platform.rect.left
                    elif self.knockback_x < 0:
                        self.rect.left = platform.rect.right
                    self.knockback_x = 0
        else:
            self.rect.x += self.speed * self.direction
            
            if self.rect.x <= self.patrol_start:
                self.rect.x = self.patrol_start
                self.direction = 1
            elif self.rect.x >= self.patrol_end:
                self.rect.x = self.patrol_end
                self.direction = -1

            for platform in platforms:
                if self.rect.colliderect(platform.rect):
                    if self.direction > 0:
                        self.rect.right = platform.rect.left
                        self.direction = -1
                    elif self.direction < 0:
                        self.rect.left = platform.rect.right
                        self.direction = 1

    def draw(self, screen, camera_offset_x):
        if self.rect.right - camera_offset_x < 0 or self.rect.left - camera_offset_x > Config.SCREEN_WIDTH:
            return

        rx = int(self.rect.x - camera_offset_x)
        ry = int(self.rect.y)

        bone_color = (255, 100, 100) if self.hit_timer > 0 else Config.SKELETON_BONE
        shadow_color = (180, 70, 70) if self.hit_timer > 0 else Config.SKELETON_SHADOW

        pygame.draw.circle(screen, bone_color, (rx + 14, ry + 8), 7)
        pygame.draw.circle(screen, Config.SKELETON_EYES, (rx + 12, ry + 6), 1)
        pygame.draw.circle(screen, Config.SKELETON_EYES, (rx + 16, ry + 6), 1)
        
        pygame.draw.line(screen, bone_color, (rx + 14, ry + 15), (rx + 14, ry + 32), 3)
        pygame.draw.line(screen, shadow_color, (rx + 6, ry + 19), (rx + 22, ry + 19), 2)
        pygame.draw.line(screen, shadow_color, (rx + 5, ry + 24), (rx + 23, ry + 24), 2)
        pygame.draw.line(screen, shadow_color, (rx + 7, ry + 29), (rx + 21, ry + 29), 2)
        pygame.draw.rect(screen, bone_color, (rx + 10, ry + 31, 8, 4))
        
        leg_anim = math.sin(pygame.time.get_ticks() * 0.015) * 4 if self.stun_timer == 0 else 0
        pygame.draw.line(screen, bone_color, (rx + 10, ry + 35), (rx + 8 + leg_anim, ry + 48), 3)
        pygame.draw.line(screen, bone_color, (rx + 18, ry + 35), (rx + 20 - leg_anim, ry + 48), 3)
        
        sh_x = rx - 4 if self.direction < 0 else rx + 16
        pygame.draw.circle(screen, (90, 60, 40), (sh_x + 6, ry + 26), 9)
        pygame.draw.circle(screen, (150, 150, 150), (sh_x + 6, ry + 26), 9, 2)
        pygame.draw.circle(screen, (170, 170, 170), (sh_x + 6, ry + 26), 2)

        if self.direction < 0:
            pygame.draw.line(screen, bone_color, (rx + 8, ry + 17), (rx + 2, ry + 28), 2)
            pygame.draw.line(screen, (90, 90, 95), (rx + 2, ry + 28), (rx - 6, ry + 16), 3)
        else:
            pygame.draw.line(screen, bone_color, (rx + 20, ry + 17), (rx + 26, ry + 28), 2)
            pygame.draw.line(screen, (90, 90, 95), (rx + 26, ry + 28), (rx + 34, ry + 16), 3)

# Engine do Jogo
class Game:
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_GAME_OVER = 2
    STATE_VICTORY = 3

    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # Inicializa mixer de áudio especificando frequência e tamanho para compatibilidade de WAVs
        try:
            pygame.mixer.init(22050, -16, 1, 512)
        except Exception:
            try:
                pygame.mixer.init()
            except Exception:
                pass
            
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("O Cavaleiro das Sombras")
        self.clock = pygame.time.Clock()
        
        self.fonts = {
            'title': self.get_safe_font('georgia', 48, bold=True),
            'subtitle': self.get_safe_font('georgia', 24),
            'hud': self.get_safe_font('georgia', 18, bold=True),
            'info': self.get_safe_font('georgia', 15),
            'gameover': self.get_safe_font('georgia', 64, bold=True)
        }
        self.font_cache = {}
        
        self.sky_bg = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        for y in range(Config.SCREEN_HEIGHT):
            ratio = y / Config.SCREEN_HEIGHT
            r = int(Config.SKY_TOP[0] * (1 - ratio) + Config.SKY_BOTTOM[0] * ratio)
            g = int(Config.SKY_TOP[1] * (1 - ratio) + Config.SKY_BOTTOM[1] * ratio)
            b = int(Config.SKY_TOP[2] * (1 - ratio) + Config.SKY_BOTTOM[2] * ratio)
            pygame.draw.line(self.sky_bg, (r, g, b), (0, y), (Config.SCREEN_WIDTH, y))

        self.torch_aura = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(self.torch_aura, (255, 140, 30, 10), (40, 40), 38)
        pygame.draw.circle(self.torch_aura, (255, 140, 30, 22), (40, 40), 22)
        pygame.draw.circle(self.torch_aura, (255, 190, 50, 45), (40, 40), 10)

        self.state = Game.STATE_MENU
        self.reset_game()
        
        self.init_sounds()
        self.play_bg_music()

    def get_safe_font(self, name, size, bold=False):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            return pygame.font.Font(None, size)

    def init_sounds(self):
        swing_path = "sword_swing.wav"
        hit_path = "enemy_hit.wav"
        
        # Sempre gera do zero para evitar arquivos silenciosos ou corrompidos em cache
        try:
            generate_swing_wav(swing_path)
        except Exception:
            pass
        try:
            generate_hit_wav(hit_path)
        except Exception:
            pass
                
        self.sfx_swing = None
        self.sfx_hit = None
        
        if pygame.mixer.get_init():
            try:
                if os.path.exists(swing_path):
                    self.sfx_swing = pygame.mixer.Sound(swing_path)
                    self.sfx_swing.set_volume(0.35)
                if os.path.exists(hit_path):
                    self.sfx_hit = pygame.mixer.Sound(hit_path)
                    self.sfx_hit.set_volume(0.40)
            except Exception as e:
                print(f"Erro no áudio SFX: {e}")

    def play_bg_music(self):
        wav_filename = "medieval_theme.wav"
        # Sempre gera do zero para garantir integridade da música antiga
        try:
            generate_medieval_wav(wav_filename)
        except Exception as e:
            print(f"Erro na música: {e}")
            return
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.load(wav_filename)
                pygame.mixer.music.set_volume(0.12)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"Erro ao tocar música: {e}")

    def reset_game(self):
        self.player = Player(100, 400)
        self.particles = []
        self.score = 0
        self.screen_shake = 0
        self.time_counter = 0
        self.dragon_timer = 0
        
        self.enemies = [
            Enemy(450, 400, 300, 600),
            Enemy(900, 300, 750, 1050),
            Enemy(1200, 400, 1100, 1350),
            Enemy(1800, 400, 1600, 2050),
            Enemy(2100, 300, 1850, 2300)
        ]

        self.platforms = [
            Platform(0, 520, 1400, 80, 'forest'),
            Platform(300, 420, 160, 22, 'forest'),
            Platform(600, 340, 180, 22, 'forest'),
            Platform(900, 420, 160, 22, 'forest'),
            
            Platform(1150, 460, 100, 25, 'castle'),
            Platform(1270, 390, 100, 25, 'castle'),
            Platform(1380, 320, 80, 25, 'castle'),
            Platform(1440, 250, 60, 25, 'castle'),
            
            Platform(1400, 520, 1600, 80, 'castle'),
            Platform(1480, 200, 50, 320, 'castle'),
            
            Platform(1650, 400, 850, 25, 'castle'),
            Platform(1800, 280, 700, 25, 'castle'),
            Platform(1950, 160, 350, 25, 'castle'),
            
            Platform(1560, 460, 80, 20, 'castle'),
            Platform(2520, 340, 80, 20, 'castle'),
            Platform(1880, 220, 80, 20, 'castle')
        ]

        self.flag_rect = pygame.Rect(2230, 80, 40, 80)

        self.stars = []
        for _ in range(80):
            self.stars.append((
                random.randint(0, Config.SCREEN_WIDTH), 
                random.randint(0, 380), 
                random.uniform(0.04, 0.1), 
                random.uniform(0, 2 * math.pi)
            ))
            
        self.bg_trees = []
        for _ in range(15):
            self.bg_trees.append((random.randint(20, 1380), random.uniform(0.85, 1.25)))
            
        self.torches = [
            (1495, 230),
            (1720, 350),
            (2100, 350),
            (1900, 230),
            (2250, 230)
        ]

        self.mountain_points_1 = []
        for x in range(-200, 3200, 140):
            y = 330 + (x % 7) * 12 + (x % 3) * 15
            self.mountain_points_1.append((x, y))
            
        self.mountain_points_2 = []
        for x in range(-200, 3200, 90):
            y = 390 + (x % 5) * 18 + (x % 4) * 10
            self.mountain_points_2.append((x, y))

        self.clouds = []
        for _ in range(7):
            self.clouds.append({
                'x': random.uniform(0, Config.WORLD_WIDTH),
                'y': random.uniform(20, 220),
                'speed': random.uniform(0.15, 0.35),
                'w': random.uniform(90, 160),
                'h': random.uniform(22, 40)
            })

        self.camera_offset_x = 0
        self.hit_enemies_this_swing = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if self.state == Game.STATE_MENU:
                    if event.key == pygame.K_SPACE:
                        self.state = Game.STATE_PLAYING
                elif self.state in [Game.STATE_GAME_OVER, Game.STATE_VICTORY]:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = Game.STATE_PLAYING

    def update(self):
        if self.state != Game.STATE_PLAYING:
            return

        self.time_counter += 1

        self.player.handle_input()
        self.player.update(self.platforms, self.particles)

        if self.player.should_play_swing:
            self.player.should_play_swing = False
            try:
                if self.sfx_swing:
                    self.sfx_swing.play()
            except Exception:
                pass

        target_cam_x = self.player.rect.centerx - Config.SCREEN_WIDTH // 2
        max_cam_x = Config.WORLD_WIDTH - Config.SCREEN_WIDTH
        self.camera_offset_x += (target_cam_x - self.camera_offset_x) * 0.1
        self.camera_offset_x = max(0, min(max_cam_x, self.camera_offset_x))

        for cloud in self.clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > Config.WORLD_WIDTH + 100:
                cloud['x'] = -150

        for enemy in self.enemies:
            if enemy.health > 0:
                enemy.update(self.platforms)

        if self.player.is_attacking:
            attack_width = 45
            if self.player.facing_right:
                attack_rect = pygame.Rect(self.player.rect.right, self.player.rect.y, attack_width, self.player.rect.height)
            else:
                attack_rect = pygame.Rect(self.player.rect.left - attack_width, self.player.rect.y, attack_width, self.player.rect.height)
                
            for enemy in self.enemies:
                if enemy.health > 0 and enemy not in self.hit_enemies_this_swing:
                    if attack_rect.colliderect(enemy.rect):
                        enemy.health -= 1
                        self.hit_enemies_this_swing.append(enemy)
                        enemy.hit_timer = 12
                        enemy.stun_timer = 18
                        
                        k_dir = 1 if self.player.facing_right else -1
                        enemy.knockback_x = k_dir * 8
                        self.screen_shake = 6
                        
                        try:
                            if self.sfx_hit:
                                self.sfx_hit.play()
                        except Exception:
                            pass
                        
                        for _ in range(6):
                            self.particles.append(Particle(
                                enemy.rect.centerx, enemy.rect.centery,
                                random.uniform(-4, 4) + k_dir * 2,
                                random.uniform(-4, 1),
                                Config.SWORD_SPARK,
                                random.uniform(2, 4),
                                random.randint(10, 20)
                            ))
                            
                        if enemy.health <= 0:
                            self.score += 1
                            for _ in range(12):
                                self.particles.append(Particle(
                                    enemy.rect.centerx, enemy.rect.centery,
                                    random.uniform(-3, 3),
                                    random.uniform(-5, 0),
                                    Config.SKELETON_BONE,
                                    random.uniform(3, 5),
                                    random.randint(20, 35)
                                ))
        else:
            self.hit_enemies_this_swing.clear()

        if self.player.invulnerable_timer == 0:
            for enemy in self.enemies:
                if enemy.health > 0:
                    if self.player.rect.colliderect(enemy.rect):
                        self.player.health -= 1
                        self.player.invulnerable_timer = 60
                        
                        k_dir = 1 if enemy.rect.centerx < self.player.rect.centerx else -1
                        self.player.velocity_x = k_dir * 6
                        self.player.velocity_y = -4
                        self.player.on_ground = False
                        self.screen_shake = 12
                        
                        for _ in range(10):
                            self.particles.append(Particle(
                                self.player.rect.centerx, self.player.rect.centery,
                                random.uniform(-3, 3),
                                random.uniform(-3, 1),
                                (200, 30, 30),
                                random.uniform(3, 5),
                                random.randint(15, 25)
                            ))
                            
                        if self.player.health <= 0:
                            self.state = Game.STATE_GAME_OVER
                        break

        if self.player.rect.colliderect(self.flag_rect):
            self.state = Game.STATE_VICTORY

        for tx, ty in self.torches:
            if abs(tx - self.player.rect.x) < 600:
                self.particles.append(Particle(
                    tx + 3, ty - 8,
                    random.uniform(-0.3, 0.3),
                    random.uniform(-1.0, -0.4),
                    random.choice([(255, 100, 0), (255, 180, 0), (230, 40, 10)]),
                    random.uniform(2.5, 4.5),
                    random.randint(15, 25),
                    decay=0.94
                ))

        self.dragon_timer += 1
        if self.dragon_timer % 90 == 0:
            self.particles.append(TextParticle(
                "Z", 2030, 105, 
                random.uniform(-0.5, -0.1), 
                random.uniform(-0.8, -0.4), 
                (180, 190, 240), 20, 75
            ))
        if self.dragon_timer % 5 == 0:
            self.particles.append(Particle(
                2030, 110,
                random.uniform(-1.2, -0.3),
                random.uniform(-0.4, 0.4),
                (255, 120, 40),
                random.uniform(2, 4),
                random.randint(25, 45),
                decay=0.97
            ))

        for part in self.particles[:]:
            part.update()
            if part.lifetime <= 0:
                self.particles.remove(part)

        if self.screen_shake > 0:
            self.screen_shake -= 1

    def draw(self):
        self.screen.blit(self.sky_bg, (0, 0))

        for star in self.stars:
            x, y, speed, offset = star
            brightness = int(140 + 115 * math.sin(self.time_counter * speed + offset))
            star_rx = int((x - self.camera_offset_x * 0.05) % Config.SCREEN_WIDTH)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (star_rx, y), 1)

        moon_rx = int(620 - self.camera_offset_x * 0.08)
        pygame.draw.circle(self.screen, Config.MOON_GLOW, (moon_rx, 110), 55)
        pygame.draw.circle(self.screen, Config.MOON_COLOR, (moon_rx, 110), 45)
        pygame.draw.circle(self.screen, (225, 225, 215), (moon_rx - 15, 100), 8)
        pygame.draw.circle(self.screen, (225, 225, 215), (moon_rx + 15, 120), 10)
        pygame.draw.circle(self.screen, (225, 225, 215), (moon_rx, 128), 6)

        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.randint(-self.screen_shake, self.screen_shake)
            shake_y = random.randint(-self.screen_shake, self.screen_shake)
            
        render_cam_x = self.camera_offset_x + shake_x

        for cloud in self.clouds:
            cloud_rx = int((cloud['x'] - render_cam_x * 0.07) % (Config.WORLD_WIDTH + 200) - 100)
            if -180 <= cloud_rx <= Config.SCREEN_WIDTH + 180:
                cw = cloud['w']
                ch = cloud['h']
                cy = cloud['y'] + shake_y
                pygame.draw.ellipse(self.screen, (32, 28, 48), (cloud_rx, cy, cw, ch))
                pygame.draw.ellipse(self.screen, (32, 28, 48), (cloud_rx + cw*0.2, cy - ch*0.3, cw*0.6, ch*1.3))
                pygame.draw.ellipse(self.screen, (32, 28, 48), (cloud_rx - cw*0.1, cy + ch*0.1, cw*0.5, ch*0.8))

        pts_m1 = []
        for px, py in self.mountain_points_1:
            pts_m1.append((int(px - render_cam_x * 0.04), int(py + shake_y)))
        pts_m1.append((Config.SCREEN_WIDTH + 300, Config.SCREEN_HEIGHT))
        pts_m1.append((-300, Config.SCREEN_HEIGHT))
        pygame.draw.polygon(self.screen, (20, 16, 32), pts_m1)

        pts_m2 = []
        for px, py in self.mountain_points_2:
            pts_m2.append((int(px - render_cam_x * 0.12), int(py + shake_y)))
        pts_m2.append((Config.SCREEN_WIDTH + 300, Config.SCREEN_HEIGHT))
        pts_m2.append((-300, Config.SCREEN_HEIGHT))
        pygame.draw.polygon(self.screen, (26, 22, 38), pts_m2)

        for tx, scale in self.bg_trees:
            draw_x = int(tx - render_cam_x * 0.4)
            if -100 <= draw_x <= Config.SCREEN_WIDTH + 100:
                tw = int(14 * scale)
                th = int(35 * scale)
                pygame.draw.rect(self.screen, (28, 20, 16), (draw_x, 520 - th + shake_y, tw, th))
                for i in range(3):
                    bot_y = 520 - th - int(i * 18 * scale) + shake_y
                    w = int(70 * scale * (1 - i * 0.25))
                    h = int(40 * scale)
                    pts = [
                        (draw_x + tw // 2, bot_y - h),
                        (draw_x + tw // 2 - w // 2, bot_y),
                        (draw_x + tw // 2 + w // 2, bot_y)
                    ]
                    pygame.draw.polygon(self.screen, (10, 23, 14), pts)

        for platform in self.platforms:
            platform.draw(self.screen, render_cam_x)

        gate_x = int(1530 - render_cam_x)
        if -100 <= gate_x <= Config.SCREEN_WIDTH + 100:
            pygame.draw.rect(self.screen, (18, 18, 22), (gate_x, 420 + shake_y, 60, 100))
            pygame.draw.ellipse(self.screen, (18, 18, 22), (gate_x, 390 + shake_y, 60, 60))
            pygame.draw.ellipse(self.screen, Config.CASTLE_BORDER, (gate_x, 390 + shake_y, 60, 60), 2)
            pygame.draw.rect(self.screen, Config.CASTLE_BORDER, (gate_x, 420 + shake_y, 60, 100), 2)
            
            for gx in range(gate_x + 10, gate_x + 60, 10):
                pygame.draw.line(self.screen, (40, 40, 45), (gx, 400 + shake_y), (gx, 520 + shake_y), 2)

        for tx, ty in self.torches:
            rx = int(tx - render_cam_x)
            if -50 <= rx <= Config.SCREEN_WIDTH + 50:
                self.screen.blit(self.torch_aura, (rx - 40 + 3, ty - 40 - 12 + shake_y))
                pygame.draw.line(self.screen, (85, 55, 30), (rx, ty + shake_y), (rx + 6, ty - 12 + shake_y), 3)
                pygame.draw.rect(self.screen, Config.BLACK, (rx + 3, ty - 12 + shake_y, 6, 6))

        for enemy in self.enemies:
            if enemy.health > 0:
                enemy.draw(self.screen, render_cam_x)

        drag_x = int(2020 - render_cam_x)
        drag_y = int(70 + shake_y)
        if -200 <= drag_x <= Config.SCREEN_WIDTH + 200:
            breath = int(math.sin(self.time_counter * 0.04) * 3)
            
            pygame.draw.circle(self.screen, (20, 75, 45), (drag_x + 135, drag_y + 60 + breath), 14)
            pygame.draw.circle(self.screen, (15, 65, 38), (drag_x + 150, drag_y + 48), 10)
            
            body_rect = pygame.Rect(drag_x + 40, drag_y + 20 - breath//2, 110, 65 + breath)
            pygame.draw.ellipse(self.screen, (25, 85, 50), body_rect)
            
            for sx in range(50, 120, 16):
                for sy in range(25, 55, 12):
                    pygame.draw.arc(self.screen, (15, 60, 35), (drag_x + sx, drag_y + sy - breath//2, 10, 8), 0, math.pi, 1)
            
            wing_pts = [
                (drag_x + 70, drag_y + 25),
                (drag_x + 110, drag_y + 3),
                (drag_x + 105, drag_y + 42),
                (drag_x + 85, drag_y + 47)
            ]
            pygame.draw.polygon(self.screen, (15, 55, 30), wing_pts)
            pygame.draw.polygon(self.screen, Config.BLACK, wing_pts, 1)

            neck_rect = pygame.Rect(drag_x + 15, drag_y + 35, 40, 25)
            pygame.draw.ellipse(self.screen, (25, 85, 50), neck_rect)
            
            head_rect = pygame.Rect(drag_x + 10, drag_y + 20, 32, 24)
            pygame.draw.ellipse(self.screen, (30, 95, 58), head_rect)
            
            pygame.draw.line(self.screen, Config.KNIGHT_GOLD, (drag_x + 35, drag_y + 22), (drag_x + 50, drag_y + 12), 3)
            pygame.draw.line(self.screen, Config.KNIGHT_GOLD, (drag_x + 32, drag_y + 26), (drag_x + 46, drag_y + 18), 3)
            
            pygame.draw.arc(self.screen, Config.BLACK, (drag_x + 16, drag_y + 24, 8, 8), 0, math.pi, 2)
            pygame.draw.circle(self.screen, (15, 45, 28), (drag_x + 12, drag_y + 32), 3)

        flag_x = int(self.flag_rect.x - render_cam_x)
        flag_y = int(self.flag_rect.y + shake_y)
        if -100 <= flag_x <= Config.SCREEN_WIDTH + 100:
            pygame.draw.rect(self.screen, (80, 50, 25), (flag_x, flag_y, 6, 80))
            pygame.draw.rect(self.screen, Config.BLACK, (flag_x + 6, flag_y, 40, 28))
            pygame.draw.circle(self.screen, Config.WHITE, (flag_x + 24, flag_y + 12), 5)
            pygame.draw.rect(self.screen, Config.WHITE, (flag_x + 22, flag_y + 17, 4, 3))
            pygame.draw.line(self.screen, Config.WHITE, (flag_x + 12, flag_y + 22), (flag_x + 36, flag_y + 6), 2)
            pygame.draw.line(self.screen, Config.WHITE, (flag_x + 12, flag_y + 6), (flag_x + 36, flag_y + 22), 2)

        self.player.draw(self.screen, render_cam_x)

        for part in self.particles:
            if isinstance(part, TextParticle):
                part.draw(self.screen, render_cam_x, self.font_cache)
            else:
                part.draw(self.screen, render_cam_x)

        pygame.draw.rect(self.screen, (30, 30, 35), (15, 10, 320, 60))
        pygame.draw.rect(self.screen, Config.KNIGHT_GOLD, (15, 10, 320, 60), 2)
        
        for i in range(self.player.max_health):
            hx = 30 + i * 36
            hy = 26
            
            if i < self.player.health:
                pygame.draw.circle(self.screen, Config.TEXT_RED, (hx, hy), 7)
                pygame.draw.circle(self.screen, Config.TEXT_RED, (hx + 10, hy), 7)
                pts = [(hx - 7, hy + 2), (hx + 17, hy + 2), (hx + 5, hy + 14)]
                pygame.draw.polygon(self.screen, Config.TEXT_RED, pts)
                pygame.draw.circle(self.screen, Config.WHITE, (hx - 2, hy - 2), 2)
            else:
                pygame.draw.circle(self.screen, (80, 20, 20), (hx, hy), 7, 2)
                pygame.draw.circle(self.screen, (80, 20, 20), (hx + 10, hy), 7, 2)
                pts = [(hx - 7, hy + 2), (hx + 17, hy + 2), (hx + 5, hy + 14)]
                pygame.draw.line(self.screen, (80, 20, 20), pts[0], pts[2], 2)
                pygame.draw.line(self.screen, (80, 20, 20), pts[1], pts[2], 2)

        hud_text = self.fonts['hud'].render(f"Banidos: {self.score}", True, Config.TEXT_GOLD)
        self.screen.blit(hud_text, (30, 44))
        
        if 1150 < self.player.rect.x < 1450:
            warn_text = self.fonts['hud'].render("<- Floresta Negra | Castelo Sombrio ->", True, (160, 160, 170))
            self.screen.blit(warn_text, (Config.SCREEN_WIDTH // 2 - warn_text.get_width() // 2, 40))

        if self.state == Game.STATE_MENU:
            self.draw_overlay_screen(
                "O CAVALEIRO DAS SOMBRAS",
                "Pressione ESPAÇO para Iniciar",
                [
                    "Controles de Movimento:",
                    "A, D ou Setas: Mover Cavaleiro | W, ESPAÇO ou Seta Cima: Pular",
                    "",
                    "Controles de Combate:",
                    "E, F, J ou Clique Esquerdo do Mouse: Ataque com Espada",
                    "",
                    "Instruções:",
                    "Derrote os esqueletos na floresta e suba ao topo do castelo",
                    "para recolher a bandeira sob o olhar do dragão!"
                ],
                Config.TEXT_GOLD
            )
            
        elif self.state == Game.STATE_GAME_OVER:
            self.draw_overlay_screen(
                "GAME OVER",
                "Pressione 'R' para Renascer",
                [
                    f"Você derrotou {self.score} esqueletos nesta tentativa.",
                    "Sua alma agora vaga nos confins da floresta sombria..."
                ],
                Config.TEXT_RED
            )
            
        elif self.state == Game.STATE_VICTORY:
            self.draw_overlay_screen(
                "VITÓRIA COMPLETA!",
                "Pressione 'R' para Jogar Novamente",
                [
                    "Você superou os perigos do castelo medieval,",
                    "banindo os guardas e resgatando a Bandeira de Pirata",
                    "do alto da fortaleza do dragão!",
                    "",
                    f"Total de esqueletos derrotados: {self.score}"
                ],
                Config.TEXT_GOLD
            )

        pygame.display.flip()

    def draw_overlay_screen(self, title, subtitle, info_lines, title_color):
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 8, 12, 225))
        self.screen.blit(overlay, (0, 0))

        box_width = 620
        box_height = 430
        bx = (Config.SCREEN_WIDTH - box_width) // 2
        by = (Config.SCREEN_HEIGHT - box_height) // 2
        
        pygame.draw.rect(self.screen, (24, 24, 32), (bx, by, box_width, box_height))
        pygame.draw.rect(self.screen, title_color, (bx, by, box_width, box_height), 3)
        for corner_x in [bx, bx + box_width - 10]:
            for corner_y in [by, by + box_height - 10]:
                pygame.draw.rect(self.screen, Config.KNIGHT_GOLD, (corner_x, corner_y, 10, 10))

        title_surf = self.fonts['title'].render(title, True, title_color)
        self.screen.blit(title_surf, (Config.SCREEN_WIDTH // 2 - title_surf.get_width() // 2, by + 40))

        sub_surf = self.fonts['subtitle'].render(subtitle, True, Config.WHITE)
        self.screen.blit(sub_surf, (Config.SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, by + 110))

        pygame.draw.line(self.screen, (60, 60, 85), (bx + 50, by + 160), (bx + box_width - 50, by + 160), 2)

        y_offset = by + 185
        font_info = self.fonts['info']
        for line in info_lines:
            if line == "":
                y_offset += 15
                continue
            txt_surf = font_info.render(line, True, (190, 190, 205))
            self.screen.blit(txt_surf, (Config.SCREEN_WIDTH // 2 - txt_surf.get_width() // 2, y_offset))
            y_offset += 25

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
