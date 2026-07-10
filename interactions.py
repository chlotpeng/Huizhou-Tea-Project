# file_name: interactions.py
"""
用户输入与手势交互（InteractionMixin）
"""

import math

import pygame

from constants import *

try:
    import cv2
except Exception:
    cv2 = None


class InteractionMixin:
    """负责鼠标点击/移动、弹窗开合、以及摄像头手势交互的处理逻辑。"""

    def toggle_hand_mode(self):
        if self.hand_mode:
            self.hand_mode = False
            self.show_status("已切换回鼠标模式", 1500)
            return

        try:
            self.hand_tracker.start()
        except Exception:
            pass

        self.hand_mode = True

        if self.hand_tracker.error_message and not self.hand_tracker.available:
            self.show_status(self.hand_tracker.error_message or "手势控制初始化中…", 3000)
        else:
            self.show_status("手势模式已开启：食指移动，拇指食指捏合来点击，张开手掌向右挥动可返回上一级", 3200)

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

    # ------------------------------------------------------------------
    # 目录
    # ------------------------------------------------------------------
    def visible_menu_items(self):
        """返回 [(action_id, rect), ...]
        action_id: 0 节气采茶 / 1 茶田种茶 / 2 煮茶论道 / 3 散席辞归"""
        ids = [0, 1, 2, 3]
        return [(aid, MENU_ITEM_RECTS[idx]) for idx, aid in enumerate(ids)]

    # ------------------------------------------------------------------
    # 手势“向右挥手”返回上一级
    # ------------------------------------------------------------------
    def _trigger_back_swipe(self):
        if self.transition is not None or self.poem_transition is not None:
            return
        if self.state == STATE_SELECT:
            self.start_transition(STATE_MENU)
            self.play_page_sound()
        elif self.state == STATE_DETAIL:
            if self.pick_state != "idle":
                return
            self.start_transition(
                STATE_SELECT, on_switch=lambda: setattr(self, "active_info_index", None)
            )
            self.play_page_sound()
        elif self.state == STATE_GAME:
            self.start_transition(STATE_MENU)
            self.play_page_sound()
        elif self.state == STATE_CHAT:
            self.exit_chat()
        elif self.state == STATE_MENU:
            self.start_transition(STATE_INTRO)
            self.play_page_sound()

    def handle_click(self, pos):
        if self.exiting:
            return

        # “散席辞归”确认弹窗优先处理
        if self.show_exit_dialog:
            if EXIT_LEAVE_BTN_RECT.collidepoint(pos):
                self.start_exit()
            elif EXIT_STAY_BTN_RECT.collidepoint(pos):
                self.show_exit_dialog = False
            return

        if self.transition is not None:
            return

        if self.state == STATE_CHAT:
            if CHAT_BACK_BTN_RECT.collidepoint(pos):
                self.exit_chat()
                return
            if CHAT_SEND_BTN_RECT.collidepoint(pos):
                self.chat_send()
                return
            return

        if self.show_codex:
            self.request_close_codex()
            return
        if self.state not in (STATE_INTRO, STATE_MENU) and CODEX_BTN_RECT.collidepoint(pos):
            self.open_codex()
            return

        if self.poem_transition is not None:
            return

        if self.state == STATE_INTRO:
            self.start_transition(STATE_MENU)
            self.play_page_sound()

        elif self.state == STATE_MENU:
            if MENU_BACK_BTN_RECT.collidepoint(pos):
                self.start_transition(STATE_INTRO)
                self.play_page_sound()
                return
            for i, rect in self.visible_menu_items():
                if rect.collidepoint(pos):
                    if i == 0:      # 节气采茶
                        self.start_transition(STATE_SELECT)
                        self.play_page_sound()
                    elif i == 1:    # 茶田种茶
                        self.start_transition(STATE_GAME, on_switch=self.start_game)
                        self.play_page_sound()
                    elif i == 2:    # 煮茶论道
                        self.chat_origin = STATE_MENU
                        self.start_transition(STATE_CHAT, on_switch=self.enter_chat)
                        self.play_page_sound()
                    elif i == 3:    # 散席辞归
                        self.open_exit_dialog()
                    return

        elif self.state == STATE_SELECT:
            if SELECT_BACK_BTN_RECT.collidepoint(pos):
                self.start_transition(STATE_MENU)
                self.play_page_sound()
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
                self.start_transition(STATE_MENU)
                self.play_page_sound()
                return
            self.game_grab(pos)

        elif self.state == STATE_DETAIL:
            if self.pick_state == "popup":
                self.request_close_popup()
                return
            if self.pick_state == "ink":
                return
            if BACK_BTN_RECT.collidepoint(pos):
                self.start_transition(
                    STATE_SELECT,
                    on_switch=lambda: setattr(self, "active_info_index", None),
                )
                self.play_page_sound()
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
        self.visited.add(tea["id"])
        self.poem_transition = {
            "tea": tea, "pos": pos, "start": pygame.time.get_ticks(),
            "color": tea["accent_dark"], "entered": False,
        }

    def _enter_detail(self, tea):
        self.selected_tea = tea
        self.active_info_index = None
        self.state = STATE_DETAIL
        self.play_page_sound()
        self.kite_anim = None

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

    # ------------------------------------------------------------------
    # 手势追踪
    # ------------------------------------------------------------------
    def update_hand_tracking(self):
        state = self.hand_tracker.get_state()
        now = pygame.time.get_ticks()

        if not state["hand_present"]:
            self.gesture_pinch_prev = False
            self._swipe_history = []
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

        open_palm = bool(state.get("open_palm", False))

        self.handle_motion((px, py))

        # ---- 张开手掌快速向右挥动 = 返回上一级 ----
        self._swipe_history.append((now, raw_px, open_palm))
        self._swipe_history = [h for h in self._swipe_history if now - h[0] < 400]
        if len(self._swipe_history) >= 3:
            xs = [h[1] for h in self._swipe_history]
            opens = [h[2] for h in self._swipe_history]
            if all(opens[-3:]) and (xs[-1] - xs[0]) > GESTURE_SWIPE_DISTANCE and \
                    (now - self.gesture_last_swipe_tick) > GESTURE_SWIPE_COOLDOWN_MS:
                self.gesture_last_swipe_tick = now
                self.play_click_sound()
                self._trigger_back_swipe()
                self._swipe_history = []
                self.camera_preview_surf = self._build_camera_preview(state["frame_rgb"])
                return

        just_pinched = state["pinch"] and not self.gesture_pinch_prev
        cooldown_ok = (now - self.gesture_last_click_tick) > GESTURE_PINCH_COOLDOWN_MS

        if self.state == STATE_GAME:
            if BACK_BTN_RECT.collidepoint((px, py)) and just_pinched:
                self.play_click_sound()
                self.start_transition(STATE_MENU)
                self.play_page_sound()
            elif state["pinch"] and not self.gesture_pinch_prev:
                self.play_click_sound()
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
            self.play_click_sound()
            if self.show_codex:
                self.request_close_codex()
            elif self.state not in (STATE_INTRO, STATE_MENU) and CODEX_BTN_RECT.collidepoint((px, py)):
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