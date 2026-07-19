"""gRPCを使用しないローカルカメラ表示例。"""

import time

import cv2

from image_server import ImageStreamDeviceClass


def main():
    image_stream = ImageStreamDeviceClass(camera_id=0)
    if not image_stream.connect():
        raise RuntimeError(str(image_stream.get_status()))

    try:
        while True:
            frame = image_stream.get_latest_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            cv2.imshow("Local Image Viewer", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break
    finally:
        image_stream.disconnect()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
