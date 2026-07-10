# file_name: game.py
"""
茶田种植小游戏（GameMixin）
"""

import random
import math

import pygame

from constants import *
from effects import InkSplash


class GameMixin:
    """负责“茶田种植”小游戏的交互逻辑与绘制。"""

    def start_game(self):
        self.state = STATE_GAME
        n = min(3, len(TEAS))
        chosen = random.sample(TEAS, n)

        pad = sx(34)
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
        # 备选框向下调整，与右下角“茗簿”按钮竖直对齐（中心对齐）
        y = CODEX_BTN_RECT.centery - chip_h // 2
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

    def _randomize_plot_tea(self, plot):
        candidates = [t for t in TEAS if t["id"] != plot["tea"]["id"]]
        if candidates:
            plot["tea"] = random.choice(candidates)

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
                self._randomize_plot_tea(plot)
                # 成功采茶入筐，标记“茶田种茶”项目已完成
                self.game_completed = True
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

        back = self.font_hint.render("← 返回目录", True, INK_SOFT)
        self.screen.blit(back, back.get_rect(midleft=(BACK_BTN_RECT.x, BACK_BTN_RECT.centery)))

        tip = "请按照节气种植茶叶"
        ts = self.font_subtitle.render(tip, True, INK)
        self.screen.blit(ts, ts.get_rect(center=(WIDTH // 2, sy(70))))

        for plot in self.game_plots:
            self._draw_plot(plot)

        self._draw_basket()

        for s in self.ink_splashes:
            s.draw(self.screen)

        self._draw_plant_toast()

        chips = self.game_chip_rects()
        mouse_pos = pygame.mouse.get_pos()
        if not chips:
            note = "还没有收集到茶叶，请先返回选择节气去采茶吧"
            ns = self.font_hint.render(note, True, INK_SOFT)
            self.screen.blit(ns, ns.get_rect(center=(WIDTH // 2, CODEX_BTN_RECT.centery)))
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

        if self.basket_collected:
            start_y = rect.top + sy(30)
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
        dot_y = rect.centery
        pygame.draw.circle(self.screen, tea["liquor"], (rect.x + sx(24), dot_y), sx(9))
        name = self.font_tea_name.render(tea["name"], True, INK)
        name_rect = name.get_rect(midleft=(rect.x + sx(42), dot_y))
        self.screen.blit(name, name_rect)
        if is_hover:
            underline_y = name_rect.bottom + sy(3)
            pygame.draw.line(self.screen, tea["accent_dark"],
                              (name_rect.left, underline_y), (name_rect.right, underline_y), 2)