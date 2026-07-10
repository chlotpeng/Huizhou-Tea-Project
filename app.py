# file_name: app.py
"""
App 主类
"""

import sys
import threading

import pygame

from constants import *
from hand_tracker import HandTracker

from interactions import InteractionMixin
from game import GameMixin
from ui_screens import UIMixin
from decor import DecorMixin
from chat import ChatMixin


class App(InteractionMixin, GameMixin, UIMixin, DecorMixin, ChatMixin):
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

        try:
            self.kite_image_raw = pygame.image.load("assets/纸鸢.png").convert_alpha()
        except Exception:
            self.kite_image_raw = None

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
        # “已收集 XXX” 提示：再小一号
        self.font_popup_collected = pygame.font.Font(FONT_PATH, sf(10))
        self.font_collect_toast = pygame.font.Font(FONT_PATH, sf(34))
        self.font_poem = pygame.font.Font(FONT_PATH, sf(30))

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

        self.seal_scale = [1.0] * len(TEAS)
        self.pending_seal_click = None

        self.poem_transition = None
        self.transition = None
        self.kite_anim = None

        self.hand_tracker = HandTracker()
        self.hand_mode = False
        self.gesture_cursor_px = None
        self.gesture_pinch_prev = False
        self.gesture_last_click_tick = -10_000
        self.gesture_last_swipe_tick = -10_000
        self._swipe_history = []

        self.pick_state = "idle"
        self.ink_progress = 0
        self.ink_start = 0
        self.ink_pos = (0, 0)
        self.ink_color = SEAL_RED
        self.pick_circle_rect = None
        self.popup_tea = None

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

        # ---- 茶话徽州 · 对话界面状态 ----
        self.chat_messages = []
        self.chat_input = ""
        self.chat_pending = False
        self.chat_scroll = 0
        self.chat_stick_bottom = True
        self.chat_visited = False
        self.chat_origin = STATE_SELECT
        self._chat_lock = threading.Lock()

        self.game_completed = False

        # ---- 散席辞归（退出确认 + 水墨蔓延退出动画）----
        self.show_exit_dialog = False
        self.exit_dialog_start = 0
        self.exiting = False
        self.exit_start = 0
        self.exit_ink_origin = (WIDTH // 2, HEIGHT // 2)
        # 水墨颜色采用“清明”节气标签色
        self.exit_ink_color = TEAS[0]["accent"]

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

        self.field_rect = pygame.Rect(sx(60), sy(140), sx(640), sy(340))
        self.basket_rect = pygame.Rect(sx(722), sy(250), sx(231), sy(308))

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

        self.page_sound = None
        try:
            self.page_sound = pygame.mixer.Sound(PAGE_SOUND_PATH)
            vol = min(PAGE_SOUND_VOLUME, BGM_TARGET_VOLUME - 0.05)
            self.page_sound.set_volume(max(0.05, vol))
        except Exception:
            self.page_sound = None

        self.click_sound = None
        try:
            self.click_sound = pygame.mixer.Sound(CLICK_SOUND_PATH)
            click_vol = min(CLICK_SOUND_VOLUME, PAGE_SOUND_VOLUME - 0.05, BGM_TARGET_VOLUME - 0.05)
            self.click_sound.set_volume(max(0.05, click_vol))
        except Exception:
            self.click_sound = None

        self.rain_particles = self._spawn_rain_particles(70)
        self.frost_particles = self._spawn_frost_particles(50)
        self.lixia_petals = self._spawn_lixia_petals(22)

        self.running = True

    # ------------------------------------------------------------------

    def play_page_sound(self):
        if self.page_sound is not None:
            try:
                self.page_sound.play()
            except Exception:
                pass

    def play_click_sound(self):
        if self.click_sound is not None:
            try:
                self.click_sound.play()
            except Exception:
                pass

    # ------------------------------------------------------------------
    def start_transition(self, next_state, on_switch=None):
        if self.transition is not None:
            return
        self.transition = {
            "start": pygame.time.get_ticks(),
            "next_state": next_state,
            "switched": False,
            "on_switch": on_switch,
        }

    def _draw_transition_overlay(self):
        tr = self.transition
        elapsed = pygame.time.get_ticks() - tr["start"]
        if elapsed < FADE_MS:
            alpha = int(255 * ease_in_out(elapsed / FADE_MS))
        else:
            alpha = int(255 * (1 - ease_in_out(min(1.0, (elapsed - FADE_MS) / FADE_MS))))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill(PAPER)
        overlay.set_alpha(max(0, min(255, alpha)))
        self.screen.blit(overlay, (0, 0))

    # ------------------------------------------------------------------
    # 散席辞归
    # ------------------------------------------------------------------
    def open_exit_dialog(self):
        if self.exiting:
            return
        self.show_exit_dialog = True
        self.exit_dialog_start = pygame.time.get_ticks()

    def start_exit(self):
        self.show_exit_dialog = False
        self.exiting = True
        self.exit_start = pygame.time.get_ticks()
        self.exit_ink_origin = EXIT_LEAVE_BTN_RECT.center
        self.exit_ink_color = TEAS[0]["accent"]  # 清明色

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
                if self.show_exit_dialog:
                    self.show_exit_dialog = False
                elif self.state == STATE_CHAT:
                    self.exit_chat()
                else:
                    self.running = False
            elif self.state == STATE_CHAT and event.type == pygame.TEXTINPUT:
                self.chat_input += event.text
            elif self.state == STATE_CHAT and event.type == pygame.MOUSEWHEEL:
                self.handle_chat_scroll(event.y)
            elif self.state == STATE_CHAT and event.type == pygame.KEYDOWN:
                self.handle_chat_key(event)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                self.toggle_hand_mode()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.play_click_sound()
                self.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.state == STATE_GAME:
                    self.game_release(event.pos)

    def update(self):
        self._update_decor()
        self._update_seal_scale()
        self._update_weather_particles()

        # ---- 散席辞归：水墨蔓延 + 背景音乐减弱 + 关闭窗口 ----
        if self.exiting:
            elapsed = pygame.time.get_ticks() - self.exit_start
            if self.bgm_ok:
                try:
                    pygame.mixer.music.set_volume(
                        max(0.0, BGM_TARGET_VOLUME * (1 - elapsed / EXIT_MS)))
                except Exception:
                    pass
            if elapsed >= EXIT_MS:
                self.running = False
            return

        if self.transition is not None:
            tr = self.transition
            elapsed = pygame.time.get_ticks() - tr["start"]
            if elapsed >= FADE_MS and not tr["switched"]:
                tr["switched"] = True
                if tr["next_state"] is not None:
                    self.state = tr["next_state"]
                if tr["on_switch"] is not None:
                    tr["on_switch"]()
            if elapsed >= FADE_MS * 2:
                self.transition = None

        if self.pending_seal_click is not None:
            elapsed = pygame.time.get_ticks() - self.pending_seal_click["start"]
            if elapsed >= SEAL_CLICK_DELAY_MS:
                pc = self.pending_seal_click
                self.pending_seal_click = None
                self.start_ink_burst(pc["pos"], pc["color"], pc["tea"])

        if self.poem_transition is not None:
            pt = self.poem_transition
            elapsed = pygame.time.get_ticks() - pt["start"]
            t1 = POEM_INK_EXPAND_MS
            t2 = t1 + POEM_HOLD_MS
            t3 = t2 + POEM_FADE_OUT_MS

            if elapsed >= t1 and not pt["entered"]:
                pt["entered"] = True
                self._enter_detail(pt["tea"])

            if elapsed >= t3:
                finished_tea = pt["tea"]
                self.poem_transition = None
                if (finished_tea["id"] == "qingming" and self.kite_image_raw is not None):
                    self.kite_anim = {"start": pygame.time.get_ticks(), "duration": 3200}

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

    def draw(self):
        self.screen.fill(PAPER)
        if self.state == STATE_INTRO:
            self.draw_intro()
        elif self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_SELECT:
            self.draw_select()
        elif self.state == STATE_DETAIL:
            self.draw_detail()
        elif self.state == STATE_GAME:
            self.draw_game()
        elif self.state == STATE_CHAT:
            self.draw_chat()

        if self.burst_active:
            self.draw_ink_burst()

        if self.state == STATE_DETAIL and self.pick_state == "ink":
            self.draw_pick_ink_animation()
        if self.state == STATE_DETAIL and self.pick_state == "popup":
            self.draw_tea_popup()

        self.draw_mode_hint()

        if self.state not in (STATE_INTRO, STATE_MENU, STATE_CHAT):
            self.draw_codex_button()
        self.draw_collect_toast()
        if self.show_codex:
            self.draw_codex()

        self.draw_status_message()

        if self.state not in (STATE_GAME, STATE_CHAT):
            self.screen.blit(self.border_overlay, (0, 0))

        if self.poem_transition is not None:
            self.draw_poem_transition()

        if self.show_exit_dialog:
            self.draw_exit_dialog()

        if self.transition is not None:
            self._draw_transition_overlay()

        if self.exiting:
            self.draw_exit_ink()

        if self.hand_mode:
            self.draw_camera_preview()
            self.draw_gesture_cursor()

        pygame.display.flip()