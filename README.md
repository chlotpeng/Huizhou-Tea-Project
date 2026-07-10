# 徽州茶事 · 节气寻茶

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

“徽州茶事”是一款结合**传统节气文化**、**人工智能交互**与**大模型对话**的沉浸式应用。用户可以在水墨意境中通过手势交互，领略皖南名茶，并与虚拟“茶艺师”煮茶论道。

## 🛠️ 项目模块职责
- **`main.py`**: 程序总入口。负责 Windows 系统 DPI 适配并初始化 App。
- **`app.py`**: 应用核心调度器。管理主循环、状态机（路由）与各 Mixin 组件的渲染调度。
- **`hand_tracker.py`**: 基于 MediaPipe 的后台手势追踪线程。实时识别食指移动与捏合动作，为交互提供数据输入。
- **`chat.py`**: “茶话徽州”对话系统。通过 REST API 与本地 Ollama 大模型交互，实现茶文化问答。
- **`game.py`**: “茶田种植”小游戏逻辑。
- **`ui_screens.py`**: 界面视图层（首页、详情页、对话页、图鉴等）。
- **`interactions.py`**: 输入处理逻辑（鼠标与手势映射）。
- **`constants.py`**: 常量定义、屏幕适配工具、模型 API 配置。
- **`decor.py` / `effects.py`**: 水墨粒子系统与环境特效。

## 🚀 快速开始

### 1. 环境准备
确保安装 Python 3.8+，并在项目目录下执行：
```bash
pip install -r requirements.txt

2. 模型下载
你需要手势识别模型文件 hand_landmarker.task。在终端执行：

curl -L -o hand_landmarker.task [https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)

3. AI 茶艺师配置
本项目接入了本地 Ollama 模型，请确保已安装 Ollama 并拉取模型：

ollama pull qwen2.5:7b

4. 运行

python main.py

🎮 交互指南
手势交互：开启手势模式后，食指移动为光标，拇指食指捏合为点击，张开手掌向右挥动返回上一级。

AI 问答：进入“茶话徽州”界面，直接键入关于徽州茶文化的问题即可与茶童对话。

📸 运行截图
assets/demo


📜 许可证
本项目采用 MIT License。
