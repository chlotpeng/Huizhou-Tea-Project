# file_name: ui_screens.py
"""
主要界面绘制（UIMixin）
"""

import math

import pygame

from constants import *

class UIMixin:
    """负责首页 / 目录 / 选择页 / 详情页 / 图鉴弹窗 / 采茶弹窗 / 茶语寄情等界面的绘制。"""

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
        surf = self.font_collect_toast.render(self.collect_toast_text, True, SEAL_RED)
        surf.set_alpha(max(0, alpha))
        rect = surf.get_rect(center=(WIDTH // 2, sy(90) - rise))
        bg = pygame.Surface((rect.width + 24, rect.height + 12), pygame.SRCALPHA)
        bg.fill((242, 236, 224, min(210, alpha)))
        self.screen.blit(bg, (rect.x - 12, rect.y - 6))
        self.screen.blit(surf, rect)

    # ------------------------------------------------------------------
    # 散席辞归：退出确认弹窗 + 水墨蔓延退出动画
    # ------------------------------------------------------------------
    def draw_exit_dialog(self):
        now = pygame.time.get_ticks()
        t = min(1.0, (now - self.exit_dialog_start) / MIST_OPEN_MS)
        e = ease_out_cubic(t)
        alpha = int(255 * e)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 28, 24, int(150 * e)))
        self.screen.blit(overlay, (0, 0))

        card = EXIT_DIALOG_RECT
        card_surf = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (*PAPER, alpha), card_surf.get_rect(), border_radius=12)
        pygame.draw.rect(card_surf, (*SEAL_RED, alpha), card_surf.get_rect(), width=3, border_radius=12)
        self.screen.blit(card_surf, card.topleft)

        # 标题、正文均小一号
        title = self.font_popup.render("散席辞归", True, INK)
        title.set_alpha(alpha)
        self.screen.blit(title, title.get_rect(center=(card.centerx, card.top + sy(48))))

        text = self.font_body.render("山中清幽，再品一盏如何？", True, INK_SOFT)
        text.set_alpha(alpha)
        self.screen.blit(text, text.get_rect(center=(card.centerx, card.top + sy(110))))

        # 选项：只保留文字，无外边框；悬浮变红并显示下划线
        mouse = pygame.mouse.get_pos()
        for rect, label in ((EXIT_LEAVE_BTN_RECT, "暂别山水"),
                            (EXIT_STAY_BTN_RECT, "继续寻茶")):
            hover = rect.collidepoint(mouse)
            col = SEAL_RED if hover else INK
            ls = self.font_body.render(label, True, col)
            lr = ls.get_rect(center=rect.center)
            self.screen.blit(ls, lr)
            if hover:
                uy = lr.bottom + sy(3)
                pygame.draw.line(self.screen, col, (lr.left, uy), (lr.right, uy), 2)

    def draw_exit_ink(self):
        """归隐山水后的水墨蔓延：与节气标签点击后的水墨晕染过程一致
        （相同的缓动函数与整屏覆盖方式，只是持续时间更长、且不会淡出）。"""
        now = pygame.time.get_ticks()
        elapsed = now - self.exit_start
        progress = min(1.0, elapsed / EXIT_MS)
        max_r = int(math.hypot(WIDTH, HEIGHT))
        radius = int(ease_in_out(progress) * max_r)
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(255 * ease_in_out(progress))
        pygame.draw.circle(surf, (*self.exit_ink_color, alpha), self.exit_ink_origin, max(1, radius))
        self.screen.blit(surf, (0, 0))

    def _mist_alpha_scale(self, open_start, closing, close_start):
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

    # ------------------------------------------------------------------
    # 功能目录界面
    # ------------------------------------------------------------------
    def draw_menu(self):
        self._draw_horizon_wash((240, 234, 223), (247, 242, 231), 0, sy(430))
        mountain = [
            (0, sy(400)), (sx(200), sy(320)), (sx(430), sy(390)), (sx(660), sy(320)),
            (sx(880), sy(390)), (WIDTH, sy(330)), (WIDTH, sy(430)), (0, sy(430)),
        ]
        pygame.draw.polygon(self.screen, (204, 208, 198), mountain)
        self._draw_water(sy(600))
        self._draw_petals()

        is_back_hover = MENU_BACK_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        back_color = SEAL_RED if is_back_hover else INK_SOFT
        back_surf = self.font_hint.render("← 返回首页", True, back_color)
        back_rect = back_surf.get_rect(midleft=(MENU_BACK_BTN_RECT.x, MENU_BACK_BTN_RECT.centery))
        self.screen.blit(back_surf, back_rect)
        if is_back_hover:
            pygame.draw.line(self.screen, back_color,
                              (back_rect.left, back_rect.bottom + 2), (back_rect.right, back_rect.bottom + 2), 1)

        heading = self.font_heading.render("茶事 · 功能目录", True, INK)
        self.screen.blit(heading, heading.get_rect(center=(WIDTH // 2, sy(150))))

        mouse_pos = pygame.mouse.get_pos()
        for i, rect in self.visible_menu_items():
            label = MENU_ITEM_LABELS[i]
            is_hover = rect.collidepoint(mouse_pos)
            color = SEAL_RED if is_hover else INK
            txt = self.font_subtitle.render(label, True, color)
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)
            if is_hover:
                uy = txt_rect.bottom + sy(4)
                pygame.draw.line(self.screen, color, (txt_rect.left, uy), (txt_rect.right, uy), 2)

    def draw_select(self):
        self._draw_horizon_wash((240, 234, 223), (247, 242, 231), 0, sy(430))
        mountain = [
            (0, sy(400)), (sx(200), sy(320)), (sx(430), sy(390)), (sx(660), sy(320)),
            (sx(880), sy(390)), (WIDTH, sy(330)), (WIDTH, sy(430)), (0, sy(430)),
        ]
        pygame.draw.polygon(self.screen, (204, 208, 198), mountain)
        self._draw_water(sy(560))
        self._draw_petals()

        is_back_hover = SELECT_BACK_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        back_color = SEAL_RED if is_back_hover else INK_SOFT
        back_surf = self.font_hint.render("← 返回目录", True, back_color)
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

        if tea["id"] == "guyu":
            self._draw_rain_effect_detail()
        elif tea["id"] == "shuangjiang":
            self._draw_frost_effect_detail()
        elif tea["id"] == "lixia":
            self._draw_lixia_petals_effect()
        elif tea["id"] == "qingming":
            self._draw_rain_effect_qingming()
            self._draw_kite_effect()

    def draw_poem_transition(self):
        pt = self.poem_transition
        now = pygame.time.get_ticks()
        elapsed = now - pt["start"]

        t1 = POEM_INK_EXPAND_MS
        t2 = t1 + POEM_HOLD_MS
        t3 = t2 + POEM_FADE_OUT_MS

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        if elapsed < t1:
            cover_t = min(1.0, elapsed / POEM_INK_EXPAND_MS)
            mask_alpha = int(255 * ease_in_out(cover_t))
            overlay.fill((*pt["color"], mask_alpha))
        elif elapsed < t2:
            overlay.fill((*pt["color"], 255))
        else:
            fade_t = min(1.0, (elapsed - t2) / POEM_FADE_OUT_MS)
            mask_alpha = int(255 * (1 - ease_in_out(fade_t)))
            overlay.fill((*pt["color"], max(0, mask_alpha)))

        self.screen.blit(overlay, (0, 0))

        if elapsed < t3:
            fade_in_ms = 350
            if elapsed < t1:
                text_alpha = 0
            elif elapsed < t1 + fade_in_ms:
                hold_elapsed = elapsed - t1
                text_alpha = int(255 * ease_out_cubic(hold_elapsed / fade_in_ms))
            elif elapsed < t2:
                text_alpha = 255
            else:
                fade_t = min(1.0, (elapsed - t2) / POEM_FADE_OUT_MS)
                text_alpha = int(255 * (1 - ease_in_out(fade_t)))

            poem = pt["tea"].get("poem", "")
            if poem and text_alpha > 0:
                poem_surf = self.font_poem.render(poem, True, (255, 255, 255))
                poem_surf.set_alpha(max(0, text_alpha))
                poem_rect = poem_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                self.screen.blit(poem_surf, poem_rect)

                term_surf = self.font_subtitle.render(pt["tea"]["term"], True, (255, 255, 255))
                term_surf.set_alpha(max(0, int(text_alpha * 0.85)))
                self.screen.blit(term_surf, term_surf.get_rect(center=(WIDTH // 2, poem_rect.top - sy(36))))

    def _draw_kite_effect(self):
        if self.kite_anim is None or self.kite_image_raw is None:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.kite_anim["start"]
        duration = self.kite_anim["duration"]
        if elapsed > duration:
            self.kite_anim = None
            return

        t = elapsed / duration
        e = t

        start_pos = (sx(-60), HEIGHT + sy(40))
        end_pos = (WIDTH + sx(80), sy(-100))

        x = start_pos[0] + (end_pos[0] - start_pos[0]) * e
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * e
        arc = -math.sin(e * math.pi) * sy(160)
        y += arc

        angle = -35 + math.sin(e * math.pi) * 20

        kite_w = sx(130)
        kite_h = int(kite_w * self.kite_image_raw.get_height() / max(1, self.kite_image_raw.get_width()))
        kite_scaled = pygame.transform.smoothscale(self.kite_image_raw, (kite_w, kite_h))
        kite_rotated = pygame.transform.rotate(kite_scaled, angle)
        rect = kite_rotated.get_rect(center=(int(x), int(y)))

        fade_edge = 0.08
        if e < fade_edge:
            alpha = int(255 * (e / fade_edge))
        elif e > 1 - fade_edge:
            alpha = int(255 * ((1 - e) / fade_edge))
        else:
            alpha = 255
        kite_rotated.set_alpha(max(0, min(255, alpha)))

        self.screen.blit(kite_rotated, rect.topleft)

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

        collected_surf = self.font_popup_collected.render(f"已收集 {tea['name']}", True, tea["accent_dark"])
        collected_surf.set_alpha(alpha)
        card_surf.blit(collected_surf, collected_surf.get_rect(midtop=(card_w // 2, sy(14))))

        big_img = pygame.transform.smoothscale(self.tea_popup_images[tea["id"]],
                                                (int(sx(360) * scale), int(sy(360) * scale)))
        big_img.set_alpha(alpha)
        img_rect = big_img.get_rect(midtop=(card_w // 2, sy(42)))
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