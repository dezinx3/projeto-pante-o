import pgzrun
import math
import random
import os
from pathlib import Path

# Configurações globais
WIDTH = 800
HEIGHT = 600
TITLE = "Panteão"

# Configurar para tela cheia
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
DARK_BLUE = (0, 0, 139)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
DARK_PURPLE = (50, 0, 50)
GOLD = (255, 215, 0)
DARK_RED = (139, 0, 0)
CYAN = (0, 255, 255)
LAVA = (255, 80, 0)
DARK_GREEN = (0, 100, 0)
LIGHT_BLUE = (173, 216, 230)
PINK = (255, 192, 203)
SILVER = (192, 192, 192)

# Variáveis globais
game = None
intro_text = [
    "Há muito tempo, no reino de square...",
    "",
    "Um poderoso guerreiro foi escolhido pelos deuses",
    "para enfrentar as criaturas sombrias que ameaçam",
    "o Panteão Sagrado. Armado apenas com seu chicote",
    "ancestral, você deve ascender através de 10 níveis",
    "de desafios mortais para restaurar a paz no reino.",
    "",
    "Cada nível conquistado concede novas habilidades",
    "divinas, mas também traz inimigos mais poderosos.",
    "",
    "A última batalha aguarda no nível 10, onde o",
    "Grande Boss guarda os portões do Panteão...",
    "",
    "Que a sorte esteja com você, guerreiro!"
]
intro_scroll_pos = HEIGHT
intro_line_height = 30
intro_speed = 1
showing_intro = True
skip_intro = False
tutorial_step = 0
tutorial_timer = 0
camera_offset_x = 0
camera_offset_y = 0
fullscreen = False

# Sistema de áudio - CORRIGIDO
sounds_loaded = False
music_playing = False

# Verificar se os arquivos de som existem
def check_sound_files():
    sound_files = ['ability', 'attack', 'collect', 'door', 'hurt', 'jump', 'music', 'select', 'shield']
    sound_extensions = ['.wav', '.mp3', '.ogg']
    
    missing_files = []
    
    for sound in sound_files:
        found = False
        for ext in sound_extensions:
            if Path(f"sounds/{sound}{ext}").exists():
                found = True
                break
        if not found:
            missing_files.append(sound)
    
    if missing_files:
        print(f"Arquivos de áudio faltando: {missing_files}")
        return False
    return True

# Tentar carregar música de fundo
def load_music():
    global music_playing
    try:
        # Tentar diferentes formatos
        for ext in ['.wav', '.mp3', '.ogg']:
            if Path(f"sounds/music{ext}").exists():
                music.play(f'music{ext}')
                music.set_volume(0.9)
                music_playing = True
                return True
        
        print("Arquivo de música não encontrado em nenhum formato")
        music_playing = False
        return False
    except Exception as e:
        print(f"Erro ao carregar música: {e}")
        music_playing = False
        return False

# Tentar tocar um som
def play_sound(sound_name, volume=1.0):
    try:
        # Tentar diferentes formatos
        for ext in ['.wav', '.mp3', '.ogg']:
            if Path(f"sounds/{sound_name}{ext}").exists():
                sound = getattr(sounds, f"{sound_name}{ext}")
                sound.set_volume(volume)
                sound.play()
                return True
        
        print(f"Arquivo de som {sound_name} não encontrado em nenhum formato")
        return False
    except Exception as e:
        print(f"Erro ao tocar som {sound_name}: {e}")
        return False

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = (
            min(color[0] + 30, 255),
            min(color[1] + 30, 255),
            min(color[2] + 30, 255)
        )
        self.is_hovered = False
    
    def draw(self):
        color = self.hover_color if self.is_hovered else self.color
        screen.draw.filled_rect(self.rect, color)
        screen.draw.rect(self.rect, WHITE)
        screen.draw.text(
            self.text, 
            center=self.rect.center, 
            color=WHITE,
            fontsize=24
        )
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            play_sound('select', 0.8)
            return True
        return False

class Player:
    def __init__(self, x, y):
        self.rect = Rect(x, y, 32, 32)
        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        self.is_jumping = False
        self.health = 100
        self.max_health = 100
        self.mana = 100
        self.max_mana = 100
        self.mana_regen = 0.5
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        self.attacking = False
        self.shielding = False
        self.shield_timer = 0
        self.max_shield_time = 300
        self.shield_cooldown = 0
        self.max_shield_cooldown = 300
        self.attack_timer = 0
        self.attack_rect = None
        self.invincibility_timer = 0
        self.hit_cooldown = 30
        self.collected_ability = None
        self.ability_cooldown = 0
        self.ability_active = False
        self.ability_timer = 0
        self.laser_active = False
        self.laser_duration = 0
        self.necromanced_enemies = []
        self.ability_effects = []
    
    def update(self, platforms, hazards, enemies):
        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y
        self.rect.x += self.velocity_x
        self.check_collisions(platforms, hazards)
        
        if self.mana < self.max_mana and not self.laser_active:
            self.mana += self.mana_regen
            if self.mana > self.max_mana:
                self.mana = self.max_mana
        
        if self.shielding:
            self.shield_timer += 1
            if self.shield_timer >= self.max_shield_time:
                self.stop_shield()
                self.shield_cooldown = self.max_shield_cooldown
        
        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1
        
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
        
        if self.attacking:
            self.attack_timer += 1
            if self.attack_timer > 15:
                self.attacking = False
                self.attack_timer = 0
                self.attack_rect = None
        
        if self.ability_cooldown > 0:
            self.ability_cooldown -= 1
        
        if self.ability_active:
            self.ability_timer -= 1
            if self.ability_timer <= 0:
                self.ability_active = False
                if self.collected_ability == "necromancer":
                    self.necromanced_enemies = []
        
        if self.laser_active:
            self.laser_duration += 1
            self.mana -= 0.1
            if self.mana <= 0:
                self.laser_active = False
                self.mana = 0
        
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
        
        # Atualizar efeitos de habilidade
        for effect in self.ability_effects[:]:
            effect["timer"] -= 1
            if effect["timer"] <= 0:
                self.ability_effects.remove(effect)
    
    def check_collisions(self, platforms, hazards):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.is_jumping = False
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0
        
        for hazard in hazards:
            if self.rect.colliderect(hazard.rect):
                if self.shielding:
                    self.take_damage(3)
                else:
                    self.take_damage(10)
                if self.velocity_y > 0:
                    self.velocity_y = -10
        
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
            self.velocity_y = 0
            self.is_jumping = False
    
    def jump(self):
        if not self.is_jumping:
            self.velocity_y = self.jump_power
            self.is_jumping = True
            play_sound('jump', 0.7)
    
    def move_left(self):
        self.velocity_x = -self.speed
        self.facing_right = False
    
    def move_right(self):
        self.velocity_x = self.speed
        self.facing_right = True
    
    def stop(self):
        self.velocity_x = 0
    
    def attack(self):
        if not self.attacking:
            self.attacking = True
            self.attack_timer = 0
            self.attack_rect = None
            play_sound('attack', 0.8)
    
    def shield(self):
        if not self.shielding and self.shield_cooldown <= 0:
            self.shielding = True
            self.shield_timer = 0
            play_sound('shield', 0.7)
    
    def stop_shield(self):
        if self.shielding:
            self.shielding = False
            self.shield_timer = 0
    
    def take_damage(self, amount):
        if self.invincibility_timer <= 0 and not self.shielding:
            self.health -= amount
            self.invincibility_timer = self.hit_cooldown
            play_sound('hurt', 0.8)
            return True
        return False
    
    def collect_ability(self, ability_type):
        self.collected_ability = ability_type
        play_sound('collect', 0.8)
    
    def use_ability(self, enemies):
        if self.collected_ability and not self.ability_active and self.ability_cooldown <= 0:
            ability_cost = {
                "big_fireball": 30,
                "energy_wave": 37,
                "lightning": 45,
                "slow_time": 55,
                "energy_orbs": 55,
                "necromancer": 70,
                "pain_spikes": 75,
                "superman": 100
            }
            
            cost = ability_cost.get(self.collected_ability, 0)
            
            if self.mana >= cost:
                self.mana -= cost
                self.ability_active = True
                self.ability_cooldown = 180
                
                # Criar efeitos visuais para a habilidade
                if self.collected_ability == "big_fireball":
                    self.ability_timer = 30
                    direction = 1 if self.facing_right else -1
                    self.ability_effects.append({
                        "type": "big_fireball",
                        "x": self.rect.centerx,
                        "y": self.rect.centery,
                        "direction": direction,
                        "timer": 60,
                        "damage": 50
                    })
                elif self.collected_ability == "energy_wave":
                    self.ability_timer = 30
                    self.ability_effects.append({
                        "type": "energy_wave",
                        "x": self.rect.centerx,
                        "y": self.rect.centery,
                        "radius": 10,
                        "timer": 30,
                        "damage": 40
                    })
                elif self.collected_ability == "lightning":
                    self.ability_timer = 60
                    self.ability_effects.append({
                        "type": "lightning",
                        "x": self.rect.centerx,
                        "y": self.rect.centery,
                        "timer": 60,
                        "damage": 35
                    })
                elif self.collected_ability == "slow_time":
                    self.ability_timer = 600
                    # Aplicar lentidão aos inimigos será feito no update deles
                elif self.collected_ability == "energy_orbs":
                    self.ability_timer = 600
                    self.ability_effects.append({
                        "type": "energy_orbs",
                        "x": self.rect.centerx,
                        "y": self.rect.centery,
                        "timer": 600,
                        "angle": 0,
                        "damage": 10
                    })
                elif self.collected_ability == "necromancer":
                    self.ability_timer = 1800
                    # A necromancia será aplicada quando inimigos morrerem
                elif self.collected_ability == "pain_spikes":
                    self.ability_timer = 180
                    direction = 1 if self.facing_right else -1
                    self.ability_effects.append({
                        "type": "pain_spikes",
                        "x": self.rect.centerx,
                        "y": self.rect.centery,
                        "direction": direction,
                        "timer": 60,
                        "damage": 60
                    })
                elif self.collected_ability == "superman":
                    self.ability_timer = 1800
                    self.laser_active = False
                
                play_sound('ability', 0.8)
                return True
        return False
    
    def draw(self):
        color = BLUE
        if self.invincibility_timer > 0 and self.invincibility_timer % 5 < 3:
            color = (100, 100, 255)
        
        screen.draw.filled_rect(self.rect, color)
        
        eye_size = 4
        if self.facing_right:
            screen.draw.filled_circle((self.rect.right - 10, self.rect.y + 10), eye_size, WHITE)
            screen.draw.filled_circle((self.rect.right - 10, self.rect.y + 22), eye_size, WHITE)
        else:
            screen.draw.filled_circle((self.rect.x + 10, self.rect.y + 10), eye_size, WHITE)
            screen.draw.filled_circle((self.rect.x + 10, self.rect.y + 22), eye_size, WHITE)
        
        if self.shielding:
            shield_radius = 25
            screen.draw.circle(self.rect.center, shield_radius, (200, 200, 200))
            
            # Barra de tempo do escudo
            if self.shield_timer > 0:
                remaining = 1.0 - (self.shield_timer / self.max_shield_time)
                bar_width = 40
                screen.draw.filled_rect(Rect(self.rect.centerx - bar_width//2, self.rect.top - 15, bar_width, 5), RED)
                screen.draw.filled_rect(Rect(self.rect.centerx - bar_width//2, self.rect.top - 15, int(bar_width * remaining), 5), GREEN)
        
        # Desenhar chicote
        if self.attacking:
            whip_length = 64
            whip_width = 3
            
            if self.facing_right:
                start_x = self.rect.right
                start_y = self.rect.centery
                end_x = start_x + whip_length
                end_y = start_y
                self.attack_rect = Rect(start_x, start_y - whip_width//2, whip_length, whip_width)
            else:
                start_x = self.rect.left
                start_y = self.rect.centery
                end_x = start_x - whip_length
                end_y = start_y
                self.attack_rect = Rect(start_x - whip_length, start_y - whip_width//2, whip_length, whip_width)
            
            screen.draw.line((start_x, start_y), (end_x, end_y), WHITE)
            screen.draw.filled_circle((end_x, end_y), 4, WHITE)

        if self.laser_active:
            laser_length = WIDTH if self.facing_right else 0
            laser_width = 10
            if self.facing_right:
                screen.draw.filled_rect(Rect(self.rect.right, self.rect.centery - laser_width//2, 
                                           WIDTH - self.rect.right, laser_width), RED)
            else:
                screen.draw.filled_rect(Rect(0, self.rect.centery - laser_width//2, 
                                           self.rect.left, laser_width), RED)
        
        # Desenhar efeitos de habilidade
        for effect in self.ability_effects:
            if effect["type"] == "big_fireball":
                x = effect["x"] + effect["direction"] * 10 * (60 - effect["timer"])
                screen.draw.filled_circle((x, effect["y"]), 20, ORANGE)
                screen.draw.circle((x, effect["y"]), 20, RED)
            
            elif effect["type"] == "energy_wave":
                radius = effect["radius"] + (30 - effect["timer"]) * 5
                screen.draw.circle((effect["x"], effect["y"]), radius, CYAN)
            
            elif effect["type"] == "lightning":
                for i in range(5):
                    angle = random.uniform(0, 2 * math.pi)
                    length = random.randint(50, 150)
                    end_x = effect["x"] + math.cos(angle) * length
                    end_y = effect["y"] + math.sin(angle) * length
                    screen.draw.line((effect["x"], effect["y"]), (end_x, end_y), YELLOW)
            
            elif effect["type"] == "energy_orbs":
                effect["angle"] += 0.1
                for i in range(3):
                    angle = effect["angle"] + i * (2 * math.pi / 3)
                    x = effect["x"] + math.cos(angle) * 40
                    y = effect["y"] + math.sin(angle) * 40
                    screen.draw.filled_circle((x, y), 10, YELLOW)
                    screen.draw.circle((x, y), 10, ORANGE)
            
            elif effect["type"] == "pain_spikes":
                x = effect["x"] + effect["direction"] * 10 * (60 - effect["timer"])
                screen.draw.filled_rect(Rect(x - 30, effect["y"] - 5, 60, 10), DARK_RED)
                for i in range(6):
                    spike_x = x - 25 + i * 10
                    screen.draw.line((spike_x, effect["y"] - 5), (spike_x + 5, effect["y"] - 15), RED)

class Platform:
    def __init__(self, x, y, width, height, is_ground=False):
        self.rect = Rect(x, y, width, height)
        self.is_ground = is_ground
    
    def draw(self):
        if self.is_ground:
            screen.draw.filled_rect(self.rect, BROWN)
            for i in range(0, self.rect.width, 20):
                screen.draw.line((self.rect.x + i, self.rect.y),
                                (self.rect.x + i, self.rect.y + self.rect.height),
                                (100, 50, 0))
        else:
            screen.draw.filled_rect(self.rect, GREEN)
            screen.draw.rect(self.rect, DARK_GREEN)

class Hazard:
    def __init__(self, x, y, width, height, hazard_type="spikes"):
        self.rect = Rect(x, y, width, height)
        self.type = hazard_type
    
    def draw(self):
        if self.type == "spikes":
            screen.draw.filled_rect(self.rect, LAVA)
            for i in range(0, self.rect.width, 10):
                screen.draw.line((self.rect.x + i, self.rect.y + self.rect.height),
                                (self.rect.x + i + 5, self.rect.y),
                                RED)

class Enemy:
    def __init__(self, x, y, enemy_type, level):
        self.rect = Rect(x, y, 32, 32)
        self.type = enemy_type
        self.level = level
        self.direction = 1
        self.velocity_y = 0
        self.gravity = 0.8
        self.is_jumping = False
        self.animation_frame = 0
        self.animation_timer = 0
        self.attack_cooldown = 0
        self.aggro = False
        self.aggro_timer = 0
        self.projectiles = []
        self.necromanced = False
        self.slowed = False
        self.slow_timer = 0
        
        stat_multiplier = 1 + (level * 0.1)
        
        if enemy_type == 1:
            self.color = RED
            self.health = 30 + (level * 5)
            self.max_health = 30 + (level * 5)
            self.damage = int(20 * stat_multiplier)
            self.speed = random.uniform(1.0, 2.0) * stat_multiplier
            self.aggro_range = 200
        elif enemy_type == 2:
            self.color = CYAN
            self.health = 40 + (level * 5)
            self.max_health = 40 + (level * 5)
            self.damage = int(25 * stat_multiplier)
            self.speed = random.uniform(1.5, 2.5) * stat_multiplier
            self.aggro_range = 250
            self.jump_power = -12
        elif enemy_type == 3:
            self.color = GREEN
            self.health = 25 + (level * 5)
            self.max_health = 25 + (level * 5)
            self.damage = int(15 * stat_multiplier)
            self.speed = random.uniform(2.0, 3.0) * stat_multiplier
            self.aggro_range = 220
        elif enemy_type == 4:
            self.color = PURPLE
            self.health = 35 + (level * 5)
            self.max_health = 35 + (level * 5)
            self.damage = int(30 * stat_multiplier)
            self.speed = random.uniform(1.0, 1.5) * stat_multiplier
            self.aggro_range = 300
            self.teleport_cooldown = 0
        elif enemy_type == 5:
            self.color = ORANGE
            self.health = 30 + (level * 5)
            self.max_health = 30 + (level * 5)
            self.damage = int(15 * stat_multiplier)
            self.speed = random.uniform(1.0, 1.5) * stat_multiplier
            self.aggro_range = 350
            self.shoot_cooldown = 0
        elif enemy_type == 6:
            self.rect = Rect(x, y, 64, 64)
            self.color = GRAY
            self.health = 100 + (level * 10)
            self.max_health = 100 + (level * 10)
            self.damage = int(35 * stat_multiplier)
            self.speed = random.uniform(0.3, 0.8) * stat_multiplier
            self.aggro_range = 180
        elif enemy_type == 7:
            self.color = (150, 150, 150)
            self.health = 50 + (level * 5)
            self.max_health = 50 + (level * 5)
            self.damage = int(25 * stat_multiplier)
            self.speed = random.uniform(1.0, 2.0) * stat_multiplier
            self.aggro_range = 250
            self.current_form = 1
            self.form_change_timer = 0
        elif enemy_type == 8:
            self.color = LIGHT_BLUE
            self.health = 35 + (level * 5)
            self.max_health = 35 + (level * 5)
            self.damage = int(20 * stat_multiplier)
            self.speed = random.uniform(1.5, 2.5) * stat_multiplier
            self.aggro_range = 300
            self.flying = True
        elif enemy_type == 9:
            self.color = PINK
            self.health = 40 + (level * 5)
            self.max_health = 40 + (level * 5)
            self.damage = int(30 * stat_multiplier)
            self.speed = random.uniform(1.0, 1.5) * stat_multiplier
            self.aggro_range = 280
            self.has_twin = False
        elif enemy_type == 10:  # Boss
            self.rect = Rect(x, y, 96, 96)
            self.color = DARK_RED
            self.health = 2000
            self.max_health = 2000
            self.damage = int(50 * stat_multiplier)
            self.speed = random.uniform(0.5, 1.0) * stat_multiplier
            self.aggro_range = 500
            self.boss_state = "approach"
            self.boss_timer = 0
            self.boss_attack_cooldown = 0
    
    def update(self, player, platforms):
        if self.slowed:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.slowed = False
                self.speed /= 0.4
        
        if not hasattr(self, 'flying') or not self.flying:
            self.velocity_y += self.gravity
            self.rect.y += self.velocity_y
            self.check_collisions(platforms)
        
        player_distance = math.sqrt((self.rect.x - player.rect.x)**2 + (self.rect.y - player.rect.y)**2)
        
        if player_distance < self.aggro_range:
            self.aggro = True
            self.aggro_timer = 120
        elif self.aggro_timer > 0:
            self.aggro_timer -= 1
        else:
            self.aggro = False
        
        if self.aggro:
            self.aggro_behavior(player)
        else:
            self.patrol_behavior()
        
        self.special_update(player)
        
        self.animation_timer += 1
        if self.animation_timer >= 15:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
        
        if self.type == 10:
            self.boss_behavior(player)
    
    def apply_slow(self):
        if not self.slowed:
            self.slowed = True
            self.slow_timer = 600
            self.speed *= 0.4
    
    def boss_behavior(self, player):
        self.boss_timer += 1
        self.boss_attack_cooldown -= 1
        
        if self.boss_state == "approach":
            if self.rect.x < player.rect.x:
                self.rect.x += self.speed
            else:
                self.rect.x -= self.speed
                
            if abs(self.rect.x - player.rect.x) < 100:
                self.boss_state = "retreat"
                self.boss_timer = 0
        
        elif self.boss_state == "retreat":
            if self.rect.x < player.rect.x:
                self.rect.x -= self.speed
            else:
                self.rect.x += self.speed
                
            if self.boss_timer > 60:
                self.boss_state = "tremble"
                self.boss_timer = 0
        
        elif self.boss_state == "tremble":
            self.rect.x += random.randint(-2, 2)
            if self.boss_timer > 30:
                self.boss_state = "shoot"
                self.boss_timer = 0
        
        elif self.boss_state == "shoot":
            if self.boss_attack_cooldown <= 0:
                direction = 1 if self.rect.x < player.rect.x else -1
                self.projectiles.append([self.rect.centerx, self.rect.centery, direction])
                self.boss_attack_cooldown = 60
                self.boss_state = "speed"
                self.boss_timer = 0
        
        elif self.boss_state == "speed":
            self.speed = 5
            if self.rect.x < player.rect.x:
                self.rect.x += self.speed
            else:
                self.rect.x -= self.speed
                
            if abs(self.rect.x - player.rect.x) < 50:
                self.boss_state = "teleport"
                self.boss_timer = 0
        
        elif self.boss_state == "teleport":
            self.rect.x = player.rect.x - 160
            self.boss_state = "jump"
            self.boss_timer = 0
        
        elif self.boss_state == "jump":
            if not self.is_jumping:
                self.velocity_y = -15
                self.is_jumping = True
                
            if self.rect.bottom >= player.rect.top and self.velocity_y > 0:
                self.boss_state = "approach"
                self.speed = random.uniform(0.5, 1.0)
                self.boss_timer = 0
    
    def aggro_behavior(self, player):
        if self.type == 10:
            return
            
        if self.rect.x < player.rect.x:
            self.rect.x += self.speed
            self.direction = 1
        else:
            self.rect.x -= self.speed
            self.direction = -1
        
        if self.type == 2 and not self.is_jumping and random.random() < 0.02:
            self.velocity_y = self.jump_power
            self.is_jumping = True
        
        elif self.type == 4 and self.teleport_cooldown <= 0:
            if random.random() < 0.01:
                self.rect.x = player.rect.x - 160
                self.teleport_cooldown = 180
        
        elif self.type == 5 and self.shoot_cooldown <= 0:
            direction = 1 if self.rect.x < player.rect.x else -1
            self.projectiles.append([self.rect.centerx, self.rect.centery, direction])
            self.shoot_cooldown = 120 - (self.level * 5)
        
        elif self.type == 7:
            self.form_change_timer += 1
            if self.form_change_timer >= 300:
                self.current_form = random.randint(1, 8)
                self.form_change_timer = 0
        
        elif self.type == 8:
            if self.rect.y < player.rect.y:
                self.rect.y += 1
            else:
                self.rect.y -= 1
        
        elif self.type == 9 and not self.has_twin:
            self.has_twin = True
        
        if self.type == 4:
            self.teleport_cooldown -= 1
        if self.type == 5:
            self.shoot_cooldown -= 1
    
    def patrol_behavior(self):
        if self.type == 10:
            return
            
        self.rect.x += self.speed * self.direction
        
        if self.rect.left < 0 or self.rect.right > WIDTH or random.random() < 0.01:
            self.direction *= -1
    
    def special_update(self, player):
        if self.type == 5 or self.type == 10:
            for proj in self.projectiles[:]:
                proj[0] += proj[2] * 5
                if proj[0] < 0 or proj[0] > WIDTH:
                    self.projectiles.remove(proj)
                elif player.rect.collidepoint(proj[0], proj[1]):
                    player.take_damage(self.damage // 2)
                    self.projectiles.remove(proj)
    
    def check_collisions(self, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.is_jumping = False
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0
        
        if self.rect.left < 0:
            self.rect.left = 0
            self.direction = 1
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.direction = -1
        if self.rect.bottom > HEIGHT and not hasattr(self, 'flying'):
            self.rect.bottom = HEIGHT
            self.velocity_y = 0
            self.is_jumping = False
    
    def draw(self):
        if self.necromanced:
            screen.draw.filled_rect(self.rect, GRAY)
        else:
            screen.draw.filled_rect(self.rect, self.color)
        
        eye_size = 4
        if self.type == 10:
            eye_size = 8
            
        if self.direction > 0:
            screen.draw.filled_circle((self.rect.right - 10, self.rect.y + 10), eye_size, WHITE)
            screen.draw.filled_circle((self.rect.right - 10, self.rect.y + 22), eye_size, WHITE)
        else:
            screen.draw.filled_circle((self.rect.x + 10, self.rect.y + 10), eye_size, WHITE)
            screen.draw.filled_circle((self.rect.x + 10, self.rect.y + 22), eye_size, WHITE)
        
        if self.health < self.max_health:
            health_width = int((self.health / self.max_health) * self.rect.width)
            screen.draw.filled_rect(Rect(self.rect.x, self.rect.y - 10, self.rect.width, 5), RED)
            screen.draw.filled_rect(Rect(self.rect.x, self.rect.y - 10, health_width, 5), GREEN)
        
        if self.type == 5 or self.type == 10:
            for proj in self.projectiles:
                screen.draw.filled_circle((int(proj[0]), int(proj[1])), 5, ORANGE)

class AbilityOrb:
    def __init__(self, x, y, ability_type):
        self.rect = Rect(x, y, 30, 30)
        self.type = ability_type
        self.collected = False
        self.animation_timer = 0
        
        self.colors = {
            "big_fireball": ORANGE,
            "energy_wave": BLUE,
            "lightning": PURPLE,
            "slow_time": GRAY,
            "energy_orbs": YELLOW,
            "necromancer": (50, 50, 50),
            "pain_spikes": DARK_RED,
            "superman": RED
        }
        
        self.color = self.colors.get(ability_type, WHITE)
    
    def update(self, player):
        if not self.collected and player.rect.colliderect(self.rect):
            player.collect_ability(self.type)
            self.collected = True
            return True
        return False
    
    def draw(self):
        if not self.collected:
            self.animation_timer += 1
            pulse = (math.sin(self.animation_timer * 0.1) + 1) / 2
            size = 15 + pulse * 10
            
            screen.draw.filled_circle(self.rect.center, int(size), self.color)
            screen.draw.circle(self.rect.center, int(size), WHITE)

class Door:
    def __init__(self, x, y):
        self.rect = Rect(x, y, 50, 70)
    
    def draw(self):
        screen.draw.filled_rect(self.rect, GOLD)
        screen.draw.rect(self.rect, (200, 150, 0))
        screen.draw.rect(Rect(self.rect.x + 10, self.rect.y + 20, 30, 5), (200, 150, 0))
        screen.draw.rect(Rect(self.rect.x + 10, self.rect.y + 40, 30, 5), (200, 150, 0))

class Game:
    def __init__(self):
        self.state = "menu"
        self.player = None
        self.enemies = []
        self.platforms = []
        self.hazards = []
        self.door = None
        self.ability_orbs = []
        self.level = 1
        self.max_level = 10
        self.music_on = True
        self.sounds_on = True
        self.paused = False
        self.transition_timer = 0
        self.transitioning = False
        self.ability_choices = []
        self.showing_options = False
        
        # Verificar arquivos de áudio
        self.audio_available = check_sound_files()
        if not self.audio_available:
            print("Alguns arquivos de áudio estão faltando. O jogo funcionará sem som.")
        
        self.play_button = Button(300, 200, 200, 50, "JOGAR", BLUE)
        self.options_button = Button(300, 270, 200, 50, "OPÇÕES", GREEN)
        self.quit_button = Button(300, 340, 200, 50, "SAIR", RED)
        
        self.resume_button = Button(300, 200, 200, 50, "RETORNAR", BLUE)
        self.menu_button = Button(300, 270, 200, 50, "MENU PRINCIPAL", GREEN)
        self.back_button = Button(300, 340, 200, 50, "VOLTAR", PURPLE)
        
        self.music_toggle = Button(300, 200, 200, 50, "MÚSICA: LIGADA", GREEN)
        self.sounds_toggle = Button(300, 270, 200, 50, "SONS: LIGADOS", PURPLE)
        
        self.generate_level()
    
    def generate_level(self):
        self.platforms = []
        self.enemies = []
        self.hazards = []
        self.ability_orbs = []
        self.transitioning = False
        
        # Plataforma principal
        self.platforms.append(Platform(0, 550, 800, 50, True))
        
        if self.level == 1:
            # Tutorial level
            self.platforms.extend([
                Platform(100, 450, 150, 20),
                Platform(350, 350, 150, 20),
                Platform(600, 450, 150, 20)
            ])
            
            # Inimigos básicos
            enemy_positions = [(200, 518), (400, 518), (600, 518), (300, 418), (500, 418)]
            for x, y in enemy_positions:
                self.enemies.append(Enemy(x, y, 1, self.level))
            
            # Porta
            self.door = Door(675, 320)
            
            # Orbe de habilidade
            self.ability_orbs.append(AbilityOrb(700, 520, "big_fireball"))
        
        elif self.level == 10:
            # Boss level
            self.platforms.extend([
                Platform(150, 450, 150, 20),
                Platform(500, 450, 150, 20)
            ])
            
            # Boss
            self.enemies.append(Enemy(400, 350, 10, self.level))
            
            # Porta
            self.door = Door(675, 380)
            
            # Orbe de habilidade
            self.ability_orbs.append(AbilityOrb(700, 520, "superman"))
            
            # Escolhas de habilidade para o boss
            self.ability_choices = [
                "big_fireball", "energy_wave", "lightning", 
                "slow_time", "energy_orbs", "necromancer", 
                "pain_spikes", "superman"
            ]
        
        else:
            # Níveis regulares
            platform_count = min(5 + self.level, 10)
            
            for i in range(platform_count):
                if i % 2 == 0:
                    x = 100
                else:
                    x = 500
                
                y = 500 - (i * 60)
                self.platforms.append(Platform(x, y, 200, 20))
            
            # Adicionar hazards a partir do nível 4
            if self.level > 3:
                hazard_count = min(self.level - 3, 4)
                hazard_positions = [(200, 550), (400, 550), (600, 550)]
                for i in range(hazard_count):
                    if i < len(hazard_positions):
                        x, y = hazard_positions[i]
                        self.hazards.append(Hazard(x, y, 50, 50))
            
            # Adicionar inimigos
            enemy_count = 5 + self.level
            enemy_types = min(self.level, 9)
            
            for i in range(enemy_count):
                if i % 2 == 0:
                    x = random.randint(100, 700)
                    y = 518
                else:
                    platform = random.choice([p for p in self.platforms if not p.is_ground])
                    x = platform.rect.x + random.randint(0, platform.rect.width - 32)
                    y = platform.rect.y - 32
                
                enemy_type = random.randint(1, enemy_types)
                self.enemies.append(Enemy(x, y, enemy_type, self.level))
            
            # Porta
            top_platform = sorted([p for p in self.platforms if not p.is_ground], key=lambda p: p.rect.y)[0]
            self.door = Door(top_platform.rect.x + top_platform.rect.width // 2 - 25, top_platform.rect.y - 70)

            # Orbe de habilidade
            abilities = [
                "big_fireball", "energy_wave", "lightning", 
                "slow_time", "energy_orbs", "necromancer", 
                "pain_spikes", "superman"
            ]
            if self.level - 1 < len(abilities):
                ability_type = abilities[self.level - 1]
                self.ability_orbs.append(AbilityOrb(700, 520, ability_type))
        
        # Inicializar jogador
        if not self.player:
            self.player = Player(50, 500)
        else:
            self.player.rect.x = 50
            self.player.rect.y = 500
            self.player.health = self.player.max_health
            self.player.mana = self.player.max_mana

            if self.level != 10:
                self.player.collected_ability = None
                self.player.ability_active = False
    
    def update(self):
        if self.paused or self.transitioning:
            return
        
        if self.state == "playing":
            self.player.update(self.platforms, self.hazards, self.enemies)
            
            # Verificar morte do jogador
            if self.player.health <= 0:
                self.state = "game_over"
                return
            
            # Verificar colisão de efeitos de habilidade com inimigos
            for effect in self.player.ability_effects[:]:
                for enemy in self.enemies[:]:
                    if effect["type"] == "big_fireball":
                        effect_rect = Rect(effect["x"] - 20, effect["y"] - 20, 40, 40)
                        if enemy.rect.colliderect(effect_rect):
                            enemy.health -= effect["damage"]
                            if enemy.health <= 0:
                                if self.player.ability_active and self.player.collected_ability == "necromancer":
                                    enemy.necromanced = True
                                    enemy.health = enemy.max_health // 2
                                    self.player.necromanced_enemies.append(enemy)
                                else:
                                    self.enemies.remove(enemy)
                    
                    elif effect["type"] == "energy_wave":
                        distance = math.sqrt((enemy.rect.centerx - effect["x"])**2 + (enemy.rect.centery - effect["y"])**2)
                        if distance < effect["radius"]:
                            enemy.health -= effect["damage"]
                            if enemy.health <= 0:
                                if self.player.ability_active and self.player.collected_ability == "necromancer":
                                    enemy.necromanced = True
                                    enemy.health = enemy.max_health // 2
                                    self.player.necromanced_enemies.append(enemy)
                                else:
                                    self.enemies.remove(enemy)
                    
                    elif effect["type"] == "lightning":
                        for i in range(5):
                            angle = random.uniform(0, 2 * math.pi)
                            length = random.randint(50, 150)
                            end_x = effect["x"] + math.cos(angle) * length
                            end_y = effect["y"] + math.sin(angle) * length
                            screen.draw.line((effect["x"], effect["y"]), (end_x, end_y), YELLOW)
                    
                    elif effect["type"] == "energy_orbs":
                        effect["angle"] += 0.1
                        for i in range(3):
                            angle = effect["angle"] + i * (2 * math.pi / 3)
                            x = effect["x"] + math.cos(angle) * 40
                            y = effect["y"] + math.sin(angle) * 40
                            screen.draw.filled_circle((x, y), 10, YELLOW)
                            screen.draw.circle((x, y), 10, ORANGE)
                    
                    elif effect["type"] == "pain_spikes":
                        effect_rect = Rect(effect["x"] - 30, effect["y"] - 5, 60, 10)
                        if enemy.rect.colliderect(effect_rect):
                            enemy.health -= effect["damage"]
                            if enemy.health <= 0:
                                if self.player.ability_active and self.player.collected_ability == "necromancer":
                                    enemy.necromanced = True
                                    enemy.health = enemy.max_health // 2
                                    self.player.necromanced_enemies.append(enemy)
                                else:
                                    self.enemies.remove(enemy)
            
            # Atualizar inimigos
            for enemy in self.enemies[:]:
                enemy.update(self.player, self.platforms)
                
                # Aplicar lentidão temporal se a habilidade estiver ativa
                if self.player.ability_active and self.player.collected_ability == "slow_time":
                    enemy.apply_slow()
                
                # Verificar colisão com chicote
                if self.player.attacking and self.player.attack_rect:
                    if enemy.rect.colliderect(self.player.attack_rect):
                        enemy.health -= 50
                        if enemy.health <= 0:
                            if self.player.ability_active and self.player.collected_ability == "necromancer":
                                enemy.necromanced = True
                                enemy.health = enemy.max_health // 2
                                self.player.necromanced_enemies.append(enemy)
                            else:
                                self.enemies.remove(enemy)
                
                # Verificar colisão com jogador
                if not self.player.invincibility_timer and enemy.rect.colliderect(self.player.rect):
                    if self.player.take_damage(enemy.damage):
                        if enemy.rect.x < self.player.rect.x:
                            self.player.rect.x += 20
                        else:
                            self.player.rect.x -= 20
            
            # Verificar orbes de habilidade
            for orb in self.ability_orbs[:]:
                if orb.update(self.player):
                    self.ability_orbs.remove(orb)
            
            # Verificar porta
            if self.door and self.player.rect.colliderect(self.door.rect):
                self.transitioning = True
                self.transition_timer = 60
                play_sound('door', 0.8)
    
    def draw(self):
        screen.clear()
        
        if self.state == "menu":
            screen.draw.text("PANTEÃO", center=(400, 100), fontsize=64, color=WHITE)
            self.play_button.draw()
            self.options_button.draw()
            self.quit_button.draw()
        
        elif self.state == "playing":
            # Fundo
            if self.level == 10:
                screen.draw.filled_rect(Rect(0, 0, 800, 600), DARK_PURPLE)
                for i in range(50):
                    x = (i * 37) % 800
                    y = (i * 23) % 600
                    screen.draw.filled_circle((x, y), 1, WHITE)
            else:
                screen.draw.filled_rect(Rect(0, 0, 800, 600), DARK_BLUE)
                for i in range(10):
                    x = (i * 120) % 800
                    y = 100 + (i * 30) % 100
                    screen.draw.filled_circle((x, y), 15, WHITE)
                    screen.draw.filled_circle((x+10, y-5), 12, WHITE)
                    screen.draw.filled_circle((x-10, y+5), 10, WHITE)
            
            # Plataformas
            for platform in self.platforms:
                platform.draw()
            
            # Hazards
            for hazard in self.hazards:
                hazard.draw()
            
            # Porta
            if self.door:
                self.door.draw()
            
            # Orbes
            for orb in self.ability_orbs:
                orb.draw()
            
            # Inimigos
            for enemy in self.enemies:
                enemy.draw()
            
            # Jogador
            self.player.draw()
            
            # UI
            screen.draw.filled_rect(Rect(10, 10, 200, 20), BLACK)
            screen.draw.filled_rect(Rect(10, 10, int(200 * (self.player.health / self.player.max_health)), 20), RED)
            screen.draw.text(f"HP: {int(self.player.health)}/{self.player.max_health}", (15, 12), color=WHITE)
            
            screen.draw.filled_rect(Rect(10, 40, 200, 20), BLACK)
            screen.draw.filled_rect(Rect(10, 40, int(200 * (self.player.mana / self.player.max_mana)), 20), BLUE)
            screen.draw.text(f"MP: {int(self.player.mana)}/{self.player.max_mana}", (15, 42), color=WHITE)
            
            screen.draw.text(f"NÍVEL: {self.level}", (700, 10), color=WHITE)
            
            if self.player.collected_ability:
                screen.draw.text(f"HABILIDADE: {self.player.collected_ability.upper()}", (10, 70), color=YELLOW)
            
            if self.paused:
                screen.draw.filled_rect(Rect(200, 150, 400, 300), (0, 0, 0, 200))
                screen.draw.text("PAUSADO", center=(400, 180), fontsize=48, color=WHITE)
                
                if self.showing_options:
                    screen.draw.text("OPÇÕES", center=(400, 150), fontsize=32, color=WHITE)
                    self.music_toggle.draw()
                    self.sounds_toggle.draw()
                    self.back_button.draw()
                else:
                    self.resume_button.draw()
                    self.options_button.draw()
                    self.menu_button.draw()
            
            if self.transitioning:
                screen.draw.filled_rect(Rect(0, 0, 800, 600), (0, 0, 0, 200))
                screen.draw.text("CARREGANDO PRÓXIMO NÍVEL...", center=(400, 300), fontsize=32, color=WHITE)
        
        elif self.state == "game_over":
            screen.draw.filled_rect(Rect(0, 0, 800, 600), BLACK)
            screen.draw.text("GAME OVER", center=(400, 200), fontsize=64, color=RED)
            screen.draw.text(f"Você chegou ao nível {self.level}", center=(400, 300), fontsize=32, color=WHITE)
            self.menu_button.draw()
            self.quit_button.draw()
    
    def handle_click(self, pos):
        if self.state == "menu":
            if self.play_button.check_click(pos):
                self.state = "playing"
                self.level = 1
                self.player = Player(50, 500)
                self.generate_level()
                if self.music_on and self.audio_available:
                    load_music()
            elif self.options_button.check_click(pos):
                self.showing_options = True
            elif self.quit_button.check_click(pos):
                exit()
        
        elif self.state == "playing" and self.paused:
            if self.showing_options:
                if self.music_toggle.check_click(pos):
                    self.music_on = not self.music_on
                    self.music_toggle.text = f"MÚSICA: {'LIGADA' if self.music_on else 'DESLIGADA'}"
                    if self.music_on and self.audio_available:
                        load_music()
                    else:
                        music.stop()
                elif self.sounds_toggle.check_click(pos):
                    self.sounds_on = not self.sounds_on
                    self.sounds_toggle.text = f"SONS: {'LIGADOS' if self.sounds_on else 'DESLIGADOS'}"
                elif self.back_button.check_click(pos):
                    self.showing_options = False
            else:
                if self.resume_button.check_click(pos):
                    self.paused = False
                elif self.options_button.check_click(pos):
                    self.showing_options = True
                elif self.menu_button.check_click(pos):
                    self.state = "menu"
                    music.stop()
        
        elif self.state == "game_over":
            if self.menu_button.check_click(pos):
                self.state = "menu"
            elif self.quit_button.check_click(pos):
                exit()
    
    def next_level(self):
        self.level += 1
        if self.level > self.max_level:
            self.state = "victory"
        else:
            self.generate_level()

# Inicializar o jogo
game = Game()

def update():
    global intro_scroll_pos, tutorial_timer, showing_intro, skip_intro, tutorial_step
    
    if showing_intro and not skip_intro:
        intro_scroll_pos -= intro_speed
        if intro_scroll_pos < -len(intro_text) * intro_line_height:
            showing_intro = False
        return
    
    if tutorial_step > 0:
        tutorial_timer += 1
        if tutorial_timer > 180:
            tutorial_step += 1
            tutorial_timer = 0
            if tutorial_step > 3:
                tutorial_step = 0
    
    if game.transitioning:
        game.transition_timer -= 1
        if game.transition_timer <= 0:
            game.next_level()
            game.transitioning = False
    
    game.update()

def draw():
    if showing_intro and not skip_intro:
        screen.clear()
        screen.draw.filled_rect(Rect(0, 0, 800, 600), BLACK)
        
        for i, line in enumerate(intro_text):
            y_pos = intro_scroll_pos + i * intro_line_height
            if 0 <= y_pos < HEIGHT:
                screen.draw.text(line, center=(400, y_pos), fontsize=24, color=YELLOW)
        
        if intro_scroll_pos < HEIGHT - 100:
            screen.draw.text("Pressione ESPAÇO para pular", center=(400, 550), fontsize=20, color=WHITE)
        return
    
    if tutorial_step > 0:
        game.draw()
        # Tutorial na parte superior da tela
        screen.draw.filled_rect(Rect(100, 50, 600, 100), (0, 0, 0, 180))
        
        if tutorial_step == 1:
            screen.draw.text("Use as setas ESQUERDA e DIREITA para se mover", center=(400, 80), fontsize=24, color=WHITE)
        elif tutorial_step == 2:
            screen.draw.text("Pressione ESPAÇO para pular", center=(400, 80), fontsize=24, color=WHITE)
        elif tutorial_step == 3:
            screen.draw.text("Pressione J para atacar e K para defender", center=(400, 80), fontsize=24, color=WHITE)
        
        screen.draw.text(f"{tutorial_step}/3", center=(400, 120), fontsize=20, color=WHITE)
        return
    
    game.draw()

def on_mouse_down(pos):
    game.handle_click(pos)

def on_mouse_move(pos):
    if game.state == "menu":
        game.play_button.check_hover(pos)
        game.options_button.check_hover(pos)
        game.quit_button.check_hover(pos)
    
    elif game.state == "playing" and game.paused:
        if game.showing_options:
            game.music_toggle.check_hover(pos)
            game.sounds_toggle.check_hover(pos)
            game.back_button.check_hover(pos)
        else:
            game.resume_button.check_hover(pos)
            game.options_button.check_hover(pos)
            game.menu_button.check_hover(pos)
    
    elif game.state == "game_over":
        game.menu_button.check_hover(pos)
        game.quit_button.check_hover(pos)

def on_key_down(key):
    global showing_intro, skip_intro, tutorial_step
    
    if showing_intro:
        if key == keys.SPACE:
            skip_intro = True
            showing_intro = False
        return
    
    if key == keys.ESCAPE:
        game.paused = not game.paused
        return
    
    if game.paused:
        return
        
    if game.state == "playing":
        if key == keys.LEFT:
            game.player.move_left()
            if tutorial_step == 0:
                tutorial_step = 1
        elif key == keys.RIGHT:
            game.player.move_right()
            if tutorial_step == 0:
                tutorial_step = 1
        elif key == keys.SPACE:
            game.player.jump()
            if tutorial_step == 1:
                tutorial_step = 2
        elif key == keys.J:
            game.player.attack()
            if tutorial_step == 2:
                tutorial_step = 3
        elif key == keys.K:
            game.player.shield()
            if tutorial_step == 3:
                tutorial_step = 0
        elif key == keys.L:
            game.player.use_ability(game.enemies)

def on_key_up(key):
    if game.paused:
        return
        
    if game.state == "playing":
        if key == keys.LEFT or key == keys.RIGHT:
            game.player.stop()
        elif key == keys.K:
            game.player.stop_shield()

# Executar o jogo
pgzrun.go()