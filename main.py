# file_name: main.py
"""
徽州茶事 · 节气寻茶
一个用 Pygame 制作的交互小程序：
跟随清明 / 谷雨 / 立夏 / 白露 / 霜降五个节气，认识对应的安徽名茶，
并在“茶田种植”小游戏中把收集到的茶叶种下、等待生长、再把长成的枝条采入竹筐。

运行方式：
    pip install pygame
    python main.py

本文件是程序入口，只负责：
    1. Windows 下的高 DPI 适配（需在创建窗口前设置）
    2. 导入并启动 App
其余功能已按模块拆分至同目录下的：
    constants.py     常量、缩放函数、配色、节气/茶叶数据、通用小工具
    effects.py        通用视觉特效（水墨飞溅 InkSplash）
    interactions.py   鼠标点击/移动、弹窗开合、手势交互（InteractionMixin）
    game.py           “茶田种植”小游戏（GameMixin）
    ui_screens.py      首页/选择页/详情页/图鉴/采茶弹窗界面（UIMixin）
    decor.py           背景装饰、节气天气特效、徽派风景绘制（DecorMixin）
    app.py             组合以上 Mixin 的 App 主类（初始化、主循环、事件分发）
"""

import sys

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from app import App

if __name__ == "__main__":
    App().run()