"""
hand_tracker.py
基于 MediaPipe Hand Landmarker 的手势追踪模块。

在后台线程里持续读取摄像头画面、运行手部关键点检测，
主线程（pygame 主循环）只需要调用 get_state() 读取最新结果，
不会被摄像头读取或模型推理的速度拖慢游戏画面的帧率。

使用前需要先下载模型文件 hand_landmarker.task，放在本文件同一目录下：
    https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

也可以直接在终端里用下面的命令下载（Windows PowerShell / Mac / Linux 都可以）：
    curl -L -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
"""

import os
import threading
import time

try:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    _IMPORT_OK = True
    _IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - 环境缺依赖时的兜底
    _IMPORT_OK = False
    _IMPORT_ERROR = exc

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

# MediaPipe 21 个手部关键点里，我们用得到的几个下标
WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_MCP = 9  # 用来估计手掌尺寸，做“捏合距离”的相对阈值，避免离摄像头远近导致误判
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

PINCH_RATIO_THRESHOLD = 0.4  # (拇指食指距离 / 手掌参考距离) 小于这个比例，判定为“捏合”
OPEN_PALM_RATIO_THRESHOLD = 1.7  # 五指尖到手腕的平均距离 / 手掌参考距离，大于该比例判定为“张开手掌”


def _dist2d(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


class HandTracker:
    """
    后台线程持续追踪一只手的位置、“捏合”手势与“张开手掌”手势。

    典型用法：
        tracker = HandTracker()
        tracker.start()
        ...
        state = tracker.get_state()
        if state["hand_present"]:
            x, y = state["cursor"]  # 归一化坐标 (0~1)，已做镜像翻转，可直接乘屏幕宽高
            if state["pinch"]:
                ...
            if state["open_palm"]:
                ...
        tracker.stop()
    """

    def __init__(self, camera_index=0):
        self.available = False
        self.error_message = None

        if not _IMPORT_OK:
            self.error_message = f"未安装 mediapipe / opencv-python：{_IMPORT_ERROR}"
            return
        if not os.path.exists(MODEL_PATH):
            self.error_message = (
                f"找不到模型文件 {os.path.basename(MODEL_PATH)}，"
                "请参考本文件顶部注释下载后放到同一目录下。"
            )
            return

        self._lock = threading.Lock()
        self._latest = {
            "hand_present": False,
            "cursor": (0.5, 0.5),   # 归一化坐标 (0~1)
            "pinch": False,
            "open_palm": False,
            "frame_rgb": None,      # 给摄像头小窗口预览用，没有则为 None
        }
        self._running = False
        self._thread = None
        self._camera_index = camera_index

        try:
            base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
            options = mp_vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
            self.available = True
        except Exception as exc:
            self.error_message = f"初始化 HandLandmarker 失败：{exc}"

    def start(self):
        """启动后台摄像头 + 追踪线程。重复调用是安全的。"""
        if not self.available or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def get_state(self):
        """线程安全地读取最新一帧的追踪结果。"""
        if not self.available:
            return {
                "hand_present": False, "cursor": (0.5, 0.5),
                "pinch": False, "open_palm": False, "frame_rgb": None,
            }
        with self._lock:
            return dict(self._latest)

    def _run_loop(self):
        cap = cv2.VideoCapture(self._camera_index)
        if not cap.isOpened():
            self.error_message = "打不开摄像头，手势控制不可用，仍可以用鼠标操作。"
            self._running = False
            return

        start_time = time.time()
        while self._running:
            ok, frame = cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)  # 左右镜像，符合“对着屏幕比划”的直觉
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            timestamp_ms = int((time.time() - start_time) * 1000)

            result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

            hand_present = False
            cursor = (0.5, 0.5)
            pinch = False
            open_palm = False

            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]
                hand_present = True

                index_tip = landmarks[INDEX_TIP]
                cursor = (index_tip.x, index_tip.y)

                thumb_tip = landmarks[THUMB_TIP]
                wrist = landmarks[WRIST]
                middle_mcp = landmarks[MIDDLE_MCP]

                pinch_dist = _dist2d(thumb_tip, index_tip)
                palm_ref = _dist2d(wrist, middle_mcp) or 1e-6
                pinch = (pinch_dist / palm_ref) < PINCH_RATIO_THRESHOLD

                tips = [landmarks[i] for i in (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)]
                avg_tip_dist = sum(_dist2d(t, wrist) for t in tips) / len(tips)
                open_palm = (avg_tip_dist / palm_ref) > OPEN_PALM_RATIO_THRESHOLD and not pinch

            with self._lock:
                self._latest["hand_present"] = hand_present
                self._latest["cursor"] = cursor
                self._latest["pinch"] = pinch
                self._latest["open_palm"] = open_palm
                self._latest["frame_rgb"] = frame_rgb

        cap.release()