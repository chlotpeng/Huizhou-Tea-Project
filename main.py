# file_name: main.py
"""
徽州茶事 · 节气寻茶
一个用 Pygame 制作的交互小程序：
跟随清明 / 谷雨 / 立夏 / 白露 / 霜降五个节气，认识对应的安徽名茶，
并在“茶田种植”小游戏中把收集到的茶叶种下、等待生长、再把长成的枝条采入竹筐。

运行方式：
    pip install pygame
    python main.py
"""

import math
import sys
import random

import pygame

from hand_tracker import HandTracker

try:
    import cv2
except Exception:
    cv2 = None

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

WIDTH, HEIGHT = 1440, 900
FPS = 60

_BASE_WIDTH, _BASE_HEIGHT = 1000, 650
SCALE_X = WIDTH / _BASE_WIDTH
SCALE_Y = HEIGHT / _BASE_HEIGHT
SCALE_AVG = (SCALE_X + SCALE_Y) / 2


def sx(v):
    return round(v * SCALE_X)


def sy(v):
    return round(v * SCALE_Y)


def sf(v):
    return max(10, round(v * SCALE_AVG))


_CJK_FONT_CANDIDATES = ["simsun", "nsimsun", "simsun-extb"]

STATE_GAME = "game"

GAME_BTN_RECT = pygame.Rect(WIDTH // 2 - sx(130), HEIGHT - sy(95), sx(260), sy(52))


def _find_cjk_font_path():
    path = pygame.font.match_font(_CJK_FONT_CANDIDATES)
    if path:
        return path
    for name in pygame.font.get_fonts():
        if "simsun" in name or "song" in name:
            path = pygame.font.match_font(name)
            if path:
                return path
    return None


pygame.font.init()
FONT_PATH = _find_cjk_font_path()

PAPER = (242, 236, 224)
PAPER_DIM = (232, 224, 207)
INK = (43, 42, 40)
INK_SOFT = (92, 90, 85)
SEAL_RED = (156, 59, 46)
WHITE = (255, 255, 255)

STATE_INTRO = "intro"
STATE_SELECT = "select"
STATE_DETAIL = "detail"

TEAS = [
    {
        "id": "qingming", "term": "清明", "name": "黄山毛峰",
        "tagline": "明前嫩芽，形如雀舌",
        "accent": (124, 148, 115), "accent_dark": (91, 112, 82),
        "liquor": (217, 200, 120),
        "info": [("采摘", "清明前后采摘嫩芽"), ("工艺", "手工炒制，银毫显露"), ("汤色", "清澈微黄，香气清雅")],
        "weather": {"icon": "drizzle", "desc": "细雨纷纷"},
    },
    {
        "id": "guyu", "term": "谷雨", "name": "六安瓜片",
        "tagline": "唯一无芽无梗的绿茶",
        "accent": (71, 86, 58), "accent_dark": (49, 63, 40),
        "liquor": (143, 166, 107),
        "info": [("采摘", "谷雨前后采摘"), ("工艺", "生锅、熟锅、拉火"), ("汤色", "绿亮清澈")],
        "weather": {"icon": "rain", "desc": "雨水渐多"},
    },
    {
        "id": "lixia", "term": "立夏", "name": "太平猴魁",
        "tagline": "两叶抱一芽，猴魁独有",
        "accent": (100, 130, 70), "accent_dark": (70, 90, 50),
        "liquor": (170, 180, 100),
        "info": [("采摘", "谷雨后采摘"), ("工艺", "传统捏尖工艺"), ("汤色", "兰香高爽")],
        "weather": {"icon": "sun", "desc": "日头渐烈"},
    },
    {
        "id": "bailu", "term": "白露", "name": "祁门红茶",
        "tagline": "群芳最，红茶皇后",
        "accent": (169, 75, 56), "accent_dark": (124, 53, 39),
        "liquor": (193, 81, 46),
        "info": [("采摘", "秋季采摘"), ("工艺", "萎凋、揉捻、发酵"), ("汤色", "红艳明亮")],
        "weather": {"icon": "dew", "desc": "夜凉如水"},
    },
    {
        "id": "shuangjiang", "term": "霜降", "name": "老竹大方",
        "tagline": "板栗香浓，古法制茶",
        "accent": (120, 100, 70), "accent_dark": (80, 70, 50),
        "liquor": (180, 160, 90),
        "info": [("采摘", "秋末采摘"), ("工艺", "传统烘焙"), ("汤色", "黄亮醇厚")],
        "weather": {"icon": "frost", "desc": "寒气渐重"},
    },
]

SEAL_SIZE = sx(110)
SEAL_GAP = sx(55)
_total_w = len(TEAS) * SEAL_SIZE + (len(TEAS) - 1) * SEAL_GAP
SEAL_START_X = (WIDTH - _total_w) // 2
SEAL_Y = HEIGHT // 2 + sy(20)

SEAL_RECTS = [
    pygame.Rect(SEAL_START_X + i * (SEAL_SIZE + SEAL_GAP), SEAL_Y, SEAL_SIZE, SEAL_SIZE)
    for i in range(len(TEAS))
]

BACK_BTN_RECT = pygame.Rect(sx(40), sy(16), sx(120), sy(30))
SELECT_BACK_BTN_RECT = pygame.Rect(sx(40), sy(16), sx(120), sy(30))

INFO_ITEM_RECTS = [
    pygame.Rect(sx(560), sy(190) + i * sy(130), sx(380), sy(115)) for i in range(3)
]

HOTSPOT_RADIUS = sx(22)
HOTSPOT_POS = [(sx(160), sy(330)), (sx(330), sy(190)), (sx(140), sy(470))]

TEA_IMG_CENTER = (sx(240), sy(380))
TEA_IMG_SIZE = (sx(400), sy(400))

LEAF_POS_DEFAULT = (230, 230)
PICK_CIRCLE_RADIUS = sx(50)

CODEX_BTN_RECT = pygame.Rect(WIDTH - sx(150), HEIGHT - sy(70), sx(110), sy(46))
COLLECT_TOAST_MS = 1600

CAM_PREVIEW_SIZE = (sx(160), sy(120))
CAM_PREVIEW_POS = (WIDTH - CAM_PREVIEW_SIZE[0] - sx(20), HEIGHT - CAM_PREVIEW_SIZE[1] - sy(20))
GESTURE_CURSOR_RADIUS = sx(14)
GESTURE_PINCH_COOLDOWN_MS = 500

BORDER_OVERLAY_ALPHA = 70
GROW_DURATION_MS = 5000

BGM_PATH = "assets/雨打青瓦.mp3"
BGM_FADE_IN_MS = 4000
BGM_TARGET_VOLUME = 0.55

# ---- 弹窗“水雾”动画时长 ----
MIST_OPEN_MS = 420
MIST_CLOSE_MS = 380
# ---- 节气卡片“果冻”动画 ----
SEAL_HOVER_SCALE = 1.16
SEAL_EASE = 0.22
SEAL_CLICK_DELAY_MS = 260


def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if font.size(test)[0] > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class InkSplash:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color
        self.start = pygame.time.get_ticks()
        self.duration = 900
        self.blobs = []
        n = random.randint(6, 10)
        for _ in range(n):
            ang = random.uniform(0, math.pi * 2)
            dist = random.uniform(6, 50) * SCALE_AVG
            r = random.uniform(8, 28) * SCALE_AVG
            self.blobs.append({
                "dx": math.cos(ang) * dist, "dy": math.sin(ang) * dist,
                "r": r, "delay": random.uniform(0, 200),
            })

    def alive(self):
        return pygame.time.get_ticks() - self.start < self.duration

    def draw(self, surf):
        t = pygame.time.get_ticks() - self.start
        for b in self.blobs:
            local_t = t - b["delay"]
            if local_t < 0:
                continue
            progress = min(1.0, local_t / (self.duration - b["delay"] + 1))
            alpha = max(0, int(150 * (1 - progress)))
            if alpha <= 0:
                continue
            scale = 0.4 + 0.9 * progress
            radius = max(1, int(b["r"] * scale))
            x = self.pos[0] + b["dx"] * (0.3 + progress)
            y = self.pos[1] + b["dy"] * (0.3 + progress)
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
            surf.blit(s, (x - radius, y - radius))


class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()

        self.tea_images = {
            "qingming": pygame.image.load("assets/黄山毛峰.png"),
            "guyu": pygame.image.load("assets/六安瓜片.png"),
            "lixia": pygame.image.load("assets/太平猴魁.png"),
            "bailu": pygame.image.load("assets/祁门红茶.png"),
            "shuangjiang": pygame.image.load("assets/老竹大方.png"),
        }

        self.tea_popup_images = {
            "qingming": pygame.image.load("assets/黄山毛峰叶子大图.png"),
            "guyu": pygame.image.load("assets/六安瓜片大图.png"),
            "lixia": pygame.image.load("assets/太平猴魁大图.png"),
            "bailu": pygame.image.load("assets/祁门红茶大图.png"),
            "shuangjiang": pygame.image.load("assets/老竹大方大图.png"),
        }

        self.basket_image_raw = pygame.image.load("assets/竹筐.png")
        self.border_overlay_raw = pygame.image.load("assets/边框.png")
        self.field_bg_raw = pygame.image.load("assets/田地背景.png")

        self.hint_time = 0

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("徽州茶事 · 节气寻茶")
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.Font(FONT_PATH, sf(56))
        self.font_subtitle = pygame.font.Font(FONT_PATH, sf(20))
        self.font_hint = pygame.font.Font(FONT_PATH, sf(16))
        self.font_seal = pygame.font.Font(FONT_PATH, sf(30))
        self.font_tea_name = pygame.font.Font(FONT_PATH, sf(15))
        self.font_tagline = pygame.font.Font(FONT_PATH, sf(13))
        self.font_heading = pygame.font.Font(FONT_PATH, sf(44))
        self.font_body = pygame.font.Font(FONT_PATH, sf(17))
        self.font_label = pygame.font.Font(FONT_PATH, sf(14))
        self.font_codex_btn = pygame.font.Font(FONT_PATH, sf(24))
        self.font_toast = pygame.font.Font(FONT_PATH, sf(24))
        self.font_popup = pygame.font.Font(FONT_PATH, sf(26))
        self.font_basket_item = pygame.font.Font(FONT_PATH, sf(16))
        self.font_plot_label = pygame.font.Font(FONT_PATH, sf(15))

        self.state = STATE_INTRO
        self.start_ticks = pygame.time.get_ticks()

        self.hover_seal_index = None
        self.selected_tea = None
        self.active_info_index = None
        self.visited = set()

        self.burst_active = False
        self.burst_pos = (0, 0)
        self.burst_color = SEAL_RED
        self.burst_start = 0
        self.burst_next_tea = None

        # 节气卡片“果冻”悬浮缩放动画
        self.seal_scale = [1.0] * len(TEAS)
        # 点击后的延迟过渡（先放大一下，再进入详情）
        self.pending_seal_click = None  # {"tea":..., "pos":..., "start":...}

        self.hand_tracker = HandTracker()
        self.hand_mode = False
        self.gesture_cursor_px = None
        self.gesture_pinch_prev = False
        self.gesture_last_click_tick = -10_000

        self.pick_state = "idle"
        self.ink_progress = 0
        self.ink_start = 0
        self.ink_pos = (0, 0)
        self.ink_color = SEAL_RED
        self.pick_circle_rect = None
        self.popup_tea = None

        # 弹窗水雾动画状态
        self.popup_open_start = 0
        self.popup_closing = False
        self.popup_close_start = 0

        self.collected = set()
        self.collect_toast_text = None
        self.collect_toast_start = 0

        self.show_codex = False
        self.codex_open_start = 0
        self.codex_closing = False
        self.codex_close_start = 0

        self.camera_preview_surf = None
        self.status_message = None
        self.status_message_until = 0

        self.petals = self._spawn_petals(18)
        self.ripples = []
        self.lanterns = self._spawn_lanterns(5)
        self._last_ripple_ms = 0

        self.game_plots = []
        self.dragging_tea = None
        self.dragging_branch = None
        self.drag_pos = None
        self.basket_collected = []
        self.plant_toast = None
        self.ink_splashes = []

        self.field_rect = pygame.Rect(sx(140), sy(150), sx(520), sy(260))
        self.basket_rect = pygame.Rect(sx(700), sy(150), sx(210), sy(300))

        self.basket_image = pygame.transform.smoothscale(self.basket_image_raw, self.basket_rect.size)
        self.field_bg_full = pygame.transform.smoothscale(self.field_bg_raw, (WIDTH, HEIGHT))

        self.border_overlay = pygame.transform.smoothscale(self.border_overlay_raw, (WIDTH, HEIGHT)).convert_alpha()
        self.border_overlay.set_alpha(BORDER_OVERLAY_ALPHA)

        self.bgm_ok = False
        try:
            pygame.mixer.music.load(BGM_PATH)
            pygame.mixer.music.set_volume(BGM_TARGET_VOLUME)
            pygame.mixer.music.play(loops=-1, fade_ms=BGM_FADE_IN_MS)
            self.bgm_ok = True
        except Exception:
            self.bgm_ok = False

        self.running = True

    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        self.hand_tracker.stop()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                self.toggle_hand_mode()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.state == STATE_GAME:
                    self.game_release(event.pos)

    def toggle_hand_mode(self):
        if not self.hand_tracker.available:
            self.show_status(self.hand_tracker.error_message or "手势控制不可用", 3000)
            return
        self.hand_mode = not self.hand_mode
        if self.hand_mode:
            self.hand_tracker.start()
            self.show_status("手势模式已开启：食指移动，拇指食指捏合来点击", 2500)
        else:
            self.show_status("已切换回鼠标模式", 1500)

    def show_status(self, text, duration_ms):
        self.status_message = text
        self.status_message_until = pygame.time.get_ticks() + duration_ms

    def open_codex(self):
        self.show_codex = True
        self.codex_open_start = pygame.time.get_ticks()
        self.codex_closing = False

    def request_close_codex(self):
        if not self.show_codex or self.codex_closing:
            return
        self.codex_closing = True
        self.codex_close_start = pygame.time.get_ticks()

    def open_popup(self, tea):
        self.popup_tea = tea
        self.pick_state = "popup"
        self.popup_open_start = pygame.time.get_ticks()
        self.popup_closing = False

    def request_close_popup(self):
        if self.pick_state != "popup" or self.popup_closing:
            return
        self.popup_closing = True
        self.popup_close_start = pygame.time.get_ticks()

    def handle_click(self, pos):
        if self.show_codex:
            self.request_close_codex()
            return
        if self.state != STATE_INTRO and CODEX_BTN_RECT.collidepoint(pos):
            self.open_codex()
            return

        if self.state == STATE_INTRO:
            self.state = STATE_SELECT

        elif self.state == STATE_SELECT:
            if SELECT_BACK_BTN_RECT.collidepoint(pos):
                self.state = STATE_INTRO
                return
            if len(self.collected) == len(TEAS) and GAME_BTN_RECT.collidepoint(pos):
                self.start_game()
                return
            if self.pending_seal_click is None:
                for i, rect in enumerate(SEAL_RECTS):
                    if rect.collidepoint(pos):
                        self.pending_seal_click = {
                            "tea": TEAS[i], "pos": pos, "start": pygame.time.get_ticks(),
                            "color": TEAS[i]["accent_dark"],
                        }
                        break

        elif self.state == STATE_GAME:
            if BACK_BTN_RECT.collidepoint(pos):
                self.state = STATE_SELECT
                return
            self.game_grab(pos)

        elif self.state == STATE_DETAIL:
            if self.pick_state == "popup":
                self.request_close_popup()
                return
            if self.pick_state == "ink":
                return
            if BACK_BTN_RECT.collidepoint(pos):
                self.state = STATE_SELECT
                self.active_info_index = None
                return
            if self.pick_circle_rect is not None and self.pick_circle_rect.collidepoint(pos):
                self.start_pick_ink(pos)
                return
            for i, center in enumerate(HOTSPOT_POS):
                if math.hypot(pos[0] - center[0], pos[1] - center[1]) <= HOTSPOT_RADIUS:
                    self.active_info_index = None if self.active_info_index == i else i
                    return
            for i, rect in enumerate(INFO_ITEM_RECTS):
                if rect.collidepoint(pos):
                    self.active_info_index = None if self.active_info_index == i else i
                    return

    def handle_motion(self, pos):
        self.hover_seal_index = None
        self._add_ripple(pos)
        if self.state == STATE_SELECT:
            for i, rect in enumerate(SEAL_RECTS):
                if rect.collidepoint(pos):
                    self.hover_seal_index = i
                    break
        if self.state == STATE_GAME and (self.dragging_tea or self.dragging_branch):
            self.drag_pos = pos

    def start_ink_burst(self, pos, color, tea):
        self.burst_active = True
        self.burst_pos = pos
        self.burst_color = color
        self.burst_start = pygame.time.get_ticks()
        self.burst_next_tea = tea
        self.visited.add(tea["id"])

    def update(self):
        self._update_decor()
        self._update_seal_scale()

        if self.pending_seal_click is not None:
            elapsed = pygame.time.get_ticks() - self.pending_seal_click["start"]
            if elapsed >= SEAL_CLICK_DELAY_MS:
                pc = self.pending_seal_click
                self.pending_seal_click = None
                self.start_ink_burst(pc["pos"], pc["color"], pc["tea"])

        if self.burst_active:
            elapsed = pygame.time.get_ticks() - self.burst_start
            if elapsed > 450:
                self.burst_active = False
                self.selected_tea = self.burst_next_tea
                self.active_info_index = None
                self.state = STATE_DETAIL

        if self.state == STATE_DETAIL:
            self.refresh_pick_circle()
        else:
            self.pick_circle_rect = None

        if self.pick_state == "ink":
            elapsed = pygame.time.get_ticks() - self.ink_start
            self.ink_progress = min(1.0, elapsed / 500)
            if self.ink_progress >= 1.0:
                self.open_popup(self.selected_tea)

        if self.pick_state == "popup" and self.popup_closing:
            elapsed = pygame.time.get_ticks() - self.popup_close_start
            if elapsed >= MIST_CLOSE_MS:
                self.pick_state = "idle"
                self.popup_tea = None
                self.popup_closing = False

        if self.show_codex and self.codex_closing:
            elapsed = pygame.time.get_ticks() - self.codex_close_start
            if elapsed >= MIST_CLOSE_MS:
                self.show_codex = False
                self.codex_closing = False

        if self.hand_mode and self.hand_tracker.available:
            self.update_hand_tracking()

        self.ink_splashes = [s for s in self.ink_splashes if s.alive()]

    def _update_seal_scale(self):
        for i in range(len(TEAS)):
            target = SEAL_HOVER_SCALE if (self.hover_seal_index == i or
                                           (self.pending_seal_click and self.pending_seal_click["tea"] is TEAS[i])) else 1.0
            self.seal_scale[i] += (target - self.seal_scale[i]) * SEAL_EASE

    def refresh_pick_circle(self):
        if self.selected_tea is None or self.selected_tea["id"] not in self.tea_images:
            self.pick_circle_rect = None
            return
        base_x, base_y = self.selected_tea.get("leaf_pos", LEAF_POS_DEFAULT)
        cx, cy = sx(base_x), sy(base_y)
        r = PICK_CIRCLE_RADIUS
        self.pick_circle_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)

    def start_pick_ink(self, pos):
        self.pick_state = "ink"
        self.ink_start = pygame.time.get_ticks()
        self.ink_progress = 0
        self.ink_pos = pos
        self.ink_color = self.selected_tea["accent_dark"] if self.selected_tea else SEAL_RED
        if self.selected_tea is not None:
            self.collected.add(self.selected_tea["id"])
            self.collect_toast_text = f"已收集 {self.selected_tea['name']}"
            self.collect_toast_start = pygame.time.get_ticks()

    def update_hand_tracking(self):
        state = self.hand_tracker.get_state()

        if not state["hand_present"]:
            self.gesture_pinch_prev = False
            self.camera_preview_surf = self._build_camera_preview(state["frame_rgb"])
            return

        nx, ny = state["cursor"]
        raw_px, raw_py = int(nx * WIDTH), int(ny * HEIGHT)

        if self.gesture_cursor_px is None:
            sm_px, sm_py = raw_px, raw_py
        else:
            a = 0.35
            sm_px = int(self.gesture_cursor_px[0] * (1 - a) + raw_px * a)
            sm_py = int(self.gesture_cursor_px[1] * (1 - a) + raw_py * a)
        self.gesture_cursor_px = (sm_px, sm_py)
        px, py = sm_px, sm_py

        self.handle_motion((px, py))

        now = pygame.time.get_ticks()
        just_pinched = state["pinch"] and not self.gesture_pinch_prev
        cooldown_ok = (now - self.gesture_last_click_tick) > GESTURE_PINCH_COOLDOWN_MS

        if self.state == STATE_GAME:
            if BACK_BTN_RECT.collidepoint((px, py)) and just_pinched:
                self.state = STATE_SELECT
            elif state["pinch"] and not self.gesture_pinch_prev:
                self.game_grab((px, py))
            elif state["pinch"]:
                self.drag_pos = (px, py)
            elif (not state["pinch"]) and self.gesture_pinch_prev:
                self.game_release((px, py))
            self.gesture_pinch_prev = state["pinch"]
            self.camera_preview_surf = self._build_camera_preview(state["frame_rgb"])
            return

        if just_pinched and cooldown_ok:
            self.gesture_last_click_tick = now
            if self.show_codex:
                self.request_close_codex()
            elif self.state != STATE_INTRO and CODEX_BTN_RECT.collidepoint((px, py)):
                self.open_codex()
            elif self.state == STATE_DETAIL and self.pick_state == "popup":
                self.request_close_popup()
            elif (
                self.state == STATE_DETAIL
                and self.pick_state == "idle"
                and self.pick_circle_rect is not None
                and self.pick_circle_rect.collidepoint(px, py)
            ):
                self.start_pick_ink((px, py))
            else:
                self.handle_click((px, py))

        self.gesture_pinch_prev = state["pinch"]
        self.camera_preview_surf = self._build_camera_preview(state["frame_rgb"])

    def _build_camera_preview(self, frame_rgb):
        if frame_rgb is None or cv2 is None:
            return None
        small = cv2.resize(frame_rgb, CAM_PREVIEW_SIZE)
        return pygame.surfarray.make_surface(small.swapaxes(0, 1))

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def draw(self):
        self.screen.fill(PAPER)
        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_SELECT:
            self.draw_select()
        elif self.state == STATE_DETAIL:
            self.draw_detail()
        elif self.state == STATE_GAME:
            self.draw_game()

        if self.burst_active:
            self.draw_ink_burst()

        if self.state == STATE_DETAIL and self.pick_state == "ink":
            self.draw_pick_ink_animation()
        if self.state == STATE_DETAIL and self.pick_state == "popup":
            self.draw_tea_popup()

        self.draw_mode_hint()
        if self.hand_mode:
            self.draw_camera_preview()
            self.draw_gesture_cursor()

        if self.state != STATE_INTRO:
            self.draw_codex_button()
        self.draw_collect_toast()
        if self.show_codex:
            self.draw_codex()

        self.draw_status_message()

        if self.state != STATE_GAME:
            self.screen.blit(self.border_overlay, (0, 0))

        pygame.display.flip()

    def draw_codex_button(self):
        rect = CODEX_BTN_RECT
        is_hover = rect.collidepoint(pygame.mouse.get_pos())
        color = SEAL_RED if is_hover else INK

        label = self.font_codex_btn.render("茗簿", True, color)
        label_rect = label.get_rect(center=(rect.centerx, rect.centery - sy(6)))
        self.screen.blit(label, label_rect)
        if is_hover:
            underline_y = label_rect.bottom + sy(2)
            pygame.draw.line(self.screen, color,
                              (label_rect.left, underline_y), (label_rect.right, underline_y), 2)

        cnt = self.font_hint.render(f"{len(self.collected)}/{len(TEAS)}", True, INK_SOFT)
        self.screen.blit(cnt, cnt.get_rect(center=(rect.centerx, label_rect.bottom + sy(14))))

    def draw_collect_toast(self):
        if not self.collect_toast_text:
            return
        elapsed = pygame.time.get_ticks() - self.collect_toast_start
        if elapsed > COLLECT_TOAST_MS:
            self.collect_toast_text = None
            return
        t = elapsed / COLLECT_TOAST_MS
        if t < 0.2:
            alpha = int(255 * (t / 0.2))
        elif t > 0.7:
            alpha = int(255 * (1 - (t - 0.7) / 0.3))
        else:
            alpha = 255
        rise = int((1 - t) * sy(10))
        surf = self.font_heading.render(self.collect_toast_text, True, SEAL_RED)
        surf.set_alpha(max(0, alpha))
        rect = surf.get_rect(center=(WIDTH // 2, sy(90) - rise))
        bg = pygame.Surface((rect.width + 24, rect.height + 12), pygame.SRCALPHA)
        bg.fill((242, 236, 224, min(210, alpha)))
        self.screen.blit(bg, (rect.x - 12, rect.y - 6))
        self.screen.blit(surf, rect)

    def _mist_alpha_scale(self, open_start, closing, close_start):
        """返回 (alpha 0-255, scale 0.9-1.0) 用于弹窗“水雾”渐显/渐隐动画"""
        now = pygame.time.get_ticks()
        if closing:
            t = min(1.0, (now - close_start) / MIST_CLOSE_MS)
            alpha = int(255 * (1 - t))
            scale = 1.0 + 0.03 * t
        else:
            t = min(1.0, (now - open_start) / MIST_OPEN_MS)
            e = ease_out_cubic(t)
            alpha = int(255 * e)
            scale = 0.94 + 0.06 * e
        return max(0, alpha), scale

    def draw_codex(self):
        alpha, scale = self._mist_alpha_scale(self.codex_open_start, self.codex_closing, self.codex_close_start)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 28, 24, int(170 * (alpha / 255))))
        self.screen.blit(overlay, (0, 0))

        base_w, base_h = sx(820), sy(560)
        card_w, card_h = int(base_w * scale), int(base_h * scale)
        card_rect = pygame.Rect(0, 0, card_w, card_h)
        card_rect.center = (WIDTH // 2, HEIGHT // 2)

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (*PAPER, alpha), card_surf.get_rect(), border_radius=12)
        pygame.draw.rect(card_surf, (*INK, alpha), card_surf.get_rect(), width=3, border_radius=12)

        title = self.font_heading.render("茗 簿", True, INK)
        title.set_alpha(alpha)
        card_surf.blit(title, title.get_rect(midtop=(card_w // 2, sy(20))))
        sub = self.font_hint.render(
            f"已收集 {len(self.collected)} / {len(TEAS)} 款 · 点击任意处关闭", True, INK_SOFT)
        sub.set_alpha(alpha)
        card_surf.blit(sub, sub.get_rect(midtop=(card_w // 2, sy(100))))

        cols = 3
        cell_w = sx(240)
        cell_h = sy(150)
        gap_x = sx(20)
        gap_y = sy(20)
        grid_w = cols * cell_w + (cols - 1) * gap_x
        start_x = card_w // 2 - grid_w // 2
        start_y = sy(120)

        for i, tea in enumerate(TEAS):
            r = i // cols
            c = i % cols
            cx = start_x + c * (cell_w + gap_x)
            cy = start_y + r * (cell_h + gap_y)
            cell = pygame.Rect(cx, cy, cell_w, cell_h)
            got = tea["id"] in self.collected

            cell_bg = (PAPER_DIM if not got else PAPER)
            pygame.draw.rect(card_surf, (*cell_bg, alpha), cell, border_radius=8)
            border_c = tea["accent"] if got else (200, 194, 182)
            pygame.draw.rect(card_surf, (*border_c, alpha), cell, width=2, border_radius=8)

            if got:
                pygame.draw.circle(card_surf, (*tea["liquor"], alpha),
                                    (cell.x + sx(30), cell.y + sy(34)), sx(14))
                name = self.font_tea_name.render(tea["name"], True, INK)
                name.set_alpha(alpha)
                card_surf.blit(name, (cell.x + sx(54), cell.y + sy(20)))
                term = self.font_tagline.render(f"节气 · {tea['term']}", True, tea["accent_dark"])
                term.set_alpha(alpha)
                card_surf.blit(term, (cell.x + sx(54), cell.y + sy(44)))
                tag = self.font_tagline.render(tea["tagline"], True, INK_SOFT)
                tag.set_alpha(alpha)
                card_surf.blit(tag, (cell.x + sx(18), cell.y + sy(78)))
                for li, (label, text) in enumerate(tea["info"][:1]):
                    line = self.font_tagline.render(f"{label}：{text}", True, INK_SOFT)
                    line.set_alpha(alpha)
                    card_surf.blit(line, (cell.x + sx(18), cell.y + sy(104)))
            else:
                q = self.font_heading.render("？", True, (170, 164, 152))
                q.set_alpha(alpha)
                card_surf.blit(q, q.get_rect(center=cell.center))
                hint = self.font_tagline.render("尚未收集", True, (170, 164, 152))
                hint.set_alpha(alpha)
                card_surf.blit(hint, hint.get_rect(midbottom=(cell.centerx, cell.bottom - sy(12))))

        self.screen.blit(card_surf, card_rect.topleft)

    def draw_mode_hint(self):
        label = "手势模式（按 H 切换回鼠标）" if self.hand_mode else "鼠标模式（按 H 切换为手势）"
        hint_surf = self.font_hint.render(label, True, INK_SOFT)
        hint_rect = hint_surf.get_rect(topright=(WIDTH - sx(30), sy(30)))
        self.screen.blit(hint_surf, hint_rect)

    def draw_camera_preview(self):
        frame_rect = pygame.Rect(CAM_PREVIEW_POS, CAM_PREVIEW_SIZE)
        if self.camera_preview_surf is not None:
            self.screen.blit(self.camera_preview_surf, frame_rect.topleft)
        else:
            pygame.draw.rect(self.screen, PAPER_DIM, frame_rect)
            no_cam_surf = self.font_hint.render("无摄像头画面", True, INK_SOFT)
            self.screen.blit(no_cam_surf, no_cam_surf.get_rect(center=frame_rect.center))
        pygame.draw.rect(self.screen, INK_SOFT, frame_rect, width=2)

    def draw_gesture_cursor(self):
        if self.gesture_cursor_px is None:
            return
        is_pinch = self.gesture_pinch_prev
        color = SEAL_RED if is_pinch else INK
        radius = GESTURE_CURSOR_RADIUS if not is_pinch else int(GESTURE_CURSOR_RADIUS * 0.7)
        pygame.draw.circle(self.screen, color, self.gesture_cursor_px, radius, width=0 if is_pinch else 2)

    def draw_status_message(self):
        if self.status_message and pygame.time.get_ticks() < self.status_message_until:
            msg_surf = self.font_body.render(self.status_message, True, INK)
            bg_rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT - sy(30)))
            bg_rect.inflate_ip(sx(30), sy(14))
            pygame.draw.rect(self.screen, PAPER_DIM, bg_rect, border_radius=6)
            self.screen.blit(msg_surf, msg_surf.get_rect(center=bg_rect.center))

    def draw_intro(self):
        elapsed = pygame.time.get_ticks() - self.start_ticks
        t = pygame.time.get_ticks() / 1000

        self._draw_horizon_wash((236, 232, 222), (246, 240, 229), 0, sy(430))

        wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._draw_ink_blot(wash, sx(260), sy(250), sx(120), (120, 130, 120), 120)
        self._draw_ink_blot(wash, sx(720), sy(220), sx(150), (110, 120, 118), 110)
        self.screen.blit(wash, (0, 0))

        mountain_far = [
            (0, sy(360)), (sx(180), sy(250)), (sx(360), sy(330)), (sx(520), sy(240)),
            (sx(700), sy(320)), (sx(880), sy(250)), (WIDTH, sy(330)),
            (WIDTH, sy(430)), (0, sy(430)),
        ]
        pygame.draw.polygon(self.screen, (196, 200, 190), mountain_far)
        mountain_near = [
            (0, sy(420)), (sx(220), sy(340)), (sx(430), sy(410)), (sx(640), sy(330)),
            (sx(860), sy(410)), (WIDTH, sy(360)), (WIDTH, sy(470)), (0, sy(470)),
        ]
        pygame.draw.polygon(self.screen, (176, 184, 172), mountain_near)

        village_base = sy(470)
        self._draw_village(village_base)
        self._draw_smoke(sx(150), village_base - sy(120), t)
        self._draw_smoke(sx(880), village_base - sy(130), t + 1.5)

        water_y = sy(470)
        self._draw_water(water_y)
        self._draw_bridge(WIDTH // 2, water_y + sy(30), sx(260), sy(70), (170, 176, 176))

        self._draw_petals()

        mist = pygame.Surface((WIDTH, sy(120)), pygame.SRCALPHA)
        offset = math.sin(elapsed / 1800) * sx(40)
        for i in range(3):
            band = pygame.Surface((WIDTH + sx(200), sy(40)), pygame.SRCALPHA)
            band.fill((246, 240, 229, 70 - i * 18))
            mist.blit(band, (offset - sx(100) + i * sx(30), i * sy(30)))
        self.screen.blit(mist, (0, sy(400)))

        fade_in = min(1.0, elapsed / 1200)
        title_surf = self.font_title.render("徽州茶事", True, INK)
        title_surf.set_alpha(int(255 * fade_in))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, sy(150)))
        self.screen.blit(title_surf, title_rect)
        seal = pygame.Rect(0, 0, sx(46), sx(46))
        seal.center = (title_rect.right + sx(40), title_rect.centery)
        if fade_in > 0.6:
            pygame.draw.rect(self.screen, SEAL_RED, seal, border_radius=6)
            zi = self.font_tea_name.render("茶", True, PAPER)
            self.screen.blit(zi, zi.get_rect(center=seal.center))

        if elapsed > 500:
            sub_fade = min(1.0, (elapsed - 500) / 1000)
            sub_surf = self.font_subtitle.render("跟随二十四节气 · 遇见皖南茶山", True, INK_SOFT)
            sub_surf.set_alpha(int(255 * sub_fade))
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, sy(205))))

        if elapsed > 1400:
            pulse = (math.sin(elapsed / 300) + 1) / 2
            hint_color = tuple(int(INK_SOFT[c] + (INK[c] - INK_SOFT[c]) * pulse) for c in range(3))
            hint_surf = self.font_hint.render("点击画面开始 · 移动鼠标可拨动水面", True, hint_color)
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - sy(70))))

    def draw_select(self):
        self._draw_horizon_wash((240, 234, 223), (247, 242, 231), 0, sy(430))
        mountain = [
            (0, sy(400)), (sx(200), sy(320)), (sx(430), sy(390)), (sx(660), sy(320)),
            (sx(880), sy(390)), (WIDTH, sy(330)), (WIDTH, sy(430)), (0, sy(430)),
        ]
        pygame.draw.polygon(self.screen, (204, 208, 198), mountain)
        self._draw_water(sy(560))
        self._draw_petals()

        # 返回首页按钮（与其它页面风格一致：简洁文字 + hover 下划线）
        is_back_hover = SELECT_BACK_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        back_color = SEAL_RED if is_back_hover else INK_SOFT
        back_surf = self.font_hint.render("← 返回首页", True, back_color)
        back_rect = back_surf.get_rect(midleft=(SELECT_BACK_BTN_RECT.x, SELECT_BACK_BTN_RECT.centery))
        self.screen.blit(back_surf, back_rect)
        if is_back_hover:
            pygame.draw.line(self.screen, back_color,
                              (back_rect.left, back_rect.bottom + 2), (back_rect.right, back_rect.bottom + 2), 1)

        heading = self.font_heading.render("选择一个节气", True, INK)
        self.screen.blit(heading, heading.get_rect(center=(WIDTH // 2, sy(120))))
        sub = self.font_subtitle.render("点击印章，走入茶山", True, INK_SOFT)
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, sy(165))))

        for i, tea in enumerate(TEAS):
            rect = SEAL_RECTS[i]
            is_hover = self.hover_seal_index == i
            color = tea["accent_dark"]
            scale = self.seal_scale[i]

            if is_hover:
                blot = pygame.Surface((SEAL_SIZE * 3, SEAL_SIZE * 3), pygame.SRCALPHA)
                self._draw_ink_blot(blot, blot.get_width() // 2, blot.get_height() // 2,
                                     SEAL_SIZE // 2, color, 160)
                self.screen.blit(blot, blot.get_rect(center=rect.center))

            # 果冻式平滑放大
            w = int(rect.width * scale)
            h = int(rect.height * scale)
            seal_rect = pygame.Rect(0, 0, w, h)
            seal_rect.center = rect.center

            pygame.draw.rect(self.screen, PAPER, seal_rect, border_radius=8)
            pygame.draw.rect(self.screen, color, seal_rect, width=3, border_radius=8)
            pygame.draw.rect(self.screen, color, seal_rect.inflate(-sx(10), -sx(10)),
                              width=1, border_radius=6)

            term_surf = self.font_seal.render(tea["term"], True, color)
            self.screen.blit(term_surf, term_surf.get_rect(center=seal_rect.center))

            name_surf = self.font_tea_name.render(tea["name"], True, INK)
            self.screen.blit(name_surf,
                              name_surf.get_rect(center=(rect.centerx, rect.bottom + sy(26))))

            if is_hover:
                tag_surf = self.font_tagline.render(tea["tagline"], True, INK_SOFT)
                self.screen.blit(tag_surf,
                                  tag_surf.get_rect(center=(rect.centerx, rect.bottom + sy(48))))

            dot_color = tea["accent"] if tea["id"] in self.visited else PAPER_DIM
            pygame.draw.circle(self.screen, dot_color,
                                (WIDTH // 2 - sx(40) + i * sx(20), HEIGHT - sy(40)), sx(5))

        if len(self.collected) == len(TEAS):
            is_game_btn_hover = GAME_BTN_RECT.collidepoint(pygame.mouse.get_pos())
            btn_color = SEAL_RED if is_game_btn_hover else INK
            txt = self.font_subtitle.render("进入茶田 · 采茶", True, btn_color)
            txt_rect = txt.get_rect(center=GAME_BTN_RECT.center)
            self.screen.blit(txt, txt_rect)
            if is_game_btn_hover:
                underline_y = txt_rect.bottom + sy(4)
                pygame.draw.line(self.screen, SEAL_RED,
                                  (txt_rect.left, underline_y), (txt_rect.right, underline_y), 2)

    def draw_detail(self):
        tea = self.selected_tea
        if tea is None:
            return
        accent = tea["accent"]
        accent_dark = tea["accent_dark"]

        is_back_hover = BACK_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        back_color = accent_dark if is_back_hover else INK_SOFT
        back_surf = self.font_hint.render("← 返回节气", True, back_color)
        back_rect = back_surf.get_rect(midleft=(BACK_BTN_RECT.x, BACK_BTN_RECT.centery))
        self.screen.blit(back_surf, back_rect)
        if is_back_hover:
            pygame.draw.line(
                self.screen, back_color,
                (back_rect.left, back_rect.bottom + 2), (back_rect.right, back_rect.bottom + 2), 1
            )

        term_surf = self.font_label.render(tea["term"].upper(), True, accent_dark)
        self.screen.blit(term_surf, (sx(40), sy(70)))

        name_surf = self.font_heading.render(tea["name"], True, INK)
        self.screen.blit(name_surf, (sx(38), sy(92)))

        tagline_surf = self.font_body.render(tea["tagline"], True, INK_SOFT)
        self.screen.blit(tagline_surf, (sx(40), sy(155)))

        self.draw_tea_image(tea["id"])

        for i, (label, text) in enumerate(tea["info"]):
            rect = INFO_ITEM_RECTS[i]
            active = self.active_info_index == i
            border_color = accent if active else PAPER_DIM
            pygame.draw.line(
                self.screen, border_color, (rect.x, rect.y), (rect.x, rect.bottom), 3
            )

            label_surf = self.font_label.render(label.upper(), True, accent_dark)
            self.screen.blit(label_surf, (rect.x + sx(16), rect.y))

            if active:
                lines = wrap_text(text, self.font_body, rect.width - sx(30))
                for li, line in enumerate(lines):
                    line_surf = self.font_body.render(line, True, INK)
                    self.screen.blit(line_surf, (rect.x + sx(16), rect.y + sy(28) + li * sy(26)))

        liquor_y = INFO_ITEM_RECTS[-1].bottom + sy(30)
        pygame.draw.circle(self.screen, tea["liquor"], (sx(576), liquor_y), sx(10))
        liquor_label = self.font_hint.render("汤色参考", True, INK_SOFT)
        self.screen.blit(liquor_label, (sx(596), liquor_y - sy(9)))

    # ------------------------------------------------------------------
    # 茶田种植
    # ------------------------------------------------------------------

    def start_game(self):
        self.state = STATE_GAME
        n = min(3, len(TEAS))
        chosen = random.sample(TEAS, n)

        pad = sx(16)
        plot_w = (self.field_rect.width - pad * (n + 1)) // n
        plot_h = self.field_rect.height - sy(20)
        y = self.field_rect.top + sy(10)
        x = self.field_rect.left + pad
        self.game_plots = []
        for tea in chosen:
            rect = pygame.Rect(x, y, plot_w, plot_h)
            self.game_plots.append({
                "tea": tea, "planted": False, "harvested": False,
                "rect": rect, "plant_time": 0, "planted_pos": None,
            })
            x += plot_w + pad

        self.basket_collected = []
        self.plant_toast = None
        self.dragging_tea = None
        self.dragging_branch = None
        self.drag_pos = None
        self.ink_splashes = []

    def game_chip_rects(self):
        teas = [t for t in TEAS if t["id"] in self.collected]
        if not teas:
            return []
        n = len(teas)
        chip_w, chip_h, gap = sx(132), sy(72), sx(22)
        total = n * chip_w + (n - 1) * gap
        start_x = (WIDTH - total) // 2
        y = sy(470)
        return [(teas[i], pygame.Rect(start_x + i * (chip_w + gap), y, chip_w, chip_h))
                for i in range(n)]

    def _is_grown(self, plot):
        if not plot["planted"] or plot["harvested"]:
            return False
        return pygame.time.get_ticks() - plot["plant_time"] >= GROW_DURATION_MS

    def _branch_grab_rect(self, plot):
        cx, cy = plot.get("planted_pos") or plot["rect"].center
        r = sx(38)
        return pygame.Rect(cx - r, cy - r, r * 2, r * 2)

    def game_grab(self, pos):
        for plot in self.game_plots:
            if self._is_grown(plot):
                if self._branch_grab_rect(plot).collidepoint(pos):
                    self.dragging_branch = plot
                    self.drag_pos = pos
                    return
        for tea, rect in self.game_chip_rects():
            if rect.collidepoint(pos):
                self.dragging_tea = tea
                self.drag_pos = pos
                return

    def game_release(self, pos):
        if self.dragging_branch:
            plot = self.dragging_branch
            if self.basket_rect.collidepoint(pos):
                tea_name = plot["tea"]["name"]
                plot["planted"] = False
                plot["harvested"] = False
                plot["plant_time"] = 0
                plot["planted_pos"] = None

                self.ink_splashes.append(InkSplash(self.basket_rect.center, plot["tea"]["accent_dark"]))
                if tea_name not in self.basket_collected:
                    self.basket_collected.append(tea_name)
                self.show_plant_toast(
                    (self.basket_rect.centerx, self.basket_rect.top - sy(6)),
                    f"{tea_name}已采入竹筐", True, plot["tea"]["accent_dark"],
                )
            else:
                self.show_plant_toast(
                    (plot["rect"].centerx, plot["rect"].top + sy(6)),
                    "未采入竹筐，请拖到竹筐中", False, INK_SOFT,
                )
            self.dragging_branch = None
            self.drag_pos = None
            return

        if self.dragging_tea:
            for plot in self.game_plots:
                if plot["rect"].collidepoint(pos):
                    self.drop_tea_on_plot(plot, self.dragging_tea, pos)
                    break
            self.dragging_tea = None
            self.drag_pos = None

    def drop_tea_on_plot(self, plot, tea, pos):
        if plot["planted"]:
            self.show_plant_toast(pos, "此处已种下茶苗", False, INK_SOFT)
            return
        correct = tea["id"] == plot["tea"]["id"]
        if correct:
            plot["planted"] = True
            plot["plant_time"] = pygame.time.get_ticks()
            plot["planted_pos"] = pos
            self.ink_splashes.append(InkSplash(pos, plot["tea"]["accent_dark"]))
            self.show_plant_toast(
                (plot["rect"].centerx, plot["rect"].top + sy(6)),
                f"节气相合，{tea['name']}正在生长",
                True, plot["tea"]["accent_dark"],
            )
        else:
            self.show_plant_toast((plot["rect"].centerx, plot["rect"].top + sy(6)),
                                   "节气不合，种植失败", False, SEAL_RED)

    def show_plant_toast(self, pos, text, ok, color):
        self.plant_toast = {
            "text": text, "pos": pos, "color": color,
            "start": pygame.time.get_ticks(), "ok": ok,
        }

    def draw_game(self):
        self.screen.blit(self.field_bg_full, (0, 0))

        if any(p["tea"]["weather"]["icon"] in ("drizzle", "rain") for p in self.game_plots):
            self._draw_rain()

        back = self.font_hint.render("← 返回节气", True, INK_SOFT)
        self.screen.blit(back, back.get_rect(midleft=(BACK_BTN_RECT.x, BACK_BTN_RECT.centery)))

        tip = "把符合节气的茶叶拖到对应茶田任意处生长，5秒后再拖入竹筐采收"
        ts = self.font_subtitle.render(tip, True, INK)
        self.screen.blit(ts, ts.get_rect(center=(WIDTH // 2, sy(70))))

        for plot in self.game_plots:
            self._draw_plot(plot)

        self._draw_basket()

        for s in self.ink_splashes:
            s.draw(self.screen)

        self._draw_plant_toast()

        label = self.font_hint.render("茗簿 · 拖拽下方茶叶去种植（可重复选取）", True, INK_SOFT)
        self.screen.blit(label, label.get_rect(center=(WIDTH // 2, sy(430))))

        chips = self.game_chip_rects()
        mouse_pos = pygame.mouse.get_pos()
        if not chips:
            note = "还没有收集到茶叶，请先返回选择节气去采茶吧"
            ns = self.font_hint.render(note, True, INK_SOFT)
            self.screen.blit(ns, ns.get_rect(center=(WIDTH // 2, sy(505))))
        else:
            for tea, rect in chips:
                if self.dragging_tea is tea:
                    continue
                self._draw_tea_chip(tea, rect, rect.collidepoint(mouse_pos))

        if self.dragging_tea and self.drag_pos:
            r = pygame.Rect(0, 0, sx(132), sy(72))
            r.center = self.drag_pos
            self._draw_tea_chip(self.dragging_tea, r, False)

        if self.dragging_branch and self.drag_pos:
            self._draw_plant(self.drag_pos[0], self.drag_pos[1] + sy(18), grown=True)

    def _draw_plot(self, plot):
        rect = plot["rect"]
        tea = plot["tea"]

        pos = plot.get("planted_pos") or rect.center

        if plot["planted"] and not plot["harvested"] and not (self.dragging_branch is plot):
            grown = self._is_grown(plot)
            t = pygame.time.get_ticks() / 500.0
            sway = math.sin(t) * sx(3)
            px, py = pos

            if grown:
                self._draw_plant(px + sway, py, grown=True)
                hint = self.font_tagline.render("拖拽入竹筐", True, INK_SOFT)
                self.screen.blit(hint, hint.get_rect(midtop=(px, py + sy(30))))
            else:
                progress = min(1.0, (pygame.time.get_ticks() - plot["plant_time"]) / GROW_DURATION_MS)
                self._draw_plant(px + sway, py, grown=False, scale=0.4 + progress * 0.6)
                bar_w, bar_h = sx(60), sy(7)
                bar_rect = pygame.Rect(0, 0, bar_w, bar_h)
                bar_rect.midtop = (px, py + sy(10))
                pygame.draw.rect(self.screen, PAPER, bar_rect, border_radius=4)
                fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_w * progress), bar_h)
                pygame.draw.rect(self.screen, tea["accent_dark"], fill_rect, border_radius=4)
                pygame.draw.rect(self.screen, INK_SOFT, bar_rect, width=1, border_radius=4)

        # 节气提示：去掉边框底板，仅用有色文字 + 淡淡阴影，简洁古朴
        term_text = tea["term"]
        shadow = self.font_plot_label.render(term_text, True, PAPER)
        term_surf = self.font_plot_label.render(term_text, True, tea["accent_dark"])
        term_pos = (rect.centerx - term_surf.get_width() // 2, rect.top + sy(6))
        self.screen.blit(shadow, (term_pos[0] + 1, term_pos[1] + 1))
        self.screen.blit(term_surf, term_pos)

    def _draw_plant(self, x, y, grown=True, scale=1.0):
        color = (94, 118, 78)
        size_boost = 1.8 if grown else 1.4
        stem_h = sy(18) * scale * size_boost
        pygame.draw.line(self.screen, color, (x, y), (x, y - stem_h), max(2, int(3 * size_boost)))
        leaf_r = (sx(7) if grown else sx(4)) * scale * size_boost
        for dx, dy in [(-9, -14), (9, -14), (0, -25)]:
            pygame.draw.circle(
                self.screen, (114, 142, 92),
                (int(x + sx(dx) * scale * size_boost / 1.4), int(y + sy(dy) * scale * size_boost / 1.4)),
                max(3, int(leaf_r)),
            )

    def _draw_basket(self):
        rect = self.basket_rect
        self.screen.blit(self.basket_image, rect.topleft)

        bl = self.font_hint.render("竹筐", True, INK_SOFT)
        self.screen.blit(bl, bl.get_rect(midbottom=(rect.centerx, rect.top - sy(8))))

        if not self.basket_collected:
            hint = self.font_hint.render("（尚未采得）", True, INK_SOFT)
            self.screen.blit(hint, hint.get_rect(center=(rect.centerx, rect.centery)))
        else:
            start_y = rect.top + sy(24)
            for i, name in enumerate(self.basket_collected):
                item = self.font_basket_item.render("• " + name, True, INK)
                self.screen.blit(item, item.get_rect(
                    midtop=(rect.centerx, start_y + i * (item.get_height() + sy(6)))))

    def _draw_rain(self):
        t = pygame.time.get_ticks()
        for i in range(70):
            x = (i * 137 + t // 3) % WIDTH
            y = (i * 89 + t // 2) % HEIGHT
            pygame.draw.line(self.screen, (185, 195, 205),
                              (x, y), (x - sx(6), y + sy(14)), 1)

    def _draw_plant_toast(self):
        toast = self.plant_toast
        if not toast:
            return
        elapsed = pygame.time.get_ticks() - toast["start"]
        if elapsed > 1400:
            self.plant_toast = None
            return
        alpha = 255 if elapsed < 900 else max(0, int(255 * (1 - (elapsed - 900) / 500)))
        rise = int(elapsed / 1400 * sy(26))
        surf = self.font_body.render(toast["text"], True, toast["color"])
        surf.set_alpha(alpha)
        x, y = toast["pos"]
        rect = surf.get_rect(center=(x, y - rise))
        self.screen.blit(surf, rect)

    def _draw_tea_chip(self, tea, rect, is_hover):
        """底部收藏栏茶叶卡片：无边框，仅汤色小圆点 + 茶名，悬浮时显示下划线。"""
        dot_y = rect.centery
        pygame.draw.circle(self.screen, tea["liquor"], (rect.x + sx(24), dot_y), sx(9))
        name = self.font_tea_name.render(tea["name"], True, INK)
        name_rect = name.get_rect(midleft=(rect.x + sx(42), dot_y))
        self.screen.blit(name, name_rect)
        if is_hover:
            underline_y = name_rect.bottom + sy(3)
            pygame.draw.line(self.screen, tea["accent_dark"],
                              (name_rect.left, underline_y), (name_rect.right, underline_y), 2)

    # ------------------------------------------------------------------
    # 采茶大图弹窗 / 引导圆圈
    # ------------------------------------------------------------------

    def draw_pick_hint(self):
        if self.pick_circle_rect is None:
            return
        if self.pick_state != "idle":
            return

        self.hint_time += 0.08
        pulse = (math.sin(self.hint_time) + 1) / 2
        radius = int(PICK_CIRCLE_RADIUS * (0.75 + pulse * 0.25))
        alpha = int(80 + pulse * 100)

        size = self.pick_circle_rect.size
        hint = pygame.Surface(size, pygame.SRCALPHA)
        center_local = (size[0] // 2, size[1] // 2)
        pygame.draw.circle(hint, (100, 100, 70, alpha), center_local, radius, 3)

        self.screen.blit(hint, self.pick_circle_rect.topleft)

        tip_surf = self.font_hint.render("轻捏此处，看茶叶大图", True, INK_SOFT)
        tip_rect = tip_surf.get_rect(
            midtop=(self.pick_circle_rect.centerx, self.pick_circle_rect.bottom + sy(6))
        )
        self.screen.blit(tip_surf, tip_rect)

    def draw_tea_image(self, tea_id):
        if tea_id not in self.tea_images:
            return
        img = self.tea_images[tea_id]
        img = pygame.transform.smoothscale(img, TEA_IMG_SIZE)
        rect = img.get_rect(center=TEA_IMG_CENTER)
        self.screen.blit(img, rect)
        self.draw_pick_hint()

    def draw_pick_ink_animation(self):
        progress = self.ink_progress
        radius = int(sx(10) + progress * sx(500))
        alpha = max(0, int(220 * (1 - progress * 0.6)))
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.ink_color, alpha), (radius, radius), radius)
        rect = surf.get_rect(center=self.ink_pos)
        self.screen.blit(surf, rect)

    def draw_tea_popup(self):
        tea = self.popup_tea
        if tea is None or tea["id"] not in self.tea_popup_images:
            self.pick_state = "idle"
            self.popup_tea = None
            return

        alpha, scale = self._mist_alpha_scale(self.popup_open_start, self.popup_closing, self.popup_close_start)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 28, 24, int(150 * (alpha / 255))))
        self.screen.blit(overlay, (0, 0))

        base_w, base_h = sx(520), sy(560)
        card_w, card_h = int(base_w * scale), int(base_h * scale)
        card_rect = pygame.Rect(0, 0, card_w, card_h)
        card_rect.center = (WIDTH // 2, HEIGHT // 2)

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (*PAPER, alpha), card_surf.get_rect(), border_radius=10)
        pygame.draw.rect(card_surf, (*tea["accent_dark"], alpha), card_surf.get_rect(), width=3, border_radius=10)

        # “已收集 XXX” 放在弹窗顶部，不遮挡下方图片
        collected_surf = self.font_hint.render(f"已收集 {tea['name']}", True, tea["accent_dark"])
        collected_surf.set_alpha(alpha)
        card_surf.blit(collected_surf, collected_surf.get_rect(midtop=(card_w // 2, sy(16))))

        big_img = pygame.transform.smoothscale(self.tea_popup_images[tea["id"]],
                                                (int(sx(360) * scale), int(sy(360) * scale)))
        big_img.set_alpha(alpha)
        img_rect = big_img.get_rect(midtop=(card_w // 2, sy(46)))
        card_surf.blit(big_img, img_rect)

        name_surf = self.font_heading.render(tea["name"], True, INK)
        name_surf.set_alpha(alpha)
        card_surf.blit(name_surf, name_surf.get_rect(midtop=(card_w // 2, img_rect.bottom + sy(16))))

        tag_surf = self.font_body.render(tea["tagline"], True, INK_SOFT)
        tag_surf.set_alpha(alpha)
        card_surf.blit(tag_surf, tag_surf.get_rect(midtop=(card_w // 2, img_rect.bottom + sy(70))))

        close_surf = self.font_hint.render("点击任意处关闭", True, INK_SOFT)
        close_surf.set_alpha(alpha)
        card_surf.blit(close_surf, close_surf.get_rect(midbottom=(card_w // 2, card_h - sy(14))))

        self.screen.blit(card_surf, card_rect.topleft)

    def draw_leaf(self, center, size, angle, color):
        w, h = max(4, size[0]), max(4, size[1])
        leaf_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(leaf_surf, (*color, 200), (0, 0, w, h))
        rotated = pygame.transform.rotate(leaf_surf, angle)
        rect = rotated.get_rect(center=center)
        self.screen.blit(rotated, rect)

    def draw_ink_burst(self):
        elapsed = pygame.time.get_ticks() - self.burst_start
        progress = min(1.0, elapsed / 450)
        radius = int(sx(14) + progress * sx(260))
        alpha = max(0, int(200 * (1 - progress)))
        burst_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(burst_surf, (*self.burst_color, alpha), (radius, radius), radius)
        rect = burst_surf.get_rect(center=self.burst_pos)
        self.screen.blit(burst_surf, rect)

    # ------------------------------------------------------------------
    # 动态装饰元素
    # ------------------------------------------------------------------
    def _spawn_petals(self, n):
        petals = []
        for _ in range(n):
            petals.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(-HEIGHT, HEIGHT),
                "spd": random.uniform(0.3, 1.1),
                "sway": random.uniform(0.4, 1.4),
                "phase": random.uniform(0, math.tau),
                "size": random.uniform(0.6, 1.4),
                "kind": random.choice(["leaf", "leaf", "dot"]),
            })
        return petals

    def _spawn_lanterns(self, n):
        ls = []
        for i in range(n):
            ls.append({
                "x": random.uniform(0, WIDTH),
                "phase": random.uniform(0, math.tau),
                "spd": random.uniform(0.15, 0.4),
                "glow": random.uniform(0.7, 1.0),
            })
        return ls

    def _update_decor(self):
        for p in self.petals:
            p["y"] += p["spd"] * SCALE_Y * 1.2
            p["x"] += math.sin(p["phase"] + p["y"] * 0.01) * p["sway"] * 0.6
            p["phase"] += 0.01
            if p["y"] > HEIGHT + 20:
                p["y"] = -20
                p["x"] = random.uniform(0, WIDTH)
        for l in self.lanterns:
            l["x"] += l["spd"] * SCALE_X
            if l["x"] > WIDTH + 40:
                l["x"] = -40
        now = pygame.time.get_ticks()
        self.ripples = [r for r in self.ripples if now - r[2] < 1400]

    def _add_ripple(self, pos):
        now = pygame.time.get_ticks()
        if now - self._last_ripple_ms < 90:
            return
        if pos[1] < HEIGHT * 0.62:
            return
        self._last_ripple_ms = now
        self.ripples.append((pos[0], pos[1], now))

    # ------------------------------------------------------------------
    # 徽派风景绘制
    # ------------------------------------------------------------------
    def _draw_horizon_wash(self, top_color, bottom_color, y0, y1):
        h = max(1, y1 - y0)
        for i in range(0, h, 2):
            t = i / h
            col = tuple(int(top_color[c] + (bottom_color[c] - top_color[c]) * t) for c in range(3))
            pygame.draw.line(self.screen, col, (0, y0 + i), (WIDTH, y0 + i))

    def _draw_ink_blot(self, surf, cx, cy, r, color, alpha):
        for i in range(4):
            a = int(alpha * (0.35 - i * 0.07))
            if a <= 0:
                continue
            rr = int(r * (1 + i * 0.35))
            pygame.draw.circle(surf, (*color, a), (cx, cy), rr)

    def _draw_huizhou_house(self, x, base_y, w, h, color):
        body = pygame.Rect(x, base_y - h, w, h)
        pygame.draw.rect(self.screen, color, body)
        step_h = h * 0.16
        step_w = w * 0.22
        top_y = base_y - h
        pts = [
            (x, top_y),
            (x + step_w, top_y),
            (x + step_w, top_y - step_h),
            (x + w * 0.5, top_y - step_h),
            (x + w * 0.5, top_y - step_h * 2),
            (x + w - step_w, top_y - step_h * 2),
            (x + w - step_w, top_y - step_h),
            (x + w, top_y - step_h),
            (x + w, top_y),
        ]
        pygame.draw.polygon(self.screen, color, pts)
        eave = tuple(max(0, c - 22) for c in color)
        pygame.draw.line(self.screen, eave, (x, top_y), (x + w, top_y), 2)
        win = tuple(max(0, c - 40) for c in color)
        wr = pygame.Rect(0, 0, int(w * 0.18), int(h * 0.2))
        wr.center = (int(x + w * 0.5), int(base_y - h * 0.45))
        pygame.draw.rect(self.screen, win, wr)

    def _draw_village(self, base_y):
        wall = (222, 216, 205)
        houses = [
            (0.02, 90, 130), (0.12, 70, 100), (0.20, 100, 150),
            (0.72, 95, 140), (0.83, 72, 105), (0.90, 105, 160),
        ]
        for fx, bw, bh in houses:
            x = sx(fx * 1000)
            w, h = sx(bw), sy(bh)
            self._draw_huizhou_house(x, base_y, w, h, wall)

    def _draw_bridge(self, cx, base_y, span, rise, color):
        left = cx - span // 2
        right = cx + span // 2
        top = base_y - rise
        pts = []
        steps = 24
        for i in range(steps + 1):
            t = i / steps
            bx = left + t * span
            by = base_y - math.sin(t * math.pi) * rise
            pts.append((bx, by))
        pts.append((right, base_y))
        pts.append((left, base_y))
        pygame.draw.polygon(self.screen, color, pts)
        arch = []
        ah = rise * 0.62
        for i in range(steps + 1):
            t = i / steps
            bx = left + span * 0.2 + t * span * 0.6
            by = base_y - math.sin(t * math.pi) * ah
            arch.append((bx, by))
        arch.append((left + span * 0.8, base_y + 4))
        arch.append((left + span * 0.2, base_y + 4))
        pygame.draw.polygon(self.screen, (206, 210, 210), arch)

    def _draw_smoke(self, x, y, t):
        smoke = pygame.Surface((sx(60), sy(140)), pygame.SRCALPHA)
        for i in range(6):
            yy = sy(120) - i * sy(20)
            xx = sx(30) + math.sin(t * 1.5 + i * 0.7) * sx(10)
            a = max(0, 60 - i * 9)
            pygame.draw.circle(smoke, (245, 240, 232, a), (int(xx), int(yy)), sx(8) + i)
        self.screen.blit(smoke, (x - sx(30), y - sy(140)))

    def _draw_water(self, y0):
        self._draw_horizon_wash((208, 214, 213), (188, 197, 200), y0, HEIGHT)
        t = pygame.time.get_ticks() / 1000

        wave = pygame.Surface((WIDTH, HEIGHT - y0), pygame.SRCALPHA)
        for i in range(0, HEIGHT - y0, sy(18)):
            a = 26 - i // sy(18) * 2
            if a <= 0:
                continue
            off = math.sin(t * 1.2 + i * 0.05) * sx(12)
            pygame.draw.line(wave, (255, 255, 255, max(0, a)),
                              (0 + off, i), (WIDTH + off, i), 2)
        self.screen.blit(wave, (0, y0))

        for l in self.lanterns:
            gx = int(l["x"])
            gy = int(y0 + sy(40) + math.sin(t + l["phase"]) * sy(6))
            glow = pygame.Surface((sx(40), sy(40)), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 170, 90, int(70 * l["glow"])), (sx(20), sy(20)), sx(16))
            pygame.draw.circle(glow, (255, 210, 140, int(160 * l["glow"])), (sx(20), sy(20)), sx(7))
            self.screen.blit(glow, (gx - sx(20), gy - sy(20)))
            refl = pygame.Surface((sx(20), sy(30)), pygame.SRCALPHA)
            pygame.draw.circle(refl, (255, 180, 110, 50), (sx(10), sy(6)), sx(6))
            self.screen.blit(refl, (gx - sx(10), gy + sy(10)))

        now = pygame.time.get_ticks()
        for (rx, ry, start) in self.ripples:
            age = (now - start) / 1400
            rr = int(sx(6) + age * sx(60))
            a = max(0, int(120 * (1 - age)))
            ring = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 255, 255, a), (rr + 2, rr + 2), rr, 2)
            self.screen.blit(ring, (rx - rr, ry - rr))

    def _draw_petals(self):
        for p in self.petals:
            col = (120, 140, 100) if p["kind"] == "leaf" else (170, 110, 95)
            if p["kind"] == "leaf":
                self.draw_leaf((int(p["x"]), int(p["y"])),
                                (int(sx(14) * p["size"]), int(sy(7) * p["size"])),
                                p["phase"] * 40 % 360, col)
            else:
                s = pygame.Surface((sx(8), sy(8)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*col, 150), (sx(4), sy(4)), max(2, int(sx(3) * p["size"])))
                self.screen.blit(s, (int(p["x"]), int(p["y"])))


if __name__ == "__main__":
    App().run()