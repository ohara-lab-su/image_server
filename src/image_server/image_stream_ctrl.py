from __future__ import annotations

import threading
import time
from typing import Any

import cv2


class ImageStreamDeviceClass:
    """画像転送用のローカル DeviceClass である。

    grpc_frame の create_grpc_server に ctrl_obj として渡す実体である。
    gRPC の Control RPC では public メソッドが公開される。
    EventBus は grpc_frame 側から _set_event_bus() で注入される。
    """

    def __init__(
        self,
        camera_id: int = 0,
        topic_name: str = "camera.frame",
        interval_sec: float = 0.1,
        jpeg_quality: int = 85,
        logger: Any | None = None,
    ) -> None:
        self._logger: Any | None = logger
        self._camera_id: int = int(camera_id)
        self._topic_name: str = str(topic_name)
        self._interval_sec: float = float(interval_sec)
        self._jpeg_quality: int = int(jpeg_quality)

        self._event_bus: Any | None = None
        self._capture: cv2.VideoCapture | None = None
        self._thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()

        self._running: bool = False
        self._frame_id: int = 0
        self._last_error: str | None = None
        self._last_publish_time_ns: int | None = None

    def _set_event_bus(
        self,
        event_bus: Any,
    ) -> None:
        """grpc_frame から EventBus を受け取る。

        Args:
            event_bus: grpc_frame.event_bus.EventBus 互換オブジェクトである。
        """
        self._event_bus = event_bus

    def connect(self) -> bool:
        """カメラを開く。

        Returns:
            bool: 接続処理の結果である。
        """
        if self._capture is not None:
            if self._capture.isOpened():
                return True

        self._capture = cv2.VideoCapture(self._camera_id)

        if not self._capture.isOpened():
            self._last_error = "Failed to open camera."
            return False

        self._last_error = None
        return True

    def disconnect(self) -> bool:
        """画像転送を停止し、カメラを閉じる。

        Returns:
            bool: 切断処理の結果である。
        """
        self.stop_stream()

        if self._capture is not None:
            self._capture.release()

        self._capture = None
        return True

    def start_stream(self) -> bool:
        """画像イベント配信を開始する。

        Returns:
            bool: 開始処理の結果である。
        """
        if self._event_bus is None:
            raise RuntimeError("EventBus is not set.")

        connected: bool = self.connect()
        if not connected:
            return False

        if self._running:
            return True

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._stream_loop,
            name="ImageStreamDeviceClass",
            daemon=True,
        )
        self._running = True
        self._thread.start()
        return True

    def stop_stream(self) -> bool:
        """画像イベント配信を停止する。

        Returns:
            bool: 停止処理の結果である。
        """
        self._stop_event.set()

        if self._thread is not None:
            if self._thread.is_alive():
                self._thread.join(timeout=2.0)

        self._thread = None
        self._running = False
        return True

    def get_status(self) -> dict[str, Any]:
        """画像転送 DeviceClass の状態を取得する。

        Returns:
            dict[str, Any]: 状態である。
        """
        capture_opened: bool = False
        if self._capture is not None:
            capture_opened = bool(self._capture.isOpened())

        return {
            "running": self._running,
            "camera_id": self._camera_id,
            "capture_opened": capture_opened,
            "topic_name": self._topic_name,
            "interval_sec": self._interval_sec,
            "jpeg_quality": self._jpeg_quality,
            "frame_id": self._frame_id,
            "last_publish_time_ns": self._last_publish_time_ns,
            "last_error": self._last_error,
        }

    def capture_once(self) -> dict[str, Any]:
        """画像を1枚取得し、JPEG bytes を返す。

        Returns:
            dict[str, Any]: JPEG 画像 payload である。
        """
        connected: bool = self.connect()
        if not connected:
            raise RuntimeError(str(self._last_error))

        if self._capture is None:
            raise RuntimeError("Camera is not connected.")

        ok, frame = self._capture.read()
        if not ok:
            self._last_error = "Failed to read frame."
            raise RuntimeError(self._last_error)

        payload: dict[str, Any] = self._encode_frame(frame)
        return payload

    def publish_once(self) -> bool:
        """画像を1枚取得し、EventBus へ publish する。

        Returns:
            bool: publish 処理の結果である。
        """
        if self._event_bus is None:
            raise RuntimeError("EventBus is not set.")

        payload: dict[str, Any] = self.capture_once()
        self._event_bus.publish(
            self._topic_name,
            payload,
            source="image_stream_device",
        )
        self._last_publish_time_ns = time.time_ns()
        return True

    def _stream_loop(self) -> None:
        """画像を周期的に publish する内部ループである。"""
        while not self._stop_event.is_set():
            try:
                self.publish_once()
            except Exception as exc:
                self._last_error = str(exc)

            time.sleep(self._interval_sec)

        self._running = False

    def _encode_frame(
        self,
        frame: Any,
    ) -> dict[str, Any]:
        """OpenCV frame を JPEG payload に変換する。

        Args:
            frame: OpenCV BGR 画像である。

        Returns:
            dict[str, Any]: EventBus に載せる payload である。
        """
        encode_params: list[int] = [
            int(cv2.IMWRITE_JPEG_QUALITY),
            self._jpeg_quality,
        ]

        ok, encoded = cv2.imencode(
            ".jpg",
            frame,
            encode_params,
        )

        if not ok:
            raise RuntimeError("Failed to encode frame.")

        self._frame_id = self._frame_id + 1

        height: int = int(frame.shape[0])
        width: int = int(frame.shape[1])

        return {
            "frame_id": self._frame_id,
            "timestamp_ns": time.time_ns(),
            "encoding": "jpg",
            "width": width,
            "height": height,
            "image": encoded.tobytes(),
        }