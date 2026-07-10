# file_name: chat.py
"""
茶话徽州 · 水墨对话界面（ChatMixin）
"""

import json
import threading
import urllib.request

import pygame

from constants import *


class ChatMixin:
    """负责“茶话徽州”水墨对话界面的交互与绘制，及本地大模型的调用。"""

    def enter_chat(self):
        self.state = STATE_CHAT
        self.chat_stick_bottom = True
        self.chat_visited = True
        try:
            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(CHAT_INPUT_RECT)
        except Exception:
            pass
        if not self.chat_messages:
            self._chat_greeting()

    def _chat_greeting(self):
        with self._chat_lock:
            self.chat_messages.append((
                "assistant",
                "客官请坐，奉上一盏新茶。我乃徽州茶童，"
                "清明毛峰、谷雨瓜片、立夏猴魁、白露祁红、霜降大方，"
                "皖南名茶与茶事典故，皆可与你细说。",
            ))

    def _chat_back_label(self):
        origin = getattr(self, "chat_origin", STATE_SELECT)
        if origin == STATE_GAME:
            return "← 返回茶田"
        if origin == STATE_MENU:
            return "← 返回目录"
        return "← 返回节气"

    def exit_chat(self):
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass
        origin = getattr(self, "chat_origin", STATE_SELECT)
        self.start_transition(origin)
        self.play_page_sound()

    # ------------------------------------------------------------------
    # 输入与发送
    # ------------------------------------------------------------------
    def handle_chat_key(self, event):
        # 文本录入交由 TEXTINPUT 事件处理（支持中文/IME），这里只处理控制键
        if event.key == pygame.K_RETURN:
            self.chat_send()
        elif event.key == pygame.K_BACKSPACE:
            self.chat_input = self.chat_input[:-1]

    def handle_chat_scroll(self, dy):
        """鼠标滚轮：向上滚查看历史，向下滚回到底部"""
        self.chat_scroll -= dy * sy(40)
        self.chat_stick_bottom = False
        if self.chat_scroll < 0:
            self.chat_scroll = 0

    def chat_send(self):
        text = self.chat_input.strip()
        if not text or self.chat_pending:
            return
        with self._chat_lock:
            self.chat_messages.append(("user", text))
            self.chat_pending = True
        self.chat_input = ""
        self.chat_stick_bottom = True

        history = [{"role": r, "content": c} for r, c in self.chat_messages]
        threading.Thread(target=self._chat_worker, args=(history,), daemon=True).start()

    def _chat_worker(self, history):
        system = {
            "role": "system",
            "content": (
                "你是一位精通徽州（皖南）茶文化的雅士茶童，谈吐文雅、简洁亲切，"
                "熟悉黄山毛峰、六安瓜片、太平猴魁、祁门红茶、老竹大方等安徽名茶，"
                "以及二十四节气与徽州风物。请用简体中文回答，篇幅不宜过长。"
            ),
        }
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [system] + history,
            "stream": False,
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                OLLAMA_URL, data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            reply = (result.get("message", {}) or {}).get("content", "").strip()
            if not reply:
                reply = "（茶友一时无言，请再问一句。）"
        except Exception as e:
            reply = f"（无法连接本地模型 qwen2.5:7b，请确认 ollama 已在运行：{e}）"

        with self._chat_lock:
            self.chat_messages.append(("assistant", reply))
            self.chat_pending = False
        self.chat_stick_bottom = True

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def draw_chat(self):
        if not self.chat_messages:
            self._chat_greeting()

        self._draw_horizon_wash((240, 234, 223), (247, 242, 231), 0, HEIGHT)
        wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._draw_ink_blot(wash, sx(200), sy(220), sx(120), (120, 130, 120), 90)
        self._draw_ink_blot(wash, sx(820), sy(180), sx(150), (110, 120, 118), 80)
        self.screen.blit(wash, (0, 0))
        self._draw_petals()

        title = self.font_heading.render("茶话徽州", True, INK)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, sy(58))))

        is_back = CHAT_BACK_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        bc = SEAL_RED if is_back else INK_SOFT
        bs = self.font_hint.render(self._chat_back_label(), True, bc)
        br = bs.get_rect(midleft=(CHAT_BACK_BTN_RECT.x, CHAT_BACK_BTN_RECT.centery))
        self.screen.blit(bs, br)
        if is_back:
            pygame.draw.line(self.screen, bc, (br.left, br.bottom + 2), (br.right, br.bottom + 2), 1)

        area = pygame.Rect(sx(120), sy(130), WIDTH - sx(240), HEIGHT - sy(130) - sy(130))
        panel = pygame.Surface(area.size, pygame.SRCALPHA)
        panel.fill((255, 255, 255, 70))
        self.screen.blit(panel, area.topleft)
        pygame.draw.rect(self.screen, INK_SOFT, area, width=2, border_radius=10)

        max_w = area.width - sx(40)

        total_h = 0
        for role, text in self.chat_messages:
            total_h += sy(26)
            total_h += sy(26) * len(wrap_text(text, self.font_body, max_w))
            total_h += sy(12)
        if self.chat_pending:
            total_h += sy(26)

        view_h = area.height - sy(32)
        max_scroll = max(0, total_h - view_h)
        if self.chat_stick_bottom:
            self.chat_scroll = max_scroll
        else:
            self.chat_scroll = max(0, min(self.chat_scroll, max_scroll))
            if self.chat_scroll >= max_scroll:
                self.chat_stick_bottom = True

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        y = area.top + sy(16) - self.chat_scroll
        for role, text in self.chat_messages:
            if role == "user":
                name, name_color = "我", INK
            else:
                name, name_color = "茶友", SEAL_RED
            header = self.font_body.render(name, True, name_color)
            self.screen.blit(header, (area.left + sx(20), y))
            y += sy(26)
            for line in wrap_text(text, self.font_body, max_w):
                ls = self.font_body.render(line, True, INK)
                self.screen.blit(ls, (area.left + sx(20), y))
                y += sy(26)
            y += sy(12)
        if self.chat_pending:
            dots = "。" * (1 + (pygame.time.get_ticks() // 400) % 3)
            ps = self.font_body.render("茶友正在斟茶思量" + dots, True, INK_SOFT)
            self.screen.blit(ps, (area.left + sx(20), y))
        self.screen.set_clip(prev_clip)

        input_rect = CHAT_INPUT_RECT
        pygame.draw.rect(self.screen, PAPER, input_rect, border_radius=8)
        pygame.draw.rect(self.screen, INK_SOFT, input_rect, width=2, border_radius=8)
        if self.chat_input:
            shown = self.chat_input
            col = INK
        else:
            shown = "在此题字，与茶友对话……"
            col = INK_SOFT
        cursor = "｜" if (self.chat_input and (pygame.time.get_ticks() // 500) % 2 == 0) else ""
        ts = self.font_body.render(shown + cursor, True, col)
        avail = input_rect.width - sx(28)
        if ts.get_width() > avail:
            self.screen.set_clip(input_rect.inflate(-sx(16), 0))
        self.screen.blit(ts, (input_rect.x + sx(14), input_rect.centery - ts.get_height() // 2))
        self.screen.set_clip(prev_clip)

        is_send = CHAT_SEND_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        sc = SEAL_RED if is_send else INK
        ss = self.font_subtitle.render("寄语", True, sc)
        sr = ss.get_rect(center=CHAT_SEND_BTN_RECT.center)
        self.screen.blit(ss, sr)
        if is_send:
            pygame.draw.line(self.screen, sc, (sr.left, sr.bottom + 3), (sr.right, sr.bottom + 3), 2)