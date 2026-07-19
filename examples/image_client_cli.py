"""gRPC画像サーバー操作例。"""

import json
import os

import cv2

from image_server.server_grpc import ImageStreamClient


SERVER_IP = "127.0.0.1"
SERVER_PORT = 50051
TIMEOUT_SEC = 5.0
TOPIC_NAME = "camera.frame"

COMMAND = "status"

CAPTURE_OUTPUT = "capture.jpg"
SERVER_SNAPSHOT_PATH = "snapshot.jpg"

STREAM_INTERVAL_SEC = None
JPEG_QUALITY = None
STREAM_TOPIC_NAME = None

CAMERA_WIDTH = None
CAMERA_HEIGHT = None
CAMERA_FPS = None
CAMERA_ID = 0


def print_result(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main():
    client = ImageStreamClient(
        SERVER_IP,
        SERVER_PORT,
        TIMEOUT_SEC,
    )

    try:
        if COMMAND == "status":
            print_result(client.get_status())
        elif COMMAND == "config":
            print_result(client.get_config())
        elif COMMAND == "connect":
            print_result(client.connect())
        elif COMMAND == "disconnect":
            print_result(client.disconnect())
        elif COMMAND == "start":
            print_result(client.start_stream())
        elif COMMAND == "stop":
            print_result(client.stop_stream())
        elif COMMAND == "show":
            client.show_camera_frame_stream(topic=TOPIC_NAME)
        elif COMMAND == "capture":
            payload = client.capture_once()
            frame = client.decode_payload(payload)
            output = os.path.abspath(CAPTURE_OUTPUT)
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
        elif COMMAND == "stream-config":
            print_result(
                client.set_stream_config(
                    STREAM_INTERVAL_SEC,
                    JPEG_QUALITY,
                    STREAM_TOPIC_NAME,
                )
            )
        elif COMMAND == "camera-config":
            print_result(
                client.set_camera_config(
                    CAMERA_WIDTH,
                    CAMERA_HEIGHT,
                    CAMERA_FPS,
                )
            )
        elif COMMAND == "camera-id":
            print_result(client.set_camera_id(CAMERA_ID))
        elif COMMAND == "server-snapshot":
            print_result(client.save_snapshot(SERVER_SNAPSHOT_PATH))
        else:
            raise ValueError("Unsupported COMMAND: {}".format(COMMAND))
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
