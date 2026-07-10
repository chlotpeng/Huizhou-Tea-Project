# file_name: decor.py
"""
动态装饰与徽派风景绘制（DecorMixin）
------------------------------------
包含：
  * 背景装饰元素（飘落的花瓣/茶叶、河面灯笼、点击水波纹）的生成与更新
  * 节气天气特效（谷雨细雨、清明细雨、霜降飞霜、立夏水墨花瓣）的粒子生成、
    更新与绘制
  * 徽派山水/村落/石桥/炊烟/流水等背景元素的绘制

这是一个 Mixin，需与 App 主类组合使用（App 依赖 self.screen / self.petals /
self.rain_particles 等在 App.__init__ 中创建的属性）。
"""

import math
import random

import pygame

from constants import *


class DecorMixin:
    """负责背景装饰粒子、节气天气特效、徽派风景的绘制逻辑。"""

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
    # 节气天气特效：谷雨细雨 / 霜降飞霜 / 立夏水墨花瓣
    # ------------------------------------------------------------------
    def _spawn_rain_particles(self, n):
        drops = []
        for _ in range(n):
            drops.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(0, HEIGHT),
                "spd": random.uniform(3.5, 6.5) * SCALE_Y,
                "len": random.uniform(10, 20) * SCALE_AVG,
                "drift": random.uniform(-0.6, -0.2) * SCALE_X,
            })
        return drops

    def _spawn_frost_particles(self, n):
        flakes = []
        for _ in range(n):
            flakes.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(-HEIGHT, 0),
                "spd": random.uniform(0.5, 1.4) * SCALE_Y,
                "sway": random.uniform(0.3, 1.0),
                "phase": random.uniform(0, math.tau),
                "size": random.uniform(2, 5) * SCALE_AVG,
                "alpha": random.uniform(90, 170),
            })
        return flakes

    def _spawn_lixia_petals(self, n):
        colors = [
            (196, 168, 176), (176, 190, 168), (200, 186, 150),
            (180, 172, 196), (198, 178, 158),
        ]
        petals = []
        for _ in range(n):
            petals.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(-HEIGHT, HEIGHT),
                "spd": random.uniform(0.4, 1.0) * SCALE_Y,
                "sway": random.uniform(0.5, 1.3),
                "phase": random.uniform(0, math.tau),
                "size": random.uniform(0.8, 1.6),
                "angle": random.uniform(0, 360),
                "spin": random.uniform(-1.2, 1.2),
                "color": random.choice(colors),
            })
        return petals

    def _update_weather_particles(self):
        for d in self.rain_particles:
            d["y"] += d["spd"]
            d["x"] += d["drift"]
            if d["y"] > HEIGHT:
                d["y"] = random.uniform(-40, 0)
                d["x"] = random.uniform(0, WIDTH)

        for f in self.frost_particles:
            f["y"] += f["spd"]
            f["x"] += math.sin(f["phase"] + f["y"] * 0.01) * f["sway"] * 0.4
            f["phase"] += 0.01
            if f["y"] > HEIGHT + 10:
                f["y"] = random.uniform(-60, -10)
                f["x"] = random.uniform(0, WIDTH)

        for p in self.lixia_petals:
            p["y"] += p["spd"]
            p["x"] += math.sin(p["phase"] + p["y"] * 0.008) * p["sway"] * 0.5
            p["phase"] += 0.008
            p["angle"] += p["spin"]
            if p["y"] > HEIGHT + 20:
                p["y"] = random.uniform(-HEIGHT * 0.3, -10)
                p["x"] = random.uniform(0, WIDTH)

    def _draw_rain_effect_detail(self):
        """谷雨节气：淅淅沥沥的小雨特效，覆盖在详情页上方，透明度/饱和度较原版提高约20%"""
        rain_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for d in self.rain_particles:
            x, y = d["x"], d["y"]
            length = d["len"]
            pygame.draw.line(rain_surf, (120, 150, 175, 132),
                              (x, y), (x + d["drift"] * 4, y + length), 1)
        self.screen.blit(rain_surf, (0, 0))

    def _draw_rain_effect_qingming(self):
        """清明节气：细雨纷纷，雨丝比谷雨更轻盈纤细，透明度在原基础上上调约5%"""
        rain_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        base_alpha = min(255, int(90 * 1.05))
        for d in self.rain_particles:
            x, y = d["x"], d["y"]
            length = d["len"] * 0.7
            pygame.draw.line(rain_surf, (150, 165, 185, base_alpha),
                              (x, y), (x + d["drift"] * 3, y + length), 1)
        self.screen.blit(rain_surf, (0, 0))

    def _draw_frost_effect_detail(self):
        """霜降节气：白色半透明的霜从屏幕上端飘落"""
        frost_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for f in self.frost_particles:
            a = min(255, int(f["alpha"] * 1.2 * 1.1))
            pygame.draw.circle(frost_surf, (255, 255, 255, a),
                                (int(f["x"]), int(f["y"])), max(1, int(f["size"])))
        self.screen.blit(frost_surf, (0, 0))

    def _draw_lixia_petals_effect(self):
        """立夏节气：低饱和度、半透明、水墨风格的多彩花瓣飘落"""
        petal_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for p in self.lixia_petals:
            w = max(4, int(sx(16) * p["size"]))
            h = max(3, int(sy(8) * p["size"]))
            leaf_s = pygame.Surface((w, h), pygame.SRCALPHA)
            base_color = p["color"]
            avg = sum(base_color) / 3
            boosted_color = tuple(
                max(0, min(255, int(avg + (c - avg) * 1.2))) for c in base_color
            )
            pygame.draw.ellipse(leaf_s, (*boosted_color, 114), (0, 0, w, h))
            rotated = pygame.transform.rotate(leaf_s, p["angle"])
            rect = rotated.get_rect(center=(int(p["x"]), int(p["y"])))
            petal_surf.blit(rotated, rect)
        self.screen.blit(petal_surf, (0, 0))

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
            rr = int(sx(6) + age * sx(70))
            a = max(0, int(190 * (1 - age)))
            ring = pygame.Surface((rr * 2 + 8, rr * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 255, 255, a), (rr + 4, rr + 4), rr, 4)
            inner_r = max(1, int(rr * 0.6))
            a2 = max(0, int(a * 0.6))
            pygame.draw.circle(ring, (255, 255, 255, a2), (rr + 4, rr + 4), inner_r, 3)
            self.screen.blit(ring, (rx - rr - 4, ry - rr - 4))

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