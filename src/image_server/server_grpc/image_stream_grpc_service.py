"""ImageStreamDeviceClassをgrpc_frameへ公開するサービス層。"""

import os
import threading
import time
from typing import Any, Dict, Optional

import cv2

from image_server.image_stream_ctrl import ImageStreamDeviceClass


class ImageStreamGrpcService:
    """ローカル画像制御をgRPC公開およびEventBus配信へ接続する。"""

    def __init__(
        self,
        image_stream=None,
        topic_name="camera.frame",
        publish_interval_sec=0.1,
        jpeg_quality=85,
        logger=None,
    ):
        # type: (Optional[ImageStreamDeviceClass], str, float, int, Optional[Any]) -> None
        self._logger = logger
        self._image_stream = image_stream
        if self._image_stream is None:
            self._image_stream = ImageStreamDeviceClass(logger=logger)

        self._topic_name = str(topic_name)
        self._publish_interval_sec = max(
            0.001,
            float(publish_interval_sec),
        )
        self._jpeg_quality = self._validate_jpeg_quality(jpeg_quality)
        self._event_bus = None
        self._thread = None  # type: Optional[threading.Thread]
        self._stop_event = threading.Event()
        self._running = False
        self._published_count = 0
        self._encode_error_count = 0
        self._last_publish_time_ns = None  # type: Optional[int]
        self._last_error = None  # type: Optional[str]

    def _set_event_bus(self, event_bus):
        # type: (Any) -> None
        """grpc_frameからEventBusを設定する。"""
        self._event_bus = event_bus

    def connect(self):
        # type: () -> bool
        """ローカル画像取得デバイスへ接続する。"""
        return self._image_stream.connect()

    def disconnect(self):
        # type: () -> bool
        """配信を停止し、ローカル画像取得デバイスを切断する。"""
        self.stop_stream()
        return self._image_stream.disconnect()

    def is_connected(self):
        # type: () -> bool
        return self._image_stream.is_connected()

    def start_stream(self):
        # type: () -> bool
        """EventBusへのJPEG画像配信を開始する。"""
        if self._event_bus is None:
            raise RuntimeError("EventBus is not set.")
        if not self._image_stream.connect():
            return False
        if self._running:
            return True

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._publish_loop,
            name="ImageStreamGrpcService",
        )
        self._thread.daemon = True
        self._thread.start()
        return True

    def stop_stream(self):
        # type: () -> bool
        """EventBusへの画像配信を停止する。"""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            if thread is not threading.current_thread():
                thread.join(3.0)
        self._thread = None
        self._running = False
        return True

    def capture_once(self):
        # type: () -> Dict[str, Any]
        """最新画像をJPEGペイロードとして返す。"""
        frame = self._image_stream.get_latest_frame()
        if frame is None:
            frame = self._image_stream.read_once()
        return self._encode_frame(frame)

    def publish_once(self):
        # type: () -> bool
        """最新画像をEventBusへ1回配信する。"""
        if self._event_bus is None:
            raise RuntimeError("EventBus is not set.")

        payload = self.capture_once()
        self._event_bus.publish(
            self._topic_name,
            payload,
            source="image_stream_grpc_service",
        )
        self._published_count += 1
        self._last_publish_time_ns = self._time_ns()
        return True

    def save_snapshot(self, file_path):
        # type: (str) -> Dict[str, Any]
        """サーバー側ファイルへ最新画像を保存する。"""
        if not file_path:
            raise ValueError("file_path is required.")

        frame = self._image_stream.get_latest_frame()
        if frame is None:
            frame = self._image_stream.read_once()

        directory = os.path.dirname(os.path.abspath(file_path))
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)

        if not cv2.imwrite(file_path, frame):
            raise RuntimeError(
                "Failed to save snapshot: {}".format(file_path)
            )

        return {
            "file_path": os.path.abspath(file_path),
            "width": int(frame.shape[1]),
            "height": int(frame.shape[0]),
            "timestamp_ns": self._time_ns(),
        }

    def get_status(self):
        # type: () -> Dict[str, Any]
        """ローカル取得状態とgRPC配信状態を統合して返す。"""
        status = self._image_stream.get_status()
        status.update(
            {
                "stream_running": self._running,
                "topic_name": self._topic_name,
                "publish_interval_sec": self._publish_interval_sec,
                "jpeg_quality": self._jpeg_quality,
                "published_count": self._published_count,
                "encode_error_count": self._encode_error_count,
                "last_publish_time_ns": self._last_publish_time_ns,
                "grpc_last_error": self._last_error,
            }
        )
        return status

    def get_config(self):
        # type: () -> Dict[str, Any]
        """ローカル設定と配信設定を返す。"""
        return {
            "camera": self._image_stream.get_config(),
            "stream": {
                "topic_name": self._topic_name,
                "publish_interval_sec": self._publish_interval_sec,
                "jpeg_quality": self._jpeg_quality,
            },
        }

    def set_stream_config(
        self,
        interval_sec=None,
        jpeg_quality=None,
        topic_name=None,
    ):
        # type: (Optional[float], Optional[int], Optional[str]) -> Dict[str, Any]
        """gRPC配信設定を変更する。"""
        if interval_sec is not None:
            self._publish_interval_sec = max(
                0.001,
                float(interval_sec),
            )
        if jpeg_quality is not None:
            self._jpeg_quality = self._validate_jpeg_quality(
                jpeg_quality
            )
        if topic_name is not None:
            if not str(topic_name).strip():
                raise ValueError("topic_name must not be empty.")
            self._topic_name = str(topic_name)
        return self.get_config()

    def set_camera_config(self, width=None, height=None, fps=None):
        # type: (Optional[int], Optional[int], Optional[float]) -> Dict[str, Any]
        return self._image_stream.set_camera_config(
            width,
            height,
            fps,
        )

    def set_camera_id(self, camera_id):
        # type: (int) -> bool
        return self._image_stream.set_camera_id(camera_id)

    def clear_error(self):
        # type: () -> bool
        self._last_error = None
        self._image_stream.clear_error()
        return True

    def _publish_loop(self):
        # type: () -> None
        next_time = time.monotonic()

        try:
            while not self._stop_event.is_set():
                try:
                    self.publish_once()
                    self._last_error = None
                except Exception as exc:
                    self._last_error = str(exc)

                next_time += self._publish_interval_sec
                delay = next_time - time.monotonic()
                if delay > 0.0:
                    self._stop_event.wait(delay)
                else:
                    next_time = time.monotonic()
        finally:
            self._running = False

    def _encode_frame(self, frame):
        # type: (Any) -> Dict[str, Any]
        params = [
            int(cv2.IMWRITE_JPEG_QUALITY),
            self._jpeg_quality,
        ]
        ok, encoded = cv2.imencode(".jpg", frame, params)
        if not ok:
            self._encode_error_count += 1
            raise RuntimeError("Failed to encode frame.")

        return {
            "frame_id": self._image_stream.get_status().get("frame_id"),
            "timestamp_ns": self._time_ns(),
            "encoding": "jpg",
            "width": int(frame.shape[1]),
            "height": int(frame.shape[0]),
            "image": encoded.tobytes(),
        }

    @staticmethod
    def _validate_jpeg_quality(value):
        # type: (int) -> int
        quality = int(value)
        if quality < 1 or quality > 100:
            raise ValueError(
                "jpeg_quality must be between 1 and 100."
            )
        return quality

    @staticmethod
    def _time_ns():
        # type: () -> int
        return int(time.time() * 1000000000)
