import pygame
import os
import sys
import random
import math

# --- 1. SYSTEM SETUP ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

pygame.init()
pygame.mixer.init()

# Screen Settings
GAME_WIDTH = 800
GAME_HEIGHT = 600
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("STRANGER THINGS: HAWKINS DEFENDER (ULTIMATE)")

# We keep canvas for the Retro Resolution + CRT Effect scaling
canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
clock = pygame.time.Clock()

# --- COLORS ---
SKY_BLUE = (20, 20, 40)
UPSIDE_DOWN_RED = (40, 0, 0) # Dark Red Background
NEON_RED = (255, 50, 50)     # Enemy
NEON_GREEN = (50, 255, 50)   # Friend
NEON_BLUE = (0, 200, 255)    # Ultimate Energy
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

# --- FONTS ---
try:
    FONT_HUD = pygame.font.SysFont("Impact", 30)
    FONT_MSG = pygame.font.SysFont("Arial", 14, bold=True)
    FONT_BIG = pygame.font.SysFont("Impact", 60)
    FONT_MENU = pygame.font.SysFont("Courier New", 40, bold=True) # Retro Font
except:
    FONT_HUD = pygame.font.Font(None, 30)
    FONT_MSG = pygame.font.Font(None, 20)
    FONT_BIG = pygame.font.Font(None, 60)
    FONT_MENU = pygame.font.Font(None, 50)

# --- 2. ASSET MANAGER ---
class AssetLoader:
    def __init__(self):
        self.images = {}
        self.sounds = {}

    def get_image(self, filename, size, color, label="?"):
        if filename in self.images: return self.images[filename]
        
        path = os.path.join(ASSETS_DIR, filename)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, size)
                self.images[filename] = img
                return img
            except: pass
        
        # Placeholder
        surf = pygame.Surface(size)
        surf.fill(color)
        pygame.draw.rect(surf, WHITE, surf.get_rect(), 2)
        txt = FONT_MSG.render(label, True, (0,0,0))
        surf.blit(txt, txt.get_rect(center=(size[0]//2, size[1]//2)))
        self.images[filename] = surf
        return surf

    def load_audio(self):
        m_path = os.path.join(ASSETS_DIR, "theme.mp3")
        if os.path.exists(m_path):
            try:
                pygame.mixer.music.load(m_path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
            except: pass
        
        self.sounds['shoot'] = self._load_sfx("blast.wav")
        self.sounds['hit'] = self._load_sfx("screech.wav")
        self.sounds['rescue'] = self._load_sfx("powerup.wav")
        self.sounds['ultimate'] = self._load_sfx("ultimate.wav")
        self.sounds['select'] = self._load_sfx("select.wav") # New Menu Sound

    def _load_sfx(self, filename):
        path = os.path.join(ASSETS_DIR, filename)
        if os.path.exists(path): return pygame.mixer.Sound(path)
        return None

    def play_sfx(self, name):
        if self.sounds.get(name): self.sounds[name].play()

loader = AssetLoader()
loader.load_audio()

# --- 3. HELPER FUNCTIONS ---
def load_high_score():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read())
        except: return 0
    return 0

def save_high_score(score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(score))

# --- NEW: CRT EFFECT GENERATOR ---
def create_crt_scanlines():
    """ Creates a transparent surface with horizontal scanlines """
    scan_surf = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    # Darken every 2nd line
    for y in range(0, GAME_HEIGHT, 2):
        # (0, 0, 0, 50) -> Black with 50/255 transparency (subtle)
        pygame.draw.line(scan_surf, (0, 0, 0, 40), (0, y), (GAME_WIDTH, y), 1)
    
    # Optional: Vignette (Dark corners)
    # This creates a radial gradient look roughly
    pygame.draw.rect(scan_surf, (0,0,0, 20), (0, 0, GAME_WIDTH, GAME_HEIGHT), 10) 
    
    return scan_surf

scanline_surface = create_crt_scanlines()

# --- 4. GAME CLASSES ---

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(3, 6)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.life = random.randint(20, 40)

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.life -= 1
        if self.life <= 0: self.kill()

class FloatingText(pygame.sprite.Sprite):
    def __init__(self, x, y, text, color):
        super().__init__()
        self.image = FONT_MSG.render(text, True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.timer = 90
    def update(self):
        self.rect.y -= 0.5
        self.timer -= 1
        if self.timer <= 0: self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = loader.get_image("player.png", (50, 60), (0, 191, 255), "EL")
        self.rect = self.image.get_rect(midbottom=(GAME_WIDTH // 2, GAME_HEIGHT - 40))
        self.speed = 6
        self.health = 3
        self.energy = 0
        self.vel_y = 0
        self.jump_power = -15
        self.gravity = 0.8
        self.on_ground = True

    def update(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and self.rect.left > 0:
            self.rect.x -= self.speed
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and self.rect.right < GAME_WIDTH:
            self.rect.x += self.speed

        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.bottom >= GAME_HEIGHT - 40:
            self.rect.bottom = GAME_HEIGHT - 40
            self.vel_y = 0
            self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False

    def shoot(self, target_pos):
        loader.play_sfx('shoot')
        return Bullet(self.rect.centerx, self.rect.centery - 20, target_pos)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, target_pos):
        super().__init__()
        self.image = loader.get_image("bullet.png", (8, 8), GOLD, "o")
        self.rect = self.image.get_rect(center=(start_x, start_y))
        
        dx = target_pos[0] - start_x
        dy = target_pos[1] - start_y
        angle = math.atan2(dy, dx)
        speed = 15
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.bottom < 0 or self.rect.top > GAME_HEIGHT or 
            self.rect.right < 0 or self.rect.left > GAME_WIDTH):
            self.kill()

class Helicopter(pygame.sprite.Sprite):
    def __init__(self, is_upside_down):
        super().__init__()
        self.direction = random.choice([-1, 1])
        img = loader.get_image("chopper.png", (90, 40), (120, 120, 120), "HELI")
        
        if self.direction == -1: 
            self.image = pygame.transform.flip(img, True, False)
        else:
            self.image = img 
            
        lanes = [80, 150, 220]
        altitude = random.choice(lanes)
        start_x = -100 if self.direction == 1 else GAME_WIDTH + 100
        self.rect = self.image.get_rect(center=(start_x, altitude))
        
        self.speed = 2 * self.direction 
        self.drop_timer = random.randint(100, 300) if is_upside_down else random.randint(150, 400)

    def update(self):
        self.rect.x += self.speed
        if self.direction == 1 and self.rect.left > GAME_WIDTH: self.kill()
        if self.direction == -1 and self.rect.right < 0: self.kill()
        self.drop_timer -= 1
        return self.drop_timer == 0

class FallingObject(pygame.sprite.Sprite):
    def __init__(self, x, y, is_upside_down):
        super().__init__()
        threat_chance = 0.7 if is_upside_down else 0.5
        
        if random.random() > threat_chance:
            self.type = 'friend'
            self.image = loader.get_image("trooper.png", (30, 40), NEON_GREEN, "PILOT")
        else:
            self.type = 'enemy'
            img_name = "demobat.png" 
            self.image = loader.get_image(img_name, (35, 35), NEON_RED, "BOMB")
            
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_y = 1.5 

    def update(self):
        self.vel_y += 0.05
        if self.vel_y > 4: self.vel_y = 4
        self.rect.y += self.vel_y
        if self.rect.top > GAME_HEIGHT:
            self.kill()
            return "landed"
        return "falling"

# --- 5. HELPER FUNCTION ---
def get_canvas_mouse_pos():
    mx, my = pygame.mouse.get_pos()
    window_w, window_h = screen.get_size()
    scale_x = GAME_WIDTH / window_w
    scale_y = GAME_HEIGHT / window_h
    return mx * scale_x, my * scale_y

# --- 6. MAIN GAME LOGIC (STATE MACHINE) ---

def run_game():
    global screen
    
    # Init Game Objects
    player = Player()
    player_grp = pygame.sprite.GroupSingle(player)
    bullets = pygame.sprite.Group()
    helicopters = pygame.sprite.Group()
    falling_objects = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    texts = pygame.sprite.Group()
    
    score = 0
    high_score = load_high_score()
    is_upside_down = False
    
    # Backgrounds
    bg_normal = loader.get_image("bg_normal.png", (GAME_WIDTH, GAME_HEIGHT), SKY_BLUE, "BG")
    bg_upside = loader.get_image("bg_upside.png", (GAME_WIDTH, GAME_HEIGHT), UPSIDE_DOWN_RED, "HELL")
    current_bg = bg_normal

    # Game States
    STATE_MENU = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    STATE_GAMEOVER = 3
    
    current_state = STATE_MENU
    blink_timer = 0 # For blinking text

    running = True
    while running:
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            elif event.type == pygame.KEYDOWN:
                # MENU CONTROLS
                if current_state == STATE_MENU:
                    # Added Keypad Enter support
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        loader.play_sfx('select')
                        current_state = STATE_PLAYING
                        score = 0
                        player.health = 3
                        player.energy = 0
                        # Reset World State (Fixes bug where restarting keeps Upside Down mode)
                        is_upside_down = False
                        current_bg = bg_normal
                        
                        # Reset groups
                        helicopters.empty()
                        falling_objects.empty()
                        bullets.empty()
                        particles.empty()
                        texts.empty()
                        player.rect.midbottom = (GAME_WIDTH // 2, GAME_HEIGHT - 40)

                # GAME CONTROLS
                elif current_state == STATE_PLAYING:
                    if event.key == pygame.K_p: # PAUSE
                        current_state = STATE_PAUSED
                    
                    if (event.key == pygame.K_SPACE or event.key == pygame.K_w):
                        player.jump()
                    
                    if event.key == pygame.K_z:
                        if player.energy >= 100:
                            loader.play_sfx('ultimate')
                            for obj in falling_objects:
                                if obj.type == 'enemy':
                                    score += 20
                                    for _ in range(10):
                                        particles.add(Particle(obj.rect.centerx, obj.rect.centery, NEON_RED))
                                    obj.kill()
                            texts.add(FloatingText(player.rect.centerx, player.rect.top, "PSYCHIC BLAST!", NEON_BLUE))
                            player.energy = 0
                
                # PAUSE CONTROLS
                elif current_state == STATE_PAUSED:
                    if event.key == pygame.K_p: # UNPAUSE
                        current_state = STATE_PLAYING
                
                # GAME OVER CONTROLS
                elif current_state == STATE_GAMEOVER:
                    # Allow R or ENTER to retry
                    if event.key == pygame.K_r or event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER: 
                        current_state = STATE_MENU

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if current_state == STATE_PLAYING and event.button == 1:
                    target = get_canvas_mouse_pos()
                    bullets.add(player.shoot(target))

        # --- UPDATE & DRAW LOGIC ---
        
        canvas.fill(BLACK) # Clear frame

        if current_state == STATE_MENU:
            # Draw Menu Background
            canvas.blit(bg_normal, (0,0))
            
            # Title
            title_txt = FONT_BIG.render("STRANGER THINGS", True, NEON_RED)
            sub_title = FONT_HUD.render("HAWKINS DEFENDER", True, WHITE)
            
            # Glowing Border for Title
            pygame.draw.rect(canvas, NEON_RED, title_txt.get_rect(center=(GAME_WIDTH//2, 200)).inflate(20, 20), 2)
            
            canvas.blit(title_txt, title_txt.get_rect(center=(GAME_WIDTH//2, 200)))
            canvas.blit(sub_title, sub_title.get_rect(center=(GAME_WIDTH//2, 250)))

            # Blinking Start Text
            blink_timer += 1
            if blink_timer % 60 < 30: # Blink every half second
                start_txt = FONT_MENU.render("PRESS ENTER TO START", True, GOLD)
                canvas.blit(start_txt, start_txt.get_rect(center=(GAME_WIDTH//2, 450)))
            
            controls_txt = FONT_MSG.render("WASD/Arrows to Move | Mouse to Shoot | P to Pause", True, GRAY)
            canvas.blit(controls_txt, controls_txt.get_rect(center=(GAME_WIDTH//2, 550)))

        elif current_state == STATE_PLAYING:
            # Update Logic
            
            # Difficulty & Bg
            if score >= 500 and not is_upside_down:
                is_upside_down = True
                texts.add(FloatingText(GAME_WIDTH//2, GAME_HEIGHT//2, "ENTERING UPSIDE DOWN!", NEON_RED))
            current_bg = bg_upside if is_upside_down else bg_normal

            # Spawning
            if random.randint(0, 180) == 0: # Increased spawn rate slightly
                helicopters.add(Helicopter(is_upside_down))

            player_grp.update()
            bullets.update()
            texts.update()
            particles.update()
            
            for heli in helicopters:
                if heli.update():
                    falling_objects.add(FallingObject(heli.rect.centerx, heli.rect.centery, is_upside_down))

            for obj in falling_objects:
                status = obj.update()
                if status == "landed":
                    if obj.type == 'friend':
                        player.health += 1 
                        score += 200
                        texts.add(FloatingText(obj.rect.centerx, GAME_HEIGHT-60, "SAVED! +1 LIFE", NEON_GREEN))
                        loader.play_sfx('rescue')
                    elif obj.type == 'enemy':
                        player.health -= 1
                        texts.add(FloatingText(obj.rect.centerx, GAME_HEIGHT-60, "DAMAGE! -1 LIFE", NEON_RED))
                        loader.play_sfx('hit')
                        if player.health <= 0:
                            current_state = STATE_GAMEOVER
                            if score > high_score:
                                save_high_score(score)

            # Collisions
            hits = pygame.sprite.groupcollide(helicopters, bullets, True, True)
            for hit in hits:
                score += 50
                player.energy = min(100, player.energy + 10)
                loader.play_sfx('hit')
                texts.add(FloatingText(hit.rect.centerx, hit.rect.centery, "+50", WHITE))
                for _ in range(15):
                    particles.add(Particle(hit.rect.centerx, hit.rect.centery, GRAY))

            hits = pygame.sprite.groupcollide(falling_objects, bullets, True, True)
            for obj in hits:
                if obj.type == 'enemy':
                    score += 20
                    player.energy = min(100, player.energy + 5)
                    loader.play_sfx('hit')
                    texts.add(FloatingText(obj.rect.centerx, obj.rect.centery, "DESTROYED!", GOLD))
                    for _ in range(10):
                        particles.add(Particle(obj.rect.centerx, obj.rect.centery, NEON_RED))
                elif obj.type == 'friend':
                    score -= 50
                    texts.add(FloatingText(obj.rect.centerx, obj.rect.centery, "FRIENDLY FIRE!", NEON_RED))

            # DRAW GAME
            canvas.blit(current_bg, (0, 0))
            pygame.draw.rect(canvas, (40, 40, 40), (0, GAME_HEIGHT-40, GAME_WIDTH, 40)) # Floor
            
            player_grp.draw(canvas)
            helicopters.draw(canvas)
            falling_objects.draw(canvas)
            bullets.draw(canvas)
            particles.draw(canvas)
            texts.draw(canvas)

            # HUD
            score_surf = FONT_HUD.render(f"SCORE: {score}", True, WHITE)
            canvas.blit(score_surf, (20, 20))
            
            # Energy Bar
            pygame.draw.rect(canvas, BLACK, (GAME_WIDTH - 150, 60, 100, 15))
            if player.energy > 0:
                pygame.draw.rect(canvas, NEON_BLUE, (GAME_WIDTH - 150, 60, player.energy, 15))
            pygame.draw.rect(canvas, WHITE, (GAME_WIDTH - 150, 60, 100, 15), 2)
            if player.energy >= 100:
                ready_txt = FONT_MSG.render("PRESS 'Z'!", True, NEON_BLUE)
                canvas.blit(ready_txt, (GAME_WIDTH - 150, 80))
            
            # Lives
            lives_txt = FONT_HUD.render(f"LIVES: {player.health}", True, NEON_GREEN if player.health > 1 else NEON_RED)
            canvas.blit(lives_txt, (GAME_WIDTH - 150, 20))

            # Crosshair (on canvas coordinate)
            cmx, cmy = get_canvas_mouse_pos()
            pygame.draw.circle(canvas, NEON_RED, (int(cmx), int(cmy)), 5, 1)

        elif current_state == STATE_PAUSED:
            # Draw game frozen in background
            canvas.blit(current_bg, (0,0))
            player_grp.draw(canvas)
            
            # Pause Overlay
            overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0, 150))
            canvas.blit(overlay, (0,0))
            
            pause_txt = FONT_BIG.render("PAUSED", True, WHITE)
            sub_pause = FONT_HUD.render("Press 'P' to Resume", True, GOLD)
            canvas.blit(pause_txt, pause_txt.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 - 20)))
            canvas.blit(sub_pause, sub_pause.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 + 40)))

        elif current_state == STATE_GAMEOVER:
            overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0, 180))
            canvas.blit(overlay, (0,0))
            
            t1 = FONT_BIG.render("GAME OVER", True, NEON_RED)
            t2 = FONT_HUD.render(f"Final Score: {score}", True, WHITE)
            t3 = FONT_HUD.render("Press 'R' or 'ENTER' to Return to Menu", True, GOLD)
            
            canvas.blit(t1, t1.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 - 40)))
            canvas.blit(t2, t2.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 + 20)))
            canvas.blit(t3, t3.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 + 60)))

        # --- FINAL RENDER & POST-PROCESSING ---
        
        # 1. Apply Scanlines (CRT Effect)
        canvas.blit(scanline_surface, (0,0))
        
        # 2. Scale to User Screen
        scaled = pygame.transform.scale(canvas, screen.get_size())
        screen.blit(scaled, (0,0))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    run_game()
    pygame.quit()
    sys.exit()