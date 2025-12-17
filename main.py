import pygame
import sys

# --- 1. الإعدادات الأساسية والفنية ---
pygame.init()
WIDTH, HEIGHT = 1060, 2200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("World Cup Air Hockey 2025")
clock = pygame.time.Clock()

# الألوان
COLOR_BG = (10, 10, 20)
COLOR_ACCENT = (0, 255, 150)
COLOR_P1 = (0, 150, 255) 
COLOR_P2 = (255, 50, 80)  
WHITE = (255, 255, 255)
RED = (200, 0, 0)

# الثوابت
FIELD_RECT = pygame.Rect(50, 250, WIDTH - 100, HEIGHT - 500)
GOAL_WIDTH = 400
COUNTRIES = ["Morocco", "Algeria", "UAE", "Palestine", "Egypt", "Tunisia", "Syria", "Qatar", "Jordan"]
TIME_OPTIONS = [60, 90, 120, 180, 360] 

# --- 2. محرك تحميل الأصول ---
def load_asset(name, size=None, is_flag=False):
    path = f"flag_{name}.png" if is_flag else f"{name}.png"
    try:
        img = pygame.image.load(path).convert_alpha()
        if size: img = pygame.transform.scale(img, size)
        return img
    except:
        surf = pygame.Surface(size if size else (100, 100), pygame.SRCALPHA)
        pygame.draw.circle(surf, (60, 60, 60), (surf.get_width()//2, surf.get_height()//2), surf.get_width()//2)
        return surf

# --- 3. كائنات اللعبة ---
class Ball:
    def __init__(self, img_name):
        self.radius = 85 
        self.pos = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
        self.vel = pygame.math.Vector2(0, 0)
        self.friction = 0.99
        self.img = load_asset(img_name, (self.radius*2, self.radius*2))

    def reset(self):
        self.pos = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
        self.vel = pygame.math.Vector2(0, 0)

    def update(self):
        self.vel *= self.friction
        self.pos += self.vel
        if self.pos.x - self.radius < FIELD_RECT.left or self.pos.x + self.radius > FIELD_RECT.right:
            self.vel.x *= -1
            self.pos.x = max(FIELD_RECT.left + self.radius, min(FIELD_RECT.right - self.radius, self.pos.x))
        in_goal = (WIDTH//2 - GOAL_WIDTH//2) < self.pos.x < (WIDTH//2 + GOAL_WIDTH//2)
        if not in_goal:
            if self.pos.y - self.radius < FIELD_RECT.top:
                self.vel.y *= -1
                self.pos.y = FIELD_RECT.top + self.radius
            elif self.pos.y + self.radius > FIELD_RECT.bottom:
                self.vel.y *= -1
                self.pos.y = FIELD_RECT.bottom - self.radius

    def draw(self):
        screen.blit(self.img, (self.pos.x - self.radius, self.pos.y - self.radius))

class Paddle:
    def __init__(self, is_p1, flag_name):
        self.radius = 110
        self.is_p1 = is_p1
        self.pos = pygame.math.Vector2(WIDTH//2, HEIGHT*0.8 if is_p1 else HEIGHT*0.2)
        self.flag_img = load_asset(flag_name, (self.radius*1.5, self.radius*1.5), True)

    def draw(self):
        color = COLOR_P1 if self.is_p1 else COLOR_P2
        pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.pos.x), int(self.pos.y)), self.radius, 4)
        rect = self.flag_img.get_rect(center=(self.pos.x, self.pos.y))
        screen.blit(self.flag_img, rect)

# --- 4. إدارة التطبيق والشاشات ---
class App:
    def __init__(self):
        self.stage = "INTRO"
        self.p1_flag = self.p2_flag = None
        self.ball_choice = "Circle1"
        self.selected_time = 60
        self.score = [0, 0]
        self.active_touches = {}
        self.start_ticks = 0
        self.paused = False
        self.pause_start_time = 0

    def draw_back_button(self, events, target_stage):
        back_rect = pygame.Rect(30, 30, 180, 80)
        pygame.draw.rect(screen, RED, back_rect, border_radius=15)
        screen.blit(pygame.font.Font(None, 60).render("BACK", True, WHITE), (back_rect.x+35, back_rect.y+20))
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(ev.pos):
                if target_stage == "RESET": self.__init__()
                else: self.stage = target_stage

    def run(self):
        while True:
            screen.fill(COLOR_BG)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if not self.paused:
                    if event.type in [pygame.FINGERDOWN, pygame.FINGERMOTION]:
                        self.active_touches[event.finger_id] = (event.x * WIDTH, event.y * HEIGHT)
                    if event.type == pygame.FINGERUP:
                        if event.finger_id in self.active_touches: del self.active_touches[event.finger_id]
                    if event.type == pygame.MOUSEBUTTONDOWN: self.active_touches[0] = event.pos
                    if event.type == pygame.MOUSEMOTION and 0 in self.active_touches: self.active_touches[0] = event.pos
                    if event.type == pygame.MOUSEBUTTONUP: 
                        if 0 in self.active_touches: del self.active_touches[0]

            if self.stage == "INTRO": self.draw_intro(events)
            elif self.stage == "SELECT_FLAGS": 
                self.draw_select_flags(events)
                self.draw_back_button(events, "INTRO")
            elif self.stage == "SELECT_BALL": 
                self.draw_select_ball(events)
                self.draw_back_button(events, "SELECT_FLAGS")
            elif self.stage == "SELECT_TIME": 
                self.draw_select_time(events)
                self.draw_back_button(events, "SELECT_BALL")
            elif self.stage == "PLAYING": self.update_gameplay(events)
            elif self.stage == "GAMEOVER": self.draw_winner(events)
            
            pygame.display.flip()
            clock.tick(60)

    def draw_intro(self, events):
        trophy = load_asset("trophy", (750, 750))
        screen.blit(trophy, trophy.get_rect(center=(WIDTH//2, HEIGHT//3 + 100)))
        btn = pygame.Rect(WIDTH//2 - 250, HEIGHT - 500, 500, 150)
        pygame.draw.rect(screen, COLOR_ACCENT, btn, border_radius=30)
        screen.blit(pygame.font.Font(None, 120).render("START", True, COLOR_BG), (btn.x+115, btn.y+35))
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(ev.pos): self.stage = "SELECT_FLAGS"

    def draw_select_flags(self, events):
        for i, name in enumerate(COUNTRIES):
            col, row = i % 3, i // 3
            center = (180 + col*350, 450 + row*400)
            is_sel = (self.p1_flag == name or self.p2_flag == name)
            pygame.draw.circle(screen, COLOR_ACCENT if is_sel else (40, 40, 60), center, 155)
            img = load_asset(name, (180, 130), True)
            screen.blit(img, img.get_rect(center=center))
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and pygame.math.Vector2(ev.pos).distance_to(center) < 155:
                    if self.p1_flag == name: self.p1_flag = None
                    elif self.p2_flag == name: self.p2_flag = None
                    elif not self.p1_flag: self.p1_flag = name
                    elif not self.p2_flag: self.p2_flag = name
        if self.p1_flag and self.p2_flag:
            btn = pygame.Rect(WIDTH//2-200, HEIGHT-250, 400, 120)
            pygame.draw.rect(screen, COLOR_ACCENT, btn, border_radius=20)
            screen.blit(pygame.font.Font(None, 80).render("NEXT", True, COLOR_BG), (btn.x+120, btn.y+30))
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(ev.pos): self.stage = "SELECT_BALL"

    def draw_select_ball(self, events):
        for i in range(1, 6):
            center = (WIDTH//2, 450 + i*280)
            is_sel = (self.ball_choice == f"Circle{i}")
            pygame.draw.circle(screen, COLOR_P1 if is_sel else (40, 40, 60), center, 120)
            img = load_asset(f"Circle{i}", (180, 180))
            screen.blit(img, img.get_rect(center=center))
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and pygame.math.Vector2(ev.pos).distance_to(center) < 120:
                    self.ball_choice = f"Circle{i}"
        btn = pygame.Rect(WIDTH//2-200, HEIGHT-250, 400, 120)
        pygame.draw.rect(screen, COLOR_P1, btn, border_radius=20)
        screen.blit(pygame.font.Font(None, 80).render("NEXT", True, WHITE), (btn.x+120, btn.y+30))
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(ev.pos): self.stage = "SELECT_TIME"

    def draw_select_time(self, events):
        font = pygame.font.Font(None, 100)
        labels = ["1 Min", "1.5 Min", "2 Min", "3 Min", "6 Min"]
        for i, val in enumerate(TIME_OPTIONS):
            btn = pygame.Rect(WIDTH//2-250, 450 + i*280, 500, 150)
            is_sel = (self.selected_time == val)
            pygame.draw.rect(screen, COLOR_ACCENT if is_sel else (40, 40, 60), btn, border_radius=30)
            screen.blit(font.render(labels[i], True, COLOR_BG if is_sel else WHITE), (btn.x+150, btn.y+45))
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(ev.pos): self.selected_time = val
        btn_p = pygame.Rect(WIDTH//2-200, HEIGHT-250, 400, 120)
        pygame.draw.rect(screen, COLOR_ACCENT, btn_p, border_radius=20)
        screen.blit(font.render("PLAY", True, COLOR_BG), (btn_p.x+115, btn_p.y+30))
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and btn_p.collidepoint(ev.pos):
                self.ball = Ball(self.ball_choice)
                self.p1 = Paddle(True, self.p1_flag); self.p2 = Paddle(False, self.p2_flag)
                self.start_ticks = pygame.time.get_ticks()
                self.stage = "PLAYING"

    def update_gameplay(self, events):
        # منطق الإيقاف المؤقت
        pause_rect = pygame.Rect(WIDTH - 220, 30, 190, 80)
        pygame.draw.rect(screen, (200, 200, 0), pause_rect, border_radius=15)
        btn_text = "RESUME" if self.paused else "PAUSE"
        screen.blit(pygame.font.Font(None, 50).render(btn_text, True, COLOR_BG), (pause_rect.x+25, pause_rect.y+20))
        
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and pause_rect.collidepoint(ev.pos):
                self.paused = not self.paused
                if self.paused: self.pause_start_time = pygame.time.get_ticks()
                else: self.start_ticks += (pygame.time.get_ticks() - self.pause_start_time)

        self.draw_back_button(events, "RESET")

        if not self.paused:
            passed = (pygame.time.get_ticks() - self.start_ticks) // 1000
            left = max(0, self.selected_time - passed)
            if left <= 0: self.stage = "GAMEOVER"

            for tid, pos in self.active_touches.items():
                p_pos = pygame.math.Vector2(pos)
                if p_pos.y > HEIGHT // 2: self.p1.pos.update(p_pos.x, max(HEIGHT//2 + self.p1.radius, min(FIELD_RECT.bottom - self.p1.radius, p_pos.y)))
                else: self.p2.pos.update(p_pos.x, min(HEIGHT//2 - self.p2.radius, max(FIELD_RECT.top + self.p2.radius, p_pos.y)))

            if self.ball.pos.distance_to(self.p1.pos) < (self.ball.radius + self.p1.radius):
                d = (self.ball.pos - self.p1.pos).normalize(); self.ball.pos = self.p1.pos + d * (self.ball.radius + self.p1.radius); self.ball.vel = d * 52
            if self.ball.pos.distance_to(self.p2.pos) < (self.ball.radius + self.p2.radius):
                d = (self.ball.pos - self.p2.pos).normalize(); self.ball.pos = self.p2.pos + d * (self.ball.radius + self.p2.radius); self.ball.vel = d * 52
            
            self.ball.update()
            if self.ball.pos.y < FIELD_RECT.top and (WIDTH//2-GOAL_WIDTH//2 < self.ball.pos.x < WIDTH//2+GOAL_WIDTH//2):
                self.score[0] += 1; self.ball.reset()
            elif self.ball.pos.y > FIELD_RECT.bottom and (WIDTH//2-GOAL_WIDTH//2 < self.ball.pos.x < WIDTH//2+GOAL_WIDTH//2):
                self.score[1] += 1; self.ball.reset()
        else:
            left = max(0, self.selected_time - (self.pause_start_time - self.start_ticks) // 1000)

        pygame.draw.rect(screen, (20, 30, 50), FIELD_RECT, border_radius=40)
        pygame.draw.rect(screen, WHITE, FIELD_RECT, 6, border_radius=40)
        pygame.draw.rect(screen, COLOR_P2, (WIDTH//2-GOAL_WIDTH//2, FIELD_RECT.top-20, GOAL_WIDTH, 40), border_radius=10)
        pygame.draw.rect(screen, COLOR_P1, (WIDTH//2-GOAL_WIDTH//2, FIELD_RECT.bottom-20, GOAL_WIDTH, 40), border_radius=10)
        screen.blit(pygame.font.Font(None, 150).render(f"{left//60:02}:{left%60:02}", True, COLOR_ACCENT), (WIDTH//2-130, HEIGHT//2-75))
        
        self.p1.draw(); self.p2.draw(); self.ball.draw()
        f = pygame.font.Font(None, 200)
        screen.blit(f.render(str(self.score[1]), True, (255, 50, 80, 100)), (100, 130))
        screen.blit(f.render(str(self.score[0]), True, (0, 150, 255, 100)), (WIDTH-200, 130))

    def draw_winner(self, events):
        win = "DRAW" if self.score[0] == self.score[1] else ("PLAYER 1" if self.score[0] > self.score[1] else "PLAYER 2")
        screen.blit(pygame.font.Font(None, 150).render(f"{win} WINS!", True, COLOR_ACCENT), (WIDTH//2-350, HEIGHT//2))
        btn = pygame.Rect(WIDTH//2-250, HEIGHT//2+200, 500, 150)
        pygame.draw.rect(screen, WHITE, btn, border_radius=30)
        screen.blit(pygame.font.Font(None, 100).render("REPLAY", True, COLOR_BG), (btn.x+120, btn.y+40))
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(ev.pos): self.__init__()

if __name__ == "__main__":
    App().run()
