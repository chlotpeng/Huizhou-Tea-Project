# file_name: effects.py
"""
通用视觉特效
------------
目前只包含“水墨飞溅”特效 InkSplash：在采茶收集、种植入筐等动作发生时，
在指定位置炸开若干墨点并随时间淡出。与具体界面状态无关，可被多个模块复用。
"""

import math
import random

import pygame

from constants import SCALE_AVG

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