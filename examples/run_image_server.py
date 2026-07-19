"""grpc_frame画像サーバー起動例。"""

import argparse
import time

from grpc_frame.event_bus import EventBus
from grpc_frame.grpc_server import create_grpc_server

from image_server.image_stream_ctrl import ImageStreamDeviceClass
from image_server.server_grpc import ImageStreamGrpcService


def build_parser():
    parser = argparse.ArgumentParser(
        description="grpc_frame generic image server"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--topic", default="camera.frame")
    parser.add_argument("--capture-interval", type=float, default=0.03)
    parser.add_argument("--publish-interval", type=float, default=0.1)
    parser.add_argument("--jpeg-quality", type=int, default=85)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--max-workers", type=int, default=10)
    parser.add_argument("--auto-start", action="store_true")
    return parser


def main():
    args = build_parser().parse_args()

    image_stream = ImageStreamDeviceClass(
        camera_id=args.camera_id,
        interval_sec=args.capture_interval,
        width=args.width,
        height=args.height,
        fps=args.fps,
    )
    grpc_service = ImageStreamGrpcService(
        image_stream=image_stream,
        topic_name=args.topic,
        publish_interval_sec=args.publish_interval,
        jpeg_quality=args.jpeg_quality,
    )
    event_bus = EventBus()
    server = create_grpc_server(
        ctrl_obj=grpc_service,
        event_bus=event_bus,
        max_workers=args.max_workers,
        log_level="INFO",
    )

    bind_address = "{}:{}".format(args.host, args.port)
    if server.add_insecure_port(bind_address) == 0:
        raise RuntimeError(
            "Failed to bind gRPC server: {}".format(bind_address)
        )

    server.start()
    if not grpc_service.connect():
        server.stop(grace=0.0)
        raise RuntimeError(str(grpc_service.get_status()))

    if args.auto_start:
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
