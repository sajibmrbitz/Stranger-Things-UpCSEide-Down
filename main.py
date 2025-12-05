import pygame
import sys
import time
import os

# --- Initialization ---
pygame.init()
pygame.font.init()
pygame.mixer.init()

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_PATH = os.path.join(BASE_DIR, "assets")

# --- Screen Settings ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Stranger Things: The Game (Season 1)")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 0, 0)
YELLOW = (255, 215, 0)
CYAN = (0, 255, 255)
GRAY = (50, 50, 50)

# Fonts
font_title = pygame.font.SysFont("Arial", 40, bold=True)
font_subtitle = pygame.font.SysFont("Courier New", 28, bold=True)
font_debug = pygame.font.SysFont("Arial", 16)

clock = pygame.time.Clock()

# --- HELPER: Auto-Scale Image ---
def draw_image_fit(surface, img):
    if img is None: return pygame.Rect(0,0,0,0)
    img_w, img_h = img.get_size()
    ratio_w = SCREEN_WIDTH / img_w
    ratio_h = SCREEN_HEIGHT / img_h
    scale = min(ratio_w, ratio_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
    x = (SCREEN_WIDTH - new_w) // 2
    y = (SCREEN_HEIGHT - new_h) // 2
    surface.blit(scaled_img, (x, y))
    return pygame.Rect(x, y, new_w, new_h)

# --- Asset Loading ---
def load_image(name):
    fullname = os.path.join(ASSET_PATH, name)
    try:
        img = pygame.image.load(fullname).convert_alpha()
        return img
    except Exception as e:
        print(f"[ERROR] Missing Image: {name}")
        surf = pygame.Surface((400, 300))
        surf.fill(GRAY)
        return surf

assets = {
    "logo": load_image("Stranger_Things_logo.png"),
    "menu": load_image("starting-image.jpg"),
    "slide1": load_image("Slide-1.png"),
    "slide2": load_image("Slide-2.png"),
    "wall": load_image("Main-Game-season-1.png"), 
    "mom_run": load_image("mom-run-main.png"),
    "demogorgon": load_image("season-1-game-faild-image.jpg"),
}

# --- COORDINATES (Use F1 to find these) ---
LETTER_COORDS = {
    # Default placeholder values. Use F1 in game to find exact spots.
    'G': (871, 103), 'E': (758, 108), 'I': (494, 204), 'H': (952, 84), 'T': (619, 313), 'R': (534, 297), 'U': (675, 309), 'N': (768, 190)
}

# --- Game States ---
STATE_LOGO = "logo"
STATE_MENU = "menu"
STATE_SLIDE = "slide"
STATE_DIALOGUE = "dialogue"
STATE_GAME = "game"
STATE_SUCCESS = "success"
STATE_FAIL = "fail"

slides = [
    {"img": "slide1", "txt": "Will Byers has disappeared..."},
    {"img": "slide2", "txt": "Joyce creates a way to communicate..."}
]

class Game:
    def __init__(self):
        self.state = STATE_LOGO
        
        # Fade & Timer Variables
        self.start_time = time.time()
        self.fade_alpha = 255  # Start fully black
        self.fade_mode = "IN"  # IN (Dark->Clear), OUT (Clear->Dark), WAIT
        
        # Logic Variables
        self.slide_index = 0
        self.level = 1
        self.target_msg = "RIGHT HERE" 
        self.blink_sequence = []
        self.blink_idx = 0
        self.last_blink_time = 0
        self.user_input = ""
        self.wall_rect = pygame.Rect(0,0,0,0)
        self.debug_mode = False

    def reset_level(self):
        self.user_input = ""
        self.blink_idx = 0
        self.blink_sequence = [c for c in self.target_msg if c != ' ']
        self.last_blink_time = time.time()
        self.game_phase = "blink" 

    def update(self):
        current_time = time.time()
        
        # --- INPUT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # Debug Mode Toggle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                self.debug_mode = not self.debug_mode
                print(f"Debug Mode: {self.debug_mode}")

            # Mouse Interactions
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.debug_mode and self.state in [STATE_GAME, STATE_DIALOGUE]:
                    mx, my = pygame.mouse.get_pos()
                    print(f"COORD: ({mx - self.wall_rect.x}, {my - self.wall_rect.y})")

                if self.state == STATE_MENU and self.fade_mode == "IDLE":
                    # Start Slideshow
                    self.state = STATE_SLIDE
                    self.slide_index = 0
                    self.fade_alpha = 255
                    self.fade_mode = "IN"

                elif self.state == STATE_SLIDE and self.fade_mode == "IDLE":
                    # Next Slide
                    self.fade_mode = "OUT"

                elif self.state == STATE_DIALOGUE:
                    # Start Game Blink
                    self.state = STATE_GAME
                    self.reset_level()

                elif self.state in [STATE_SUCCESS, STATE_FAIL]:
                    self.state = STATE_MENU
                    self.fade_alpha = 255
                    self.fade_mode = "IN"

            # Typing Input
            if self.state == STATE_GAME and self.game_phase == "input" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    clean_inp = self.user_input.replace(" ", "").upper()
                    clean_tgt = self.target_msg.replace(" ", "").upper()
                    if clean_inp == clean_tgt:
                        if self.level == 1:
                            self.level = 2
                            self.target_msg = "RUN"
                            self.reset_level()
                        else:
                            self.state = STATE_SUCCESS
                    else:
                        self.state = STATE_FAIL
                elif event.key == pygame.K_BACKSPACE:
                    self.user_input = self.user_input[:-1]
                else:
                    if event.unicode.isalnum() or event.unicode == " ":
                        self.user_input += event.unicode.upper()

        # --- LOGIC & ANIMATIONS ---
        
        # 1. LOGO FADE SEQUENCE
        if self.state == STATE_LOGO:
            fade_speed = 4
            if self.fade_mode == "IN":
                self.fade_alpha -= fade_speed
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fade_mode = "WAIT"
                    self.start_time = current_time
            elif self.fade_mode == "WAIT":
                if current_time - self.start_time > 2.0: # Wait 2 seconds
                    self.fade_mode = "OUT"
            elif self.fade_mode == "OUT":
                self.fade_alpha += fade_speed
                if self.fade_alpha >= 255:
                    self.state = STATE_MENU
                    self.fade_mode = "IN" # Start Menu with Fade In

        # 2. MENU FADE IN
        elif self.state == STATE_MENU:
            if self.fade_mode == "IN":
                self.fade_alpha -= 5
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fade_mode = "IDLE"

        # 3. SLIDE FADE SEQUENCE
        elif self.state == STATE_SLIDE:
            speed = 5
            if self.fade_mode == "IN":
                self.fade_alpha -= speed
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fade_mode = "IDLE"
            elif self.fade_mode == "OUT":
                self.fade_alpha += speed
                if self.fade_alpha >= 255:
                    self.slide_index += 1
                    if self.slide_index >= len(slides):
                        self.state = STATE_DIALOGUE
                    else:
                        self.fade_mode = "IN"

        # 4. GAME BLINKING
        if self.state == STATE_GAME and self.game_phase == "blink":
            if self.blink_idx < len(self.blink_sequence):
                if current_time - self.last_blink_time > 1.2:
                    self.blink_idx += 1
                    self.last_blink_time = current_time
            else:
                self.game_phase = "input"

    def draw(self):
        screen.fill(BLACK)

        # --- DRAW VISUALS ---
        if self.state == STATE_LOGO:
            draw_image_fit(screen, assets["logo"])

        elif self.state == STATE_MENU:
            draw_image_fit(screen, assets["menu"])
            if self.fade_mode == "IDLE":
                txt = font_title.render("CLICK TO START", True, RED)
                bg = txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80)).inflate(20,10)
                pygame.draw.rect(screen, BLACK, bg)
                screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80)))

        elif self.state == STATE_SLIDE:
            if self.slide_index < len(slides):
                data = slides[self.slide_index]
                draw_image_fit(screen, assets[data["img"]])
                s = pygame.Surface((SCREEN_WIDTH, 120))
                s.set_alpha(200); s.fill(BLACK)
                screen.blit(s, (0, SCREEN_HEIGHT - 120))
                txt = font_subtitle.render(data["txt"], True, WHITE)
                screen.blit(txt, (50, SCREEN_HEIGHT - 80))

        # --- DIALOGUE & GAME (They share the Wall Image) ---
        elif self.state in [STATE_DIALOGUE, STATE_GAME]:
            self.wall_rect = draw_image_fit(screen, assets["wall"])

            # DIALOGUE OVERLAY (Text at bottom)
            if self.state == STATE_DIALOGUE:
                # Black bar at bottom
                pygame.draw.rect(screen, BLACK, (0, SCREEN_HEIGHT-120, SCREEN_WIDTH, 120))
                
                name = font_title.render("MOM:", True, RED)
                msg = font_subtitle.render('"Where are you?"', True, WHITE)
                hint = font_debug.render("(Click to start connection...)", True, GRAY)
                
                screen.blit(name, (50, SCREEN_HEIGHT - 100))
                screen.blit(msg, (170, SCREEN_HEIGHT - 95))
                screen.blit(hint, (50, SCREEN_HEIGHT - 40))

            # GAME LOGIC (Lights & Input)
            elif self.state == STATE_GAME:
                # BLINKING
                if self.game_phase == "blink":
                    if self.blink_idx < len(self.blink_sequence):
                        letter = self.blink_sequence[self.blink_idx]
                        if (time.time() - self.last_blink_time < 0.8) and (letter in LETTER_COORDS):
                            lx, ly = LETTER_COORDS[letter]
                            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
                            pygame.draw.circle(glow, (237, 195, 13, 150), (30, 30), 8)
                            pygame.draw.circle(glow, (237, 195, 13), (30, 30), 4)
                            screen.blit(glow, (self.wall_rect.x + lx - 30, self.wall_rect.y + ly - 30))
                
                # INPUT
                elif self.game_phase == "input":
                    pygame.draw.rect(screen, BLACK, (0, SCREEN_HEIGHT-80, SCREEN_WIDTH, 80))
                    prompt = font_subtitle.render("TYPE: " + self.user_input + "_", True, RED)
                    screen.blit(prompt, (50, SCREEN_HEIGHT - 55))
                
                if self.debug_mode:
                    d = font_debug.render("DEBUG: Click letters for coords", True, CYAN)
                    screen.blit(d, (10, 10))

        # SUCCESS / FAIL
        elif self.state == STATE_SUCCESS:
            draw_image_fit(screen, assets["mom_run"])
            txt = font_title.render("SAFE!", True, YELLOW)
            screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 50))

        elif self.state == STATE_FAIL:
            draw_image_fit(screen, assets["demogorgon"])
            txt = font_title.render("GAME OVER", True, RED)
            screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT - 100))

        # --- GLOBAL FADE OVERLAY ---
        # Apply fade effect for Logo, Menu, and Slides
        if self.state in [STATE_LOGO, STATE_MENU, STATE_SLIDE]:
            if self.fade_alpha > 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(self.fade_alpha)
                overlay.fill(BLACK)
                screen.blit(overlay, (0, 0))

        pygame.display.flip()
        clock.tick(60)

# --- Entry Point ---
if __name__ == "__main__":
    game = Game()
    while True:
        game.update()
        game.draw()