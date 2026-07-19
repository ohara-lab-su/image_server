"""OpenCVを使用したローカル画像取得制御。"""

import threading
import time
from typing import Any, Dict, Optional

import cv2


class ImageStreamDeviceClass:
    """gRPCに依存しないOpenCVカメラ制御クラス。"""

    def __init__(
        self,
        camera_id=0,
        interval_sec=0.03,
        width=None,
        height=None,
        fps=None,
        backend=None,
        reconnect_interval_sec=1.0,
        logger=None,
    ):
        # type: (int, float, Optional[int], Optional[int], Optional[float], Optional[int], float, Optional[Any]) -> None
        self._logger = logger
        self._camera_id = int(camera_id)
        self._interval_sec = max(0.001, float(interval_sec))
        self._width = self._optional_positive_int(width)
        self._height = self._optional_positive_int(height)
        self._fps = self._optional_positive_float(fps)
        self._backend = backend
        self._reconnect_interval_sec = max(0.1, float(reconnect_interval_sec))

        self._capture = None  # type: Optional[cv2.VideoCapture]
        self._thread = None  # type: Optional[threading.Thread]
        self._stop_event = threading.Event()
        self._capture_lock = threading.RLock()
        self._frame_lock = threading.RLock()

        self._running = False
        self._frame_id = 0
        self._read_error_count = 0
        self._last_error = None  # type: Optional[str]
        self._last_frame_time_ns = None  # type: Optional[int]
        self._latest_frame = None
        self._started_time_ns = None  # type: Optional[int]

    def connect(self):
        # type: () -> bool
        """カメラを開き、ローカル画像取得ループを開始する。"""
        with self._capture_lock:
            if self._capture is None or not self._capture.isOpened():
                if not self._open_capture_unlocked():
                    return False

        return self.start_capture()

    def disconnect(self):
        # type: () -> bool
        """画像取得ループを停止し、カメラを解放する。"""
        self.stop_capture()
        with self._capture_lock:
            self._release_capture_unlocked()
        self._log("info", "camera disconnected")
        return True

    def is_connected(self):
        # type: () -> bool
        """カメラが開かれているかを返す。"""
        with self._capture_lock:
            if self._capture is None:
                return False
            return bool(self._capture.isOpened())

    def start_capture(self):
        # type: () -> bool
        """ローカル画像取得スレッドを開始する。"""
        if self._running:
            return True

        with self._capture_lock:
            if self._capture is None or not self._capture.isOpened():
                if not self._open_capture_unlocked():
                    return False

        self._stop_event.clear()
        self._running = True
        self._started_time_ns = self._time_ns()
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="ImageStreamDeviceClass",
        )
        self._thread.daemon = True
        self._thread.start()
        self._log("info", "local image capture started")
        return True

    def stop_capture(self):
        # type: () -> bool
        """ローカル画像取得スレッドを停止する。"""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            if thread is not threading.current_thread():
                thread.join(3.0)
        self._thread = None
        self._running = False
        self._log("info", "local image capture stopped")
        return True

    def read_once(self):
        # type: () -> Any
        """カメラから画像を1枚同期取得する。"""
        if not self.is_connected():
            with self._capture_lock:
                if not self._open_capture_unlocked():
                    raise RuntimeError(str(self._last_error))
        return self._read_frame()

    def get_latest_frame(self, copy_frame=True):
        # type: (bool) -> Any
        """取得済みの最新画像を返す。"""
        with self._frame_lock:
            if self._latest_frame is None:
                return None
            if copy_frame:
                return self._latest_frame.copy()
            return self._latest_frame

    def get_status(self):
        # type: () -> Dict[str, Any]
        """ローカル画像取得状態を返す。"""
        actual_width = None
        actual_height = None
        actual_fps = None

        with self._capture_lock:
            if self._capture is not None and self._capture.isOpened():
                actual_width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = float(self._capture.get(cv2.CAP_PROP_FPS))

        uptime_sec = 0.0
        if self._started_time_ns is not None:
            uptime_sec = (
                self._time_ns() - self._started_time_ns
            ) / 1000000000.0

        return {
            "running": self._running,
            "camera_id": self._camera_id,
            "capture_opened": self.is_connected(),
            "interval_sec": self._interval_sec,
            "requested_width": self._width,
            "requested_height": self._height,
            "requested_fps": self._fps,
            "actual_width": actual_width,
            "actual_height": actual_height,
            "actual_fps": actual_fps,
            "frame_id": self._frame_id,
            "read_error_count": self._read_error_count,
            "last_frame_time_ns": self._last_frame_time_ns,
            "uptime_sec": uptime_sec,
            "last_error": self._last_error,
        }

    def get_config(self):
        # type: () -> Dict[str, Any]
        """ローカルカメラ設定を返す。"""
        return {
            "camera_id": self._camera_id,
            "interval_sec": self._interval_sec,
            "width": self._width,
            "height": self._height,
            "fps": self._fps,
            "backend": self._backend,
            "reconnect_interval_sec": self._reconnect_interval_sec,
        }

    def set_camera_config(self, width=None, height=None, fps=None):
        # type: (Optional[int], Optional[int], Optional[float]) -> Dict[str, Any]
        """解像度およびFPSの要求値を更新する。"""
        self._width = self._optional_positive_int(width)
        self._height = self._optional_positive_int(height)
        self._fps = self._optional_positive_float(fps)

        with self._capture_lock:
            if self._capture is not None and self._capture.isOpened():
                self._apply_capture_settings_unlocked()

        return self.get_status()

    def set_camera_id(self, camera_id):
        # type: (int) -> bool
        """カメラIDを変更して再接続する。"""
        self.stop_capture()
        with self._capture_lock:
            self._release_capture_unlocked()
            self._camera_id = int(camera_id)
        return self.connect()

    def clear_error(self):
        # type: () -> bool
        """直近のエラー文字列を消去する。"""
        self._last_error = None
        return True

    def _capture_loop(self):
        # type: () -> None
        next_time = time.monotonic()

        try:
            while not self._stop_event.is_set():
                try:
                    self._read_frame()
                except Exception as exc:
                    self._set_error(str(exc))
                    self._stop_event.wait(self._reconnect_interval_sec)
                    with self._capture_lock:
                        self._open_capture_unlocked()

                next_time += self._interval_sec
                delay = next_time - time.monotonic()
                if delay > 0.0:
                    self._stop_event.wait(delay)
                else:
                    next_time = time.monotonic()
        finally:
            self._running = False

    def _read_frame(self):
        # type: () -> Any
        with self._capture_lock:
            if self._capture is None or not self._capture.isOpened():
                raise RuntimeError("Camera is not connected.")
            ok, frame = self._capture.read()

        if not ok or frame is None:
            self._read_error_count += 1
            with self._capture_lock:
                self._release_capture_unlocked()
            raise RuntimeError("Failed to read frame.")

        with self._frame_lock:
            self._latest_frame = frame.copy()
            self._frame_id += 1
            self._last_frame_time_ns = self._time_ns()

        self._last_error = None
        return frame

    def _open_capture_unlocked(self):
        # type: () -> bool
        self._release_capture_unlocked()

        try:
            if self._backend is None:
                capture = cv2.VideoCapture(self._camera_id)
            else:
                capture = cv2.VideoCapture(
                    self._camera_id,
                    int(self._backend),
                )
        except Exception as exc:
            self._set_error(
                "Failed to create VideoCapture: {}".format(exc)
            )
            return False

        self._capture = capture
        if not capture.isOpened():
            self._set_error(
                "Failed to open camera: {}".format(self._camera_id)
            )
            self._release_capture_unlocked()
            return False

        self._apply_capture_settings_unlocked()
        self._last_error = None
        self._log(
            "info",
            "camera connected: camera_id={}".format(self._camera_id),
        )
        return True

    def _apply_capture_settings_unlocked(self):
        # type: () -> None
        if self._capture is None:
            return
        if self._width is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        if self._height is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        if self._fps is not None:
            self._capture.set(cv2.CAP_PROP_FPS, self._fps)

    def _release_capture_unlocked(self):
        # type: () -> None
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
        self._capture = None

    def _set_error(self, message):
        # type: (str) -> None
        self._last_error = str(message)
        self._log("error", self._last_error)

    def _log(self, level, message):
        # type: (str, str) -> None
        if self._logger is None:
            return
        method = getattr(self._logger, level, None)
        if callable(method):
            method(message)

    @staticmethod
    def _optional_positive_int(value):
        # type: (Optional[int]) -> Optional[int]
        if value is None:
            return None
        converted = int(value)
        if converted <= 0:
            raise ValueError("value must be greater than zero.")
        return converted

    @staticmethod
    def _optional_positive_float(value):
        # type: (Optional[float]) -> Optional[float]
        if value is None:
            return None
        converted = float(value)
        if converted <= 0.0:
            raise ValueError("value must be greater than zero.")
        return converted

    @staticmethod
    def _time_ns():
        # type: () -> int
        return int(time.time() * 1000000000)

CAMERA_ID = 0
CAPTURE_INTERVAL_SEC = 0.03
CAMERA_WIDTH = None
CAMERA_HEIGHT = None
CAMERA_FPS = None
WINDOW_NAME = "ImageStreamDeviceClass"


def main():
    """ローカルカメラへ接続し、取得画像をOpenCVウィンドウへ表示する。"""
    image_stream = ImageStreamDeviceClass(
        camera_id=CAMERA_ID,
        interval_sec=CAPTURE_INTERVAL_SEC,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        fps=CAMERA_FPS,
    )

    if not image_stream.connect():
        raise RuntimeError(str(image_stream.get_status()))

    try:
        while True:
            frame = image_stream.get_latest_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break
    finally:
        image_stream.disconnect()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
