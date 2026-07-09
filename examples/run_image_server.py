from __future__ import annotations

import time

from grpc_frame.event_bus import EventBus
from grpc_frame.grpc_server import create_grpc_server

from power_level_monitor.image_stream_ctrl import ImageStreamDeviceClass


HOST = "0.0.0.0"
PORT = 50051


def main() -> None:
    """grpc_frame による画像転送サーバーを起動する。"""
    event_bus = EventBus()

    device = ImageStreamDeviceClass(
        camera_id=0,
        topic_name="camera.frame",
        interval_sec=0.1,
        jpeg_quality=85,
    )

    server = create_grpc_server(
        ctrl_obj=device,
        event_bus=event_bus,
        max_workers=10,
        log_level="INFO",
    )

    server.add_insecure_port(f"{HOST}:{PORT}")
    server.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        device.disconnect()
        server.stop(grace=1.0)


if __name__ == "__main__":
    main()