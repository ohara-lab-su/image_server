"""grpc_frame用同期画像クライアント。"""

from typing import Any, Dict, Iterator, Optional, Tuple

import cv2
import numpy as np

from grpc_frame.grpc_client import SyncGrpcClient


class ImageStreamClient(SyncGrpcClient):
    """ImageStreamGrpcService用同期クライアント。"""

    def __init__(
        self,
        server_ip,
        server_port,
        timeout_sec=None,
        logger=None,
        max_message_mb=64,
    ):
        # type: (str, int, Optional[float], Optional[Any], int) -> None
        kwargs = {
            "server_ip": server_ip,
            "server_port": server_port,
            "timeout_sec": timeout_sec,
            "logger": logger,
        }
        try:
            SyncGrpcClient.__init__(
                self,
                max_message_mb=max_message_mb,
                **kwargs
            )
        except TypeError:
            SyncGrpcClient.__init__(self, **kwargs)

    @staticmethod
    def decode_payload(payload):
        # type: (Dict[str, Any]) -> Any
        image_bytes = payload.get("image")
        if not isinstance(
            image_bytes,
            (bytes, bytearray, memoryview),
        ):
            raise ValueError(
                "payload does not contain JPEG bytes."
            )

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8,
        )
        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR,
        )
        if frame is None:
            raise ValueError("Failed to decode JPEG payload.")
        return frame

    def iter_frames(self, topic="camera.frame"):
        # type: (str) -> Iterator[Tuple[Dict[str, Any], Any]]
        for payload in self.subscribe(topic=topic):
            try:
                frame = self.decode_payload(payload)
            except ValueError:
                continue
            yield payload, frame

    def show_camera_frame_stream(
        self,
        topic="camera.frame",
        window_name="camera.frame",
    ):
        # type: (str, str) -> None
        self.start_stream()
        try:
            for _payload, frame in self.iter_frames(topic=topic):
                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord("q"):
                    break
        finally:
            try:
                self.stop_stream()
            finally:
                cv2.destroyAllWindows()
