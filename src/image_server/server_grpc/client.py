from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from grpc_frame.grpc_client import SyncGrpcClient


class ImageStreamClient(SyncGrpcClient):
    """grpc_frame 用の画像転送クライアントである。"""

    def __init__(
        self,
        server_ip: str,
        server_port: int,
        timeout_sec: float | None = None,
        logger: Any | None = None,
    ) -> None:
        super().__init__(
            server_ip=server_ip,
            server_port=server_port,
            timeout_sec=timeout_sec,
            logger=logger,
        )

    def show_camera_frame_stream(
        self,
        topic: str = "camera.frame",
        window_name: str = "camera.frame",
    ) -> None:
        """画像イベントを受信して OpenCV window に表示する。

        Args:
            topic: gRPC event topic である。
            window_name: 表示 window 名である。
        """
        self.start_stream()

        for payload in self.subscribe(topic=topic):
            image_bytes: bytes = payload["image"]
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            cv2.imshow(window_name, frame)
            key: int = cv2.waitKey(1)

            if key == 27:
                break

        self.stop_stream()
        cv2.destroyWindow(window_name)


def main() -> None:
    """接続確認用の最小クライアントである。"""
    client = ImageStreamClient(
        server_ip="127.0.0.1",
        server_port=50051,
    )

    print(client.get_status())
    client.show_camera_frame_stream()


if __name__ == "__main__":
    main()