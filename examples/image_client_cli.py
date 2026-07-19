"""gRPC画像サーバー操作CLI。"""

import argparse
import json
import os

import cv2

from image_server.server_grpc import ImageStreamClient


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generic image server CLI"
    )
    parser.add_argument("--server-ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--topic", default="camera.frame")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status")
    sub.add_parser("config")
    sub.add_parser("connect")
    sub.add_parser("disconnect")
    sub.add_parser("start")
    sub.add_parser("stop")
    sub.add_parser("show")

    capture = sub.add_parser("capture")
    capture.add_argument("output")

    stream = sub.add_parser("stream-config")
    stream.add_argument("--interval", type=float)
    stream.add_argument("--jpeg-quality", type=int)
    stream.add_argument("--topic-name")

    camera = sub.add_parser("camera-config")
    camera.add_argument("--width", type=int)
    camera.add_argument("--height", type=int)
    camera.add_argument("--fps", type=float)

    camera_id = sub.add_parser("camera-id")
    camera_id.add_argument("value", type=int)

    snapshot = sub.add_parser("server-snapshot")
    snapshot.add_argument("path")
    return parser


def print_result(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command is None:
        parser.error("command is required")

    client = ImageStreamClient(
        args.server_ip,
        args.port,
        args.timeout,
    )

    try:
        if args.command == "status":
            print_result(client.get_status())
        elif args.command == "config":
            print_result(client.get_config())
        elif args.command == "connect":
            print_result(client.connect())
        elif args.command == "disconnect":
            print_result(client.disconnect())
        elif args.command == "start":
            print_result(client.start_stream())
        elif args.command == "stop":
            print_result(client.stop_stream())
        elif args.command == "show":
            client.show_camera_frame_stream(topic=args.topic)
        elif args.command == "capture":
            payload = client.capture_once()
            frame = client.decode_payload(payload)
            output = os.path.abspath(args.output)
            directory = os.path.dirname(output)
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)
            if not cv2.imwrite(output, frame):
                raise RuntimeError(
                    "Failed to save image: {}".format(output)
                )
            print_result(
                {
                    "output": output,
                    "frame_id": payload.get("frame_id"),
                }
            )
        elif args.command == "stream-config":
            print_result(
                client.set_stream_config(
                    args.interval,
                    args.jpeg_quality,
                    args.topic_name,
                )
            )
        elif args.command == "camera-config":
            print_result(
                client.set_camera_config(
                    args.width,
                    args.height,
                    args.fps,
                )
            )
        elif args.command == "camera-id":
            print_result(client.set_camera_id(args.value))
        elif args.command == "server-snapshot":
            print_result(client.save_snapshot(args.path))
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
