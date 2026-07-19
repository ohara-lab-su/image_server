"""grpc_frame画像サーバー起動例。"""

import time

from grpc_frame.event_bus import EventBus
from grpc_frame.grpc_server import create_grpc_server

from image_server.image_stream_ctrl import ImageStreamDeviceClass
from image_server.server_grpc import ImageStreamGrpcService


GRPC_HOST = "0.0.0.0"
GRPC_PORT = 50051
MAX_WORKERS = 10

CAMERA_ID = 0
CAPTURE_INTERVAL_SEC = 0.03
CAMERA_WIDTH = None
CAMERA_HEIGHT = None
CAMERA_FPS = None

TOPIC_NAME = "camera.frame"
PUBLISH_INTERVAL_SEC = 0.1
JPEG_QUALITY = 85
AUTO_START = True


def main():
    image_stream = ImageStreamDeviceClass(
        camera_id=CAMERA_ID,
        interval_sec=CAPTURE_INTERVAL_SEC,
        width=CAMERA_WIDTH,
        height=CAMERA_HEIGHT,
        fps=CAMERA_FPS,
    )
    grpc_service = ImageStreamGrpcService(
        image_stream=image_stream,
        topic_name=TOPIC_NAME,
        publish_interval_sec=PUBLISH_INTERVAL_SEC,
        jpeg_quality=JPEG_QUALITY,
    )
    event_bus = EventBus()
    server = create_grpc_server(
        ctrl_obj=grpc_service,
        event_bus=event_bus,
        max_workers=MAX_WORKERS,
        log_level="INFO",
    )

    bind_address = "{}:{}".format(GRPC_HOST, GRPC_PORT)
    if server.add_insecure_port(bind_address) == 0:
        raise RuntimeError(
            "Failed to bind gRPC server: {}".format(bind_address)
        )

    server.start()
    if not grpc_service.connect():
        server.stop(grace=0.0)
        raise RuntimeError(str(grpc_service.get_status()))

    if AUTO_START:
        if not grpc_service.start_stream():
            grpc_service.disconnect()
            server.stop(grace=0.0)
            raise RuntimeError(str(grpc_service.get_status()))

    print("Image server started: {}".format(bind_address))

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        grpc_service.disconnect()
        server.stop(grace=1.0)


if __name__ == "__main__":
    main()
