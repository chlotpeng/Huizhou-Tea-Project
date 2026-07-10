# file_name: constants.py
"""
常量与工具函数模块
"""

import pygame


WIDTH, HEIGHT = 1920, 1200
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
STATE_MENU = "menu"
STATE_SELECT = "select"
STATE_DETAIL = "detail"
STATE_CHAT = "chat"

TEAS = [
    {
        "id": "qingming", "term": "清明", "name": "黄山毛峰",
        "tagline": "明前嫩芽，形如雀舌",
        "accent": (124, 148, 115), "accent_dark": (91, 112, 82),
        "liquor": (217, 200, 120),
        "info": [("采摘", "清明前后采摘嫩芽"), ("工艺", "手工炒制，银毫显露"), ("汤色", "清澈微黄，香气清雅")],
        "weather": {"icon": "drizzle", "desc": "细雨纷纷"},
        "poem": "清明时节雨纷纷。路上行人欲断魂。",
    },
    {
        "id": "guyu", "term": "谷雨", "name": "六安瓜片",
        "tagline": "唯一无芽无梗的绿茶",
        "accent": (71, 86, 58), "accent_dark": (49, 63, 40),
        "liquor": (143, 166, 107),
        "info": [("采摘", "谷雨前后采摘"), ("工艺", "生锅、熟锅、拉火"), ("汤色", "绿亮清澈")],
        "weather": {"icon": "rain", "desc": "雨水渐多"},
        "poem": "谷雨春光晓，山川黛色青。",
    },
    {
        "id": "lixia", "term": "立夏", "name": "太平猴魁",
        "tagline": "两叶抱一芽，猴魁独有",
        "accent": (100, 130, 70), "accent_dark": (70, 90, 50),
        "liquor": (170, 180, 100),
        "info": [("采摘", "谷雨后采摘"), ("工艺", "传统捏尖工艺"), ("汤色", "兰香高爽")],
        "weather": {"icon": "sun", "desc": "日头渐烈"},
        "poem": "四时天气促相催，一夜薰风带暑来。",
    },
    {
        "id": "bailu", "term": "白露", "name": "祁门红茶",
        "tagline": "群芳最，红茶皇后",
        "accent": (169, 75, 56), "accent_dark": (124, 53, 39),
        "liquor": (193, 81, 46),
        "info": [("采摘", "秋季采摘"), ("工艺", "萎凋、揉捻、发酵"), ("汤色", "红艳明亮")],
        "weather": {"icon": "dew", "desc": "夜凉如水"},
        "poem": "露从今夜白，月是故乡明。",
    },
    {
        "id": "shuangjiang", "term": "霜降", "name": "老竹大方",
        "tagline": "板栗香浓，古法制茶",
        "accent": (120, 100, 70), "accent_dark": (80, 70, 50),
        "liquor": (180, 160, 90),
        "info": [("采摘", "秋末采摘"), ("工艺", "传统烘焙"), ("汤色", "黄亮醇厚")],
        "weather": {"icon": "frost", "desc": "寒气渐重"},
        "poem": "卷帘何事看新月，一夜霜寒木叶秋。",
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
# 与右下角“茗簿”左右对称的“茶话徽州”按钮（选择页 / 详情页 通用位置）
TEAHUA_BTN_RECT = pygame.Rect(sx(40), HEIGHT - sy(70), sx(160), sy(46))
# 茶田种茶界面：茶话徽州按钮移到最左下角，与右下角“茗簿”同一高度
GAME_TEAHUA_BTN_RECT = pygame.Rect(sx(40), HEIGHT - sy(70), sx(160), sy(46))
COLLECT_TOAST_MS = 1600

# ---- 目录（功能集合）界面 ----
MENU_BACK_BTN_RECT = pygame.Rect(sx(40), sy(16), sx(120), sy(30))
MENU_ITEM_LABELS = ["节气采茶", "茶田种茶", "煮茶论道", "散席辞归"]
MENU_ITEM_RECTS = [
    pygame.Rect(WIDTH // 2 - sx(240), sy(210) + i * sy(96), sx(480), sy(80))
    for i in range(4)
]

# ---- “散席辞归”退出确认弹窗（较原来小一号）----
_ED_W, _ED_H = sx(500), sy(240)
EXIT_DIALOG_RECT = pygame.Rect(WIDTH // 2 - _ED_W // 2, HEIGHT // 2 - _ED_H // 2, _ED_W, _ED_H)
_EDBTN_W, _EDBTN_H = sx(160), sy(50)
# 暂别山水（离开）在左，继续寻茶（留下）在右
EXIT_LEAVE_BTN_RECT = pygame.Rect(EXIT_DIALOG_RECT.centerx - sx(180),
                                  EXIT_DIALOG_RECT.bottom - sy(80), _EDBTN_W, _EDBTN_H)
EXIT_STAY_BTN_RECT = pygame.Rect(EXIT_DIALOG_RECT.centerx + sx(20),
                                 EXIT_DIALOG_RECT.bottom - sy(80), _EDBTN_W, _EDBTN_H)
# 水墨蔓延放慢：延长整体时长
EXIT_MS = 2800

CAM_PREVIEW_SIZE = (sx(160), sy(120))
CAM_PREVIEW_POS = (WIDTH - CAM_PREVIEW_SIZE[0] - sx(20), sy(20))
GESTURE_CURSOR_RADIUS = sx(14)
GESTURE_PINCH_COOLDOWN_MS = 500

BORDER_OVERLAY_ALPHA = 70
GROW_DURATION_MS = 5000

# ---- 茶话徽州 · 对话界面相关布局与本地大模型配置 ----
CHAT_BACK_BTN_RECT = pygame.Rect(sx(40), sy(16), sx(120), sy(30))
CHAT_INPUT_RECT = pygame.Rect(sx(120), HEIGHT - sy(100), WIDTH - sx(120) * 2 - sx(160), sy(60))
CHAT_SEND_BTN_RECT = pygame.Rect(WIDTH - sx(120) - sx(150), HEIGHT - sy(100), sx(150), sy(60))
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"

# ---- 手势“向右挥手”返回上一级 ----
GESTURE_SWIPE_COOLDOWN_MS = 1000
GESTURE_SWIPE_DISTANCE = sx(220)

BGM_PATH = "assets/雨打青瓦.mp3"
BGM_FADE_IN_MS = 4000
BGM_TARGET_VOLUME = 0.55

PAGE_SOUND_PATH = "assets/翻页声.mp3"
PAGE_SOUND_VOLUME = 0.35

CLICK_SOUND_PATH = "assets/点击.mp3"
CLICK_SOUND_VOLUME = 0.20

# ---- 弹窗“水雾”动画时长 ----
MIST_OPEN_MS = 420
MIST_CLOSE_MS = 380
# ---- 节气卡片“果冻”动画 ----
SEAL_HOVER_SCALE = 1.16
SEAL_EASE = 0.22
SEAL_CLICK_DELAY_MS = 260

# ---- 页面之间的淡入淡出转场 ----
FADE_MS = 420

# ---- 点击节气标签后：水墨蒙版扩散 + 诗句 的时序 ----
POEM_INK_EXPAND_MS = 750
POEM_HOLD_MS = 2000
POEM_FADE_OUT_MS = 750


def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for ch in text:
        if ch == "\n":
            lines.append(current)
            current = ""
            continue
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


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)