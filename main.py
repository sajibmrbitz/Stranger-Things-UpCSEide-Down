import pygame
import sys
import time
import os
import cv2  # OpenCV লাইব্রেরি ইমপোর্ট

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
font_title1 = pygame.font.SysFont("Courier New", 20, bold=True)
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
    "slide1": load_image("Slide-1.jpg"),
    "slide2": load_image("Slide-2.jpg"),
    "slide2.5": load_image("Slide-2.5.jpg"),
    "slide3": load_image("Slide-3.png"),
    "slide4": load_image("Slide-4.png"),
    "slide5": load_image("Slide-5.jpg"),
    "slide6": load_image("Slide-6.jpg"),
    "slide7": load_image("Slide-7.jpg"),
    "slide8": load_image("Slide-8.jpg"),
    "slide9": load_image("Slide-9.jpg"),
    "slide10": load_image("Slide-10.jpg"),
    "slide11": load_image("Slide-11.jpg"),
    "slide12": load_image("Slide-12.jpg"),
    "slide-x": load_image("Black.jpg"),
    "slide13": load_image("Slide-13.jpg"),
    "slide14": load_image("Slide-14.jpg"),
    "slide15": load_image("Slide-15.jpg"),
    "wall": load_image("Main-Game-season-1.png"), 
    "mom_run": load_image("mom-run-main.png"),
    "demogorgon": load_image("game-faild-image.jpg"),
}

# --- COORDINATES (Use F1 to find these) ---
LETTER_COORDS = {
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
STATE_ENDING = "ending"
STATE_VIDEO = "video"

slides = [
    {"img": "slide1", "txt": "" , "pos": "bottom"},
    {"img": "slide2", "txt": ["Will,Mike,Lucas,and Dustin playing Dungeons & Dragons."] , "pos": "bottom"},
    {"img": "slide2.5", "txt": ["Time to head home..."], "pos": "bottom"},
    {"img": "slide3", "txt": ["Every one went home except Will.", "Now the search begins..."], "pos": "bottom"},
    {"img": "slide4", "txt": ["They couldn't find Will anywhere.", "But they came across a strange girl, named Eleven."], "pos": "bottom"},
    {"img": "slide5", "txt": ["Everyone left hope to find Will except his mom, Joyce.", "Soon enough, she discovered will is alive and communicating through lights."], "pos": "bottom"},
]

ending_slides = [
    {"img": "slide-x", "txt": ["Click to continue..."], "pos": "center"},
    {"img": "slide6", "txt": ["Meanwhile, Mike and Dustin got in to a fight." , "El came into the scene to save Mike"], "pos": "bottom"},
    {"img": "slide7", "txt": "", "pos": "bottom"},
    {"img": "slide-x", "txt": ["Now that El blew up her cover.", "Now we all know that 'EL ISN'T AN ORDINARY GIRL.'"], "pos": "center"},
    {"img": "slide8", "txt": ["With Eleven's help, they found Will", "in a parallel dimension called the Upside Down."], "pos": "bottom"},
    {"img": "slide9", "txt": ["Hopper and Joyce went to rescue Will."], "pos": "bottom"},
    {"img": "slide10", "txt": "", "pos": "bottom"},
    {"img": "slide11", "txt": ["Will was saved that night."], "pos": "bottom"},
    {"img": "slide12", "txt": "", "pos": "bottom"},
    {"img": "slide13", "txt": ["They are enjoying their time together again."], "pos": "bottom"},
    {"img": "slide14", "txt": ["Everything seems normal now..."], "pos": "bottom"},
    {"img": "slide15", "txt": ["NOT REALLY..."], "pos": "bottom"},
]

class Game:
    def __init__(self):
        self.state = STATE_LOGO
        
        self.start_time = time.time()
        self.fade_alpha = 255 
        self.fade_mode = "IN" 
        
        self.slide_index = 0
        self.level = 1
        self.target_msg = "RIGHT HERE" 
        self.blink_sequence = []
        self.blink_idx = 0
        self.last_blink_time = 0
        self.user_input = ""
        self.wall_rect = pygame.Rect(0,0,0,0)
        self.debug_mode = False
        self.current_fps = 60 # ডিফল্ট গেম স্পিড
        
        # VIDEO VARIABLES
        self.cap = None             
        self.video_frame = None     
        self.video_playing = False

        # --- BACKGROUND MUSIC START ---
        self.play_bg_music()

    def play_bg_music(self):
        """Helper function to play background music loop."""
        bg_path = os.path.join(ASSET_PATH, "strangerthings_theme.mp3")
        if os.path.exists(bg_path):
            try:
                pygame.mixer.music.load(bg_path)
                pygame.mixer.music.play(-1) # Loop indefinitely
                pygame.mixer.music.set_volume(0.5) # Volume set to 50%
                print("BG Music playing...")
            except Exception as e:
                print(f"[BG MUSIC ERROR] {e}")
        else:
            print(f"[BG MUSIC MISSING] File should be at: {bg_path}")

    def reset_level(self):
        self.user_input = ""
        self.blink_idx = 0
        self.blink_sequence = [c for c in self.target_msg if c != ' ']
        self.last_blink_time = time.time()
        self.game_phase = "blink" 

    # NEW FUNCTION: ভিডিও এবং অডিও শুরু করার জন্য (অটোমেটিক)
    def start_ending_sequence(self):
        self.state = STATE_VIDEO
        video_path = os.path.join(ASSET_PATH, "After-game.mp4")
        
        # 1. Video Load
        self.cap = cv2.VideoCapture(video_path)
        
        # 2. Get Video FPS (Sync করার জন্য)
        try:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                self.current_fps = int(fps) 
            else:
                self.current_fps = 30 
        except:
            self.current_fps = 30
            
        self.video_playing = True
        
        # 3. Audio Start (This replaces the BG music)
        audio_path = os.path.join(ASSET_PATH, "After-game.mp3")
        if os.path.exists(audio_path):
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                print("Video Audio playing...")
            except Exception as e:
                print(f"[AUDIO ERROR] {e}")
        else:
            print(f"[AUDIO MISSING] File should be at: {audio_path}")

    def update(self):
        current_time = time.time()
        
        # --- INPUT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                self.debug_mode = not self.debug_mode
                print(f"Debug Mode: {self.debug_mode}")

            # Mouse Interactions
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.debug_mode and self.state in [STATE_GAME, STATE_DIALOGUE]:
                    mx, my = pygame.mouse.get_pos()
                    print(f"COORD: ({mx - self.wall_rect.x}, {my - self.wall_rect.y})")

                if self.state == STATE_MENU and self.fade_mode == "IDLE":
                    self.state = STATE_SLIDE
                    self.slide_index = 0
                    self.fade_alpha = 255
                    self.fade_mode = "IN"

                elif self.state == STATE_SLIDE and self.fade_mode == "IDLE":
                    self.fade_mode = "OUT"

                elif self.state == STATE_DIALOGUE:
                    self.state = STATE_GAME
                    self.reset_level()

                elif self.state == STATE_FAIL:
                    self.state = STATE_GAME
                    self.level = 1
                    self.target_msg = "RIGHT HERE" 
                    self.reset_level()

                elif self.state == STATE_ENDING and self.fade_mode == "IDLE":
                     self.fade_mode = "OUT"
                
                # Skip Video if clicked
                elif self.state == STATE_VIDEO:
                     if self.cap: self.cap.release()
                     
                     # Restart BG Music instead of just stopping
                     self.play_bg_music()
                     
                     self.current_fps = 60 # Reset FPS
                     self.state = STATE_ENDING
                     self.slide_index = 0
                     self.fade_alpha = 255
                     self.fade_mode = "IN"

            # Typing Input
            if self.state == STATE_GAME and self.game_phase == "input" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    clean_inp = self.user_input.replace(" ", "").upper()
                    clean_tgt = self.target_msg.replace(" ", "").upper()
                    if clean_inp == clean_tgt:
                        # Auto Start Video (No click needed)
                        self.start_ending_sequence()
                    else:
                        self.state = STATE_FAIL
                elif event.key == pygame.K_BACKSPACE:
                    self.user_input = self.user_input[:-1]
                else:
                    if event.unicode.isalnum() or event.unicode == " ":
                        self.user_input += event.unicode.upper()

        # --- LOGIC & ANIMATIONS ---
        
        if self.state == STATE_LOGO:
            fade_speed = 4
            if self.fade_mode == "IN":
                self.fade_alpha -= fade_speed
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fade_mode = "WAIT"
                    self.start_time = current_time
            elif self.fade_mode == "WAIT":
                if current_time - self.start_time > 2.0: 
                    self.fade_mode = "OUT"
            elif self.fade_mode == "OUT":
                self.fade_alpha += fade_speed
                if self.fade_alpha >= 255:
                    self.state = STATE_MENU
                    self.fade_mode = "IN" 

        elif self.state == STATE_MENU:
            if self.fade_mode == "IN":
                self.fade_alpha -= 5
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fade_mode = "IDLE"
        
        # --- VIDEO FRAME UPDATE ---
        elif self.state == STATE_VIDEO:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    frame = frame.swapaxes(0, 1)
                    self.video_frame = pygame.surfarray.make_surface(frame)
                else:
                    # Video finished
                    self.cap.release()
                    
                    # Restart BG Music
                    self.play_bg_music()
                    
                    self.current_fps = 60 # Reset FPS
                    self.state = STATE_ENDING
                    self.slide_index = 0
                    self.fade_alpha = 255
                    self.fade_mode = "IN"
        # ---------------------------

        elif self.state == STATE_ENDING:
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
                    if self.slide_index >= len(ending_slides):
                        self.state = STATE_MENU
                        self.fade_mode = "IN"
                    else:
                        self.fade_mode = "IN"
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

        if self.state == STATE_GAME and self.game_phase == "blink":
            if self.blink_idx < len(self.blink_sequence):
                if current_time - self.last_blink_time > 1.2:
                    self.blink_idx += 1
                    self.last_blink_time = current_time
            else:
                self.game_phase = "input"

    def draw(self):
        screen.fill(BLACK)

        if self.state == STATE_LOGO:
            draw_image_fit(screen, assets["logo"])

        elif self.state == STATE_MENU:
            draw_image_fit(screen, assets["menu"])
            if self.fade_mode == "IDLE":
                if int(time.time() * 2) % 2 == 0:
                    txt = font_title1.render("CLICK TO START", True, WHITE)
                    screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 80)))

        elif self.state in [STATE_SLIDE, STATE_ENDING]:
            current_list = slides if self.state == STATE_SLIDE else ending_slides
            
            if self.slide_index < len(current_list):
                data = current_list[self.slide_index]
                draw_image_fit(screen, assets[data["img"]])

                lines = data["txt"] 
                position = data.get("pos", "bottom")

                line_height = font_subtitle.get_height() + 5
                total_text_height = len(lines) * line_height

                start_y = 0
                if position == "center":
                    start_y = (SCREEN_HEIGHT - total_text_height) // 2
                else: 
                    s = pygame.Surface((SCREEN_WIDTH, total_text_height + 40))
                    s.set_alpha(200); s.fill(BLACK)
                    screen.blit(s, (0, SCREEN_HEIGHT - (total_text_height + 40)))
                    start_y = SCREEN_HEIGHT - (total_text_height + 20)

                for i, line in enumerate(lines):
                    txt_surf = font_subtitle.render(line, True, WHITE)
                    text_x = (SCREEN_WIDTH - txt_surf.get_width()) // 2
                    text_y = start_y + (i * line_height)
                    
                    if position == "center":
                        shadow = font_subtitle.render(line, True, BLACK)
                        screen.blit(shadow, (text_x + 2, text_y + 2))

                    screen.blit(txt_surf, (text_x, text_y))
        
        elif self.state in [STATE_DIALOGUE, STATE_GAME]:
            self.wall_rect = draw_image_fit(screen, assets["wall"])

            if self.state == STATE_DIALOGUE:
                pygame.draw.rect(screen, BLACK, (0, SCREEN_HEIGHT-120, SCREEN_WIDTH, 120))
                name = font_title.render("Joyce:", True, RED)
                msg = font_subtitle.render('"Will, Where are you?"', True, WHITE)
                hint = font_debug.render("(Click to start connection...)", True, GRAY)
                screen.blit(name, (50, SCREEN_HEIGHT - 100))
                screen.blit(msg, (170, SCREEN_HEIGHT - 95))
                screen.blit(hint, (50, SCREEN_HEIGHT - 40))

            elif self.state == STATE_GAME:
                if self.game_phase == "blink":
                    if self.blink_idx < len(self.blink_sequence):
                        letter = self.blink_sequence[self.blink_idx]
                        if (time.time() - self.last_blink_time < 0.8) and (letter in LETTER_COORDS):
                            lx, ly = LETTER_COORDS[letter]
                            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
                            pygame.draw.circle(glow, (237, 195, 13, 150), (30, 30), 8)
                            pygame.draw.circle(glow, (237, 195, 13), (30, 30), 4)
                            screen.blit(glow, (self.wall_rect.x + lx - 30, self.wall_rect.y + ly - 30))
                
                elif self.game_phase == "input":
                    pygame.draw.rect(screen, BLACK, (0, SCREEN_HEIGHT-80, SCREEN_WIDTH, 80))
                    prompt = font_subtitle.render("TYPE: " + self.user_input + "_", True, RED)
                    screen.blit(prompt, (50, SCREEN_HEIGHT - 55))
                
                if self.debug_mode:
                    d = font_debug.render("DEBUG: Click letters for coords", True, CYAN)
                    screen.blit(d, (10, 10))

        # elif self.state == STATE_SUCCESS:
        #     draw_image_fit(screen, assets["mom_run"])
        #     txt = font_title.render("SAFE!", True, YELLOW)
        #     screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 50))

        elif self.state == STATE_FAIL:
            draw_image_fit(screen, assets["demogorgon"])
            txt = font_title.render("", True, RED)
            screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT - 100))
        
        elif self.state == STATE_VIDEO:
            if self.video_frame is not None:
                screen.blit(self.video_frame, (0, 0))
            else:
                screen.fill(BLACK)

        if self.state in [STATE_LOGO, STATE_MENU, STATE_SLIDE, STATE_ENDING]:
            if self.fade_alpha > 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(self.fade_alpha)
                overlay.fill(BLACK)
                screen.blit(overlay, (0, 0))

        pygame.display.flip()
        
        # FPS Control (Dynamic for Video Sync)
        clock.tick(game.current_fps)

if __name__ == "__main__":
    game = Game()
    while True:
        game.update()
        game.draw()